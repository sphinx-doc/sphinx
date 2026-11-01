class Foo:
    """docstring of Foo."""


class Exc(Exception):
    """docstring of Exc."""

    attribute = None
    """docstring of attribute."""

    def method(self):
        """docstring of method."""
        pass


class Outer:
    """docstring of Class"""

    class Exc(Exception):
        """docstring of Class.Exc."""
        pass
