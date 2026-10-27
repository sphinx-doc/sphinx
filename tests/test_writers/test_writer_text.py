"""Test the LaTeX writer"""

from __future__ import annotations

import pytest
from docutils.utils import column_width

from sphinx.writers.text import TextWrapper

find_break_end = TextWrapper._find_break_end


@pytest.mark.parametrize(
    # glyph of column width 0
    'glyph',
    ['', '\N{COMBINING TILDE}'],
)
def test_text_wrapper_break_phantom_symbol(glyph: str) -> None:
    assert column_width(glyph) == 0
    glyph_length = len(glyph)

    for n in range(1, 5):
        # Since the glyph has length 0 and column width 0,
        # we can always take the entire glpyh.
        assert find_break_end(glyph, n) == glyph_length
        for m in range(1, 5):
            # The multiplied glyph may have non-zero length
            # but its column width will always be 0, so we
            # take the entire glyph again.
            assert find_break_end(m * glyph, n) == m * glyph_length


@pytest.mark.parametrize(
    ('text', 'colwidth'),
    [
        # Glyph of length 1 and column width 1
        ('X', 1),
        # Glyph of length 1 and column width 2
        ('\N{CJK UNIFIED IDEOGRAPH-65E5}', 2),
        # Glyph of length 2 and column width 1
        ('\N{COMBINING TILDE}X', 1),
        # Glyph of length 2 and column width 2
        ('\N{COMBINING TILDE}\N{CJK UNIFIED IDEOGRAPH-65E5}', 2),
        # Glyph of length 3 and column width 1
        ('\N{COMBINING TILDE}\N{COMBINING BREVE}X', 1),
    ],
)
def test_text_wrapper_break_visible_symbol(text: str, colwidth: int) -> None:
    assert column_width(text) == colwidth
    for n in range(1, 5):
        end = find_break_end(text, n)
        assert column_width(text[:end]) <= n
        for m in range(2, 5):
            m_text = m * text
            end = find_break_end(m_text, n)
            assert column_width(m_text[:end]) <= n
            assert end == m * len(text) or column_width(m_text[: end + 1]) > n


def test_text_wrapper_break_stop_after_combining_symbols() -> None:
    tilde = '\N{COMBINING TILDE}'
    multi = '\N{CJK UNIFIED IDEOGRAPH-65E5}'

    head = tilde + tilde + '....'
    tail = multi + tilde + tilde
    text = head + tail
    assert find_break_end(head + tail, column_width(head)) == len(head)


@pytest.mark.parametrize(
    ('text', 'results'),
    [
        ('Hello', {1: list('Hello'), 2: ['He', 'll', 'o']}),
        (
            'Hello a\N{CJK UNIFIED IDEOGRAPH-65E5}ab!',
            {
                1: list('Helloa\N{CJK UNIFIED IDEOGRAPH-65E5}ab!'),
                2: ['He', 'll', 'o', 'a', '\N{CJK UNIFIED IDEOGRAPH-65E5}', 'ab', '!'],
                3: ['Hel', 'lo', 'a\N{CJK UNIFIED IDEOGRAPH-65E5}', 'ab!'],
            },
        ),
        (
            'ab c\N{COMBINING TILDE}def',
            {
                1: ['a', 'b', 'c\N{COMBINING TILDE}', 'd', 'e', 'f'],
                2: ['ab', 'c\N{COMBINING TILDE}d', 'ef'],
                3: ['ab ', 'c\N{COMBINING TILDE}de', 'f'],
            },
        ),
        (
            'abc\N{COMBINING TILDE}\N{CJK UNIFIED IDEOGRAPH-65E5}def',
            {
                1: [
                    'a',
                    'b',
                    'c\N{COMBINING TILDE}',
                    '\N{CJK UNIFIED IDEOGRAPH-65E5}',
                    'd',
                    'e',
                    'f',
                ],
                2: [
                    'ab',
                    'c\N{COMBINING TILDE}',
                    '\N{CJK UNIFIED IDEOGRAPH-65E5}',
                    'de',
                    'f',
                ],
                3: ['abc\N{COMBINING TILDE}', '\N{CJK UNIFIED IDEOGRAPH-65E5}', 'def'],
            },
        ),
        (
            'abc\N{COMBINING TILDE}\N{COMBINING BREVE}def',
            {
                1: ['a', 'b', 'c\N{COMBINING TILDE}\N{COMBINING BREVE}', 'd', 'e', 'f'],
                2: ['ab', 'c\N{COMBINING TILDE}\N{COMBINING BREVE}d', 'ef'],
                3: ['abc\N{COMBINING TILDE}\N{COMBINING BREVE}', 'def'],
            },
        ),
    ],
)
def test_text_wrapper(text: str, results: dict[int, list[str]]) -> None:
    for width, expected in results.items():
        w = TextWrapper(width=width, drop_whitespace=True)
        assert w.wrap(text) == expected


@pytest.mark.parametrize(
    ('text', 'results'),
    [
        ('Hello', {1: list('Hello'), 2: ['He', 'll', 'o']}),
        (
            'Hello a\N{CJK UNIFIED IDEOGRAPH-65E5}ab!',
            {
                1: list('Hello a\N{CJK UNIFIED IDEOGRAPH-65E5}ab!'),
                2: ['He', 'll', 'o ', 'a', '\N{CJK UNIFIED IDEOGRAPH-65E5}', 'ab', '!'],
                3: ['Hel', 'lo ', 'a\N{CJK UNIFIED IDEOGRAPH-65E5}', 'ab!'],
            },
        ),
        (
            'ab c\N{COMBINING TILDE}def',
            {
                1: ['a', 'b', ' ', 'c\N{COMBINING TILDE}', 'd', 'e', 'f'],
                2: ['ab', ' c\N{COMBINING TILDE}', 'de', 'f'],
                3: ['ab ', 'c\N{COMBINING TILDE}de', 'f'],
            },
        ),
        (
            'abc\N{COMBINING TILDE}\N{CJK UNIFIED IDEOGRAPH-65E5}def',
            {
                1: [
                    'a',
                    'b',
                    'c\N{COMBINING TILDE}',
                    '\N{CJK UNIFIED IDEOGRAPH-65E5}',
                    'd',
                    'e',
                    'f',
                ],
                2: [
                    'ab',
                    'c\N{COMBINING TILDE}',
                    '\N{CJK UNIFIED IDEOGRAPH-65E5}',
                    'de',
                    'f',
                ],
                3: ['abc\N{COMBINING TILDE}', '\N{CJK UNIFIED IDEOGRAPH-65E5}', 'def'],
            },
        ),
        (
            'abc\N{COMBINING TILDE}\N{COMBINING BREVE}def',
            {
                1: ['a', 'b', 'c\N{COMBINING TILDE}\N{COMBINING BREVE}', 'd', 'e', 'f'],
                2: ['ab', 'c\N{COMBINING TILDE}\N{COMBINING BREVE}d', 'ef'],
                3: ['abc\N{COMBINING TILDE}\N{COMBINING BREVE}', 'def'],
            },
        ),
    ],
)
def test_text_wrapper_drop_ws(text: str, results: dict[int, list[str]]) -> None:
    for width, expected in results.items():
        w = TextWrapper(width=width, drop_whitespace=False)
        assert w.wrap(text) == expected
