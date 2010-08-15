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
from operator import itemgetter
from collections import defaultdict
from itertools import product

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

def merge_doctrees(old, new, condition):
    """
    Merges the `old` doctree with the `new` one while looking at nodes matching
    the `condition`.

    Each node which replaces another one or has been added to the `new` doctree
    will be yielded.

    :param condition:
        A callable which returns either ``True`` or ``False`` for a given node.
    """
    old_nodes = old.traverse(condition)
    new_nodes = new.traverse(condition)
    ratios = defaultdict(list)
    seen = set()
    for old_node, new_node in product(old_nodes, new_nodes):
        if new_node in seen:
            continue
        ratio = get_ratio(old_node.rawsource, new_node.rawsource)
        if ratio == 0:
            new_node.uid = old_node.uid
            seen.add(new_node)
        else:
            ratios[old_node, new_node] = ratio
    ratios = sorted(ratios.iteritems(), key=itemgetter(1))
    for (old_node, new_node), ratio in ratios:
        if new_node in seen:
            continue
        else:
            seen.add(new_node)
        if ratio < 65:
            new_node.uid = old_node.uid
        else:
            new_node.uid = uuid4().hex
            yield new_node

def get_ratio(old, new):
    """
    Returns a "similiarity ratio" representing the similarity between the two
    strings where 0 is equal and anything above less than equal.
    """
    return levenshtein_distance(old, new) / (len(old) / 100.0)

def levenshtein_distance(a, b):
    if a == b:
        return 0
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
