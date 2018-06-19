# -*- coding: utf-8 -*-
"""
    test_util_docutils
    ~~~~~~~~~~~~~~~~~~

    Tests util.utils functions.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

from docutils import nodes

from sphinx.util.docutils import SphinxFileOutput, docutils_namespace, register_node


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


def test_SphinxFileOutput(tmpdir):
    content = 'Hello Sphinx World'

    # write test.txt at first
    filename = str(tmpdir / 'test.txt')
    output = SphinxFileOutput(destination_path=filename)
    output.write(content)
    os.utime(filename, (0, 0))

    # overrite it again
    output.write(content)
    assert os.stat(filename).st_mtime != 0  # updated

    # write test2.txt at first
    filename = str(tmpdir / 'test2.txt')
    output = SphinxFileOutput(destination_path=filename, overwrite_if_changed=True)
    output.write(content)
    os.utime(filename, (0, 0))

    # overrite it again
    output.write(content)
    assert os.stat(filename).st_mtime == 0  # not updated

    # overrite it again (content changed)
    output.write(content + "; content change")
    assert os.stat(filename).st_mtime != 0  # updated
