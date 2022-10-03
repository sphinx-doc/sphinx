from __future__ import annotations

from typing import Generic
from typing import Optional as Opt  # rename to test resolution
from typing import TypeVar

T = TypeVar("T")


class LazyGeneric(Generic[T]):
    """Generic docstring ;)

    :param x: maybe also generic
    """

    def __init__(self, x: Opt[T]) -> None:
        ...


class LazyInit:
    """I am lazy!

    :param x: this is x
    """
    def __init__(self, x: Opt[int]) -> None:
        ...
