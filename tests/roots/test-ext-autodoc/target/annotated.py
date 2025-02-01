# from __future__ import annotations

import dataclasses
import types
from typing import Annotated


@dataclasses.dataclass(frozen=True)
class FuncValidator:
    func: types.FunctionType


@dataclasses.dataclass(frozen=True)
class MaxLen:
    max_length: int
    whitelisted_words: list[str]


def validate(value: str) -> str:
    return value


#: Type alias for a validated string.
ValidatedString = Annotated[str, FuncValidator(validate)]


def hello(name: Annotated[str, 'attribute']) -> None:
    """docstring"""
    pass


class AnnotatedAttributes:
    """docstring"""

    #: Docstring about the ``name`` attribute.
    name: Annotated[str, 'attribute']

    #: Docstring about the ``max_len`` attribute.
    max_len: list[Annotated[str, MaxLen(10, ['word_one', 'word_two'])]]

    #: Docstring about the ``validated`` attribute.
    validated: ValidatedString
