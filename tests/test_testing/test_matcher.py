from __future__ import annotations

import dataclasses
import itertools
from functools import cached_property
from typing import TYPE_CHECKING

import pytest

import sphinx.testing.matcher._util as util
import sphinx.util.console as term
from sphinx.testing.matcher import LineMatcher

if TYPE_CHECKING:
    from collections.abc import Sequence, Set

    from _pytest._code import ExceptionInfo

    from sphinx.testing.matcher._util import LinePattern
    from sphinx.testing.matcher.options import Flavor


@dataclasses.dataclass
class Source:
    total: int
    """The total number of lines in the source."""
    start: int
    """The start index of the main block."""
    width: int
    """The size of the main block."""
    dedup: int
    """Number of times the main block is duplicated."""

    @property
    def ncopy(self) -> int:
        """The number of copies of the base block in the main block."""
        return self.dedup + 1

    @property
    def stop(self) -> int:
        """Stop index of the main block."""
        # possibly out of bounds if the test fixture requires
        # more copies than possible
        return self.start + self.ncopy * self.width

    @cached_property
    def lines(self) -> list[str]:
        """The source's lines."""
        return [*self.head, *self.main, *self.tail]

    @cached_property
    def text(self) -> str:
        """The source as a single string."""
        return '\n'.join(self.lines)

    @cached_property
    def head(self) -> list[str]:
        """The lines before the highlighted block."""
        return list(map(self.outer_line, range(self.start)))

    @cached_property
    def tail(self) -> list[str]:
        """The lines after the highlighted block."""
        return list(map(self.outer_line, range(self.stop, self.total)))

    @cached_property
    def base(self) -> list[str]:
        """Single main block (no duplication)."""
        return list(map(self.block_line, range(self.start, self.start + self.width)))

    @cached_property
    def main(self) -> list[str]:
        """The block that could be highlighted (possibly duplicated)."""
        parts = itertools.repeat(self.base, self.ncopy)
        block = list(itertools.chain.from_iterable(parts))
        assert len(block) == self.ncopy * self.width, 'ill-formed block'
        return block

    def peek_prev(self, context_size: int) -> list[str]:
        """The context lines before the main block."""
        imin = max(0, self.start - context_size)
        peek = [Source.outer_line(i) for i in range(imin, self.start)]
        assert len(peek) <= context_size
        return peek

    def peek_next(self, context_size: int) -> list[str]:
        """The context lines after the main block."""
        imax = min(self.stop + context_size, self.total)
        peek = [Source.outer_line(i) for i in range(self.stop, imax)]
        assert len(peek) <= context_size
        return peek

    @staticmethod
    def outer_line(i: int) -> str:
        """Line not in the main block."""
        return f'L{i}'

    @staticmethod
    def block_line(i: int) -> str:
        """Line in the main block."""
        return f'B{i}'


def make_debug_context(
    block: list[str],  # highlighted block
    /,
    view_prev: list[str],  # context lines before the main block
    omit_prev: int,  # number of lines that were omitted before 'view_prev'
    view_next: list[str],  # context lines after the main block
    omit_next: int,  # number of lines that were omitted after 'view_next'
    *,
    context_size: int,  # the original value of the 'context_size' parameter
    indent: int = 4,
) -> list[str]:
    """Other API for :func:`sphinx.testing.matcher._util.diff`.

    The resulting lines are of the form::

    - a line indicating that *omit_prev* lines were omitted,
    - the block *view_prev*,
    - the main *block* (highlighted),
    - the block *view_next*,
    - a line indicating that *omit_next* lines were omitted.

    If *context_size = 0*, the lines indicating omitted lines are not included.
    """
    lines: list[str] = []
    writelines = lines.extend
    writelines(util.omit_line(bool(context_size) * omit_prev))
    writelines(util.indent_lines(view_prev, indent=indent, highlight=False))
    writelines(util.indent_lines(block, indent=indent, highlight=True))
    writelines(util.indent_lines(view_next, indent=indent, highlight=False))
    writelines(util.omit_line(bool(context_size) * omit_next))
    return lines


def parse_excinfo(excinfo: ExceptionInfo[AssertionError]) -> list[str]:
    # see: https://github.com/pytest-dev/pytest/issues/12175
    assert excinfo.type is AssertionError
    assert excinfo.value is not None
    return str(excinfo.value).removeprefix('AssertionError: ').splitlines()


def test_matcher_cache():
    source = [term.blue('hello'), '', 'world']
    matcher = LineMatcher.from_lines(source)

    stack_attribute = f'_{matcher.__class__.__name__.lstrip("_")}__stack'
    stack = getattr(matcher, stack_attribute)
    assert len(stack) == 1
    assert stack[0] is None

    cached = matcher.lines()
    assert len(stack) == 1
    assert stack[0] is cached
    assert cached == (term.blue('hello'), '', 'world')

    assert matcher.lines() is cached  # cached result
    assert len(stack) == 1

    with matcher.override():
        assert len(stack) == 2
        assert stack[0] is cached
        assert stack[1] is None

        assert matcher.lines() == cached
        assert len(stack) == 2
        assert stack[1] == 0  # do not duplicate the lines

        assert matcher.lines() is cached
        assert len(stack) == 2

    assert len(stack) == 1
    assert stack[0] is cached
    assert matcher.lines() is cached

    with matcher.override(keep_ansi=False):
        assert len(stack) == 2
        assert stack[0] is cached
        assert stack[1] is None

        assert matcher.lines() == ('hello', '', 'world')
        assert len(stack) == 2
        assert stack[1] == ('hello', '', 'world')


@pytest.mark.parametrize(
    ('lines', 'flavor', 'pattern', 'expect'),
    [
        ([], 'literal', [], []),
        (['a'], 'literal', '', []),
        (['a'], 'literal', [], []),
        (['1', 'b', '3', 'a', '5', '!'], 'literal', ('a', 'b'), [('b', 1), ('a', 3)]),
        (['blbl', 'yay', 'hihi', '^o^'], 'fnmatch', '*[ao]*', [('yay', 1), ('^o^', 3)]),
        (['111', 'hello', 'world', '222'], 're', r'\d+', [('111', 0), ('222', 3)]),
        (['hello', 'world', 'yay'], 'literal', {'hello', 'yay'}, [('hello', 0), ('yay', 2)]),
        (['hello', 'world', 'yay'], 'fnmatch', {'hello', 'y*y'}, [('hello', 0), ('yay', 2)]),
        (['hello', 'world', 'yay'], 're', {'hello', r'^y\wy$'}, [('hello', 0), ('yay', 2)]),
    ],
)
def test_matcher_find(
    lines: list[str],
    flavor: Flavor,
    pattern: LinePattern | Set[LinePattern] | Sequence[LinePattern],
    expect: Sequence[tuple[str, int]],
) -> None:
    matcher = LineMatcher.from_lines(lines, flavor=flavor)
    assert matcher.find(pattern) == tuple(expect)

    matcher = LineMatcher.from_lines(lines, flavor='literal')
    assert matcher.find(pattern, flavor=flavor) == tuple(expect)


def test_matcher_find_blocks():
    lines = ['hello', 'world', 'yay', 'hello', 'world', '!', 'yay']
    matcher = LineMatcher.from_lines(lines)

    assert matcher.find_blocks(['hello', 'world']) == (
        [('hello', 0), ('world', 1)],
        [('hello', 3), ('world', 4)],
    )

    assert matcher.find_blocks(['hello', 'w[oO]rld'], flavor='fnmatch') == (
        [('hello', 0), ('world', 1)],
        [('hello', 3), ('world', 4)],
    )

    assert matcher.find_blocks(['hello', r'^w[a-z]{2}\wd$'], flavor='re') == (
        [('hello', 0), ('world', 1)],
        [('hello', 3), ('world', 4)],
    )


def test_assert_match():
    matcher = LineMatcher.from_lines(['a', 'b', 'c', 'd'])
    matcher.assert_any_of('.+', flavor='re')
    matcher.assert_any_of('[abcd]', flavor='fnmatch')

    matcher = LineMatcher('')
    with pytest.raises(AssertionError, match=r'(?s:.+not found in.+)'):
        matcher.assert_any_of('.+', flavor='re')

    matcher = LineMatcher('')
    with pytest.raises(AssertionError, match=r'(?s:.+not found in.+)'):
        matcher.assert_any_of('.*', flavor='re')

    matcher = LineMatcher.from_lines(['\n'])
    assert matcher.lines() == ['']
    matcher.assert_any_of('.*', flavor='re')


@pytest.mark.parametrize(
    ('lines', 'pattern', 'flavor', 'expect'),
    [
        (
            ['a', 'b', 'c', 'd', 'e'],
            '[a-z]{3,}',
            're',
            [
                'line pattern',
                '',
                '    [a-z]{3,}',
                '',
                'not found in',
                '',
                '    a',
                '    b',
                '    c',
                '    d',
                '    e',
            ],
        ),
    ],
)
def test_assert_match_debug(lines, pattern, flavor, expect):
    matcher = LineMatcher.from_lines(lines)

    with pytest.raises(AssertionError) as exc_info:
        matcher.assert_any_of(pattern, flavor=flavor)

    assert parse_excinfo(exc_info) == expect


def test_assert_no_match():
    matcher = LineMatcher.from_lines(['a', 'b', 'c', 'd'])
    matcher.assert_none_of(r'\d+', flavor='re')
    matcher.assert_none_of('[1-9]', flavor='fnmatch')


@pytest.mark.parametrize(
    ('lines', 'pattern', 'flavor', 'context', 'expect'),
    [
        (
            ['a', 'b', '11X', '22Y', '33Z', 'c', 'd'],
            '[1-9]{2}[A-Z]',
            're',
            2,
            [
                'line pattern',
                '',
                '    [1-9]{2}[A-Z]',
                '',
                'found in',
                '',
                '    a',
                '    b',
                '>   11X',
                '    22Y',
                '    33Z',
                '... (omitted 2 lines) ...',
            ],
        ),
    ],
)
def test_assert_no_match_debug(lines, pattern, flavor, context, expect):
    matcher = LineMatcher.from_lines(lines)

    with pytest.raises(AssertionError) as exc_info:
        matcher.assert_none_of(pattern, context=context, flavor=flavor)

    assert parse_excinfo(exc_info) == expect


@pytest.mark.parametrize('dedup', range(3))
@pytest.mark.parametrize(('maxsize', 'start', 'count'), [(10, 3, 4)])
def test_assert_block_coverage(maxsize, start, count, dedup):
    # 'maxsize' might be smaller than start + (dedup +  1) * count
    # but it is fine since stop indices are clamped internally
    source = Source(maxsize, start, count, dedup=dedup)
    matcher = LineMatcher(source.text)

    # the main block is matched exactly once
    matcher.assert_block(source.main, count=1, flavor='literal')
    assert source.base * source.ncopy == source.main
    matcher.assert_block(source.base, count=source.ncopy, flavor='literal')

    for subidx in range(1, count + 1):
        # check that the sub-blocks are matched correctly
        subblock = [Source.block_line(start + i) for i in range(subidx)]
        matcher.assert_block(subblock, count=source.ncopy, flavor='literal')


@pytest.mark.parametrize(
    ('lines', 'pattern', 'count', 'expect'),
    [
        (
            ['a', 'b', 'c', 'a', 'b', 'd'],
            ['x', 'y'],
            None,
            [
                'block pattern',
                '',
                '    x',
                '    y',
                '',
                'not found in',
                '',
                '    a',
                '    b',
                '    c',
                '    a',
                '    b',
                '    d',
            ],
        ),
        (
            ['a', 'b', 'c', 'a', 'b', 'd'],
            ['a', 'b'],
            1,
            [
                'found 2 != 1 block matching',
                '',
                '    a',
                '    b',
                '',
                'in',
                '',
                '>   a',
                '>   b',
                '    c',
                '>   a',
                '>   b',
                '    d',
            ],
        ),
        (['a', 'b', 'c', 'a', 'b', 'd'], ['a', 'b'], 2, None),
        (
            ['a', 'b', 'c', 'a', 'b', 'd'],
            ['a', 'b'],
            3,
            [
                'found 2 != 3 blocks matching',
                '',
                '    a',
                '    b',
                '',
                'in',
                '',
                '>   a',
                '>   b',
                '    c',
                '>   a',
                '>   b',
                '    d',
            ],
        ),
    ],
)
def test_assert_block_debug(lines, pattern, count, expect):
    matcher = LineMatcher.from_lines(lines, flavor='literal')

    if expect is None:
        matcher.assert_block(pattern, count=count)
        return

    with pytest.raises(AssertionError, match='.*') as exc_info:
        matcher.assert_block(pattern, count=count)

    assert parse_excinfo(exc_info) == expect


@pytest.mark.parametrize(('maxsize', 'start', 'count'), [
    # combinations of integers (a, b, c) such that c >= 1 and a >= b + c
    (1, 0, 1),
    (2, 0, 1), (2, 0, 2), (2, 1, 1),
    (3, 0, 1), (3, 0, 2), (3, 0, 3), (3, 1, 1), (3, 1, 2), (3, 2, 1),
])  # fmt: skip
@pytest.mark.parametrize('dedup', range(3))
def test_assert_no_block_coverage(maxsize, start, count, dedup):
    # 'maxsize' might be smaller than start + (dedup +  1) * count
    # but it is fine since stop indices are clamped internally
    source = Source(maxsize, start, count, dedup=dedup)
    matcher = LineMatcher(source.text, flavor='literal')

    with pytest.raises(AssertionError) as exc_info:
        matcher.assert_no_block(source.main, context=0)

    assert parse_excinfo(exc_info) == [
        'block pattern',
        '',
        *util.indent_lines(source.main, indent=4, highlight=False),
        '',
        'found in',
        '',
        *util.indent_lines(source.main, indent=4, highlight=True),
    ]


@pytest.mark.parametrize(
    ('lines', 'pattern', 'flavor', 'context', 'expect'),
    [
        (
            ['a', 'b', '11X', '22Y', '33Z', 'c', 'd', 'e', 'f'],
            [r'\d{2}X', r'\d*\w+', r'^33Z$'],
            're',
            2,
            [
                'block pattern',
                '',
                r'    \d{2}X',
                r'    \d*\w+',
                r'    ^33Z$',
                '',
                'found in',
                '',
                '    a',
                '    b',
                '>   11X',
                '>   22Y',
                '>   33Z',
                '    c',
                '    d',
                '... (omitted 2 lines) ...',
            ],
        ),
    ],
)
def test_assert_no_block_debug(lines, pattern, flavor, context, expect):
    matcher = LineMatcher.from_lines(lines)

    with pytest.raises(AssertionError) as exc_info:
        matcher.assert_no_block(pattern, context=context, flavor=flavor)

    assert parse_excinfo(exc_info) == expect


@pytest.mark.parametrize(
    ('maxsize', 'start', 'count', 'dedup', 'omit_prev', 'omit_next', 'context_size'),
    [
        # with small context
        (10, 2, 4, 0, 1, 3, 1),  # [--, L1, B2, B3, B4, B5, L6, --, --, --]
        (10, 3, 4, 0, 2, 2, 1),  # [--, --, L2, B3, B4, B5, B6, L7, --, --]
        (10, 4, 4, 0, 3, 1, 1),  # [--, --, --, L3, B4, B5, B6, B7, L8, --]
        # with large context
        (10, 2, 4, 0, 0, 1, 3),  # [L0, L1, B2, B3, B4, B5, L6, L7, L8, --]
        (10, 4, 4, 0, 0, 0, 5),  # [L0, L1, L2, L3, B4, B5, B6, B7, L8, L9]
        (10, 4, 4, 0, 1, 0, 3),  # [--, L1, L2, L3, B4, B5, B6, B7, L8, L9]
        # with duplicated block and small context
        # [--, L1, (B2, B3, B4, B5) (2x), L10, -- (9x)]
        (20, 2, 4, 1, 1, 9, 1),
        # [--, --, L2, (B3, B4, B5, B6) (2x), L10, -- (8x)]
        (20, 3, 4, 1, 2, 8, 1),
        # [--, --, --, L3, (B4, B5, B6, B7) (2x), L11, -- (7x)]
        (20, 4, 4, 1, 3, 7, 1),
        # with duplicated block and large context
        # [L0, L1, (B2, B3, B4, B5) (2x), L10, L11, L12, L13, L14, -- (5x)]
        (20, 2, 4, 1, 0, 5, 5),
        # [L0, L1, (B2, B3, B4, B5) (3x), L17, L18, L19]
        (20, 2, 4, 2, 0, 0, 10),
        # [--, --, --, --, --, L5, L6, L7, (B8, B9) (5x), L18, L19]
        (20, 8, 2, 4, 5, 0, 3),
    ],
)
def test_assert_no_block_debug_coverage(
    maxsize, start, count, dedup, omit_prev, omit_next, context_size
):
    source = Source(maxsize, start, count, dedup=dedup)
    matcher = LineMatcher(source.text, flavor='literal')
    with pytest.raises(AssertionError) as exc_info:
        matcher.assert_no_block(source.main, context=context_size)

    assert parse_excinfo(exc_info) == [
        'block pattern',
        '',
        *util.indent_lines(source.main, indent=4, highlight=False),
        '',
        'found in',
        '',
        *make_debug_context(
            source.main,
            source.peek_prev(context_size),
            omit_prev,
            source.peek_next(context_size),
            omit_next,
            context_size=context_size,
            indent=4,
        ),
    ]
