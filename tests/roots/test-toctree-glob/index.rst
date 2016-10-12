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
   :reverse:

   foo
   bar/index
   bar/*
   baz
   qux/index
