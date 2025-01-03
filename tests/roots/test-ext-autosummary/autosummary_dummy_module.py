from os import path
from typing import Union

from autosummary_class_module import Class

__all__ = [
    'CONSTANT1',
    'Exc',
    'Foo',
    '_Baz',
    'bar',
    'qux',
    'path',
]

#: module variable
CONSTANT1 = None
CONSTANT2 = None


class Foo:
    #: class variable
    CONSTANT3 = None
    CONSTANT4 = None

    class Bar:  # NoQA: D106
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


def bar(x: Union[int, str], y: int = 1) -> None:  # NoQA: UP007
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

considered_as_imported = Class()
non_imported_member = Class()
""" This attribute has a docstring, so it is recognized as a not-imported member """
