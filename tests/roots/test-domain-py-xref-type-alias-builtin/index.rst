Builtin Type Alias False Positive Test
=======================================

This tests that builtin types like ``list`` in function signatures do not
incorrectly link to class attributes with the same name.


.. py:module:: mymodule

   Module to test builtin type cross-reference false positives.


.. py:class:: MyClass

   A class with an attribute that shadows a builtin type name.

   .. py:attribute:: list
      :value: [1, 2, 3]

      An attribute named ``list`` that shadows the builtin.


.. py:function:: process(items: list) -> None
   :module: mymodule

   Process a list of items.

   The ``list`` type annotation here should NOT link to ``MyClass.list``.
