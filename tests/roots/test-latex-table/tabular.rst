taburar and taburary
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

.. table::
   :widths: 30,70

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

table having :align: option (tabulary)
--------------------------------------

.. table::
   :align: center

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
