"""Test with nested classes."""


class A:
    class B:  # NoQA: D106
        pass


class C(A.B):
    pass
