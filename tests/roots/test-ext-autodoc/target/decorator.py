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


def deco_call(cls):
    _original = cls.__call__

    @wraps(_original)
    def wrapper(self, *args, **kwargs):
        return _original(self, *args, **kwargs)

    cls.__call__ = wrapper
    return cls


@deco_call
class BarCall:
    def __call__(self, name=None, age=None):
        pass


def deco_new(cls):
    _original = cls.__new__

    @wraps(_original)
    def wrapper(cls, *args, **kwargs):
        return _original(cls, *args, **kwargs)

    cls.__new__ = wrapper
    return cls


@deco_new
class BarNew:
    def __new__(cls, name=None, age=None):
        pass


def deco_init(cls):
    _original = cls.__init__

    @wraps(_original)
    def wrapper(self, *args, **kwargs):
        _original(self, *args, **kwargs)

    cls.__init__ = wrapper
    return cls


@deco_init
class BarInit:
    def __init__(self, name=None, age=None):
        pass
