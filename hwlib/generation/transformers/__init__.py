from .compositions import (process_composition,
                           forhandout, fortasks, forsolution, forlf, fortests)


def get_handout(module) -> str:
    return process_composition(module, forhandout)


def get_task(module) -> str:
    return process_composition(module, fortasks)


def get_solu(module) -> str:
    return process_composition(module, forsolution)


def get_lf(module) -> str:
    return process_composition(module, forlf)


def get_test(module, template) -> str:
    return process_composition(module, fortests, template, test=template)
