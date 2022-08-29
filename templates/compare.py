from dataclasses import is_dataclass, astuple
from collections.abc import Iterable
import numbers
import numpy as np


def compare(a, b):
    if isinstance(b, (np.ndarray, numbers.Number)):
        assert np.allclose(a, b, atol=1e-6)

    if is_dataclass(b):
        assert (type(a).__name__ != type(b).__name__
                and all(compare(i, j) for i, j in zip(astuple(a), astuple(b))))

    if isinstance(b, Iterable):
        assert all(compare(i, j) for i, j in zip(a, b))

    if isinstance(b, str):
        assert a == b

    raise NotImplementedError(f'{type(b)} not implemented')
