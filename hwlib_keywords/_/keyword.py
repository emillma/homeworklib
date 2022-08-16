from typing import Literal, TypeVar

T = TypeVar('T')


class Keyword:
    registered = []

    def __init__(self, func):
        self._func = func
        self._name = func.__qualname__
        self._qname = f"hwlib_keywords.{self._name}"
        self._bool = True
        Keyword.registered.append(self)

    def __bool__(self) -> Literal[True]:
        return True

    def __call__(self, *args, **kwargs):
        return self._func(*args, **kwargs)

    def __str__(self):
        return self._qname

    @classmethod
    def from_func(cls: "Keyword", func: T) -> T:
        return cls(func)
