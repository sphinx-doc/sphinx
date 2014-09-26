test-tocdepth
=============

.. toctree::
   :numbered:

   foo
   bar

.. figure:: rimg.png

   should be Fig.1

.. figure:: rimg.png

   should be Fig.2

.. csv-table:: should be Table 1
   :header-rows: 0

   hello,world

.. csv-table:: should be Table 2
   :header-rows: 0

   hello,world

.. code-block:: python
   :caption: should be List 1

   print('hello world')

.. code-block:: python
   :caption: should be List 2

   print('hello world')
