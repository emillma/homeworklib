from functools import wraps
from pathlib import Path
import pickle
import inspect
import __main__


def getidx(n, space):
    """
    Used to distribute data efficiently
    """
    step = 1 << (n//space).bit_length()
    if n < space:
        return n
    elif n % step != 0:
        return None
    number = n//step - (space+1)//2
    replacing = step//2 + number*step
    return getidx(replacing, space)


class DataCatcher:
    def __init__(self, maxdata):
        self.data = {}
        self.maxdata = maxdata
        self.data_is_saved = False

        self.step = 1
        self.n = 0
        self.idx = 0

    def set_maxdata(self, maxdata):
        self.maxdata = maxdata

    def catch(self, func):
        if (module := func.__module__) == '__main__':
            module = Path(__main__.__file__).stem
        fkey = f"{module}.{func.__qualname__}"

        @wraps(func)
        def wrapper(*args, **kwargs):

            tmpargs = inspect.signature(func).bind(*args, **kwargs)
            tmpargs.apply_defaults()
            argvals = tmpargs.arguments
            ret = func(*args, **kwargs)

            fdata = self.data.setdefault(fkey, [])
            if len(fdata) < self.maxdata:
                fdata.append((argvals, ret))
            elif idx := getidx(self.n, self.maxdata):
                fdata[idx] = (argvals, ret)

            self.n += 1
            return ret
        return wrapper

    def set_data(self, pos):
        if self.n % self.step != 0:
            return

    def dump(self, fpath: Path):
        with open(fpath, 'wb') as file:
            pickle.dump(self.data, file)
        self.data_is_saved = True
