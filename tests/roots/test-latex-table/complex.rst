complex tables
==============

grid table
----------

.. rst-class:: nocolorrows

+---------+---------+---------+
| header1 | header2 | header3 |
+=========+=========+=========+
| cell1-1 | cell1-2 | cell1-3 |
+---------+         +---------+
| cell2-1 |         | cell2-3 |
+         +---------+---------+
|         | cell3-2-par1      |
+---------+                   |
| cell4-1 | cell3-2-par2      |
+---------+---------+---------+
| cell5-1                     |
+---------+---------+---------+

grid table with tabularcolumns
------------------------------

.. tabularcolumns:: TTT

+---------+---------+---------+
| header1 | header2 | header3 |
+=========+=========+=========+
| cell1-1 | cell1-2 | cell1-3 |
+---------+         +---------+
| cell2-1 |         | cell2-3 |
+         +---------+---------+
|         | cell3-2-par1      |
+---------+                   |
| cell4-1 | cell3-2-par2      |
+---------+---------+---------+
| cell5-1                     |
+---------+---------+---------+

complex spanning cell
---------------------

table having ...

* consecutive multirow at top of row (1-1 and 1-2)
* consecutive multirow at end of row (1-4 and 1-5)

.. rst-class:: standard

+-----------+-----------+-----------+-----------+-----------+
|           |           |  cell1-3  |           |           |
|           |           +-----------+           |  cell1-5  |
|  cell1-1  |  cell1-2  |           |  cell1-4  |           |
|           |           |  cell2-3  |           +-----------+
|           |           |           |           |  cell3-5  |
+-----------+-----------+-----------+-----------+-----------+
