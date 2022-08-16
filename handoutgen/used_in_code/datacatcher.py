from functools import wraps
from pathlib import Path
import pickle
import inspect
import __main__


class DataCatcher:
    def __init__(self, maxdata):
        self.data = {}
        self.maxdata = maxdata

    def set_maxdata(self, maxdata):
        self.maxdata = maxdata

    def catch(self, func):
        if (module := func.__module__) == '__main__':
            module = Path(__main__.__file__).stem
        fkey = f"{module}.{func.__qualname__}"

        @wraps(func)
        def wrapper(*args, **kwargs):

            argvals = inspect.signature(func).bind(*args, **kwargs).arguments
            ret = func(*args, **kwargs)

            fdata = self.data.setdefault(fkey, [])
            if len(fdata) < self.maxdata:
                fdata.append((argvals, ret))
            else:
                raise Exception
            return ret
        return wrapper

    def dump(self, fpath: Path):
        with open(fpath, 'wb') as file:
            pickle.dump(self.data, file)
