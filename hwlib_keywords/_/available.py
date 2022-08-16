# pylint: skip-file
from typing import TypeVar
import os
import sys
from .datacatcher import DataCatcher
from .keyword import Keyword


_data_out_file = os.environ.get('HWG_DATA_OUT_FILE', None)
_collecting_data = bool(_data_out_file)
_data_catcher = DataCatcher(100)

keywords = Keyword.registered

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
