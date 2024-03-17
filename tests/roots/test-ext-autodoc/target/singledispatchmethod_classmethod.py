from functools import singledispatchmethod


class Foo:
    """docstring"""

    @singledispatchmethod
    @classmethod
    def class_meth(cls, arg, kwarg=None):
        """A class method for general use."""
        pass

    @class_meth.register(int)
    @class_meth.register(float)
    @classmethod
    def _class_meth_int(cls, arg, kwarg=None):
        """A class method for numbers."""
        pass

    @class_meth.register(str)
    @classmethod
    def _class_meth_str(cls, arg, kwarg=None):
        """A class method for str."""
        pass

    @class_meth.register
    @classmethod
    def _class_meth_dict(cls, arg: dict, kwarg=None):
        """A class method for dict."""
        # This function tests for specifying type through annotations
        pass
