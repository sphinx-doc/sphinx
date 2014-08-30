# -*- coding: utf-8 -*-
"""
    test_util_nodes
    ~~~~~~~~~~~~~~~

    Tests uti.nodes functions.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from textwrap import dedent

from docutils import nodes
from docutils.parsers import rst
from docutils.utils import new_document
from docutils import frontend

from sphinx.util.nodes import extract_messages


def _get_doctree(text):
    settings = frontend.OptionParser(
        components=(rst.Parser,)).get_default_values()
    document = new_document('dummy.txt', settings)
    rst.Parser().parse(text, document)
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
