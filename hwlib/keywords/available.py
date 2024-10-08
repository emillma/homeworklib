# pylint: skip-file
from typing import TypeVar
import os
import sys
from typing import Literal
from .datacatcher import DataCatcher

T = TypeVar('T')


class Keyword:
    registered = set()

    def __init__(self, func):
        self._func = func
        self._name = func.__qualname__
        self._qname = f"hwlib.keywords.{self._name}"
        self._bool = True
        Keyword.registered.add(self)

    def __bool__(self) -> Literal[True]:
        return True

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def __str__(self):
        return self._qname

    @classmethod
    def from_func(cls: "Keyword", func: T) -> T:
        return cls(func)


_data_out_file = os.environ.get('HWLIB_CATCH_FILE', None)
_collecting_data = bool(_data_out_file)
_data_catcher = DataCatcher(100)

keywordset = Keyword.registered

T = TypeVar('T')


@Keyword.from_func
def HOMEWORK(func: T) -> T:
    if _collecting_data:
        return _data_catcher.catch(func)
    else:
        return func


@Keyword.from_func
def EXITIFCOLLECTING():
    if _collecting_data:
        _data_catcher.dump(_data_out_file)
        sys.exit(0)


@Keyword.from_func
def KEEP(stuff: T) -> T:
    return stuff


@Keyword.from_func
def REPLACE(stuff: T, replacement) -> T:
    return stuff


@Keyword.from_func
def TOASSIGN(stuff: T) -> T:
    return stuff


if _collecting_data:
    import atexit

    def exit_handler():
        if not _data_catcher.data_is_saved:
            _data_catcher.dump(_data_out_file)

    atexit.register(exit_handler)
