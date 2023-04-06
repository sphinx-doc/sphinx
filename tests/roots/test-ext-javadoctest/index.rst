Test Java Without Third Dependencies
====================================

In case we need to test documentation for projects that consume only Java native libraries
only is needed to define `conf.py` with flavor `java`.

Arithmetic Operators Example
----------------------------

.. testcode::

    int x = 10_000;
    int y = 23_000;
    int result = x  + y;
    System.out.println(result);

.. testoutput::

    33000

Array to List Example
---------------------

.. testcode::

    import java.util.Arrays
    import java.util.List

    List<String> result = Arrays.asList("Python", "Java");
    System.out.println(result);

.. testoutput::

    [Python, Java]

Streams Example
---------------

.. testcode::

    import java.util.Arrays

    int result = Arrays.asList(1, 2, 3, 4, 5, 7).stream().filter(x -> x > 4).findFirst().get();
    System.out.println(result);

.. testoutput::

    5