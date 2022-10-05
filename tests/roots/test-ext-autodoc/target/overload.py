from typing import Any, overload


@overload
def sum(x: int, y: int = 0) -> int:
    ...


@overload
def sum(x: "float", y: "float" = 0.0) -> "float":
    ...


@overload
def sum(x: str, y: str = ...) -> str:
    ...


def sum(x, y=None):
    """docstring"""
    return x + y


class Math:
    """docstring"""

    @overload
    def sum(self, x: int, y: int = 0) -> int:
        ...

    @overload
    def sum(self, x: "float", y: "float" = 0.0) -> "float":
        ...

    @overload
    def sum(self, x: str, y: str = ...) -> str:
        ...

    def sum(self, x, y=None):
        """docstring"""
        return x + y


class Foo:
    """docstring"""

    @overload
    def __new__(cls, x: int, y: int) -> "Foo":
        ...

    @overload
    def __new__(cls, x: "str", y: "str") -> "Foo":
        ...

    def __new__(cls, x, y):
        pass


class Bar:
    """docstring"""

    @overload
    def __init__(cls, x: int, y: int) -> None:
        ...

    @overload
    def __init__(cls, x: "str", y: "str") -> "None":
        ...

    def __init__(cls, x, y):
        pass


class Meta(type):
    @overload
    def __call__(cls, x: int, y: int) -> Any:
        ...

    @overload
    def __call__(cls, x: "str", y: "str") -> "Any":
        ...

    def __call__(cls, x, y):
        pass


class Baz(metaclass=Meta):
    """docstring"""
