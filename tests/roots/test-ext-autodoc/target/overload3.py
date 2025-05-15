import typing
from typing import TYPE_CHECKING, overload

import typing_extensions
from typing_extensions import overload as over_ext  # noqa: UP035


@overload
def test(x: int) -> int: ...
@typing.overload
def test(x: list[int]) -> list[int]: ...
@over_ext
def test(x: str) -> str: ...
@typing_extensions.overload
def test(x: float) -> float: ...
def test(x):
    """Documentation."""
    return x
