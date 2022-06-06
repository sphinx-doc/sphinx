"""Test the collapsible directive with the test root."""

import pytest
from docutils import nodes

from sphinx import addnodes


@pytest.mark.sphinx('text', testroot='directive-collapsible')
def test_non_html(app, status, warning):
    app.build()

    # The content is inlined into the document:
    assert (app.outdir / 'index.txt').read_text(encoding='utf8') == """\
Collapsible directive tests
***************************

Default section summary line

Collapsible sections can also have custom summary lines

Collapsible sections can have normal reST content such as **bold** and
*emphasised* text, and also links!

Collapsible sections can have sections:


A Section
=========

Some words within a section, as opposed to outwith the section.

This is some text!
"""


@pytest.mark.sphinx('html', testroot='directive-collapsible')
def test_html(app, status, warning):
    app.build()
    doctree = app.env.get_doctree('index')
    collapsible_nodes = list(doctree.findall(addnodes.collapsible))
    assert len(collapsible_nodes) == 5

    assert isinstance(collapsible_nodes[0][0], addnodes.collapsible_summary)
    assert isinstance(collapsible_nodes[1][0], addnodes.collapsible_summary)
    assert isinstance(collapsible_nodes[2][0], addnodes.collapsible_summary)
    assert isinstance(collapsible_nodes[3][0], addnodes.collapsible_summary)
    assert isinstance(collapsible_nodes[4][0], addnodes.collapsible_summary)

    assert collapsible_nodes[0][0].astext() == 'Collapsed Content'
    assert collapsible_nodes[2][0].astext() == 'Collapsed Content'
    assert collapsible_nodes[3][0].astext() == 'Collapsed Content'

    assert isinstance(collapsible_nodes[3][2], nodes.section)

    assert "RFC 2324" in collapsible_nodes[4][0].astext()
    assert "We can also\nhave " in collapsible_nodes[4][0][8]
