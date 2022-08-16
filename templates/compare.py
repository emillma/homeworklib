import numpy as np
from dataclasses import is_dataclass, astuple
from collections.abc import Iterable
import numbers


def compare(a, b):
    if isinstance(b, np.ndarray) or isinstance(b, numbers.Number):
        if isinstance(b, np.ndarray) and a.shape != b.shape:
            return False
        return np.allclose(a, b, atol=1e-6)

    if isinstance(b, str):
        return a == b

    elif is_dataclass(b):
        if type(a).__name__ != type(b).__name__:
            return False
        a_tup, b_tup = astuple(a), astuple(b)
        return all([compare(i, j) for i, j in zip(a_tup, b_tup)])

    elif isinstance(b, Iterable):
        return all([compare(i, j) for i, j in zip(a, b)])

    else:
        return a == b
