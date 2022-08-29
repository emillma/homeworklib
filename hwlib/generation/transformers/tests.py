from typing import Union
from dataclasses import dataclass, field, fields

from libcst import matchers as m
from libcst import (FlattenSentinel, parse_expression, ClassDef, Return,
                    CSTTransformer, BaseExpression, Name, SimpleString, If,
                    Expr, RemovalSentinel, Call, SimpleStatementLine)

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
            tr.TESTCLASS = Name(f"Test_{qname.replace('.','__')}")
            tr.FUNCTION = parse_expression(qname)
            tr.FUNC_ID = SimpleString(f"'{self.id_str(func)}'")

            if anyarg := func.params.params:
                args = params_as_tuple(func)
                tr.ARGS = args.visit(NameReplacer('self', '_self'))
                tr.ARGS_SOLU = tr.ARGS.visit(NameReplacer(r'(.+)', r'\1_s'))
                tc = tc.visit(self.if_repl('ARGBLOCK', True))
                tc = tc.visit(self.comp_repl('ARG', tr.ARGS, tr.ARGS_SOLU))
            else:
                tc = tc.visit(self.if_repl('ARGBLOCK', False))

            return_node: Return = next(iter(m.findall(func, m.Return())), None)
            if anyret := getattr(return_node, 'value', None):
                tr.RETS = anyret
                tr.RETS_SOLU = tr.RETS.visit(NameReplacer(r'(.+)', r'\1_s'))
                tc = tc.visit(self.if_repl('RETBLOCK', True))
                tc = tc.visit(self.comp_repl('RET', tr.RETS, tr.RETS_SOLU))
            else:
                tc = tc.visit(self.if_repl('RETBLOCK', False))

            for field in fields(tr):
                if value := getattr(tr, field.name):
                    tc = m.replace(tc, Name(field.name), value)
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
                if m.matches(original_node.test, toremove):
                    return RemovalSentinel.REMOVE
                return updated_node
        return IfCollapser()

    @staticmethod
    def comp_repl(key: str, names: str, names_s: str):
        """replaces the compare(name, name_s)"""

        key_s = f'{key}_SOLU'

        class ComparreTrans(CSTTransformer):

            def leave_Expr(self, orig_expr: Expr, upd_expr: Expr) -> Call:

                if not m.matches(orig_expr.value,
                                 m.Call(m.Name('compare'),
                                        [m.Arg(m.Name(key)),
                                         m.Arg(m.Name(key_s))])):
                    return upd_expr

                if m.matches(names, m.Name()):
                    iterator = [(names, names_s)]
                elif m.matches(names, m.Tuple()):
                    iterator = zip(*map(elem_iter, [names, names_s]))

                upd_expr = FlattenSentinel([upd_expr
                                            .visit(NameReplacer(key, arg))
                                            .visit(NameReplacer(key_s, arg_s))
                                            for (arg, arg_s) in iterator])
                return upd_expr
        return ComparreTrans()


class PASSWORDReplacer(MetaTransformer, Passworddiffer):

    def leave_Name(self, _: Name, upd_name: Name) -> "Name":
        if m.matches(upd_name, m.Name('PASSWORD')):
            if isinstance(self.password, str):
                upd_name = SimpleString(f"'{self.password}'")
            else:
                return Name('None')
        return upd_name
