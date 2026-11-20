from __future__ import annotations

from typing import TYPE_CHECKING

import docutils
import pytest
from docutils import nodes

from sphinx.testing import restructuredtext

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('dummy', testroot='_blank')
def test_indented_doctest(app: SphinxTestApp) -> None:
    doctree = restructuredtext.parse(app, '    >>> 1 + 1\n    2\n')

    assert len(doctree) == 1
    node = doctree[0]
    if docutils.__version_info__[:2] >= (1, 0):
        assert isinstance(node, nodes.literal_block)
        assert node['language'] == 'pycon'
    else:
        assert isinstance(node, nodes.doctest_block)
    assert node.astext() == '>>> 1 + 1\n2'
    assert 'doctest' in node['classes']


@pytest.mark.parametrize(
    ('target', 'translate_doctest', 'translate_literal'),
    [('doctest-block', True, False), ('literal-block', False, True)],
)
@pytest.mark.sphinx('dummy', testroot='_blank')
def test_doctest_translation(
    app: SphinxTestApp,
    target: str,
    translate_doctest: bool,
    translate_literal: bool,
) -> None:
    app.config.gettext_additional_targets = [target]
    doctree = restructuredtext.parse(
        app, '>>> 1 + 1\n2\n\n::\n\n    an ordinary literal block\n'
    )

    doctest, literal = doctree.children
    assert isinstance(doctest, nodes.Element)
    assert doctest.get('translatable', False) is translate_doctest
    assert isinstance(literal, nodes.Element)
    assert literal.get('translatable', False) is translate_literal
