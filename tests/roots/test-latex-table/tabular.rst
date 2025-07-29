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

table having widths option
--------------------------

.. _mytabular:

.. table::
   :widths: 30,70
   :name: namedtabular
   :class: booktabs, colorrows

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

See :ref:`this <mytabular>`, same as namedtabular_.

tabulary having align option
----------------------------

.. table::
   :align: right

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

tabular having align option
---------------------------

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

table with tabularcolumns
-------------------------

.. tabularcolumns:: cc

======= =======
header1 header2
======= =======
cell1-1 cell1-2
cell2-1 cell2-2
cell3-1 cell3-2
======= =======

table having three paragraphs cell in first col
-----------------------------------------------

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

table having formerly problematic
---------------------------------

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

table having widths and formerly problematic
--------------------------------------------

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

table having stub columns and formerly problematic
--------------------------------------------------

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
