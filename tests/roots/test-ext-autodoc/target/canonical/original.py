class Foo:
    """docstring"""

    def meth(self):
        """docstring"""


def bar():
    class Bar:
        """docstring"""

    return Bar


Bar = bar()
