

.. DEBUG
     members=['A', 'B', 'CONST', 'CONST2', 'MyTestExc', 'a', 'b', 'c']
     all=['B', 'CONST2', 'MyTestExc', 'a', 'b']
     all_refs=[':class:`B <foopackage.B>`', ':data:`~foopackage.subbar.foo.CONST2`', ':exc:`MyTestExc <foopackage.MyTestExc>`', ':func:`a <foopackage.a>`', ':func:`b <foopackage.b>`']
     exceptions=['MyTestExc']
     classes=['A', 'B']
     functions=['a', 'b', 'c']
     data=['CONST2']
     private_refs=[':class:`A <foopackage.A>`', ':func:`c <foopackage.c>`']
     members_complete=['A', 'B', 'CONST', 'CONST2', 'MyTestExc', '_d', 'a', 'b', 'c', 'x', 'y']
     members_complete_table=['.. list-table::', '', '   * - :class:`A <foopackage.A>`', '     - Class `A`.', '   * - :class:`B <foopackage.B>`', '     - Class `B`.', '   * - :data:`CONST <CONST>`', '     - int([x]) -> integer int(x, base=10) -> integer', '   * - :data:`CONST2 <CONST2>`', '     - int([x]) -> integer int(x, base=10) -> integer', '   * - :exc:`MyTestExc <foopackage.MyTestExc>`', '     - Custom exception.', '   * - :func:`_d <foopackage._d>`', '     - Private function `_d`.', '   * - :func:`a <foopackage.a>`', '     - Function `a` with three arguments.', '   * - :func:`b <foopackage.b>`', '     - Function `b` with three arguments.', '   * - :func:`c <foopackage.c>`', '     - Function `c` that is not in ``__all__``.', '   * - :func:`x <foopackage.subbar.foo.x>`', '     - Function `x` that is not in ``__all__``.', '   * - :func:`y <foopackage.subbar.foo.y>`', '     - Function `y` with three arguments and a verbose docstring.', '']
     members_complete_refs=[':class:`A <foopackage.A>`', ':class:`B <foopackage.B>`', ':data:`CONST <CONST>`', ':data:`CONST2 <foopackage.subbar.foo.CONST2>`', ':exc:`MyTestExc <foopackage.MyTestExc>`', ':func:`_d <foopackage._d>`', ':func:`a <foopackage.a>`', ':func:`b <foopackage.b>`', ':func:`c <foopackage.c>`', ':func:`x <foopackage.subbar.foo.x>`', ':func:`y <foopackage.subbar.foo.y>`']
     members_complete_fullnames=['foopackage.A', 'foopackage.B', 'CONST', 'CONST2', 'foopackage.MyTestExc', 'foopackage._d', 'foopackage.a', 'foopackage.b', 'foopackage.c', 'foopackage.subbar.foo.x', 'foopackage.subbar.foo.y']
     private=['A', 'c']
     (all + private)=['B', 'CONST2', 'MyTestExc', 'a', 'b', 'A', 'c']
     all_private=['A', 'B', 'CONST2', 'MyTestExc', 'a', 'b', 'c']
     pkgname=foopackage
     submodules=[]
     subpackages=['foopackage.subbar']
   END DEBUG


foopackage package
==================


.. currentmodule:: foopackage

.. automodule:: foopackage
    :members: A, B, CONST, CONST2, MyTestExc, a, b, c
    :undoc-members:
    :show-inheritance:


    Subpackages:

    .. toctree::
       :maxdepth: 1

       foopackage.subbar

    Summary
    -------

    Exceptions:

    .. autosummary::
        :nosignatures:

        MyTestExc

    Classes:

    .. autosummary::
        :nosignatures:

        A
        B

    Functions:

    .. autosummary::
        :nosignatures:

        a
        b
        c

    Data:

    .. autosummary::
        :nosignatures:

        CONST2

    ``__all__``: :class:`B <foopackage.B>`, :data:`~foopackage.subbar.foo.CONST2`, :exc:`MyTestExc <foopackage.MyTestExc>`, :func:`a <foopackage.a>`, :func:`b <foopackage.b>`

    Reference
    ---------

