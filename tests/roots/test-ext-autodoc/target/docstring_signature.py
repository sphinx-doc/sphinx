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


class E:
    def __init__(self):
        r"""E(foo: int, bar: int, baz: int) -> None \
        E(foo: str, bar: str, baz: str) -> None \
        E(foo: float, bar: float, baz: float)"""  # NoQA: D209


class F:
    def __init__(self):
        """F(foo: int, bar: int, baz: int) -> None
        F(foo: str, bar: str, baz: str) -> None
        F(foo: float, bar: float, baz: float)"""  # NoQA: D209
