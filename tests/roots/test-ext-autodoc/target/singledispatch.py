from functools import singledispatch


@singledispatch
def func(arg, kwarg=None):
    """A function for general use."""
    pass


@func.register(int)
def _func_int(arg, kwarg=None):
    """A function for int."""
    pass


@func.register(str)
def _func_str(arg, kwarg=None):
    """A function for str."""
    pass
