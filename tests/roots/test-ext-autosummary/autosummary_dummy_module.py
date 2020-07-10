from os import path  # NOQA
from typing import Union


class Foo:
    class Bar:
        pass

    def __init__(self):
        pass

    def bar(self):
        pass

    @property
    def baz(self):
        pass


class _Baz:
    pass


def bar(x: Union[int, str], y: int = 1) -> None:
    pass


def _quux():
    pass


class Exc(Exception):
    pass


class _Exc(Exception):
    pass


#: a module-level attribute
qux = 2
