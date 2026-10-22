"""Test dirhtml builder."""

from __future__ import annotations

import posixpath
from typing import TYPE_CHECKING

import docutils
import pytest
from docutils.parsers import rst
from docutils.readers import standalone
from docutils.writers import html5_polyglot

from sphinx.util.docutils import _get_settings, new_document
from sphinx.util.inventory import InventoryFile, _InventoryItem

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('dirhtml', testroot='builder-dirhtml')
def test_dirhtml(app: SphinxTestApp) -> None:
    app.build()

    assert (app.outdir / 'index.html').exists()
    assert (app.outdir / 'foo/index.html').exists()
    assert (app.outdir / 'foo/foo_1/index.html').exists()
    assert (app.outdir / 'foo/foo_2/index.html').exists()
    assert (app.outdir / 'bar/index.html').exists()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert 'href="foo/"' in content
    assert 'href="foo/foo_1/"' in content
    assert 'href="foo/foo_2/"' in content
    assert 'href="bar/"' in content

    # objects.inv
    # See: https://github.com/sphinx-doc/sphinx/issues/7095
    with (app.outdir / 'objects.inv').open('rb') as f:
        invdata = InventoryFile.load(f, 'path/to', posixpath.join)

    assert 'index' in invdata.get('std:doc', {})
    assert invdata['std:doc']['index'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='path/to/',
        display_name='-',
    )

    assert 'foo/index' in invdata.get('std:doc', {})
    assert invdata['std:doc']['foo/index'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='path/to/foo/',
        display_name='-',
    )

    assert 'index' in invdata.get('std:label', {})
    assert invdata['std:label']['index'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='path/to/#index',
        display_name='-',
    )

    assert 'foo' in invdata.get('std:label', {})
    assert invdata['std:label']['foo'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='path/to/foo/#foo',
        display_name='foo/index',
    )


@pytest.mark.sphinx('dirhtml', testroot='builder-dirhtml')
def test_dirhtml_inherits_format_translation_handlers(app: SphinxTestApp) -> None:
    # A custom node with a dirhtml-specific handler must not hide handlers
    # registered for the shared ``html`` format (e.g. graphviz nodes).
    # See https://github.com/sphinx-doc/sphinx/issues/14587
    class DirhtmlOnlyNode(docutils.nodes.General, docutils.nodes.Element):
        pass

    class HtmlOnlyNode(docutils.nodes.General, docutils.nodes.Element):
        pass

    def visit_custom(self, node: docutils.nodes.Node) -> None:
        raise docutils.nodes.SkipNode

    app.add_node(
        DirhtmlOnlyNode, html=(visit_custom, None), dirhtml=(visit_custom, None)
    )
    app.registry.add_translation_handlers(
        HtmlOnlyNode, html=(visit_custom, None)
    )

    settings = _get_settings(
        standalone.Reader, rst.Parser, html5_polyglot.Writer, defaults={}
    )
    document = new_document('test', settings)
    translator = app.builder.create_translator(document, app.builder)
    assert hasattr(translator, 'visit_DirhtmlOnlyNode')
    assert hasattr(translator, 'visit_HtmlOnlyNode')
