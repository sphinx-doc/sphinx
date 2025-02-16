from __future__ import annotations

from enum import Enum
from typing import Literal, TypeVar


class MyEnum(Enum):
    a = 1
    b = 2


T = TypeVar('T', bound=Literal[1234, 'abcd'])
"""docstring"""


U = TypeVar('U', bound=Literal[MyEnum.a, MyEnum.b])
"""docstring"""


def bar(x: Literal[1234, 'abcd']):
    """docstring"""


def foo(x: Literal[MyEnum.a, MyEnum.b]):
    """docstring"""
