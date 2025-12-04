"""Tests util.utils functions."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx.util.docutils import (
    SphinxFileOutput,
    SphinxTranslator,
    docutils_namespace,
    new_document,
    register_node,
)

if TYPE_CHECKING:
    from pathlib import Path

    from sphinx.builders import Builder
    from sphinx.testing.util import SphinxTestApp


def test_register_node() -> None:
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


def test_SphinxFileOutput(tmp_path: Path) -> None:
    content = 'Hello Sphinx World'

    # write test.txt at first
    filename = tmp_path / 'test.txt'
    output = SphinxFileOutput(destination_path=str(filename))
    output.write(content)
    os.utime(filename, ns=(0, 0))

    # overwrite it again
    output.write(content)
    assert filename.stat().st_mtime_ns != 0  # updated

    # write test2.txt at first
    filename = tmp_path / 'test2.txt'
    output = SphinxFileOutput(destination_path=str(filename), overwrite_if_changed=True)
    output.write(content)
    os.utime(filename, ns=(0, 0))

    # overwrite it again
    output.write(content)
    assert filename.stat().st_mtime_ns == 0  # not updated

    # overwrite it again (content changed)
    output.write(content + '; content change')
    assert filename.stat().st_mtime_ns != 0  # updated


@pytest.mark.sphinx('html', testroot='root')
def test_SphinxTranslator(app: SphinxTestApp) -> None:
    class CustomNode(nodes.inline):
        pass

    class MyTranslator(SphinxTranslator):
        def __init__(self, document: nodes.document, builder: Builder):
            self.called: list[str] = []
            super().__init__(document, builder)

        def visit_document(self, node: nodes.document) -> None:
            pass

        def depart_document(self, node: nodes.document) -> None:
            pass

        def visit_inline(self, node: nodes.inline) -> None:
            self.called.append('visit_inline')

        def depart_inline(self, node: nodes.inline) -> None:
            self.called.append('depart_inline')

    document = new_document('')
    document += CustomNode()

    translator = MyTranslator(document, app.builder)
    document.walkabout(translator)

    # MyTranslator does not have visit_CustomNode. But it calls visit_inline instead.
    assert translator.called == ['visit_inline', 'depart_inline']
