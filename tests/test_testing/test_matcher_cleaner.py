from __future__ import annotations

import re
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from sphinx.testing.matcher import cleaner
from sphinx.testing.matcher._cleaner import HandlerMap, make_handlers
from sphinx.testing.matcher.options import OpCode, Options

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sphinx.testing.matcher._util import PatternLike
    from sphinx.testing.matcher.cleaner import TraceInfo


def test_implementation_details():
    # expected and supported operation codes
    expect = sorted(getattr(OpCode, '__args__', []))
    qualname = f'{HandlerMap.__module__}.{HandlerMap.__name__}'
    assert expect, f'{qualname}: invalid literal type: {OpCode}'

    # ensure that the typed dictionary is synchronized
    actual = sorted(HandlerMap.__annotations__.keys())
    qualname = f'{HandlerMap.__module__}.{HandlerMap.__name__}'
    assert actual == expect, f'invalid operation codes in: {qualname!r}'

    handlers = make_handlers(mock.Mock())
    assert isinstance(handlers, dict)
    actual = sorted(handlers.keys())
    assert actual == expect, 'invalid factory function'


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
    src = '\n'.join(['a', 'a', '', 'a', 'b', 'c', 'a'])  # NoQA: FLY002

    expect = ['a', 'b', 'c', 'a']
    assert list(cleaner.clean(src, keep_empty=False, compress=True)) == expect

    expect = ['a', 'b', 'c']
    assert list(cleaner.clean(src, keep_empty=False, unique=True)) == expect

    expect = ['a', '', 'a', 'b', 'c', 'a']
    assert list(cleaner.clean(src, keep_empty=True, compress=True)) == expect

    expect = ['a', '', 'b', 'c']
    assert list(cleaner.clean(src, keep_empty=True, unique=True)) == expect


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
    trace: TraceInfo,
) -> None:
    actual_trace: TraceInfo = []
    actual = cleaner.prune_lines(lines, patterns, trace=actual_trace)
    assert list(actual) == list(expect)
    assert actual_trace == list(trace)


def test_opcodes():
    options = Options(strip_line=True, keep_empty=False, compress=True)

    src = '\n'.join(['a', '', 'a', '', 'a'])  # NoQA: FLY002
    # empty lines removed before duplicates
    assert list(cleaner.clean(src, **options)) == ['a']

    # empty lines removed after duplicates
    options_with_opcodes = options | {'ops': ('strip', 'compress', 'check')}
    assert list(cleaner.clean(src, **options_with_opcodes)) == ['a', 'a', 'a']
