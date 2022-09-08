from dataclasses import is_dataclass, astuple, fields
from collections.abc import Iterable
import numbers
import numpy as np


def compare(a, b):
    if isinstance(b, (np.ndarray, numbers.Number)):
        assert np.allclose(a, b, atol=1e-6)

    elif is_dataclass(b):
        assert type(a).__name__ == type(b).__name__
        if isinstance(b, type):
            assert fields(a) == fields(b)
        else:
            for i, j in zip(astuple(a), astuple(b)):
                compare(i, j)

    elif isinstance(b, Iterable):
        for i, j in zip(a, b):
            compare(i, j)

    elif isinstance(b, str):
        assert a == b

    else:
        raise NotImplementedError(f'{type(b)} not implemented')
