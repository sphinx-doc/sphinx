import sys
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
        """A class method for int."""
        pass

    @class_meth.register(str)
    @classmethod
    def _class_meth_str(cls, arg, kwarg=None):
        """A class method for str."""
        pass

    if sys.version_info[:2] >= (3, 9):
        # registration of a singledispatch'ed classmethod via
        # type annotation is not supported prior to Python 3.9
        #
        # See: https://github.com/python/cpython/issues/83860

        @class_meth.register
        @classmethod
        def _class_meth_dict(cls, arg: dict, kwarg=None):
            """A class method for dict."""
            # This function tests for specifying type through annotations
            pass
