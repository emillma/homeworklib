from typing import Union
from dataclasses import dataclass, field, fields

from libcst import matchers as m
from libcst import (FlattenSentinel, parse_expression, ClassDef, Return,
                    CSTTransformer, BaseExpression, Name, SimpleString, If,
                    Assert, RemovalSentinel)

from ..utils import (MetaTransformer, MetaModule,
                     params_as_tuple, NameReplacer, elem_iter)
from .differs import Passworddiffer


class TestTransformer(MetaTransformer):
    test: MetaModule

    def __init__(self, module: MetaModule, test: MetaModule):
        super().__init__(module)
        self.test = test


class ImportNameReplacer(TestTransformer):
    def leave_Name(self, original_node: "Name", updated_node: "Name"
                   ) -> "BaseExpression":
        def matches(value):
            return m.matches(updated_node, m.Name(value))

        if matches('MODULE'):
            return Name(self.path.stem)
        if matches('MODULEFULL'):
            return parse_expression(self.module_str)
        elif matches('CODEDIRSTR'):
            return SimpleString(f"'{self.path_rel2proj.parts[0]}'")
        else:
            return updated_node


@dataclass()
class Toreplace:
    TESTCLASS: BaseExpression = field(default=None)
    FUNCTION: BaseExpression = field(default=None)
    FUNC_ID: BaseExpression = field(default=None)
    ARGS: BaseExpression = field(default=None)
    ARGS_SOLU: BaseExpression = field(default=None)
    RETS: BaseExpression = field(default=None)
    RETS_SOLU: BaseExpression = field(default=None)


class TestFuncsCreator(TestTransformer):
    def leave_ClassDef(self, original_node: "ClassDef", updated_node: "ClassDef"
                       ) -> FlattenSentinel["ClassDef"]:
        if not m.matches(original_node.name, Name('TESTCLASS')):
            raise Exception
        output = []

        for func in self.task_funcs:
            tc = updated_node.deep_clone()
            tr = Toreplace()

            qname = self.get_qname(func)
            tr.TESTCLASS = Name(f"Test_{qname.replace('.','_')}")
            tr.FUNCTION = Name(qname)
            tr.FUNC_ID = SimpleString(f"'{self.id_str(func)}'")

            if anyarg := func.params.params:
                tr.ARGS = params_as_tuple(func)
                tr.ARGS_SOLU = tr.ARGS.visit(NameReplacer(r'(.+)', r'\1_s'))
                tc = tc.visit(self.if_repl('ARGBLOCK', True))
                tc = tc.visit(self.assert_repl('ARG', tr.ARGS, tr.ARGS_SOLU))
            else:
                tc = tc.visit(self.if_repl('ARGBLOCK', False))

            return_node: Return = next(iter(m.findall(func, m.Return())), None)
            if anyret := getattr(return_node, 'value', None):
                tr.RETS = return_node.value
                tr.RETS_SOLU = tr.RETS.visit(NameReplacer(r'(.+)', r'\1_s'))
                tc = tc.visit(self.if_repl('RETBLOCK', True))
                tc = tc.visit(self.assert_repl('RET', tr.RETS, tr.RETS_SOLU))
            else:
                tc = tc.visit(self.if_repl('RETBLOCK', False))

            for f in fields(tr):
                if value := getattr(tr, f.name):
                    tc = m.replace(tc, Name(f.name), value)
            output.append(tc)

        return FlattenSentinel(output)

    @staticmethod
    def if_repl(pattern, keep):
        tocollaps = m.Name(pattern if keep else 'NO'+pattern)
        toremove = m.Name(pattern if not keep else 'NO'+pattern)

        class IfCollapser(CSTTransformer):
            def leave_If(self, original_node: "If", updated_node: "If"):
                if m.matches(original_node.test, tocollaps):
                    return FlattenSentinel(updated_node.body.body)
                elif m.matches(original_node.test, toremove):
                    return RemovalSentinel.REMOVE
                return updated_node
        return IfCollapser()

    @staticmethod
    def assert_repl(key, names, names_s):
        """replaces the assert compare(name, name_s)"""

        class AssertCompare(CSTTransformer):
            def leave_Assert(self, orig_assert: Assert, upd_assert: Assert
                             ) -> Union[Assert, FlattenSentinel[Assert],
                                        RemovalSentinel]:
                if not m.findall(orig_assert, m.Name(key)):
                    return upd_assert
                key_s = f'{key}_SOLU'
                upd = upd_assert
                if m.matches(names, m.Name()):
                    upd = m.replace(upd, m.Name(key), names)
                    upd = m.replace(upd, m.Name(key_s), names_s)

                elif m.matches(names, m.Tuple()):
                    iterator = zip(*map(elem_iter, [names, names_s]))
                    upd = FlattenSentinel([upd
                                           .visit(NameReplacer(key, arg))
                                           .visit(NameReplacer(key_s, arg_s))
                                           for (arg, arg_s) in iterator])
                return upd
        return AssertCompare()


class PASSWORDReplacer(MetaTransformer, Passworddiffer):

    def leave_Name(self, _: Name, upd_name: Name) -> "Name":
        if m.matches(upd_name, m.Name('PASSWORD')):
            if isinstance(self.password, str):
                upd_name = SimpleString(f"'{self.password}'")
            else:
                return Name('None')
        return upd_name
