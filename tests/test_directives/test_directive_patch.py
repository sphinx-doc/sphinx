"""Test the patched directives."""

from __future__ import annotations

from typing import TYPE_CHECKING

import docutils
import pytest
from docutils import nodes
from docutils.languages import get_language
from docutils.parsers.rst import directives
from docutils.parsers.rst.directives.misc import Date as DocutilsDate

from sphinx.directives.patches import Date
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx(
    'html',
    testroot='_blank',
    confoverrides={'today_fmt': '%Y-%m-%d %H:%M:%S'},
)
def test_date_directive_source_date_epoch(
    app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv('SOURCE_DATE_EPOCH', '1439131307')
    text = """\
.. |docutils-date| date:: %Y-%m-%d %H:%M:%S

Docutils: |docutils-date|

Sphinx: |today|
"""

    doctree = restructuredtext.parse(app, text)

    assert 'Docutils: 2015-08-09 14:41:47' in doctree.astext()
    assert 'Sphinx: 2015-08-09 14:41:47' in doctree.astext()


@pytest.mark.sphinx('html', testroot='_blank')
def test_date_directive_source_date_epoch_default_format(
    app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv('SOURCE_DATE_EPOCH', '0')

    doctree = restructuredtext.parse(app, '.. |date| date::\n\n|date|')

    assert doctree[-1].astext() == '1970-01-01'


@pytest.mark.sphinx('html', testroot='_blank')
@pytest.mark.parametrize('source_date_epoch', [None, ''])
def test_date_directive_without_source_date_epoch_delegates_to_docutils(
    app: SphinxTestApp,
    monkeypatch: pytest.MonkeyPatch,
    source_date_epoch: str | None,
) -> None:
    if source_date_epoch is None:
        monkeypatch.delenv('SOURCE_DATE_EPOCH', raising=False)
    else:
        monkeypatch.setenv('SOURCE_DATE_EPOCH', source_date_epoch)
    monkeypatch.setattr(DocutilsDate, 'run', lambda self: [nodes.Text('docutils-date')])

    doctree = restructuredtext.parse(app, '.. |date| date::\n\n|date|')

    assert doctree[-1].astext() == 'docutils-date'


@pytest.mark.sphinx('html', testroot='_blank')
def test_date_directive_invalid_context(
    app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv('SOURCE_DATE_EPOCH', '0')

    restructuredtext.parse(app, '.. date::')

    assert 'can only be used within a substitution definition' in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='_blank')
def test_date_directive_registration(app: SphinxTestApp) -> None:
    doctree = restructuredtext.parse(app, '.. |date| date::\n\n|date|')
    directive, _messages = directives.directive('date', get_language('en'), doctree)

    if docutils.__version_info__[:2] < (1, 0):
        assert directive is Date
    else:
        assert directive is DocutilsDate


@pytest.mark.sphinx('html', testroot='_blank')
def test_date_directive_extension_override(
    app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    class ExtensionDate(DocutilsDate):
        def run(self) -> list[nodes.Text]:
            return [nodes.Text('extension date')]

    monkeypatch.setenv('SOURCE_DATE_EPOCH', '0')
    app.add_directive('date', ExtensionDate, override=True)

    doctree = restructuredtext.parse(app, '.. |date| date::\n\n|date|')

    assert doctree[-1].astext() == 'extension date'


@pytest.mark.sphinx('html', testroot='_blank')
def test_code_directive(app: SphinxTestApp) -> None:
    # normal case
    text = '.. code::\n\n   print("hello world")\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block, 'print("hello world")'])
    assert_node(doctree[0], language='default', highlight_args={})

    # with language
    text = '.. code:: python\n\n   print("hello world")\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block, 'print("hello world")'])
    assert_node(doctree[0], language='python', highlight_args={})

    # :number-lines: option
    text = '.. code:: python\n   :number-lines:\n\n   print("hello world")\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block, 'print("hello world")'])
    assert_node(doctree[0], language='python', linenos=True, highlight_args={})

    # :number-lines: option
    text = '.. code:: python\n   :number-lines: 5\n\n   print("hello world")\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block, 'print("hello world")'])
    assert_node(
        doctree[0], language='python', linenos=True, highlight_args={'linenostart': 5}
    )


def _as_element(node: nodes.Node) -> nodes.Element:
    assert isinstance(node, nodes.Element)
    return node


@pytest.mark.sphinx('html', testroot='directive-csv-table')
def test_csv_table_directive(app: SphinxTestApp) -> None:
    # relative path from current document
    text = '.. csv-table::\n   :file: example.csv\n'
    doctree = restructuredtext.parse(app, text, docname='subdir/index')
    assert_node(
        doctree,
        (
            [
                nodes.table,
                nodes.tgroup,
                (nodes.colspec, nodes.colspec, nodes.colspec, [nodes.tbody, nodes.row]),
            ],
        ),
    )
    table = _as_element(doctree[0])
    tgroup = _as_element(table[0])
    tbody = _as_element(tgroup[3])
    first_row = _as_element(tbody[0])
    assert_node(
        first_row,
        (
            [nodes.entry, nodes.paragraph, 'FOO'],
            [nodes.entry, nodes.paragraph, 'BAR'],
            [nodes.entry, nodes.paragraph, 'BAZ'],
        ),
    )

    # absolute path from source directory
    text = '.. csv-table::\n   :file: /example.csv\n'
    doctree = restructuredtext.parse(app, text, docname='subdir/index')
    assert_node(
        doctree,
        (
            [
                nodes.table,
                nodes.tgroup,
                (nodes.colspec, nodes.colspec, nodes.colspec, [nodes.tbody, nodes.row]),
            ],
        ),
    )
    table = _as_element(doctree[0])
    tgroup = _as_element(table[0])
    tbody = _as_element(tgroup[3])
    first_row = _as_element(tbody[0])
    assert_node(
        first_row,
        (
            [nodes.entry, nodes.paragraph, 'foo'],
            [nodes.entry, nodes.paragraph, 'bar'],
            [nodes.entry, nodes.paragraph, 'baz'],
        ),
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_math_directive(app: SphinxTestApp) -> None:
    # normal case
    text = '.. math:: E = mc^2'
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.math_block, 'E = mc^2\n\n'])

    # :name: option
    text = '.. math:: E = mc^2\n   :name: eq1\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree, [nodes.document, (nodes.target, [nodes.math_block, 'E = mc^2\n\n'])]
    )
    assert_node(doctree[1], nodes.math_block, docname='index', label='eq1', number=1)

    # :label: option
    text = '.. math:: E = mc^2\n   :label: eq2\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree, [nodes.document, (nodes.target, [nodes.math_block, 'E = mc^2\n\n'])]
    )
    assert_node(doctree[1], nodes.math_block, docname='index', label='eq2', number=2)

    # :label: option without value
    text = '.. math:: E = mc^2\n   :label:\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree, [nodes.document, (nodes.target, [nodes.math_block, 'E = mc^2\n\n'])]
    )
    assert_node(
        doctree[1],
        nodes.math_block,
        ids=['equation-index-0'],
        docname='index',
        label='index:0',
        number=3,
    )
