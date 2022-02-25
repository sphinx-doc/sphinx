viewcode
========

.. py:module:: not_a_package

.. py:function:: func1(a, b)

   This is func1

.. py:function:: not_a_package.submodule.func1(a, b)

   This is func1

.. py:module:: not_a_package.submodule

.. py:class:: Class1

   This is Class1

.. py:class:: Class3

   This is Class3

.. py:class:: not_a_package.submodule.Class1

   This is Class1

.. literalinclude:: not_a_package/__init__.py
   :language: python
   :pyobject: func1

.. literalinclude:: not_a_package/submodule.py
   :language: python
   :pyobject: func1

.. py:attribute:: not_a_package.submodule.Class3.class_attr

   This is the class attribute class_attr
