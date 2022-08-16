import autopep8
from typing import Sequence
from handoutgen.metamodule import MetaModule
from handoutgen.metatraversers import HyperTraverser, MetaTraverser
from handoutgen.transformer_solu import (RedirectImports, ImportSoluUsage,
                                         MarkSoluUsage)
from handoutgen.transformer_both import (
    ImportRemover, DecoratorRemover,
    KEEPReplacer, REPLACEReplacer, TOASSIGNReplacer, EXITIFCOLLECTINGRemover)

from handoutgen.transformer_task import (
    ImportSolution, CodeRemover, SolutionBeforeReturnAdder)

from handoutgen.transformer_tests import (
    ImportNameReplacer, TestFuncsCreator)


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
fortests = (
    ImportNameReplacer,
    TestFuncsCreator,
)


def process(module: MetaModule, traversers: Sequence[MetaTraverser],
            module_to_visit=None, **kwargs
            ) -> str:
    module_to_visit = module_to_visit or module
    output = module_to_visit.visit(HyperTraverser.from_factories(factories=(
        traversers
    ), module=module, **kwargs))
    return autopep8.fix_code(output.code)


def get_handout(module) -> str:
    return process(module, forhandout)


def get_task(module) -> str:
    return process(module, fortasks)


def get_solu(module) -> str:
    return process(module, forsolution)


def get_lf(module) -> str:
    return process(module, forlf)


def get_test(module, template) -> str:
    return process(module, fortests, template, test=template)
