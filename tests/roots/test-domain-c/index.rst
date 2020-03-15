test-domain-c
=============

directives
----------

.. c:function:: int hello(const char *name)

   :rtype: int

.. c:function:: MyStruct hello2(char *name)

   :rtype: MyStruct

.. c:member:: float Sphinx.version
.. c:var:: int version

.. c:macro::  IS_SPHINX
.. c:macro::  SPHINX(arg1, arg2)

.. c:struct:: MyStruct
.. c:union:: MyUnion
.. c:enum:: MyEnum

   .. c:enumerator:: MyEnumerator

      :c:enumerator:`MyEnumerator`

   :c:enumerator:`MyEnumerator`

:c:enumerator:`MyEnumerator`

.. c:type:: Sphinx
.. c:type:: int SphinxVersionNum


.. c:struct:: A

   .. c:union:: @data

      .. c:member:: int a

- :c:member:`A.@data.a`
- :c:member:`A.a`

- :c:expr:`unsigned int`
- :c:texpr:`unsigned int`

.. c:var:: A a

- :c:expr:`a->b`
- :c:texpr:`a->b`
