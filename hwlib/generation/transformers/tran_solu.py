from functools import cached_property

from libcst import matchers as m
from libcst import (Name, FunctionDef, Attribute, ImportFrom, Import, Module,
                    parse_statement)

from ..utils import MetaTransformer
from .differs import Passworddiffer


class RedirectImports(MetaTransformer):
    siblings: set[str]

    @cached_property
    def siblings(self):
        code_dir = self.proj_dir.joinpath(self.path_rel2proj.parts[0])
        files = code_dir.rglob('*.py')
        return set('.'.join(f.relative_to(code_dir).with_suffix('').parts)
                   for f in files)

    def leave_Import(self, orig_import: Import, upd_import: Import
                     ) -> "Import":
        return super().leave_Import(orig_import, upd_import)

    def leave_ImportFrom(self, orig_ifrom: ImportFrom, upd_ifrom: ImportFrom
                         ) -> ImportFrom:
        module_name = self.code(orig_ifrom.module)
        if not orig_ifrom.relative and module_name in self.siblings:
            return upd_ifrom.with_changes(module=Attribute(Name('solution'),
                                                           orig_ifrom.module))
        return upd_ifrom


class ImportSoluUsage(MetaTransformer):
    def leave_Module(self, original_node: Module, updated_node: Module
                     ) -> Module:
        idx = next((i for i, n in enumerate(updated_node.body)
                   if not m.findall(n, m.Import() | m.ImportFrom())), 0)
        text = f'from solution.solu_usage_checker import UsageChecker'
        newline = parse_statement(text)
        newbody = [*updated_node.body[:idx], newline, *updated_node.body[idx:]]
        return updated_node.with_changes(body=newbody)


class MarkSoluUsage(MetaTransformer, Passworddiffer):
    def leave_FunctionDef(self, orig_def: FunctionDef, upd_def: FunctionDef
                          ) -> FunctionDef:
        if orig_def in self.task_funcs:
            key = self.id_str(orig_def)
            if isinstance(self.password, str):
                self.password = f"'{self.password}'"
            text = f"UsageChecker.increase_usage('{key}', {self.password})"
            s = parse_statement(text)
            indet = upd_def.body.with_changes(body=[s, *upd_def.body.body])
            upd_def = upd_def.with_changes(body=indet)
        return upd_def
