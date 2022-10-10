from ..utils.metatraversers import MetaTransformer
from libcst import FunctionDef
import re
import roman
from pathlib import Path


def to_numeral(number_match: re.Match) -> str:
    return roman.toRoman(int(number_match[0]))


def to_pascal(snake_match: re.Match) -> str:
    return snake_match[1].upper()


class LatexFuncDefCatcher(MetaTransformer):
    def leave_FunctionDef(self, orig_fdef: FunctionDef, upd_fdef: FunctionDef
                          ) -> FunctionDef:
        if orig_fdef in self.task_funcs:
            key = f'{self.module_str}.{self.get_qname(orig_fdef)}'
            relpath = Path(*key.split('.'))

            body = self.module.code_for_node(upd_fdef)
            body = re.match('^\n*(.*?)\n*$', body, re.DOTALL)[1]  # newlines
            if docstr := upd_fdef.get_docstring(clean=False):
                doc_fixed = re.sub('(?<=\\n) {5,}', ' '*4, docstr)
                body = body.replace(docstr, doc_fixed, 1)

            latex_body = ('\\begin{pythoncode}\n'
                          f'{body}\n'
                          '\\end{pythoncode}')

            latex_fdef = f'\\pythoninline{{{self.id_str(orig_fdef)}}}\\unskip'

            self.add_latex_file(relpath.joinpath('solu.tex'), latex_body)
            self.add_latex_file(relpath.joinpath('def.tex'), latex_fdef)
        return upd_fdef
