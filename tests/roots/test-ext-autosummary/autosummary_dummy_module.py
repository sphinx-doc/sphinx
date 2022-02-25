from os import path  # NOQA
from typing import Union

__all__ = [
    "CONSTANT1",
    "Exc",
    "Foo",
    "_Baz",
    "bar",
    "qux",
    "path",
]

#: module variable
CONSTANT1 = None
CONSTANT2 = None


class Foo:
    #: class variable
    CONSTANT3 = None
    CONSTANT4 = None

    class Bar:
        pass

    def __init__(self):
        #: docstring
        self.value = 1

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
#: a module-level attribute that has been excluded from __all__
quuz = 2
