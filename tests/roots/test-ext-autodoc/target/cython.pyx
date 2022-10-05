# cython: binding=True
# cython: language_level=3str

def foo(x: int, *args, y: str, **kwargs):
    """Docstring."""


class Class:
    """Docstring."""

    def meth(self, name: str, age: int = 0) -> None:
        """Docstring."""
        pass
