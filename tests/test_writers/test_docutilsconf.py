"""Test docutils.conf support for several writers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx.testing.util import assert_node
from sphinx.util.docutils import patch_docutils

if TYPE_CHECKING:
    from sphinx.application import Sphinx


@pytest.mark.sphinx(
    'dummy',
    testroot='docutilsconf',
    freshenv=True,
)
def test_html_with_default_docutilsconf(app: Sphinx) -> None:
    with patch_docutils(app.confdir):
        app.build()

    doctree = app.env.get_doctree('index')
    section = doctree[0]
    assert isinstance(section, nodes.Element)
    assert_node(
        section[1], [nodes.paragraph, ('Sphinx ', [nodes.footnote_reference, '1'])]
    )


@pytest.mark.sphinx(
    'dummy',
    testroot='docutilsconf',
    freshenv=True,
    docutils_conf='[restructuredtext parser]\ntrim_footnote_reference_space: true\n',
    copy_test_root=True,
)
def test_html_with_docutilsconf(app: Sphinx) -> None:
    with patch_docutils(app.confdir):
        app.build()

    doctree = app.env.get_doctree('index')
    section = doctree[0]
    assert isinstance(section, nodes.Element)
    assert_node(
        section[1], [nodes.paragraph, ('Sphinx', [nodes.footnote_reference, '1'])]
    )
