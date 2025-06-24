"""Tests the transformations"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='_blank')
def test_transforms_reorder_consecutive_target_and_index_nodes_preserve_order(
    app: SphinxTestApp,
) -> None:
    text = '.. index:: abc\n.. index:: def\n.. index:: ghi\n.. index:: jkl\n\ntext\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            addnodes.index,
            addnodes.index,
            addnodes.index,
            nodes.target,
            nodes.target,
            nodes.target,
            nodes.target,
            nodes.paragraph,
        ),
    )
    assert_node(
        doctree[0], addnodes.index, entries=[('single', 'abc', 'index-0', '', None)]
    )
    assert_node(
        doctree[1], addnodes.index, entries=[('single', 'def', 'index-1', '', None)]
    )
    assert_node(
        doctree[2], addnodes.index, entries=[('single', 'ghi', 'index-2', '', None)]
    )
    assert_node(
        doctree[3], addnodes.index, entries=[('single', 'jkl', 'index-3', '', None)]
    )
    assert_node(doctree[4], nodes.target, refid='index-0')
    assert_node(doctree[5], nodes.target, refid='index-1')
    assert_node(doctree[6], nodes.target, refid='index-2')
    assert_node(doctree[7], nodes.target, refid='index-3')
    # assert_node(doctree[8], nodes.paragraph)


@pytest.mark.sphinx('html', testroot='_blank')
def test_transforms_reorder_consecutive_target_and_index_nodes_no_merge_across_other_nodes(
    app: SphinxTestApp,
) -> None:
    text = (
        '.. index:: abc\n'
        '.. index:: def\n'
        '\n'
        'text\n'
        '\n'
        '.. index:: ghi\n'
        '.. index:: jkl\n'
        '\n'
        'text\n'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            addnodes.index,
            nodes.target,
            nodes.target,
            nodes.paragraph,
            addnodes.index,
            addnodes.index,
            nodes.target,
            nodes.target,
            nodes.paragraph,
        ),
    )
    assert_node(
        doctree[0], addnodes.index, entries=[('single', 'abc', 'index-0', '', None)]
    )
    assert_node(
        doctree[1], addnodes.index, entries=[('single', 'def', 'index-1', '', None)]
    )
    assert_node(doctree[2], nodes.target, refid='index-0')
    assert_node(doctree[3], nodes.target, refid='index-1')
    # assert_node(doctree[4], nodes.paragraph)
    assert_node(
        doctree[5], addnodes.index, entries=[('single', 'ghi', 'index-2', '', None)]
    )
    assert_node(
        doctree[6], addnodes.index, entries=[('single', 'jkl', 'index-3', '', None)]
    )
    assert_node(doctree[7], nodes.target, refid='index-2')
    assert_node(doctree[8], nodes.target, refid='index-3')
    # assert_node(doctree[9], nodes.paragraph)


@pytest.mark.sphinx('html', testroot='_blank')
def test_transforms_reorder_consecutive_target_and_index_nodes_merge_with_labels(
    app: SphinxTestApp,
) -> None:
    text = (
        '.. _abc:\n'
        '.. index:: def\n'
        '.. _ghi:\n'
        '.. index:: jkl\n'
        '.. _mno:\n'
        '\n'
        'Heading\n'
        '=======\n'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            nodes.title,
            addnodes.index,
            addnodes.index,
            nodes.target,
            nodes.target,
            nodes.target,
            nodes.target,
            nodes.target,
        ),
    )
    # assert_node(doctree[8], nodes.title)
    assert_node(
        doctree[1], addnodes.index, entries=[('single', 'def', 'index-0', '', None)]
    )
    assert_node(
        doctree[2], addnodes.index, entries=[('single', 'jkl', 'index-1', '', None)]
    )
    assert_node(doctree[3], nodes.target, refid='abc')
    assert_node(doctree[4], nodes.target, refid='index-0')
    assert_node(doctree[5], nodes.target, refid='ghi')
    assert_node(doctree[6], nodes.target, refid='index-1')
    assert_node(doctree[7], nodes.target, refid='mno')
