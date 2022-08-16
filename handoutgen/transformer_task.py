from libcst import (
    parse_statement, parse_expression,
    Comment, Name, EmptyLine, Assign, SimpleStatementLine, AssignTarget, Call,
    Attribute, Arg, IndentedBlock, BaseSuite, Expr, Module)
from libcst import matchers as m

from handoutgen import keywords
from handoutgen.checkers import assert_not_contain_keywords
from handoutgen.metatraversers import MetaTransformer
from handoutgen.metamodule import MetaModule


class CodeRemover(MetaTransformer):
    def __init__(self, module: MetaModule) -> None:
        super().__init__(module)
        self.keepset = set()

    def leave_IndentedBlock(self, original_node: "IndentedBlock",
                            updated_node: "IndentedBlock") -> "BaseSuite":

        if not self.parent(original_node) in self.task_funcs:
            return updated_node

        def keyword_in_close_children(node):
            def haskeyword(node):
                return any(self.qname_matches(node, kw) for kw in keywords)

            return any(map(haskeyword, self.children(node, limit=2)))

        newbody = []
        for orig_line, upd_line in zip(original_node.body,
                                       updated_node.body, strict=True):
            if m.matches(orig_line, m.SimpleStatementLine([m.Return()])):
                newbody.append(upd_line)
            elif keyword_in_close_children(orig_line):
                newbody.append(upd_line)
            else:
                assert_not_contain_keywords(self, orig_line)
        return updated_node.with_changes(body=newbody)


class SolutionBeforeReturnAdder(MetaTransformer):
    def leave_IndentedBlock(self, original_node: "IndentedBlock",
                            updated_node: "IndentedBlock") -> "BaseSuite":
        """Add stuff before return"""
        newbody = []
        for line in updated_node.body:
            is_return = m.matches(line, m.SimpleStatementLine([m.Return()]))
            if is_return and (taskf := self.parent_task(original_node)):
                qname = self.get_qname(taskf)
                name = parse_expression(f"{self.path.stem}_solu.{qname}")
                call = Call(func=name,
                            args=[Arg(p.name) for p in taskf.params.params])

                if (retarg := line.body[0].value) is not None:
                    body = [Assign(targets=[AssignTarget(retarg)], value=call)]
                else:
                    body = [Expr(call)]

                callline = SimpleStatementLine(
                    leading_lines=[EmptyLine(),
                                   EmptyLine(comment=Comment(
                                       "# TODO replace this with own code"))],
                    body=body)

                newbody.append(callline)
            newbody.append(line)

        return updated_node.with_changes(body=newbody)


class ImportSolution(MetaTransformer):
    def leave_Module(self, original_node: "Module", updated_node: "Module"
                     ) -> "Module":
        idx = next((i for i, n in enumerate(updated_node.body)
                   if not m.findall(n, m.Import() | m.ImportFrom())), 0)
        frompart = '.'.join(['solution', *self.path_rel2code.parts[:-1]])
        fname = self.path.stem
        newline = parse_statement(
            f'from {frompart} import {fname} as {fname}_solu')
        newbody = [*updated_node.body[:idx], newline, *updated_node.body[idx:]]
        return updated_node.with_changes(body=newbody)
