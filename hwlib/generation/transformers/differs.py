from libcst import Name, SimpleString
import libcst.matchers as m
from typing import Union
from ..utils import MetaTransformer


class HomeworkDiffer:
    homework: bool

    @classmethod
    def ishomework(cls, homework: bool):
        def factry(module: MetaTransformer) -> MetaTransformer:
            obj: HomeworkDiffer = cls(module)
            obj.homework = homework
            return obj
        return factry


class Passworddiffer:
    password: Union[SimpleString, Name]

    @classmethod
    def with_password(cls, password: str):
        def factry(module: MetaTransformer, **_) -> MetaTransformer:
            obj: Passworddiffer = cls(module)
            obj.password = password
            return obj
        return factry
