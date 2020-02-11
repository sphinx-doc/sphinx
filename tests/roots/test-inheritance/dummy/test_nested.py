"""
    Test with nested classes.
"""


class A(object):
    class B(object):
        pass


class C(A.B):
    pass
