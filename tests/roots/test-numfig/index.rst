test-tocdepth
=============

.. toctree::
   :numbered:

   foo
   bar

.. _fig1:

.. figure:: rimg.png

   should be Fig.1

.. figure:: rimg.png

   should be Fig.2

.. _table1:

.. csv-table:: should be Table 1
   :header-rows: 0

   hello,world

.. csv-table:: should be Table 2
   :header-rows: 0

   hello,world

.. _code1:

.. code-block:: python
   :caption: should be List 1

   print('hello world')

.. code-block:: python
   :caption: should be List 2

   print('hello world')


* Fig.1 is :numref:`fig1`
* Fig.2.2 is :numref:`Figure# <fig22>`
* Table.1 is :numref:`table1`
* Table.2.2 is :numref:`Table:# <table22>`
* List.1 is :numref:`code1`
* List.2.2 is :numref:`Code-# <code22>`
