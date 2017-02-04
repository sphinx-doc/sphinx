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

longtable having :widths: option
--------------------------------

.. table::
   :class: longtable
   :widths: 30,70

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

longtable having caption
------------------------

.. list-table:: caption for longtable
   :class: longtable
   :header-rows: 1

   * - header1
     - header2
   * - cell1-1
     - cell1-2
   * - cell2-1
     - cell2-2
   * - cell3-1
     - cell3-2

longtable having verbatim
-------------------------

.. list-table::
   :class: longtable
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

longtable having both :widths: and problematic cell
---------------------------------------------------

.. list-table::
   :class: longtable
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

longtable having problematic cell
---------------------------------

.. list-table::
   :class: longtable
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
