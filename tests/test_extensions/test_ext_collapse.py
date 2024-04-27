"""Test the collapsible directive with the test root."""

import pytest
from docutils import nodes

from sphinx.ext.collapse import collapsible, summary


@pytest.mark.sphinx('text', testroot='ext-collapse')
def test_non_html(app):
    app.build(force_all=True)

    # The content is inlined into the document:
    assert (app.outdir / 'index.txt').read_text(encoding='utf8') == """\
Collapsible directive tests
***************************

Collapsed Content:

Default section summary line

Custom summary line for the collapsible content:

Collapsible sections can also have custom summary lines

Summary text here with **bold** and *em* and a **RFC 2324** reference!
That was a newline in the reST source! We can also have links and more
links.

This is some body text!

Collapsible section with no content.

Collapsible section with reStructuredText content:

Collapsible sections can have normal reST content such as **bold** and
*emphasised* text, and also links!

Collapsible section with titles:

Collapsible sections can have sections:


A Section
=========

Some words within a section, as opposed to outwith the section.
"""


@pytest.mark.sphinx('text', testroot='ext-collapse')
def test_non_html_post_transform(app):
    app.build(force_all=True)
    doctree = app.env.get_doctree('index')
    app.env.apply_post_transforms(doctree, 'index')
    assert list(doctree.findall(collapsible)) == []

    collapsible_nodes = list(doctree.findall(nodes.container))
    no_content = collapsible_nodes[3]
    assert len(no_content) == 1
    assert no_content[0].astext() == 'Collapsible section with no content.'


@pytest.mark.sphinx('html', testroot='ext-collapse')
def test_html(app):
    app.build(force_all=True)
    doctree = app.env.get_doctree('index')
    app.env.apply_post_transforms(doctree, 'index')
    collapsible_nodes = list(doctree.findall(collapsible))
    assert len(collapsible_nodes) == 6

    default_summary = collapsible_nodes[0]
    assert isinstance(default_summary[0], summary)
    assert collapsible_nodes[0][0].astext() == 'Collapsed Content:'

    custom_summary = collapsible_nodes[1]
    assert isinstance(custom_summary[0], summary)
    assert custom_summary[0].astext() == 'Custom summary line for the collapsible content:'
    assert custom_summary[1].astext() == 'Collapsible sections can also have custom summary lines'

    rst_summary = collapsible_nodes[2]
    assert isinstance(rst_summary[0], summary)
    assert 'RFC 2324' in rst_summary[0].astext()
    assert 'We can also\nhave ' in rst_summary[0][8]  # type: ignore[operator]

    no_content = collapsible_nodes[3]
    assert isinstance(no_content[0], summary)
    assert no_content[0].astext() == 'Collapsible section with no content.'
    assert len(no_content) == 1

    rst_content = collapsible_nodes[4]
    assert isinstance(rst_content[0], summary)

    nested_titles = collapsible_nodes[5]
    assert isinstance(nested_titles[0], summary)
    assert isinstance(nested_titles[2], nodes.section)
