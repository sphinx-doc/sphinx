from functools import partial, wraps


def func():
    pass


async def coroutinefunc():
    pass


async def asyncgenerator():
    yield

partial_func = partial(func)
partial_coroutinefunc = partial(coroutinefunc)

builtin_func = print
partial_builtin_func = partial(print)

class _Callable:
    def __call__():
        pass

def _decorator(f):
    @wraps(f)
    def wrapper(*args, **kw):
        return f(*args, **kw)
    return wrapper

wrapped_callable = _decorator(_Callable())
