"""Test the patched directives."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


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

    # :number-lines: option with start value
    text = '.. code:: python\n   :number-lines: 5\n\n   print("hello world")\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block, 'print("hello world")'])
    assert_node(
        doctree[0], language='python', linenos=True, highlight_args={'linenostart': 5}
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_code_directive_emphasize_lines(app: SphinxTestApp) -> None:
    # :emphasize-lines: option
    text = '.. code:: python\n   :emphasize-lines: 2\n\n   first\n   second\n   third\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block])
    assert_node(doctree[0], language='python', highlight_args={'hl_lines': [2]})

    # multiple lines
    text = '.. code:: python\n   :emphasize-lines: 1,3\n\n   first\n   second\n   third\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[0], highlight_args={'hl_lines': [1, 3]})

    # line range
    text = '.. code:: python\n   :emphasize-lines: 1-3\n\n   first\n   second\n   third\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[0], highlight_args={'hl_lines': [1, 2, 3]})


@pytest.mark.sphinx('html', testroot='_blank')
def test_code_directive_emphasize_lines_out_of_range(app: SphinxTestApp) -> None:
    # out-of-range lines should be silently clamped with a warning
    text = '.. code:: python\n   :emphasize-lines: 5\n\n   first\n   second\n   third\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block])
    # line 5 is out of range (only 3 lines), so hl_lines should be empty
    assert_node(doctree[0], highlight_args={'hl_lines': []})


@pytest.mark.sphinx('html', testroot='_blank')
def test_code_directive_dedent(app: SphinxTestApp) -> None:
    # :dedent: without value (dedent all common leading whitespace)
    text = '.. code:: python\n   :dedent:\n\n       First line\n       Second line\n       Third line\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block])
    content = doctree[0].astext()
    # after dedent, common whitespace is stripped
    assert not content.startswith('   ')
    assert 'First line' in content

    # :dedent: with value removes N characters
    text = '.. code:: python\n   :dedent: 0\n\n       First line\n       Second line\n       Third line\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block])
    content = doctree[0].astext()
    # dedent: 0 preserves the whitespace (acts as indent fixator)
    assert 'First line' in content


@pytest.mark.sphinx('html', testroot='_blank')
def test_code_directive_lineno_start(app: SphinxTestApp) -> None:
    # :lineno-start: option
    text = '.. code:: python\n   :lineno-start: 10\n\n   print("hello")\n'

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block])
    assert_node(doctree[0], linenos=True, highlight_args={'linenostart': 10})


@pytest.mark.sphinx('html', testroot='_blank')
def test_code_directive_caption(app: SphinxTestApp) -> None:
    # :caption: option wraps in a container
    text = '.. code:: python\n   :caption: hello.py\n\n   print("hello")\n'

    doctree = restructuredtext.parse(app, text)
    # container_wrapper wraps the literal_block in a container node
    assert isinstance(doctree[0], nodes.container)
    # find the literal_block inside the container
    literal_nodes = list(doctree.findall(nodes.literal_block))
    assert len(literal_nodes) == 1
    assert literal_nodes[0]['language'] == 'python'


@pytest.mark.sphinx('html', testroot='_blank')
def test_code_directive_combined_options(app: SphinxTestApp) -> None:
    # emphasize-lines + number-lines
    text = (
        '.. code:: python\n'
        '   :emphasize-lines: 2\n'
        '   :number-lines:\n\n'
        '   first\n'
        '   second\n'
    )

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[0], linenos=True, highlight_args={'hl_lines': [2]})

    # emphasize-lines + lineno-start
    text = (
        '.. code:: python\n'
        '   :emphasize-lines: 1\n'
        '   :lineno-start: 7\n\n'
        '   first\n'
    )

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[0], linenos=True)
    assert doctree[0]['highlight_args']['hl_lines'] == [1]
    assert doctree[0]['highlight_args']['linenostart'] == 7


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
