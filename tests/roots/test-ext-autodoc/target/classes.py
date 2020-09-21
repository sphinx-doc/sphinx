from typing import Generic, TypeVar


T = TypeVar("T")


class Foo:
    pass


class Bar:
    def __init__(self, x, y):
        pass


class Baz:
    def __new__(cls, x, y):
        pass


class Qux(Generic[T]):
    def __init__(self, x, y):
        pass
