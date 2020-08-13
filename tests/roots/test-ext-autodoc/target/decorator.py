from functools import wraps


def deco1(func):
    """docstring for deco1"""
    @wraps(func)
    def wrapper():
        return func()

    return wrapper


def deco2(condition, message):
    """docstring for deco2"""
    def decorator(func):
        def wrapper():
            return func()

        return wrapper
    return decorator


@deco1
def foo(name=None, age=None):
    pass


class Bar:
    @deco1
    def meth(self, name=None, age=None):
        pass


def deco_init(cls):
    _original_init = cls.__init__

    @wraps(_original_init)
    def wrapped(self, *args, **kwargs):
        _original_init(self, *args, **kwargs)

    cls.__init__ = wrapped
    return cls

@deco_init
class Baz:
    def __init__(self, name=None, age=None):
        pass
