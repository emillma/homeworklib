# pylint: skip-file
from typing import Literal, TypeVar, Callable, Any
import os
import sys
import atexit

from .datacatcher import DataCatcher


class Keyword:
    def __init__(self, qname, func, boolval=None):
        self._qname = qname
        self._func = func
        self._bool = boolval or False

    def __bool__(self) -> Literal[True]:
        return True

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def __str__(self):
        return self._qname


T = TypeVar('T')
keywords = []
data_out_file = os.environ.get('HWG_DATA_OUT_FILE', None)
data_catcher = DataCatcher(100)
data_is_saved = [False]


def exit_handler():
    if data_out_file:
        if not data_is_saved[0]:
            data_catcher.dump(data_out_file)


atexit.register(exit_handler)


def keyword(boolval) -> Callable[[T, Any], T]:
    def dec(func):
        kw = Keyword(f"handoutgen.{func.__name__}", func, boolval)
        keywords.append(kw)
        return kw
    return dec


@keyword(True)
def HOMEWORK(func: T) -> T:
    if data_out_file:
        return data_catcher.catch(func)
    else:
        return func


@keyword(True)
def EXITIFCOLLECTING():
    if data_out_file:
        data_catcher.dump(data_out_file)
        data_is_saved[0] = True
        sys.exit(0)


@keyword(True)
def KEEP(stuff):
    return stuff


@keyword(True)
def REPLACE(stuff, replacement):
    return stuff


@keyword(True)
def TOASSIGN(stuff):
    return stuff
