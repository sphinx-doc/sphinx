tabular and tabulary
====================

simple table
------------

======= =======
header1 header2
======= =======
cell1-1 cell1-2
cell2-1 cell2-2
cell3-1 cell3-2
======= =======

table having :widths: option
----------------------------

.. _mytabular:

.. table::
   :widths: 30,70
   :name: namedtabular

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

See :ref:`this <mytabular>`, same as namedtabular_.

table having :align: option (tabulary)
--------------------------------------

.. table::
   :align: right

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

table having :align: option (tabular)
-------------------------------------

.. table::
   :align: left
   :widths: 30,70

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

table with tabularcolumn
------------------------

.. tabularcolumns:: |c|c|

======= =======
header1 header2
======= =======
cell1-1 cell1-2
cell2-1 cell2-2
cell3-1 cell3-2
======= =======

table with cell in first column having three paragraphs
-------------------------------------------------------

+--------------+
| header1      |
+==============+
| cell1-1-par1 |
|              |
| cell1-1-par2 |
|              |
| cell1-1-par3 |
+--------------+


table having caption
--------------------

.. list-table:: caption for table
   :header-rows: 1

   * - header1
     - header2
   * - cell1-1
     - cell1-2
   * - cell2-1
     - cell2-2
   * - cell3-1
     - cell3-2

table having verbatim
---------------------

.. list-table::
   :header-rows: 1

   * - header1
     - header2
   * - ::

         hello world

     - cell1-2
   * - cell2-1
     - cell2-2
   * - cell3-1
     - cell3-2

table having both :widths: and problematic cell
-----------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30,70

   * - header1
     - header2
   * - + item1
       + item2
     - cell1-2
   * - cell2-1
     - cell2-2
   * - cell3-1
     - cell3-2

table having problematic cell
-----------------------------

.. list-table::
   :header-rows: 1

   * - header1
     - header2
   * - + item1
       + item2
     - cell1-2
   * - cell2-1
     - cell2-2
   * - cell3-1
     - cell3-2

table having both stub columns and problematic cell
---------------------------------------------------

.. list-table::
   :header-rows: 1
   :stub-columns: 2

   * - header1
     - header2
     - header3
   * - + instub1-1a
       + instub1-1b
     - instub1-2
     - notinstub1-3
   * - cell2-1
     - cell2-2
     - cell2-3
