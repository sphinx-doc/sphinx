from functools import partial


def func1():
    """docstring of func1"""
    pass


func2 = partial(func1)
func3 = partial(func1)
func3.__doc__ = "docstring of func3"
