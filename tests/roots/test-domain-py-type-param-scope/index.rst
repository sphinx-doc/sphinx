test-domain-py-type-param-scope
===============================

.. py:function:: func[T](x: T, /) -> tuple[T, ...]
                 func[T](x: T, y: T, /) -> tuple[T, T]

.. py:class:: Spam[T]

   A powerful frobnicator.

   .. py:method:: eggs(arg: int) -> T

      Return the result after frobnicating.

.. py:class:: RealT

   A documented class.

.. py:class:: Box[RealT]

   .. py:method:: get() -> RealT

.. py:function:: outside(x: T) -> RealT
