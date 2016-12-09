# -*- coding: utf-8 -*-
"""
    test_util_nodes
    ~~~~~~~~~~~~~~~

    Tests uti.nodes functions.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from textwrap import dedent

from docutils import nodes
from docutils.parsers import rst
from docutils.utils import new_document
from docutils import frontend

from sphinx.util.nodes import extract_messages
from sphinx.transforms import ApplySourceWorkaround


def _transform(doctree):
    ApplySourceWorkaround(doctree).apply()


def create_new_document():
    settings = frontend.OptionParser(
        components=(rst.Parser,)).get_default_values()
    document = new_document('dummy.txt', settings)
    return document


def _get_doctree(text):
    document = create_new_document()
    rst.Parser().parse(text, document)
    _transform(document)
    return document


def assert_node_count(messages, node_type, expect_count):
    count = 0
    node_list = [node for node, msg in messages]
    for node in node_list:
        if isinstance(node, node_type):
            count += 1

    assert count == expect_count, (
        "Count of %r in the %r is %d instead of %d"
        % (node_type, node_list, count, expect_count))


def test_extract_messages():
    text = dedent(
        """
        .. admonition:: admonition title

           admonition body
        """
    )
    yield (
        assert_node_count,
        extract_messages(_get_doctree(text)),
        nodes.title, 1,
    )

    text = dedent(
        """
        .. figure:: foo.jpg

           this is title
        """
    )
    yield (
        assert_node_count,
        extract_messages(_get_doctree(text)),
        nodes.caption, 1,
    )

    text = dedent(
        """
        .. rubric:: spam
        """
    )
    yield (
        assert_node_count,
        extract_messages(_get_doctree(text)),
        nodes.rubric, 1,
    )

    text = dedent(
        """
        | spam
        | egg
        """
    )
    yield (
        assert_node_count,
        extract_messages(_get_doctree(text)),
        nodes.line, 2,
    )

    text = dedent(
        """
        section
        =======

        +----------------+
        | | **Title 1**  |
        | | Message 1    |
        +----------------+
        """
    )
    yield (
        assert_node_count,
        extract_messages(_get_doctree(text)),
        nodes.line, 2,
    )

    text = dedent(
        """
        * | **Title 1**
          | Message 1
        """
    )
    yield (
        assert_node_count,
        extract_messages(_get_doctree(text)),
        nodes.line, 2,
    )


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
