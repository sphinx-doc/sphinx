.. c:namespace:: ids_vs_tags3

.. c:function:: void f1(int i)

.. c:struct:: f1

	.. c:var:: int i


.. c:struct:: f2

	.. c:var:: int i

.. c:function:: void f2(int i)

- :c:var:`f1.i`, resolves to the function parameter
- :c:var:`struct f1.i`, resolves to struct f1.i
- :c:var:`f2.i`, resolves to the function parameter
- :c:var:`struct f2.i`, resolves to struct f2.i
