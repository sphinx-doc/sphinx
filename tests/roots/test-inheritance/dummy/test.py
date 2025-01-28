r"""Test with a class diagram like this::

           A
          / \
         B   C
        / \ / \
       E   D   F

"""  # NoQA: D208


class A:
    pass


class B(A):
    pass


class C(A):
    pass


class D(B, C):
    pass


class E(B):
    pass


class F(C):
    pass
