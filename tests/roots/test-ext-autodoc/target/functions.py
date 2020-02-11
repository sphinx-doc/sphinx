from functools import partial


def func():
    pass


async def coroutinefunc():
    pass

partial_func = partial(func)
partial_coroutinefunc = partial(coroutinefunc)

builtin_func = print
partial_builtin_func = partial(print)
