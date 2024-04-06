from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from sphinx.testing.matcher.cleaner import filter_lines, prune_lines, strip_chars, strip_lines

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sphinx.testing.matcher._util import PatternLike


def test_strip_chars():
    assert strip_chars('abaaa\n') == 'abaaa'
    assert strip_chars('abaaa\n', False) == 'abaaa\n'
    assert strip_chars('abaaa', 'a') == 'b'
    assert strip_chars('abaaa', 'ab') == ''


def test_strip_lines():
    assert list(strip_lines(['aba\n', 'aba\n'])) == ['aba', 'aba']
    assert list(strip_lines(['aba\n', 'aba\n'], False)) == ['aba\n', 'aba\n']
    assert list(strip_lines(['aba', 'aba'], 'a')) == ['b', 'b']
    assert list(strip_lines(['aba', 'aba'], 'ab')) == ['', '']


def test_filter_lines():
    src = ['a', 'a', '', 'a', 'b', 'c', 'a']
    assert list(filter_lines(src, keep_empty=False, compress=True)) == ['a', 'b', 'c', 'a']
    assert list(filter_lines(src, keep_empty=False, unique=True)) == ['a', 'b', 'c']

    expect = ['a', '', 'a', 'b', 'c', 'a']
    assert list(filter_lines(src, keep_empty=True, compress=True)) == expect

    assert list(filter_lines(src, keep_empty=True, unique=True)) == ['a', '', 'b', 'c']


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
    trace: list[list[tuple[str, list[str]]]],
) -> None:
    actual_trace: list[list[tuple[str, list[str]]]] = []
    actual = prune_lines(lines, patterns, trace=actual_trace)
    assert list(actual) == list(expect)
    assert actual_trace == list(trace)
