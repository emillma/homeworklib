from ..utils.metamodule import MetaModule
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
            body = re.match('^\n*(.*?)\n*$', body, re.DOTALL)[1]
            fdef = re.search('def [^\(]+', body)

            latex_body = ('\\begin{minted}{python}\n'
                          f'{body}\n'
                          '\\end{minted}')

            latex_fdef = (f'\\mintinline{{python}}{{{fdef}}}')

            self.add_latex_file(relpath.joinpath('solu.tex'), latex_body)
            self.add_latex_file(relpath.joinpath('def.tex'), latex_fdef)
        return upd_fdef
