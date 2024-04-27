"""Test the collapsible directive with the test root."""

import pytest
from docutils import nodes

from sphinx.ext.collapse import collapsible, summary


@pytest.mark.sphinx('text', testroot='ext-collapse')
def test_non_html(app, status, warning):
    app.build()

    # The content is inlined into the document:
    assert (app.outdir / 'index.txt').read_text(encoding='utf8') == """\
Collapsible directive tests
***************************

Collapsed Content:

Default section summary line

Custom summary line for the collapsible content:

Collapsible sections can also have custom summary lines

Collapsed Content:

Collapsible sections can have normal reST content such as **bold** and
*emphasised* text, and also links!

Collapsed Content:

Collapsible sections can have sections:


A Section
=========

Some words within a section, as opposed to outwith the section.

Summary text here with **bold** and *em* and a **RFC 2324** reference!
That was a newline in the reST source! We can also have links and more
links.

This is some text!
"""


@pytest.mark.sphinx('html', testroot='ext-collapse')
def test_html(app, status, warning):
    app.build()
    doctree = app.env.get_doctree('index')
    collapsible_nodes = list(doctree.findall(collapsible))
    assert len(collapsible_nodes) == 5

    assert isinstance(collapsible_nodes[0][0], summary)
    assert isinstance(collapsible_nodes[1][0], summary)
    assert isinstance(collapsible_nodes[2][0], summary)
    assert isinstance(collapsible_nodes[3][0], summary)
    assert isinstance(collapsible_nodes[4][0], summary)

    assert collapsible_nodes[0][0].astext() == 'Collapsed Content:'
    assert collapsible_nodes[2][0].astext() == 'Collapsed Content:'
    assert collapsible_nodes[3][0].astext() == 'Collapsed Content:'

    assert isinstance(collapsible_nodes[3][2], nodes.section)

    assert 'RFC 2324' in collapsible_nodes[4][0].astext()
    assert 'We can also\nhave ' in collapsible_nodes[4][0][8]  # type: ignore[operator]
