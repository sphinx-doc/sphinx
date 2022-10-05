from functools import partial


def func1(a, b, c):
    """docstring of func1"""
    pass


func2 = partial(func1, 1)
func3 = partial(func2, 2)
func3.__doc__ = "docstring of func3"
func4 = partial(func3, 3)
