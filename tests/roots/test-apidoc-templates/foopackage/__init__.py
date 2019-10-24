"""This is the foo package."""

__all__ = ['a', 'b', 'B', 'MyTestExc', 'CONST2']
__private__ = ['A', 'c']
__known_refs__ = {'CONST2': ':data:`~foopackage.subbar.foo.CONST2`'}

from .subbar.foo import x, y, CONST2

CONST = 1
"""A constant defined for the package."""


def a(arg1, arg2, arg3=1):
    """Function `a` with three arguments.

    :param arg1: The first argument
    :param arg2: The second argument
    :param arg3: The third argument
    """


def b(arg1, arg2, arg3=1):
    """Function `b` with three arguments."""


def c(arg1, arg2, arg3=1):
    """Function `c` that is not in ``__all__``."""


def _d(arg1, arg2, arg3):
    """Private function `_d`."""


class A:
    """Class `A`."""
    pass


class B(A):
    """Class `B`."""
    pass


class MyTestExc(ValueError):
    """Custom exception."""
    pass
