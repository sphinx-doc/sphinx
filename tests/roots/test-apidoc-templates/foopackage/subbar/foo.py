"""This is the leaf module of the package."""


__all__ = ['y', 'z', 'MyTestExc2', 'CONST2']
__private__ = ['x', 'A2', 'B2']


CONST2 = 2
"""A constant defined for the module."""

CONST3 = 3
"""A constant defined for the module which won't show up in the data
summary."""


def y(arg1, arg2, arg3=1):
    """Function `y` with three arguments and a verbose docstring. This function
    has some explantory text in its docstring so that we can test
    that summaries get extracted properly.

    Normally, it is recommended that we have a very short first sentence and
    then a paragraph break. Here, we rely on being able to extract the first
    sentence when this is not the case.
    That is, only the first sentence should show up in the summary table.

    Args:
        arg1: The first argument
        arg2: The second argument
        arg3: The third argument
    """


def z(arg1, arg2, arg3=1):
    """Function `z` with three arguments."""


def x(arg1, arg2, arg3=1):
    """Function `x` that is not in ``__all__``."""


def _v(arg1, arg2, arg3):
    """Private function `_v`."""

def _d2(arg1, arg2, arg3):
    """Private function `_d2`."""

class A2:
    """Class `A2`."""
    pass

class B2(A2):
    """Class `B2`."""
    pass

class MyTestExc2(ValueError):
    """custom exception."""
    pass
