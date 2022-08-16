from typing import Iterable, Union, TypeVar, Any


from .metamodule import MetaModule
from inspect import isclass
from libcst import (CSTVisitor, CSTTransformer, RemovalSentinel,
                    CSTNode, CSTNodeT, FlattenSentinel, Module)

T = TypeVar('T', bound=MetaModule)


class MetaTraverser(MetaModule):
    def __init__(self, module: MetaModule):
        self.__dict__.update(module.__dict__.items())


class MetaVisitor(MetaTraverser, CSTVisitor):
    ...


class MetaTransformer(MetaTraverser, CSTTransformer):
    ...


class HyperTraverser(CSTTransformer):
    traversers: Iterable[Union[MetaVisitor, MetaTransformer]]

    def __init__(self,
                 traversers: Iterable[Union[MetaVisitor, MetaTransformer]]
                 ) -> None:
        self.traversers = tuple(traversers)

    @classmethod
    def from_factories(cls: "HyperTraverser",
                       factories: Iterable[Union[MetaVisitor,
                                                 MetaTransformer]],
                       **kwargs
                       ) -> Module:
        return cls(fac(**kwargs) for fac in factories)

    def on_visit(self, node: "CSTNode") -> bool:
        retval = False
        for traverser in self.traversers:
            newret = traverser.on_visit(node)
            retval = retval or newret
        return retval

    def on_leave(self, original_node: CSTNodeT, updated_node: CSTNodeT = None
                 ) -> Union[CSTNodeT,
                            RemovalSentinel,
                            FlattenSentinel[CSTNodeT]]:
        for traverser in self.traversers:
            if isinstance(traverser, CSTVisitor):
                traverser.on_leave(original_node)
            if isinstance(traverser, CSTTransformer):
                updated_node = traverser.on_leave(original_node, updated_node)
        return updated_node
