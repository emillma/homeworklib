from libcst import Return, CSTNode, SimpleStatementLine, FunctionDef
from libcst import matchers as m

from hwlib.keywords import keywordset
from .utils import MetaModule, MetaVisitor, HyperTraverser


def assert_not_contain_keywords(module: MetaModule,
                                node: CSTNode,
                                ):
    """Checks that there are no handoutgen keywords in node that"""

    for kayword in keywordset:
        nodes = m.findall(node, module.qname_matcher_prov(kayword))
        keyword_node = next(iter(nodes), None)
        assert not keyword_node, ("Keyword has no effect\n"
                                  f"{module.pos_str(keyword_node)}")


class CheckReturns(MetaVisitor):
    def __init__(self, module: MetaModule) -> None:
        super().__init__(module)
        self.previous_retval = dict()

    def visit_Return(self, node: "Return") -> None:
        if not self.parent_task(node):
            return

        valid_return = m.Name() | m.Tuple([m.ZeroOrMore(m.Element(m.Name()))])
        msg = "Wrong retval", self.pos_str(node)
        assert node.value is None or m.matches(node.value, valid_return), msg

        if self.previous_retval.get(node, None) is None:
            self.previous_retval[node] = node.value
        else:
            msg = "Multiple different retvals", self.pos_str(node)
            assert m.matches(self.previous_retval[node], node.value), msg

        parent_line: SimpleStatementLine = self.parent_matching(
            node, m.SimpleStatementLine())
        msg = "Semicolon in return line", self.pos_str(node)
        assert len(parent_line.body) == 1, msg


class CheckFuncDefHasParams(MetaVisitor):
    def visit_FunctionDef(self, node: "FunctionDef") -> None:
        if not node in self.task_funcs:
            return
        msg = "Function has no arguments", self.pos_str(node)
        assert m.findall(node, m.Param()), msg


def pre_check_mmodule(module: MetaModule) -> None:
    trav = HyperTraverser.from_factories([
        CheckReturns,
        CheckFuncDefHasParams,
    ],
        module=module)
    module.visit(trav)
