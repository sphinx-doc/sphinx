latex-labels
============

figures
-------

.. _figure1:
.. _figure2:

.. figure:: logo.jpg

   labeled figure

.. figure:: logo.jpg
   :name: figure3

   labeled figure

   with a legend

code-blocks
-----------

.. _codeblock1:
.. _codeblock2:

.. code-block:: none

   blah blah blah

.. code-block:: none
   :name: codeblock3

   blah blah blah

tables
------

.. _table1:
.. _table2:

.. table:: table caption

   ==== ====
   head head
   cell cell
   ==== ====

.. table:: table caption
   :name: table3

   ==== ====
   head head
   cell cell
   ==== ====

.. _section1:
.. _section2:

subsection
----------

.. _section3:

subsubsection
~~~~~~~~~~~~~

.. toctree::

   otherdoc

* Embedded standalone hyperlink reference(refs: #5948): `subsection <section1_>`_.
