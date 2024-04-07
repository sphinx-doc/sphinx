from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from sphinx.testing.matcher import cleaner

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sphinx.testing.matcher._util import PatternLike
    from sphinx.testing.matcher.cleaner import Trace


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

    expect = ['a', 'b', 'c', 'a']
    assert list(cleaner.filter_lines(src, keep_empty=False, compress=True)) == expect

    expect = ['a', 'b', 'c']
    assert list(cleaner.filter_lines(src, keep_empty=False, unique=True)) == expect

    expect = ['a', '', 'a', 'b', 'c', 'a']
    assert list(cleaner.filter_lines(src, keep_empty=True, compress=True)) == expect

    expect = ['a', '', 'b', 'c']
    assert list(cleaner.filter_lines(src, keep_empty=True, unique=True)) == expect


@pytest.mark.parametrize(
    ('lines', 'patterns', 'expect', 'trace'),
    [
        (
            ['88D79F0A2', '###'],
            r'\d+',
            ['DFA', '###'],
            [
                [('88D79F0A2', ['DFA'])],
                [('###', ['###'])],
            ],
        ),
        (
            ['11a1', 'b1'],
            '^1',
            ['a1', 'b1'],
            [
                [('11a1', ['1a1']), ('1a1', ['a1'])],
                [('b1', ['b1'])],
            ],
        ),
        (
            ['ABC#123'],
            [r'^[A-Z]', r'\d$'],
            ['#'],
            [
                [
                    ('ABC#123', ['BC#123', 'BC#12']),
                    ('BC#12', ['C#12', 'C#1']),
                    ('C#1', ['#1', '#']),
                ],
            ],
        ),
        (
            ['a 123\n456x7\n8\n b'],
            [re.compile(r'\d\d'), re.compile(r'\n+')],
            ['a x b'],
            [
                [
                    # elimination of double digits and new lines (in that order)
                    ('a 123\n456x7\n8\n b', ['a 3\n6x7\n8\n b', 'a 36x78 b']),
                    # new digits appeared so we re-eliminated them
                    ('a 36x78 b', ['a x b', 'a x b']),
                ]
            ],
        ),
        (
            ['a 123\n456x7\n8\n b'],
            [re.compile(r'\n+'), re.compile(r'\d\d')],
            ['a x b'],
            [
                [
                    # elimination of new lines and double digits (in that order)
                    ('a 123\n456x7\n8\n b', ['a 123456x78 b', 'a x b']),
                ]
            ],
        ),
    ],
)
def test_prune_lines(
    lines: Sequence[str],
    patterns: PatternLike | Sequence[PatternLike],
    expect: Sequence[str],
    trace: Trace,
) -> None:
    actual_trace: Trace = []
    actual = cleaner.prune_lines(lines, patterns, trace=actual_trace)
    assert list(actual) == list(expect)
    assert actual_trace == list(trace)
