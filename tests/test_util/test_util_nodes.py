"""Tests uti.nodes functions."""

from __future__ import annotations

import warnings
from textwrap import dedent
from typing import TYPE_CHECKING, Any

import pytest
from docutils import frontend, nodes
from docutils.parsers import rst
from docutils.utils import new_document

from sphinx.transforms import ApplySourceWorkaround
from sphinx.util.nodes import (
    NodeMatcher,
    apply_source_workaround,
    clean_astext,
    extract_messages,
    make_id,
    split_explicit_title,
)

if TYPE_CHECKING:
    from docutils.nodes import document


def _transform(doctree) -> None:
    ApplySourceWorkaround(doctree).apply()


def create_new_document() -> document:
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=DeprecationWarning)
        # DeprecationWarning: The frontend.OptionParser class will be replaced
        # by a subclass of argparse.ArgumentParser in Docutils 0.21 or later.
        settings = frontend.OptionParser(components=(rst.Parser,)).get_default_values()
    settings.id_prefix = 'id'
    document = new_document('dummy.txt', settings)
    return document


def _get_doctree(text):
    document = create_new_document()
    rst.Parser().parse(text, document)
    _transform(document)
    return document


def assert_node_count(messages, node_type, expect_count) -> None:
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
def test_extract_messages(rst, node_cls, count):
    msg = extract_messages(_get_doctree(dedent(rst)))
    assert_node_count(msg, node_cls, count)


def test_extract_messages_without_rawsource():
    """
    Check node.rawsource is fall-backed by using node.astext() value.

    `extract_message` which is used from Sphinx i18n feature drop ``not node.rawsource``
    nodes. So, all nodes which want to translate must have ``rawsource`` value.
    However, sometimes node.rawsource is not set.

    For example: recommonmark-0.2.0 doesn't set rawsource to `paragraph` node.

    refs #1994: Fall back to node's astext() during i18n message extraction.
    """
    p = nodes.paragraph()
    p.append(nodes.Text('test'))
    p.append(nodes.Text('sentence'))
    assert not p.rawsource  # target node must not have rawsource value
    document = create_new_document()
    document.append(p)
    _transform(document)
    assert_node_count(extract_messages(document), nodes.TextElement, 1)
    assert [m for n, m in extract_messages(document)][0], 'text sentence'


def test_clean_astext():
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
def test_split_explicit_target(title, expected):
    assert split_explicit_title(title) == expected


def test_apply_source_workaround_literal_block_no_source():
    """Regression test for #11091.

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
