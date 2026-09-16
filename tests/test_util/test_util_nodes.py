"""Tests uti.nodes functions."""

from __future__ import annotations

from textwrap import dedent
from typing import TYPE_CHECKING, Any

import pytest
from docutils import frontend, nodes
from docutils.parsers import rst
from docutils.utils import new_document

from sphinx.transforms import ApplySourceWorkaround, HandleCodeBlocks
from sphinx.util.nodes import (
    NodeMatcher,
    _get_colwidth,
    _is_doctest_block,
    apply_source_workaround,
    clean_astext,
    extract_messages,
    make_id,
    split_explicit_title,
)

if TYPE_CHECKING:
    from collections.abc import Iterable

    from docutils.nodes import document


def _transform(doctree: nodes.document) -> None:
    ApplySourceWorkaround(doctree).apply()


def create_new_document() -> document:
    # TODO: TYPING: Upstream docutils should accept both instances and subclasses
    #       of SettingsSpec here.
    settings = frontend.get_default_settings(rst.Parser)  # type: ignore[arg-type]
    settings.id_prefix = 'id'
    document = new_document('dummy.txt', settings)
    return document


def _get_doctree(text):
    document = create_new_document()
    rst.Parser().parse(text, document)
    _transform(document)
    return document


def assert_node_count(
    messages: Iterable[tuple[nodes.Element, str]],
    node_type: type[nodes.Node],
    expect_count: int,
) -> None:
    count = 0
    node_list = [node for node, msg in messages]
    for node in node_list:
        if isinstance(node, node_type):
            count += 1

    assert count == expect_count, (
        f'Count of {node_type!r} in the {node_list!r} '
        f'is {count} instead of {expect_count}'
    )


def test_NodeMatcher():
    doctree = nodes.document(None, None)
    doctree += nodes.paragraph('', 'Hello')
    doctree += nodes.paragraph('', 'Sphinx', block=1)
    doctree += nodes.paragraph('', 'World', block=2)
    doctree += nodes.literal_block('', 'blah blah blah', block=3)

    # search by node class
    matcher = NodeMatcher(nodes.paragraph)
    assert len(list(doctree.findall(matcher))) == 3

    # search by multiple node classes
    matcher = NodeMatcher(nodes.paragraph, nodes.literal_block)
    assert len(list(doctree.findall(matcher))) == 4

    # search by node attribute
    matcher = NodeMatcher(block=1)
    assert len(list(doctree.findall(matcher))) == 1

    # search by node attribute (Any)
    matcher = NodeMatcher(block=Any)
    assert len(list(doctree.findall(matcher))) == 3

    # search by both class and attribute
    matcher = NodeMatcher(nodes.paragraph, block=Any)
    assert len(list(doctree.findall(matcher))) == 2

    # mismatched
    matcher = NodeMatcher(nodes.title)
    assert len(list(doctree.findall(matcher))) == 0

    # search with Any does not match to Text node
    matcher = NodeMatcher(blah=Any)
    assert len(list(doctree.findall(matcher))) == 0


@pytest.mark.parametrize(
    ('rst', 'node_cls', 'count'),
    [
        (
            """
           .. admonition:: admonition title

              admonition body
           """,
            nodes.title,
            1,
        ),
        (
            """
           .. figure:: foo.jpg

              this is title
           """,
            nodes.caption,
            1,
        ),
        (
            """
           .. rubric:: spam
           """,
            nodes.rubric,
            1,
        ),
        (
            """
           | spam
           | egg
           """,
            nodes.line,
            2,
        ),
        (
            """
           section
           =======

           +----------------+
           | | **Title 1**  |
           | | Message 1    |
           +----------------+
           """,
            nodes.line,
            2,
        ),
        (
            """
           * | **Title 1**
             | Message 1
           """,
            nodes.line,
            2,
        ),
    ],
)
def test_extract_messages(rst: str, node_cls: type[nodes.Element], count: int) -> None:
    msg = extract_messages(_get_doctree(dedent(rst)))
    assert_node_count(msg, node_cls, count)


def test_extract_messages_without_rawsource() -> None:
    """Check node.rawsource is fall-backed by using node.astext() value.

    `extract_message` which is used from Sphinx i18n feature drop ``not node.rawsource``
    nodes. So, all nodes which want to translate must have ``rawsource`` value.
    However, sometimes node.rawsource is not set.

    For example: recommonmark-0.2.0 doesn't set rawsource to `paragraph` node.

    See https://github.com/sphinx-doc/sphinx/pull/1994
    """
    p = nodes.paragraph()
    p.append(nodes.Text('test'))
    p.append(nodes.Text('sentence'))
    assert not p.rawsource  # target node must not have rawsource value
    document = create_new_document()
    document.append(p)
    _transform(document)
    assert_node_count(extract_messages(document), nodes.TextElement, 1)
    assert next(m for n, m in extract_messages(document)), 'text sentence'


def test_clean_astext() -> None:
    node: nodes.Element
    node = nodes.paragraph(text='hello world')
    assert clean_astext(node) == 'hello world'

    node = nodes.image(alt='hello world')
    assert clean_astext(node) == ''

    node = nodes.paragraph(text='hello world')
    node += nodes.raw('', 'raw text', format='html')
    assert clean_astext(node) == 'hello world'


@pytest.mark.parametrize(
    ('prefix', 'term', 'expected'),
    [
        ('', '', 'id0'),
        ('term', '', 'term-0'),
        ('term', 'Sphinx', 'term-Sphinx'),
        ('', 'io.StringIO', 'io.StringIO'),  # contains a dot
        (
            # contains a dot & underscore
            '',
            'sphinx.setup_command',
            'sphinx.setup_command',
        ),
        ('', '_io.StringIO', 'io.StringIO'),  # starts with underscore
        ('', 'ｓｐｈｉｎｘ', 'sphinx'),  # alphabets in unicode fullwidth characters
        ('', '悠好', 'id0'),  # multibytes text (in Chinese)
        ('', 'Hello=悠好=こんにちは', 'Hello'),  # alphabets and multibytes text
        ('', 'fünf', 'funf'),  # latin1 (umlaut)
        ('', '0sphinx', 'sphinx'),  # starts with number
        ('', 'sphinx-', 'sphinx'),  # ends with hyphen
    ],
)
@pytest.mark.sphinx('html', testroot='root')
def test_make_id(app, prefix, term, expected):
    document = create_new_document()
    assert make_id(app.env, document, prefix, term) == expected


@pytest.mark.sphinx('html', testroot='root')
def test_make_id_already_registered(app):
    document = create_new_document()
    document.ids['term-Sphinx'] = True  # register "term-Sphinx" manually
    assert make_id(app.env, document, 'term', 'Sphinx') == 'term-0'


@pytest.mark.sphinx('html', testroot='root')
def test_make_id_sequential(app):
    document = create_new_document()
    document.ids['term-0'] = True
    assert make_id(app.env, document, 'term') == 'term-1'


@pytest.mark.parametrize(
    ('title', 'expected'),
    [
        # implicit
        ('hello', (False, 'hello', 'hello')),
        # explicit
        ('hello <world>', (True, 'hello', 'world')),
        # explicit (title having angle brackets)
        ('hello <world> <sphinx>', (True, 'hello <world>', 'sphinx')),
    ],
)
def test_split_explicit_target(title: str, expected: tuple[bool, str, str]) -> None:
    assert split_explicit_title(title) == expected


def test_apply_source_workaround_literal_block_no_source() -> None:
    """Regression test for https://github.com/sphinx-doc/sphinx/issues/11091.

    Test that apply_source_workaround doesn't raise.
    """
    literal_block = nodes.literal_block('', '')
    list_item = nodes.list_item('', literal_block)
    bullet_list = nodes.bullet_list('', list_item)

    assert literal_block.source is None
    assert list_item.source is None
    assert bullet_list.source is None

    apply_source_workaround(literal_block)

    assert literal_block.source is None
    assert list_item.source is None
    assert bullet_list.source is None


def _docutils_1_doctest_block() -> nodes.literal_block:
    # Docutils 1.0 represents a doctest block as a classified literal block
    source = '>>> 1 + 1\n2'
    return nodes.literal_block(source, source, classes=['code', 'pycon', 'doctest'])


def test_is_doctest_block() -> None:
    assert _is_doctest_block(nodes.doctest_block('>>> 1', '>>> 1'))
    assert _is_doctest_block(_docutils_1_doctest_block())

    assert not _is_doctest_block(nodes.literal_block('>>> 1', '>>> 1'))
    assert not _is_doctest_block(nodes.literal_block('', '', classes=['code', 'pycon']))
    # nodes created by the sphinx.ext.doctest directives
    doctest_directive_node = _docutils_1_doctest_block()
    doctest_directive_node['testnodetype'] = 'doctest'
    assert not _is_doctest_block(doctest_directive_node)


def test_handle_code_blocks_moves_docutils_1_doctest_blocks() -> None:
    document = create_new_document()
    block = _docutils_1_doctest_block()
    document += nodes.block_quote('', block)

    HandleCodeBlocks(document).apply()

    assert not list(document.findall(nodes.block_quote))
    assert block.parent is document


@pytest.mark.parametrize(
    ('colwidth', 'expected'),
    [
        (10, 10),
        ('10', 10),
        ('10*', 10),
        ('2.5*', 2),
    ],
)
def test_get_colwidth(colwidth: int | str, expected: int) -> None:
    colspec = nodes.colspec()
    colspec.attributes['colwidth'] = colwidth
    assert _get_colwidth(colspec) == expected
