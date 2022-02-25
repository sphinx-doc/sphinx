.. _index:

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

.. _table-1:

.. csv-table:: should be Table 1
   :header-rows: 0

   hello,world

.. csv-table:: should be Table 2
   :header-rows: 0

   hello,world

.. _CODE_1:

.. code-block:: python
   :caption: should be List 1

   print('hello world')

.. code-block:: python
   :caption: should be List 2

   print('hello world')


* Fig.1 is :numref:`fig1`
* Fig.2.2 is :numref:`Figure%s <fig22>`
* Table.1 is :numref:`table-1`
* Table.2.2 is :numref:`Table:%s <table22>`
* List.1 is :numref:`CODE_1`
* List.2.2 is :numref:`Code-%s <CODE22>`
* Section.1 is :numref:`foo`
* Section.2.1 is :numref:`bar_a`
* Unnumbered section is :numref:`index`
* Invalid numfig_format 01: :numref:`invalid <fig1>`
* Invalid numfig_format 02: :numref:`Fig %s %s <fig1>`
* Fig.1 is :numref:`Fig.{number} {name} <fig1>`
* Section.1 is :numref:`Sect.{number} {name} <foo>`
