roles
=====

.. js:class:: TopLevel

.. js:function:: top_level

* :js:class:`TopLevel`
* :js:func:`top_level`


.. js:class:: NestedParentA

    * Link to :js:func:`child_1`

    .. js:function:: child_1()

        * Link to :js:func:`NestedChildA.subchild_2`
        * Link to :js:func:`child_2`
        * Link to :any:`any_child`

    .. js:function:: any_child()

        * Link to :js:class:`NestedChildA`

    .. js:class:: NestedChildA

        .. js:function:: subchild_1()

            * Link to :js:func:`subchild_2`

        .. js:function:: subchild_2()

            Link to :js:func:`NestedParentA.child_1`

    .. js:function:: child_2()

        Link to :js:func:`NestedChildA.subchild_1`

.. js:class:: NestedParentB

    * Link to :js:func:`child_1`

    .. js:function:: child_1()

        * Link to :js:class:`NestedParentB`

* :js:class:`NestedParentA.NestedChildA`
