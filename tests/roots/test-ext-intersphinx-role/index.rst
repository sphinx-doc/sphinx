- ``module1`` is only defined in ``inv``:
  :external:py:mod:`module1`

.. py:module:: module2

- ``module2`` is defined here and also in ``inv``, but should resolve to inv:
  :external:py:mod:`module2`

- ``module3`` is not defined anywhere, so should warn:
  :external:py:mod:`module3`

.. py:module:: module10

- ``module10`` is only defined here, but should still not be resolved to:
  :external:py:mod:`module10`


- a function in inv:
  :external:py:func:`module1.func`
- a method, but with old style inventory prefix, which shouldn't work:
  :external:py:meth:`inv:Foo.bar`
