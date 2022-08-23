from ..utils.metamodule import MetaModule
from ..utils.metatraversers import MetaTransformer
from libcst import FunctionDef
import re


class LatexFuncDefCatcher(MetaTransformer):
    def leave_FunctionDef(self, orig_fdef: FunctionDef, upd_fdef: FunctionDef
                          ) -> FunctionDef:
        if orig_fdef in self.task_funcs:
            key = f'{self.module_str}.{self.get_qname(orig_fdef)}'

            body = self.module.code_for_node(upd_fdef)
            fdef = re.search('def [^\(]*', body)
            latex_body = ('\\begin{minted}{python}'
                          f'{body}'
                          '\\end{minted}')

            latex_fdef = ('\\mintinline{'
                          f'{fdef}'
                          '}')

            self.add_latex_func_body(key, latex_body)
            self.add_latex_func_def(key, latex_fdef)
        return upd_fdef
