Test Java Without Third Dependencies
====================================

In case we need to test documentation for projects that consume only Java native libraries
only is needed to define `conf.py` with flavor `java`.

Simple javadoctest blocks
-------------------------

Without directives:

>>> System.out.println(1+2+3)
6

With directives:

.. javadoctest::
   :skipif: docker == true

    >>> System.out.println("A simple block test inside a directive.")
    A1 simple block test inside a directive.

Special directives
------------------

* javadoctest

.. javadoctest::

    >>> System.out.println(1+4+9)
    14

* javatestcode / javatestoutput

Arithmetic Operators Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. javatestcode::

    int x = 10_000;
    int y = 23_000;
    int result = x  + y;
    System.out.println(result);

.. javatestoutput::

    33000

Array to List Example
~~~~~~~~~~~~~~~~~~~~~

.. javatestcode::

    import java.util.Arrays
    import java.util.List

    List<String> result = Arrays.asList("Topaya", "Sayan", "Huacho");
    System.out.println(result);

.. javatestoutput::

    [Topaya, Sayan, Huacho]

Streams Example
~~~~~~~~~~~~~~~

.. javatestcode::

    import java.util.Arrays

    int result = Arrays.asList(1, 2, 3, 4, 5, 7).stream().filter(x -> x > 4).findFirst().get();
    System.out.println(result);

.. javatestoutput::

    5

* options for javadoctest / javatestcode / javatestoutput blocks

.. javatestcode::
   :hide:

    System.out.println("Output         text.");

.. javatestoutput::
   :hide:
   :options: +NORMALIZE_WHITESPACE

    Output text.

.. javadoctest::
   :javaversion: >=11, <19

    >>> System.out.println(1728+1)
    1729

.. javadoctest::
   :javaversion: < 11.0

    >>> System.out.println("Ramanujan")
    Ramanujan

.. javatestcode::
   :javaversion: > 11

   System.out.print(6174);

.. javatestoutput::
   :javaversion: > 11

   6174

Handling Escape Sequences
-------------------------

.. note::

    As part of Sphinx Java there is a fixed length assigned from `\t` to `4 blank spaces`, please consider
    that scope as part of your documentation examples.

.. javatestcode::

    System.out.println("Hello. My name is:\tDavid\n");
    System.out.println("Hello. My name is:\nDavid");

.. javatestoutput::

    Hello. My name is:    David
    Hello. My name is:
    David

Non-ASCII result
----------------

>>> System.out.println("umlauts: äöü.")
umlauts: äöü.

>>> System.out.println("Japanese: 日本語")
Japanese: 日本語

TO DO
-----

Handling bad input is not implemented for now. These are examples not supported yet.

.. code-block:: java

    >>> System.out.println(1/0)
    Exception java.lang.ArithmeticException: / by zero
          at (#1:1)

    >>> int x = 8 / 0
    Exception java.lang.ArithmeticException: / by zero
          at (#1:1)

    .. javatestcode::

        System.out.println(1+1) 9

    .. javatestoutput::

        Error:
        ';' expected
        System.out.println(1+1) 9
                           ^
