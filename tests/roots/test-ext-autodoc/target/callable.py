class Callable():
    """A callable object that behaves like a function."""

    def __call__(self, arg1, arg2, **kwargs):
        pass

    def method(self, arg1, arg2):
        """docstring of Callable.method()."""
        pass


function = Callable()
method = function.method
