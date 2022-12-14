from libcst import (
    ImportFrom, Name, BaseSmallStatement, BaseStatement, CSTNodeT,
    SimpleStatementLine, Call, Import, FlattenSentinel, RemovalSentinel,
    If, Decorator, Call, BaseExpression)
from libcst import matchers as m
from typing import Union


from handoutgen import KEEP, REPLACE, TOASSIGN
from handoutgen.libcst_utils import (
    add_leading_lines, add_comment, NoneAssigner)
from handoutgen.metatraversers import MetaTransformer
from handoutgen.metamodule import MetaModule


class DecoratorRemover(MetaTransformer):
    def leave_Decorator(self, original_node: "Decorator",
                        updated_node: "Decorator"
                        ) -> Union["Decorator", RemovalSentinel]:
        if self.qname_prov[original_node.decorator]():
            return RemovalSentinel.REMOVE
        else:
            return updated_node


class ImportRemover(MetaTransformer):
    name = 'handoutgen'

    def leave_Import(self, original_node: "Import", updated_node: "Import"
                     ) -> Union["BaseSmallStatement", RemovalSentinel]:
        if any(m.matches(n, m.Name(self.name)
                         | m.ImportAlias(m.Name(self.name)))
                for n in original_node.names):
            return RemovalSentinel.REMOVE
        else:
            return updated_node

    def leave_ImportFrom(self, original_node: "ImportFrom",
                         updated_node: "ImportFrom"
                         ) -> Union["BaseSmallStatement", RemovalSentinel]:
        if m.matches(original_node.module, m.Name(self.name)):
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


class HomeworkDiffer:
    homework: bool

    @classmethod
    def ishomework(cls, homework: bool):
        def factry(module: MetaTransformer) -> MetaTransformer:
            obj: HomeworkDiffer = cls(module)
            obj.homework = homework
            return obj
        return factry


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
