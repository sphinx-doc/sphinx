class A:
    """A(foo, bar)"""


class B:
    """B(foo, bar)"""

    def __init__(self) -> None:
        """B(foo, bar, baz)"""


class C:
    """C(foo, bar)"""

    def __new__(cls):
        """C(foo, bar, baz)"""


class D:
    def __init__(self) -> None:
        """D(foo, bar, baz)"""


class E:
    def __init__(self) -> None:
        r"""E(foo: int, bar: int, baz: int) -> None \
        E(foo: str, bar: str, baz: str) -> None \
        E(foo: float, bar: float, baz: float)"""  # NoQA: D209


class F:
    def __init__(self) -> None:
        """F(foo: int, bar: int, baz: int) -> None
        F(foo: str, bar: str, baz: str) -> None
        F(foo: float, bar: float, baz: float)"""  # NoQA: D209
