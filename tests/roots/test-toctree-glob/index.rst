test-toctree-glob
=================

normal order
------------

.. toctree::
   :glob:

   foo
   bar/index
   bar/*
   baz
   qux/index

reversed order
-------------

.. toctree::
   :glob:
   :reversed:

   foo
   bar/index
   bar/*
   baz
   qux/index
