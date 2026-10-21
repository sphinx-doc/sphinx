"""
submodule
"""  # ruff: ignore[multi-line-summary-first-line]

raise RuntimeError('This module should not get imported')  # ruff: ignore[raw-string-in-exception, raise-vanilla-args]


def decorator(f):
    return f


@decorator
def func1(a, b):
    """
    this is func1
    """  # ruff: ignore[multi-line-summary-first-line]
    return a, b


@decorator
class Class1:
    """this is Class1"""


class Class3:
    """this is Class3"""

    class_attr = 42
    """this is the class attribute class_attr"""
