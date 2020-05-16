r"""

    Test with a class diagram like this::

          _A
           |
           A       G
          / \     / \
         B   C  _H   I
        / \ / \ /
       E   D   F
           |
           J
"""

class _A(object):
    pass


class A(_A):
    pass


class B(A):
    pass


class C(A):
    pass


class D(B, C):
    pass


class E(B):
    pass


class G(object):
    pass


class _H(G):
    pass


class I(G):
    pass


class F(C, _H):
    pass


class J(D):
    pass
