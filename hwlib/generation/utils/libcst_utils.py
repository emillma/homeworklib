from libcst import (CSTVisitor, CSTTransformer, RemovalSentinel,
                    FunctionDef, BaseExpression, Call, Tuple, Element,
                    BaseStatement, SimpleStatementLine, Assign,
                    TrailingWhitespace, Comment, Name, Attribute,
                    CSTNode, Module, CSTNodeT, FlattenSentinel)

from libcst import matchers as m

from typing import Iterable, Optional, Union
import re
from functools import reduce


def children(node: CSTNode, limit: Optional[int] = 1) -> Iterable[CSTNode]:
    if limit == 1:
        yield from node.children
    else:
        for c in node.children:
            yield from children(c, limit=None if limit is None else limit-1)
            yield c


def args_as_tuple(node: Call) -> BaseExpression:
    """ g = foo(a, b, c) -> g = a, b, c"""
    if len(node.args) == 1:
        return node.args[0].value
    elif not node.args:
        return Tuple([])
    else:
        return Tuple([Element(ag.value)for ag in node.args], [], [])


def params_as_tuple(func: FunctionDef, as_iterable=False) -> BaseExpression:
    """ g = foo(a, b, c) -> g = a, b, c"""
    if len(func.params.params) == 1:
        return func.params.params[0].name
    elif not func.params.params:
        return Tuple([])
    else:
        return Tuple([Element(pa.name) for pa in func.params.params], [], [])


def as_attribute(text) -> Attribute:
    if isinstance(text, str):
        return reduce(Attribute, map(Name, text.split('.')))
    else:
        return reduce(Attribute, map(Name, text))


def elem_iter(node: Tuple) -> Iterable[BaseExpression]:
    return map(lambda x: x.value, node.elements)


def add_leading_lines(node: BaseStatement, fromnode: BaseStatement
                      ) -> BaseStatement:
    return node.with_changes(
        leading_lines=(*fromnode.leading_lines, *node.leading_lines))


def add_comment(node: SimpleStatementLine, comment) -> SimpleStatementLine:
    oldcom = getattr(node.trailing_whitespace.comment, 'value', None)
    oldcom = f",{oldcom[1:]}" if oldcom else ''
    return node.with_changes(
        trailing_whitespace=TrailingWhitespace(
            comment=Comment(f"# {comment}{oldcom}")
        )
    )


def get_transformer(func):
    class SimpleTransformer(CSTTransformer):
        ...


class NoneAssigner(CSTTransformer):
    def leave_Assign(self, _: Assign, upd_assign: Assign
                     ) -> Assign:
        return upd_assign.with_changes(value=Name('None'))


class NameReplacer(CSTTransformer):
    def __init__(self, pattern: Union[str, Name],
                 repl: Union[str, Name],
                 full=True):
        super().__init__()

        pat = pattern.value if m.matches(pattern, m.Name()) else pattern
        self.pattern = f"^{pat}$" if full else pat
        self.repl = repl.value if m.matches(repl, m.Name()) else repl

    def leave_Name(self, _: Name, upd_name: Name) -> "Name":
        newval = re.sub(self.pattern, self.repl, upd_name.value)
        return upd_name.with_changes(value=newval)
