"""
submodule
"""
raise RuntimeError('This module should not get imported')


def decorator(f):
    return f


@decorator
def func1(a, b):
    """
    this is func1
    """
    return a, b


@decorator
class Class1(object):
    """
    this is Class1
    """


class Class3(object):
    """
    this is Class3
    """
    class_attr = 42
    """this is the class attribute class_attr"""
