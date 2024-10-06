"""Test with nested classes.
"""


class A:
    class B:
        pass


class C(A.B):
    pass
