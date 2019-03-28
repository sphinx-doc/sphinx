=============
Class Members
=============

.. py:class:: A
   :module: module_c


   .. py:method:: A.foo()
      :module: module_c
      :abstract:

      Do foo.


   .. py:method:: A.bar()
      :module: module_c
      :abstractmethod:

      Do bar.


   .. py:attribute:: A.value
      :module: module_c
      :abstract:

      Return a value.


   .. py:staticmethod:: A.sfoo()
      :module: module_c
      :abstract:

      Do static foo.


   .. py:classmethod:: A.cfoo()
      :module: module_c
      :abstract:

      Do class foo.


.. py:class:: C
   :module: module_c


   .. py:staticmethod:: C.static_by_directive()
      :module: module_c

      I have the ``staticmethod::`` directive!


   .. py:method:: C.static_by_option()
      :module: module_c
      :static:

      I have the ``:static:`` option!

   .. py:classmethod:: C.cm_by_directive()
      :module: module_c

      I have the ``classmethod::`` directive!


   .. py:method:: C.cm_by_option()
      :module: module_c
      :classmethod:

      I have the ``:classmethod:`` option!
