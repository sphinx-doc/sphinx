Test Java Without Third Dependencies
====================================

In case we need to test documentation for projects that consume only Java native libraries
only is needed to define `conf.py` with flavor `java`.

Simple doctest blocks
---------------------

>>> System.out.println(1+1);
2

>>> int x = 8 / 0;
Exception java.lang.ArithmeticException: / by zero
      at (#1:1)

Special directives
------------------

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

    List<String> result = Arrays.asList("Python", "Java");
    System.out.println(result);

.. javatestoutput::

    [Python, Java]

Streams Example
~~~~~~~~~~~~~~~

.. javatestcode::

    import java.util.Arrays

    int result = Arrays.asList(1, 2, 3, 4, 5, 7).stream().filter(x -> x > 4).findFirst().get();
    System.out.println(result);

.. javatestoutput::

    5

Handling Escape Sequences
-------------------------

.. note::

    As part of Sphinx Java there is a fixed length assigned from `\t` to `4 blank spaces`, please consider
    that scope as part of your documentation examples.

.. javatestcode::

    System.out.println("Hello. My name is:\tDavid");
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

Handling Bad Input
------------------

.. javatestcode::

    print("Hello World!");

.. javatestoutput::

    Error:
    cannot find symbol
      symbol:   method print(java.lang.String)
    print("Hello World!");
    ^---^
