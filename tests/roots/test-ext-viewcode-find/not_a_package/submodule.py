"""
submodule
"""  # NoQA: D212

raise RuntimeError('This module should not get imported')  # NoQA: EM101,TRY003


def decorator(f):
    return f


@decorator
def func1(a, b):
    """
    this is func1
    """  # NoQA: D212
    return a, b


@decorator
class Class1:
    """this is Class1"""


class Class3:
    """this is Class3"""

    class_attr = 42
    """this is the class attribute class_attr"""
