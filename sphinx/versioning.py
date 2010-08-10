# -*- coding: utf-8 -*-
"""
    sphinx.versioning
    ~~~~~~~~~~~~~~~~~

    Implements the low-level algorithms Sphinx uses for the versioning of
    doctrees.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from uuid import uuid4
from itertools import izip_longest, product
from difflib import SequenceMatcher

from sphinx.util import PeekableIterator

def add_uids(doctree, condition):
    """
    Adds a unique id to every node in the `doctree` which matches the condition
    and yields it.

    :param doctree:
        A :class:`docutils.nodes.document` instance.

    :param condition:
        A callable which returns either ``True`` or ``False`` for a given node.
    """
    for node in doctree.traverse(condition):
        node.uid = uuid4().hex
        yield node

def merge_node(old, new):
    """
    Merges the `old` node with the `new` one, if it's successful the `new` node
    get's the unique identifier of the `new` one and ``True`` is returned. If
    the merge is unsuccesful ``False`` is returned.
    """
    equals, changed, replaced = make_diff(old.rawsource,
                                          new.rawsource)
    if equals or changed:
        new.uid = old.uid
        return True
    return False

def merge_doctrees(old, new, condition):
    """
    Merges the `old` doctree with the `new` one while looking at nodes matching
    the `condition`.

    Each node which replaces another one or has been added to the `new` doctree
    will be yielded.

    :param condition:
        A callable which returns either ``True`` or ``False`` for a given node.
    """
    old_iter = PeekableIterator(old.traverse(condition))
    new_iter = PeekableIterator(new.traverse(condition))
    old_nodes = []
    new_nodes = []
    for old_node, new_node in izip_longest(old_iter, new_iter):
        if old_node is None:
            new_nodes.append(new_node)
            continue
        if new_node is None:
            old_nodes.append(old_node)
            continue
        if not merge_node(old_node, new_node):
            if old_nodes:
                for i, old_node in enumerate(old_nodes):
                    if merge_node(old_node, new_node):
                        del old_nodes[i]
                        # If the last identified node which has not matched the
                        # unidentified node matches the current one, we have to
                        # assume that the last unidentified one has been
                        # inserted.
                        #
                        # As the required time multiplies with each insert, we
                        # want to avoid that by checking if the next
                        # unidentified node matches the current identified one
                        # and if so we make a shift.
                        if i == len(old_nodes):
                            next_new_node = new_iter.next()
                            if not merge_node(old_node, next_new_node):
                                new_iter.push(next_new_node)
                        break
            else:
                old_nodes.append(old_node)
                new_nodes.append(new_node)
    for (i, new_node), (j, old_node) in product(enumerate(new_nodes), enumerate(old_nodes)):
        if merge_node(old_node, new_node):
            del new_nodes[i]
            del old_nodes[j]
    new_nodes = [n for n in new_nodes if not hasattr(n, 'uid')]
    for node in new_nodes:
        node.uid = uuid4().hex
        # Yielding the new nodes here makes it possible to use this generator
        # like add_uids
        yield node

def make_diff(old, new):
    """
    Takes two strings `old` and `new` and returns a :class:`tuple` of boolean
    values ``(equals, changed, replaced)``.

    equals

        ``True`` if the `old` string and the `new` one are equal.

    changed

        ``True`` if the `new` string differs from the `old` one with at least
        one character.

    replaced

        ``True`` if the `new` string and the `old` string are totally
        different.

    .. note:: This assumes the two strings are human readable text or at least
              something very similar to that, otherwise it can not detect if
              the string has been changed or replaced. In any case the
              detection should not be considered reliable.
    """
    if old == new:
        return True, False, False
    if new in old or levenshtein_distance(old, new) / (len(old) / 100.0) < 70:
        return False, True, False
    return False, False, True

def levenshtein_distance(a, b):
    if len(a) < len(b):
        a, b = b, a
    if not a:
        return len(b)
    previous_row = xrange(len(b) + 1)
    for i, column1 in enumerate(a):
        current_row = [i + 1]
        for j, column2 in enumerate(b):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (column1 != column2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]
