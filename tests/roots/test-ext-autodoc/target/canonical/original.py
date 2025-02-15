class Foo:
    """docstring"""

    def meth(self) -> None:
        """docstring"""


def bar():
    class Bar:
        """docstring"""

    return Bar


Bar = bar()
