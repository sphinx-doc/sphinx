from functools import partial


def func():
    pass


async def coroutinefunc():
    pass


async def asyncgenerator():  # NoQA: RUF029
    yield


partial_func = partial(func)
partial_coroutinefunc = partial(coroutinefunc)

builtin_func = print
partial_builtin_func = partial(print)


def slice_arg_func(arg: 'float64[:, :]'):  # NoQA: F821
    pass
