When doing name resolution there are 4 different idenOrOps:

- identifier
- built-in operator
- user-defined literal
- type conversion

.. cpp:function:: int g()
.. cpp:function:: int operator+(int, int)
.. cpp:function:: int operator""_lit()

.. cpp:class:: B

   .. cpp:function:: operator int()

   Functions that can't be found:

   - :cpp:func:`int h()`
   - :cpp:func:`int operator+(bool, bool)`
   - :cpp:func:`int operator""_udl()`
   - :cpp:func:`operator bool()`

   Functions that should be found:

   - :cpp:func:`int g()`
   - :cpp:func:`int operator+(int, int)`
   - :cpp:func:`int operator""_lit()`
   - :cpp:func:`operator int()`
