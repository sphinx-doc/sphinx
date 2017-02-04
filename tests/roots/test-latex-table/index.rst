test-latex-table
================

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

longtable
---------

.. table::
   :class: longtable

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======
