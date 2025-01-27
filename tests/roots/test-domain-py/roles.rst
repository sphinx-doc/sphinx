roles
=====

.. py:class:: TopLevel

.. py:method:: top_level

.. py:type:: TopLevelType

* :py:class:`TopLevel`
* :py:meth:`top_level`
* :py:type:`TopLevelType`


.. py:class:: NestedParentA

    * Link to :py:meth:`child_1`

    .. py:type:: NestedTypeA

    .. py:method:: child_1()

        * Link to :py:meth:`NestedChildA.subchild_2`
        * Link to :py:meth:`child_2`
        * Link to :any:`any_child`

    .. py:method:: any_child()

        * Link to :py:class:`NestedChildA`

    .. py:class:: NestedChildA

        .. py:method:: subchild_1()

            * Link to :py:meth:`subchild_2`

        .. py:method:: subchild_2()

            Link to :py:meth:`NestedParentA.child_1`

    .. py:method:: child_2()

        Link to :py:meth:`NestedChildA.subchild_1`

.. py:class:: NestedParentB

    * Link to :py:meth:`child_1`

    .. py:method:: child_1()

        * Link to :py:class:`NestedParentB`

* :py:class:`NestedParentA.NestedChildA`
* :py:type:`NestedParentA.NestedTypeA`
