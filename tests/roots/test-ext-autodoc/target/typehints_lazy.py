from __future__ import annotations

from typing import (
    Generic,
    Optional as Opt,  # rename to test resolution
    TypeVar,
)


_T = TypeVar("_T")


class LazyGeneric(Generic[_T]):
    """Generic docstring ;)

    :param x: maybe also generic
    """

    def __init__(self, x: Opt[_T]) -> None:
        ...


class LazyInit:
    """I am lazy!

    :param x: this is x
    """
    def __init__(self, x: Opt[int]) -> None:
        ...
