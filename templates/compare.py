from dataclasses import is_dataclass, astuple, fields
from collections.abc import Iterable
import numbers
import numpy as np


def compare(a, b):
    if a is b:
        return
    elif is_dataclass(b):
        assert type(a).__name__ == type(b).__name__
        if isinstance(b, type):
            assert fields(a) == fields(b)
        else:
            for field in fields(b):
                i, j = getattr(a, field.name), getattr(b, field.name)
                compare(i, j)

    elif isinstance(b, (np.ndarray, numbers.Number)):
        assert np.allclose(a, b, atol=1e-6)

    elif isinstance(b, Iterable):
        for i, j in zip(a, b):
            compare(i, j)

    elif isinstance(b, str):
        assert a == b

    else:
        raise NotImplementedError(f'{type(b)} not implemented')
