from functools import singledispatchmethod


class Foo:
    """docstring"""

    @singledispatchmethod
    def meth(self, arg, kwarg=None):
        """A method for general use."""
        pass

    @meth.register(int)
    @meth.register(float)
    def _meth_int(self, arg, kwarg=None):
        """A method for int."""
        pass

    @meth.register(str)
    def _meth_str(self, arg, kwarg=None):
        """A method for str."""
        pass
