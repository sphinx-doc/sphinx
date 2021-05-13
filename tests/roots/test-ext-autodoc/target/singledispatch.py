import inspect
from functools import singledispatch


def assign_signature(func):
    # This is intended to cover more complex signature-rewriting decorators.
    func.__signature__ = inspect.signature(func)
    return func


@singledispatch
def func(arg, kwarg=None):
    """A function for general use."""
    pass


@func.register(int)
@func.register(float)
def _func_int(arg, kwarg=None):
    """A function for int."""
    pass


@func.register(str)
@assign_signature
def _func_str(arg, kwarg=None):
    """A function for str."""
    pass
