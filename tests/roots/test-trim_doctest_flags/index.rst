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

.. doctest_block::

   >>> datetime.date.now()   # doctest: +QUUX
   datetime.date(2008, 1, 1)
