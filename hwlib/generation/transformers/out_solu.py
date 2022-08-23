from typing import Union

from libcst import matchers as m
from libcst import (ImportFrom, Name, BaseSmallStatement, BaseStatement,
                    SimpleStatementLine, Call, Import, FlattenSentinel,
                    RemovalSentinel, If, Decorator, Call, BaseExpression)

from hwlib.keywords import KEEP, REPLACE, TOASSIGN
from ..utils import (add_leading_lines, add_comment,
                     NoneAssigner, MetaTransformer, MetaModule)
from .differs import HomeworkDiffer


class DecoratorRemover(MetaTransformer):
    def leave_Decorator(self, orig_decor: "Decorator",
                        upd_decor: "Decorator"
                        ) -> Union["Decorator", RemovalSentinel]:
        if self.get_qname(orig_decor.decorator) == 'hwlib.keywords.HOMEWORK':
            return RemovalSentinel.REMOVE
        else:
            return upd_decor


class ImportRemover(MetaTransformer):
    name = 'hwlib'

    def leave_Import(self, original_node: "Import", updated_node: "Import"
                     ) -> Union["BaseSmallStatement", RemovalSentinel]:
        if m.findall(original_node, m.Name(self.name)):
            return RemovalSentinel.REMOVE
        else:
            return updated_node

    def leave_ImportFrom(self, original_node: "ImportFrom",
                         updated_node: "ImportFrom"
                         ) -> Union["BaseSmallStatement", RemovalSentinel]:
        if m.findall(original_node, m.Name(self.name)):
            return RemovalSentinel.REMOVE
        else:
            return updated_node


class KEEPReplacer(MetaTransformer):
    def leave_Call(self, original_node: "Call", updated_node: "Call"
                   ) -> "BaseExpression":
        if self.qname_matches(original_node.func, KEEP):
            updated_node = original_node.args[0]
        return updated_node

    def leave_If(self, original_node: "If", updated_node: "If"
                 ) -> FlattenSentinel["BaseStatement"]:
        if m.findall(original_node.test, self.qname_matcher_prov(KEEP)):
            lines = list(updated_node.body.body)
            lines[0] = add_leading_lines(lines[0], original_node)
            updated_node = FlattenSentinel(lines)
        return updated_node


class EXITIFCOLLECTINGRemover(MetaTransformer):
    def leave_SimpleStatementLine(self, original_node: "SimpleStatementLine",
                                  updated_node: "SimpleStatementLine"
                                  ) -> Union["BaseStatement", RemovalSentinel]:
        if m.findall(original_node, Name('EXITIFCOLLECTING')):
            return RemovalSentinel.REMOVE
        return updated_node


class TOASSIGNReplacer(MetaTransformer, HomeworkDiffer):
    def __init__(self, module: MetaModule):
        super().__init__(module)
        self.to_comment = set()

    def leave_SimpleStatementLine(self, original_node: "SimpleStatementLine",
                                  updated_node: "SimpleStatementLine"
                                  ) -> "SimpleStatementLine":
        if original_node in self.to_comment:
            updated_node = add_comment(updated_node, 'TODO')
        return updated_node

    def leave_Call(self, original_node: "Call", updated_node: "Call"
                   ) -> "BaseExpression":
        if self.qname_matches(original_node.func, TOASSIGN):
            if self.homework:
                self.to_comment.add(self.parent_matching(
                    original_node, m.SimpleStatementLine()))
                updated_node = Name('None')
            else:
                updated_node = original_node.args[0]
        return updated_node

    def leave_If(self, original_node: "If", updated_node: "If"
                 ) -> FlattenSentinel["BaseStatement"]:
        if m.findall(original_node.test, self.qname_matcher_prov(TOASSIGN)):
            if self.homework:
                updated_node = updated_node.visit(NoneAssigner())
            lines = list(updated_node.body.body)
            lines[0] = add_leading_lines(lines[0], original_node)
            if self.homework:
                for i, line in enumerate(lines):
                    lines[i] = add_comment(line, 'TODO')
            updated_node = FlattenSentinel(lines)
        return updated_node


class REPLACEReplacer(MetaTransformer, HomeworkDiffer):
    def leave_Call(self, original_node: "Call", updated_node: "Call"
                   ) -> "BaseExpression":
        if self.qname_matches(original_node.func, REPLACE):
            updated_node = original_node.args[1 if self.homework else 0]
        return updated_node

    def leave_If(self, original_node: "If", updated_node: "If"
                 ) -> FlattenSentinel["BaseStatement"]:
        if m.findall(original_node.test, self.qname_matcher_prov(REPLACE)):
            indent = updated_node.orelse if self.homework else updated_node
            updated_node = FlattenSentinel(indent.body.body)
        return updated_node
