from libcst import FunctionDef, parse_module, CSTNode, Module

from libcst.metadata import (QualifiedNameProvider, MetadataWrapper,
                             ParentNodeProvider, PositionProvider)
from libcst.metadata.scope_provider import QualifiedName
from libcst import matchers as m
from libcst._metadata_dependent import LazyValue

from pathlib import Path

from functools import cached_property


from .libcst_utils import children
from typing import Iterable, Optional, Sequence, TYPE_CHECKING

if TYPE_CHECKING:
    from .metatraversers import MetaTraverser


class MetaModule:
    path: Path
    path_rel2proj: Path
    path_rel2code: Path

    metawrap: MetadataWrapper
    module: Module
    qname_prov: QualifiedNameProvider
    parent_prov: ParentNodeProvider
    pos_prov: PositionProvider
    task_funcs: Sequence[FunctionDef]
    latex_func_bodies: dict[str, str]
    latex_file_contents: dict[str, str]

    istask: bool

    def __init__(self, fpath: Path, project_dir: Path = None):
        self.path = fpath
        self.proj_dir = project_dir
        self.latex_func_bodies = {}
        self.latex_file_contents = {}

    @classmethod
    def from_path(cls, fpath: Path):
        module = MetaModule()
        module.path = fpath

    @cached_property
    def path_rel2proj(self):
        assert self.proj_dir
        return self.path.relative_to(self.proj_dir)

    @cached_property
    def path_rel2code(self):
        return Path(*self.path_rel2proj.parts[1:])

    @cached_property
    def module(self):
        return self.metawrap.module

    @property
    def module_str(self) -> str:
        return '.'.join((*self.path_rel2code.parts[:-1], self.path.stem))

    @cached_property
    def metawrap(self):
        return MetadataWrapper(parse_module(self.path.read_text()))

    @cached_property
    def qname_prov(self):
        return self.metawrap.resolve(QualifiedNameProvider)

    @cached_property
    def parent_prov(self):
        return self.metawrap.resolve(ParentNodeProvider)

    @cached_property
    def pos_prov(self):
        return self.metawrap.resolve(PositionProvider)

    @cached_property
    def istask(self):
        return bool(m.findall(self.module, m.Decorator(m.Name('HOMEWORK'))))

    @cached_property
    def task_funcs(self) -> Sequence[FunctionDef]:
        if not self.istask:
            return []
        mchr = m.FunctionDef(decorators=[
            m.AtLeastN(self.qname_matcher_prov('hwlib.keywords.HOMEWORK'), n=1)])
        return [c for c in children(self.module, -1) if m.matches(c, mchr)]

    def code(self, node: CSTNode) -> str:
        return self.module.code_for_node(node)

    def visit(self, traverser: "MetaTraverser") -> Module:
        return self.metawrap.visit(traverser)

    @staticmethod
    def children(node: CSTNode, limit: int = 1) -> Iterable[CSTNode]:
        return children(node, limit)

    def parent(self, node: CSTNode, step: int = 1) -> CSTNode:
        if step == 1:
            return self.parent_prov[node]
        else:
            return self.parent(node, step-1)

    def parent_matching(self, node: CSTNode, matcher: m.BaseMatcherNode,
                        *, get_chain: bool = False) -> Optional[CSTNode]:
        parents = [self.parent(node)]
        while not m.matches(parents[-1], matcher):
            parents.append(self.parent(parents[-1]))
        return parents if get_chain else parents[-1]

    def parent_task(self, node: CSTNode, *,
                    immediate: bool = True, get_chain: bool = False
                    ) -> Optional[FunctionDef]:
        parents = self.parent_matching(node, m.FunctionDef(), get_chain=True)

        if parents[-1] in self.task_funcs:
            return parents if get_chain else parents[-1]
        elif immediate or not parents:
            return None
        else:
            parents.extend(self.parent_task(parents[-1], get_chain=True))
            return parents if get_chain else parents[-1]

    def get_pos_str(self, node: CSTNode, full=False) -> str:
        posprov = self.pos_prov.get(node, None)
        if full:
            out = (f"File \"{self.path} line {posprov.start.line}")
        else:
            out = (f"{type(node).__name__} : "
                   f"{self.path.name} : {posprov.start.line}")
        return out

    def get_qname(self, node: CSTNode, *, as_strings=True, get_longest=True
                  ) -> Sequence[QualifiedName]:
        qname = self.qname_prov[node]
        if isinstance(qname, LazyValue):
            qname = qname()
        if as_strings:
            qname = [q.name for q in qname]
            if get_longest:
                return max(qname, key=len) if qname else None
            else:
                raise NotImplementedError
        else:
            raise NotImplementedError

    def qname_matches(self, node: CSTNode, qname: str) -> bool:
        return str(qname) == self.get_qname(node)

    def qname_matcher_prov(self, qname: str) -> m.MatchIfTrue:
        def hasqname(n: CSTNode):
            return self.qname_matches(n, qname)
        return m.MatchIfTrue(hasqname)

    def id_str(self, node: CSTNode) -> bool:
        return (f"{self.module_str}.{self.get_qname(node)}")

    def add_latex_file(self, key: str, def_text: str):
        assert key not in self.latex_file_contents
        self.latex_file_contents[key] = def_text
