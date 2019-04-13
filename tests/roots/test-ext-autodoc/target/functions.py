from functools import partial


def func():
    pass


partial_func = partial(func)

builtin_func = print
partial_builtin_func = partial(print)
