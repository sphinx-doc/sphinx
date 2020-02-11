class A:
    """A(foo, bar)"""


class B:
    """B(foo, bar)"""
    def __init__(self):
        """B(foo, bar, baz)"""


class C:
    """C(foo, bar)"""
    def __new__(cls):
        """C(foo, bar, baz)"""


class D:
    def __init__(self):
        """D(foo, bar, baz)"""
