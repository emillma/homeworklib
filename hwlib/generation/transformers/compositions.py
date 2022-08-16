import autopep8
from typing import Sequence
from random import randint

from ..utils import MetaModule, HyperTraverser, MetaTraverser, NameReplacer
from .tran_solu import RedirectImports, ImportSoluUsage, MarkSoluUsage
from .tran_task import ImportSolution, CodeRemover, SolutionBeforeReturnAdder
from .tran_test import ImportNameReplacer, TestFuncsCreator
from .tran_both import (ImportRemover, DecoratorRemover,
                        KEEPReplacer, REPLACEReplacer,
                        TOASSIGNReplacer, EXITIFCOLLECTINGRemover)


forall = (ImportRemover,
          DecoratorRemover,
          KEEPReplacer,
          EXITIFCOLLECTINGRemover,
          )
forhandout = (*forall,
              REPLACEReplacer.ishomework(True),
              TOASSIGNReplacer.ishomework(True)
              )
forlf = (*forall,
         REPLACEReplacer.ishomework(False),
         TOASSIGNReplacer.ishomework(False)
         )
fortasks = (*forhandout,
            ImportSolution,
            CodeRemover,
            SolutionBeforeReturnAdder,
            )
forsolution = (*forall,
               RedirectImports,
               ImportSoluUsage,
               MarkSoluUsage,
               REPLACEReplacer.ishomework(False),
               TOASSIGNReplacer.ishomework(False)
               )

password = ''.join([chr(randint(97, 123)) for i in range(6)])

forusagechecker = (lambda **_: NameReplacer('PASSWORD', 'None'),)
forgradeusagechecker = (lambda **_: NameReplacer('PASSWORD', password),)

fortests = (
    ImportNameReplacer,
    TestFuncsCreator,
    lambda **_: NameReplacer('PASSWORD', 'None'),
)

forgradetests = (
    ImportNameReplacer,
    TestFuncsCreator,
    lambda **_: NameReplacer('PASSWORD', password),
)


def process_composition(module: MetaModule, traversers: Sequence[MetaTraverser],
                        module_to_visit=None, **kwargs
                        ) -> str:
    module_to_visit = module_to_visit or module
    output = module_to_visit.visit(HyperTraverser.from_factories(factories=(
        traversers
    ), module=module, **kwargs))
    return autopep8.fix_code(output.code)
