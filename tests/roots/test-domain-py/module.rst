module
======

.. py:module:: module_a.submodule

* Link to :py:class:`ModTopLevel`

.. py:class:: ModTopLevel

    * Link to :py:meth:`mod_child_1`
    * Link to :py:meth:`ModTopLevel.mod_child_1`

.. py:method:: ModTopLevel.mod_child_1

    * Link to :py:meth:`mod_child_2`

.. py:method:: ModTopLevel.mod_child_2

    * Link to :py:meth:`module_a.submodule.ModTopLevel.mod_child_1`

.. py:property:: ModTopLevel.prop

   * Link to :py:attr:`prop attribute <.prop>`
   * Link to :py:meth:`prop method <.prop>`

.. py:currentmodule:: None

.. py:class:: ModNoModule

.. py:module:: module_b.submodule

* Link to :py:class:`ModTopLevel`

.. py:class:: ModTopLevel

    * Link to :py:class:`ModNoModule`

.. py:function:: foo(x, y)

   :param x: param x
   :type  x: int
   :param y: param y
   :type  y: tuple(str, float)
   :rtype:   list

.. py:attribute:: attr1

   :type: ModTopLevel

.. py:attribute:: attr2

   :type: :doc:`index`

.. py:module:: exceptions

.. py:exception:: Exception

.. py:module:: object

.. py:function:: sum()

.. py:data:: test
    :type: typing.Literal[2]

.. py:data:: test2
    :type: typing.Literal[-2]

.. py:type:: MyType1
    :canonical: list[int | str]
