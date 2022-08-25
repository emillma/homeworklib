from libcst import matchers as m
from libcst import (parse_statement, parse_expression,
                    Comment, EmptyLine, Assign, SimpleStatementLine, CSTNode,
                    AssignTarget, Call, Arg, IndentedBlock, Expr, Module)

from hwlib.keywords import keywordset
from ..checkers import assert_not_contain_keywords
from ..utils import MetaTransformer, MetaModule
from typing import Optional


class CodeRemover(MetaTransformer):
    def __init__(self, module: MetaModule) -> None:
        super().__init__(module)
        self.skipset = set()

    def on_visit(self, node: "CSTNode") -> bool:
        if node in self.skipset:
            return False
        else:
            return super().on_visit(node)

    def visit_IndentedBlock(self, node: "IndentedBlock") -> Optional[bool]:
        if not self.parent(node) in self.task_funcs:
            return

        def keyword_in_close_children(node):
            def haskeyword(node):
                return any(self.qname_matches(node, kw) for kw in keywordset)
            return any(map(haskeyword, self.children(node, limit=2)))

        for orig_line in node.body:
            if m.matches(orig_line, m.SimpleStatementLine([m.Return()])):
                continue
            elif keyword_in_close_children(orig_line):
                continue
            else:
                self.skipset.add(orig_line)
                assert_not_contain_keywords(self, orig_line)

    def leave_IndentedBlock(self, original_node: IndentedBlock,
                            updated_node: IndentedBlock) -> IndentedBlock:

        if not self.parent(original_node) in self.task_funcs:
            return updated_node

        newbody = []
        for upd_line in updated_node.body:
            if upd_line not in self.skipset:
                newbody.append(upd_line)
        return updated_node.with_changes(body=newbody)


class SolutionBeforeReturnAdder(MetaTransformer):
    def leave_IndentedBlock(self, original_node: IndentedBlock,
                            updated_node: IndentedBlock) -> IndentedBlock:
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
    def leave_Module(self, original_node: Module, updated_node: Module
                     ) -> Module:
        idx = next((i for i, n in enumerate(updated_node.body)
                   if not m.findall(n, m.Import() | m.ImportFrom())), 0)
        frompart = '.'.join(['solution', *self.path_rel2code.parts[:-1]])
        fname = self.path.stem
        newline = parse_statement(
            f'from {frompart} import {fname} as {fname}_solu')
        newbody = [*updated_node.body[:idx], newline, *updated_node.body[idx:]]
        return updated_node.with_changes(body=newbody)
