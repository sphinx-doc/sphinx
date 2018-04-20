# -*- coding: utf-8 -*-
"""
    test_util_docutils
    ~~~~~~~~~~~~~~~~~~

    Tests util.utils functions.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

from sphinx.util.docutils import docutils_namespace, register_node


def test_register_node():
    class custom_node(nodes.Element):
        pass

    with docutils_namespace():
        register_node(custom_node)

        # check registered
        assert hasattr(nodes.GenericNodeVisitor, 'visit_custom_node')
        assert hasattr(nodes.GenericNodeVisitor, 'depart_custom_node')
        assert hasattr(nodes.SparseNodeVisitor, 'visit_custom_node')
        assert hasattr(nodes.SparseNodeVisitor, 'depart_custom_node')

    # check unregistered outside namespace
    assert not hasattr(nodes.GenericNodeVisitor, 'visit_custom_node')
    assert not hasattr(nodes.GenericNodeVisitor, 'depart_custom_node')
    assert not hasattr(nodes.SparseNodeVisitor, 'visit_custom_node')
    assert not hasattr(nodes.SparseNodeVisitor, 'depart_custom_node')
