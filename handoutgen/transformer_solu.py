from libcst import (
    Comment, Name, EmptyLine, Assign, SimpleStatementLine, FunctionDef, Call,
    Attribute, Arg, ImportFrom, Import, Module, parse_statement)
from libcst import matchers as m
from functools import cached_property

from handoutgen import keywords
from handoutgen.checkers import assert_not_contain_keywords
from handoutgen.metatraversers import MetaTransformer
from handoutgen.metamodule import MetaModule


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
        newline = parse_statement(f'from solution.solu_vars import solu_usage')
        newbody = [*updated_node.body[:idx], newline, *updated_node.body[idx:]]
        return updated_node.with_changes(body=newbody)


class MarkSoluUsage(MetaTransformer):
    def leave_FunctionDef(self, orig_def: FunctionDef, upd_def: FunctionDef
                          ) -> FunctionDef:
        if orig_def in self.task_funcs:
            string = f"solu_usage['{self.id_str(orig_def)}'] = True"
            s = parse_statement(string)
            indet = upd_def.body.with_changes(body=[s, *upd_def.body.body])
            upd_def = upd_def.with_changes(body=indet)
        return upd_def
