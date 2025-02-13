from __future__ import annotations

import io  # NoQA: TC003
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    import fractions as frac
    from typing import Optional, Union

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


@overload
def prod(x: tuple[float, myint]) -> float: ...


@overload
def prod(x: tuple[frac.Fraction, myint]) -> frac.Fraction: ...


def prod(x):
    """docstring"""
    return x[0] * x[1]


def print_value(x: Union[frac.Fraction, myint]) -> None:  # NoQA: UP007
    """docstring"""
    print('value:', x)
