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
- a non-existing role:
  :external:py:nope:`something`

.. default-domain:: cpp

- a type where the default domain is used to find the role:
  :external:type:`std::uint8_t`
- a non-existing role in default domain:
  :external:nope:`somethingElse`

- two roles in ``std`` which can be found without a default domain:

  - :external:doc:`docname`
  - :external:option:`ls -l`


- a function with explicit inventory:
  :external+inv:c:func:`CFunc`
- a class with explicit non-existing inventory, which also has upper-case in name:
  :external+invNope:cpp:class:`foo::Bar`

- An object type being mistakenly used instead of a role name:

  - :external+inv:c:function:`CFunc`
  - :external+inv:function:`CFunc`

- explicit title:
  :external:cpp:type:`FoonsTitle <foons>`
