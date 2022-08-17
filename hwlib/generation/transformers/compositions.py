import autopep8
from typing import Sequence
from random import randint

from ..utils import MetaModule, HyperTraverser, MetaTraverser
from .tran_solu import RedirectImports, ImportSoluUsage, MarkSoluUsage
from .tran_task import ImportSolution, CodeRemover, SolutionBeforeReturnAdder
from .tran_test import ImportNameReplacer, TestFuncsCreator, PASSWORDReplacer
from .tran_both import (ImportRemover, DecoratorRemover,
                        KEEPReplacer, REPLACEReplacer,
                        TOASSIGNReplacer, EXITIFCOLLECTINGRemover)


def process_composition(module: MetaModule, traversers: Sequence[MetaTraverser],
                        module_to_visit=None, **kwargs
                        ) -> str:
    module_to_visit = module_to_visit or module
    output = module_to_visit.visit(HyperTraverser.from_factories(factories=(
        traversers
    ), module=module, **kwargs))
    return autopep8.fix_code(output.code)


PASSWORD = ''.join([chr(randint(97, 122)) for i in range(6)])

general = (ImportRemover,
           DecoratorRemover,
           KEEPReplacer,
           EXITIFCOLLECTINGRemover,
           )
ho_sup = (*general,
          REPLACEReplacer.ishomework(True),
          TOASSIGNReplacer.ishomework(True)
          )
ho__task = (*ho_sup,
            ImportSolution,
            CodeRemover,
            SolutionBeforeReturnAdder,
            )
ho__solu = (*general,
            RedirectImports,
            ImportSoluUsage,
            MarkSoluUsage,
            REPLACEReplacer.ishomework(False),
            TOASSIGNReplacer.ishomework(False),
            )

ho__tests = (ImportNameReplacer,
             TestFuncsCreator,
             PASSWORDReplacer.with_password(None),
             )
ho__check = (PASSWORDReplacer.with_password(None),
             )


lf__sup_task = (*general,
                REPLACEReplacer.ishomework(False),
                TOASSIGNReplacer.ishomework(False)
                )


gr__tests = (
    ImportNameReplacer,
    TestFuncsCreator,
    PASSWORDReplacer.with_password(PASSWORD)
)
gr__solu = ho__solu
gr__check = (PASSWORDReplacer.with_password(PASSWORD),)


def get_ho_sup(module) -> str:
    return process_composition(module, ho_sup)


def get_ho_task(module) -> str:
    return process_composition(module, ho__task)


def get_ho_solu(module) -> str:
    return process_composition(module, ho__solu)


def get_ho_usage_checker(module) -> str:
    return process_composition(module, ho__check)


def get_ho_test(module, template) -> str:
    return process_composition(module, ho__tests, template, test=template)


def get_lf_sup_task(module) -> str:
    return process_composition(module, lf__sup_task)


def get_grader_solu(module) -> str:
    return process_composition(module, gr__solu)


def get_grader_test(module, template) -> str:
    return process_composition(module, gr__tests, template, test=template)


def get_grader_usage_checker(module) -> str:
    return process_composition(module, gr__check)
