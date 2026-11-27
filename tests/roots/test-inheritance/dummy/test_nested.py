"""Test with nested classes."""


class A:
    class B:  # ruff: ignore[undocumented-public-nested-class]
        pass


class C(A.B):
    pass
