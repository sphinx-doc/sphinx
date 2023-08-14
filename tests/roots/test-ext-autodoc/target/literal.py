from __future__ import annotations

from enum import Enum
from typing import Literal, TypeVar


class MyEnum(Enum):
    a = 1


T = TypeVar('T', bound=Literal[1234])
"""docstring"""


U = TypeVar('U', bound=Literal[MyEnum.a])
"""docstring"""


def bar(x: Literal[1234]):
    """docstring"""


def foo(x: Literal[MyEnum.a]):
    """docstring"""
