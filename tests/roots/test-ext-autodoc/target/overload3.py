from typing import TYPE_CHECKING, overload
import typing

from typing_extensions import overload as over_ext
import typing_extensions

@overload
def test(x: int) -> int: ...
@typing.overload
def test(x: bool) -> bool: ...
@over_ext
def test(x: str) -> str: ...
@typing_extensions.overload
def test(x: float) -> float: ...
def test(x):
    """Documentation."""
    return x
