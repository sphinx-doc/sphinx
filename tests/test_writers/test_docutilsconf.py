"""Test docutils.conf support for several writers."""

import pytest
from docutils import nodes

from sphinx.testing.util import assert_node
from sphinx.util.docutils import patch_docutils


@pytest.mark.sphinx(
    'dummy',
    testroot='docutilsconf',
    freshenv=True,
)
def test_html_with_default_docutilsconf(app):
    with patch_docutils(app.confdir):
        app.build()

    doctree = app.env.get_doctree('index')
    assert_node(
        doctree[0][1], [nodes.paragraph, ('Sphinx ', [nodes.footnote_reference, '1'])]
    )


@pytest.mark.sphinx(
    'dummy',
    testroot='docutilsconf',
    freshenv=True,
    docutils_conf='[restructuredtext parser]\ntrim_footnote_reference_space: true\n',
)
def test_html_with_docutilsconf(app):
    with patch_docutils(app.confdir):
        app.build()

    doctree = app.env.get_doctree('index')
    assert_node(
        doctree[0][1], [nodes.paragraph, ('Sphinx', [nodes.footnote_reference, '1'])]
    )
