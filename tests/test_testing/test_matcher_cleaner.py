from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from sphinx.testing._matcher import cleaner

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence


def test_strip_chars():
    assert cleaner.strip_chars('abaaa\n') == 'abaaa'
    assert cleaner.strip_chars('abaaa\n', False) == 'abaaa\n'
    assert cleaner.strip_chars('abaaa', 'a') == 'b'
    assert cleaner.strip_chars('abaaa', 'ab') == ''


def test_strip_lines():
    assert list(cleaner.strip_lines(['aba\n', 'aba\n'])) == ['aba', 'aba']
    assert list(cleaner.strip_lines(['aba\n', 'aba\n'], False)) == ['aba\n', 'aba\n']
    assert list(cleaner.strip_lines(['aba', 'aba'], 'a')) == ['b', 'b']
    assert list(cleaner.strip_lines(['aba', 'aba'], 'ab')) == ['', '']


def test_filter_lines():
    src = ['a', 'a', '', 'a', 'b', 'c', 'a']
    assert list(cleaner.filter_lines(src, empty=False, compress=True)) == ['a', 'b', 'c', 'a']
    assert list(cleaner.filter_lines(src, empty=False, unique=True)) == ['a', 'b', 'c']

    expect = ['a', '', 'a', 'b', 'c', 'a']
    assert list(cleaner.filter_lines(src, empty=True, compress=True)) == expect

    assert list(cleaner.filter_lines(src, empty=True, unique=True)) == ['a', '', 'b', 'c']


@pytest.fixture()
def prune_trace_object() -> Callable[[], list[Sequence[tuple[str, Sequence[str]]]]]:
    return list


def test_prune_prefix(prune_trace_object):
    trace = prune_trace_object()
    lines = cleaner.prune(['1111a1', 'b1'], '1', flavor='none', trace=trace)
    assert list(lines) == ['a1', 'b1']
    assert trace == [
        [
            ('1111a1', ['111a1']),
            ('111a1', ['11a1']),
            ('11a1', ['1a1']),
            ('1a1', ['a1']),
            ('a1', ['a1']),
        ],
        [('b1', ['b1'])],
    ]

    trace = prune_trace_object()
    lines = cleaner.prune(['1111a1', 'b1'], r'\d+', flavor='re', trace=trace)
    assert list(lines) == ['a1', 'b1']
    assert trace == [
        [('1111a1', ['a1']), ('a1', ['a1'])],
        [('b1', ['b1'])],
    ]

    trace = prune_trace_object()
    lines = cleaner.prune(['/a/b/c.txt', 'keep.py'], '*.txt', flavor='fnmatch', trace=trace)
    assert list(lines) == ['', 'keep.py']
    assert trace == [
        [('/a/b/c.txt', ['']), ('', [''])],
        [('keep.py', ['keep.py'])],
    ]


def test_prune_groups(prune_trace_object):
    lines = cleaner.prune(['a123b', 'c123d'], re.compile(r'\d+'))
    assert list(lines) == ['ab', 'cd']

    p1 = re.compile(r'\d\d')
    p2 = re.compile(r'\n+')

    trace = prune_trace_object()
    lines = cleaner.prune(['a 123\n456x7\n8\n b'], [p1, p2], trace=trace)
    assert list(lines) == ['a x b']

    assert len(trace) == 1
    assert len(trace[0]) == 3
    # elimination of double digits and new lines (in that order)
    assert trace[0][0] == ('a 123\n456x7\n8\n b', ['a 3\n6x7\n8\n b', 'a 36x78 b'])
    # new digits appeared so we re-eliminated them
    assert trace[0][1] == ('a 36x78 b', ['a x b', 'a x b'])
    # identity for both patterns
    assert trace[0][2] == ('a x b', ['a x b', 'a x b'])

    trace = prune_trace_object()
    lines = cleaner.prune(['a 123\n456x7\n8\n b'], [p2, p1], trace=trace)
    assert list(lines) == ['a x b']

    assert len(trace) == 1
    assert len(trace[0]) == 2
    # elimination of new lines and double digits (in that order)
    assert trace[0][0] == ('a 123\n456x7\n8\n b', ['a 123456x78 b', 'a x b'])
    # identity for both patterns
    assert trace[0][1] == ('a x b', ['a x b', 'a x b'])
