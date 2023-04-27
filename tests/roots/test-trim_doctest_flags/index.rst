test-trim_doctest_flags
=======================

.. code-block:: pycon

   >>> datetime.date.now()   # doctest: +FOO
   datetime.date(2008, 1, 1)

.. code-block:: none

   >>> datetime.date.now()   # doctest: +BAR
   datetime.date(2008, 1, 1)

.. code-block:: guess

   # vim: set filetype=pycon
   >>> datetime.date.now()   # doctest: +BAZ
   datetime.date(2008, 1, 1)

.. testcode::

   >>> datetime.date.now()   # doctest: +QUX
   datetime.date(2008, 1, 1)

.. doctest::

   >>> datetime.date.now()   # doctest: +QUUX
   datetime.date(2008, 1, 1)

.. doctest::
   :trim-doctest-flags:

   >>> datetime.date.now()   # doctest: +CORGE
   datetime.date(2008, 1, 1)

.. doctest::
   :no-trim-doctest-flags:

   >>> datetime.date.now()   # doctest: +GRAULT
   datetime.date(2008, 1, 1)
