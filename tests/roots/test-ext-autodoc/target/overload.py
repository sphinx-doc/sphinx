from typing import overload


@overload
def sum(x: int, y: int) -> int:
    ...


@overload
def sum(x: float, y: float) -> float:
    ...


@overload
def sum(x: str, y: str) -> str:
    ...


def sum(x, y):
    """docstring"""
    return x + y


class Math:
    """docstring"""

    @overload
    def sum(self, x: int, y: int) -> int:
        ...

    @overload
    def sum(self, x: float, y: float) -> float:
        ...

    @overload
    def sum(self, x: str, y: str) -> str:
        ...

    def sum(self, x, y):
        """docstring"""
        return x + y
