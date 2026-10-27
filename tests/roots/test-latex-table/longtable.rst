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

longtable with multirow cell near page footer
---------------------------------------------

.. |lorem| replace::

   Lorem ipsum dolor sit amet consectetur adipiscing elit. Quisque faucibus ex
   sapien vitae pellentesque sem placerat. In id cursus mi pretium tellus duis
   convallis. Tempus leo eu aenean sed diam urna tempor. Pulvinar vivamus
   fringilla lacus nec metus bibendum egestas. Iaculis massa nisl malesuada
   lacinia integer nunc posuere. Ut hendrerit semper vel class aptent taciti
   sociosqu. Ad litora torquent per conubia nostra inceptos himenaeos.

table having ...

* consecutive multirow near footer

.. raw:: latex

   \newpage
   \vspace*{\dimeval{\textheight - 5\baselineskip}}

.. rst-class:: longtable

+-----------+-----------+
| |lorem|   | Cell 1    |
|           +-----------+
|           | Cell 2    |
|           +-----------+
|           | Cell 3    |
|           +-----------+
|           | Cell 4    |
|           +-----------+
|           | Cell 5    |
|           +-----------+
|           | Cell 6    |
|           +-----------+
|           | Cell 7    |
|           +-----------+
|           | Cell 8    |
|           +-----------+
|           | Cell 9    |
|           +-----------+
|           | Cell 10   |
|           +-----------+
|           | Cell 11   |
|           +-----------+
|           | Cell 12   |
|           +-----------+
|           | Cell 13   |
|           +-----------+
|           | Cell 14   |
|           +-----------+
|           | Cell 15   |
|           +-----------+
|           | Cell 16   |
+-----------+-----------+
| |lorem|   |           |
+-----------+-----------+
| |lorem|   |           |
+-----------+-----------+
| |lorem|   |           |
+-----------+-----------+
| |lorem|   |           |
+-----------+-----------+
| |lorem|   |           |
+-----------+-----------+
| |lorem|   |           |
+-----------+-----------+
| |lorem|   |           |
+-----------+-----------+
