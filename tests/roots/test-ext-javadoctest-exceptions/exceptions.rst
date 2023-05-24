Test Java Without Third Dependencies
====================================

In case we need to test documentation for projects that consume only Java native libraries
only is needed to define `conf.py` with flavor `java`.

Handling Bad Input / Output
---------------------------

.. javatestcode::

    print("Hello World!");

.. javatestoutput::

    Error:
    cannot find symbol
      symbol:   method print(java.lang.String)
    print("Hello World!");
    ^---^