from typing import overload


@overload
def overloaded(x: int) -> int: ...
@overload
def overloaded(x: str, y: int = 1) -> str: ...
def overloaded(x, y=1):
    """Two overloads."""


def regular(a, b=1):
    """A single signature."""
