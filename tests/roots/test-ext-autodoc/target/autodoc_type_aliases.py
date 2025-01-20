from __future__ import annotations

import io  # NoQA: TC003
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from typing import Optional

myint = int

#: docstring
variable: myint

#: docstring
variable2 = None  # type: myint

#: docstring
variable3: Optional[myint]  # NoQA: UP045


def read(r: io.BytesIO) -> io.StringIO:
    """docstring"""


def sum(x: myint, y: myint) -> myint:
    """docstring"""
    return x + y


@overload
def mult(x: myint, y: myint) -> myint: ...


@overload
def mult(x: float, y: float) -> float: ...


def mult(x, y):
    """docstring"""
    return x, y


class Foo:
    """docstring"""

    #: docstring
    attr1: myint

    def __init__(self):
        self.attr2: myint = None  #: docstring
