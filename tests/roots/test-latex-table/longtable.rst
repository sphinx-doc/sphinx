longtables
==========

longtable
---------

.. table::
   :class: longtable, borderless

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

longtable having widths option
------------------------------

.. _mylongtable:

.. table::
   :class: longtable
   :widths: 30,70
   :name: namedlongtable

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

See mylongtable_, same as :ref:`this one <namedlongtable>`.

longtable having align option
-----------------------------

.. table::
   :align: right
   :class: longtable

   ======= =======
   header1 header2
   ======= =======
   cell1-1 cell1-2
   cell2-1 cell2-2
   cell3-1 cell3-2
   ======= =======

longtable with tabularcolumns
-----------------------------

.. tabularcolumns:: |c|c|

.. table::
   :class: longtable

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

longtable having formerly problematic
-------------------------------------

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

longtable having widths and formerly problematic
------------------------------------------------

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

longtable having stub columns and formerly problematic
------------------------------------------------------

.. list-table::
   :class: longtable
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
