from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass, field
from typing import NamedTuple, TypedDict

#: docstring
SENTINEL = object()


#: docstring
ze_lambda = lambda z=SENTINEL: None  # NoQA: E731


def foo(x, y, z=SENTINEL):
    """docstring"""


@dataclass
class DataClass:
    """docstring"""

    a: int
    b: object = SENTINEL
    c: list[int] = field(default_factory=lambda: [1, 2, 3])


@dataclass(init=False)
class DataClassNoInit:
    """docstring"""

    a: int
    b: object = SENTINEL
    c: list[int] = field(default_factory=lambda: [1, 2, 3])


class MyTypedDict(TypedDict):
    """docstring"""

    a: int
    b: object
    c: list[int]


class MyNamedTuple1(NamedTuple):
    """docstring"""

    a: int
    b: object = object()
    c: list[int] = [1, 2, 3]


class MyNamedTuple2(namedtuple('Base', ('a', 'b'), defaults=(0, SENTINEL))):  # NoQA: PYI024,SLOT002
    """docstring"""
