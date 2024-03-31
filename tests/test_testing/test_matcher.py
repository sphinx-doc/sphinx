from __future__ import annotations

import dataclasses
import itertools
from functools import cached_property
from typing import TYPE_CHECKING, cast

import _pytest.outcomes
import pytest

import sphinx.util.console as term
from sphinx.testing._matcher import util
from sphinx.testing._matcher.buffer import Block, Line
from sphinx.testing._matcher.options import DEFAULT_OPTIONS, CompleteOptions, Options
from sphinx.testing.matcher import LineMatcher, clean

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Final

    from sphinx.testing._matcher.options import Flavor, OptionName
    from sphinx.testing._matcher.util import LinePattern


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
    block: list[str],
    /,
    view_prev: list[str],
    omit_prev: int,
    view_next: list[str],
    omit_next: int,
    *,
    context_size: int,
    indent: int = 4,
) -> list[str]:
    """Other API for :func:`sphinx.testing._matcher.util.get_debug_context`."""
    lines: list[str] = []
    writelines = lines.extend
    writelines(util.omit_line(bool(context_size) * omit_prev))
    writelines(util.indent_lines(view_prev, indent=indent, highlight=False))
    writelines(util.indent_lines(block, indent=indent, highlight=True))
    writelines(util.indent_lines(view_next, indent=indent, highlight=False))
    writelines(util.omit_line(bool(context_size) * omit_next))
    return lines


class TestClean:
    # options with no cleaning phase (equivalent to text.striplines(True))
    noop: Final[CompleteOptions] = CompleteOptions(
        color=True,
        ctrl=True,
        strip=False,
        stripline=False,
        keepends=True,
        empty=True,
        compress=False,
        unique=False,
        delete_prefix=(),
        delete_suffix=(),
        ignore=None,
        flavor='exact',
    )

    @classmethod
    def check(cls, text: str, options: Options, expect: Sequence[str]) -> None:
        options = cast(Options, cls.noop) | options
        assert clean(text, **options) == tuple(expect)

    @pytest.mark.parametrize(
        ('text', 'options', 'expect'),
        [
            ('a ', Options(), ['a ']),
            ('a\nb ', Options(), ['a\n', 'b ']),
            (
                '\n'.join(['a', 'a', '', 'a', 'b', 'c', 'a']),
                Options(keepends=False),
                ['a', 'a', '', 'a', 'b', 'c', 'a'],
            ),
        ],
    )
    def test_base(self, text, options, expect):
        self.check(text, options, expect)

    @pytest.mark.parametrize(
        ('text', 'options', 'expect'),
        [
            ('a\nb ', Options(strip=True, stripline=False), ['a\n', 'b']),
            ('a\nb ', Options(strip=False, stripline=True), ['a', 'b']),
            ('a\n b ', Options(strip=True, stripline=True), ['a', 'b']),
        ],
    )
    def test_strip(self, text, options, expect):
        self.check(text, options, expect)

    @pytest.mark.parametrize(
        ('text', 'options', 'expect'),
        [
            (
                '\n'.join(['a', 'a', '', 'a', 'b', 'c', 'a']),
                Options(keepends=False, compress=True),
                ['a', '', 'a', 'b', 'c', 'a'],
            ),
            (
                '\n'.join(['a', 'a', '', 'a', 'b', 'c', 'a']),
                Options(keepends=False, unique=True),
                ['a', '', 'b', 'c'],
            ),
            (
                '\n'.join(['a', 'a', '', 'a', 'b', 'c', 'a']),
                Options(keepends=False, compress=False, unique=True),
                ['a', '', 'b', 'c'],
            ),
        ],
    )
    def test_eliminate_keep_empty(self, text, options, expect):
        self.check(text, options, expect)

    @pytest.mark.parametrize(
        ('text', 'options', 'expect'),
        [
            (
                '\n'.join(['a', 'a', '', 'a', 'b', 'c', 'a']),
                Options(keepends=False, empty=False, compress=True),
                ['a', 'b', 'c', 'a'],
            ),
            (
                '\n'.join(['a', 'a', '', 'a', 'b', 'c', 'a']),
                Options(keepends=False, empty=False, unique=True),
                ['a', 'b', 'c'],
            ),
            (
                '\n'.join(['a', 'a', '', 'a', 'b', 'c', 'a']),
                Options(keepends=False, empty=False, compress=False, unique=True),
                ['a', 'b', 'c'],
            ),
        ],
    )
    def test_eliminate(self, text, options, expect):
        self.check(text, options, expect)


def test_line_operators():
    assert Line('a', 1) == 'a'
    assert Line('a', 1) == ('a', 1)
    assert Line('a', 1) == ['a', 1]

    assert Line('a', 2) != 'b'
    assert Line('a', 2) != ('a', 1)
    assert Line('a', 2) != ['a', 1]

    # order
    assert Line('ab', 1) > 'a'
    assert Line('a', 1) < 'ab'
    assert Line('a', 1) <= 'a'
    assert Line('a', 1) >= 'a'

    assert Line('ab', 1) > ('a', 1)
    assert Line('a', 1) < ('ab', 1)
    assert Line('a', 1) <= ('a', 1)
    assert Line('a', 1) >= ('a', 1)


@pytest.mark.parametrize('expect', [('a', 'b', 'c'), ('a', ('b', 2), Line('c', 3))])
def test_block_operators(expect: Sequence[str]) -> None:
    lines = ['a', 'b', 'c']
    assert Block(lines, 1) == expect
    assert Block(lines, 1) == [expect, 1]

    assert Block(lines, 1) != [*expect, 'x']
    assert Block(lines, 1) != [expect, 2]

    assert Block(lines, 1) <= expect
    assert Block(lines, 1) <= [expect, 1]

    assert Block(lines[:2], 1) <= expect
    assert Block(lines[:2], 1) <= [expect, 1]

    assert Block(lines[:2], 1) < expect
    assert Block(lines[:2], 1) < [expect, 1]

    assert Block(lines, 1) >= expect
    assert Block(lines, 1) >= [expect, 1]

    assert Block([*lines, 'd'], 1) > expect
    assert Block([*lines, 'd'], 1) > [expect, 1]

    assert Block(['a', 'b'], 1).context(delta=4, limit=5) == (slice(0, 1), slice(3, 5))
    assert Block(['a', 'b'], 3).context(delta=2, limit=9) == (slice(1, 3), slice(5, 7))


def test_options_class():
    # ensure that the classes are kept synchronized
    missing_keys = Options.__annotations__.keys() - CompleteOptions.__annotations__
    assert not missing_keys, f'missing fields in proxy class: {", ".join(missing_keys)}'

    foreign_keys = CompleteOptions.__annotations__.keys() - Options.__annotations__
    assert not missing_keys, f'foreign fields in proxy class: {", ".join(foreign_keys)}'


@pytest.mark.parametrize('options', [DEFAULT_OPTIONS, LineMatcher('').options])
def test_matcher_default_options(options: Mapping[str, object]) -> None:
    """Check the synchronization of default options and classes in Sphinx."""
    processed = set()

    def check(option: OptionName, default: object) -> None:
        assert option in options
        assert options[option] == default
        processed.add(option)

    check('color', False)
    check('ctrl', True)

    check('strip', True)
    check('stripline', False)

    check('keepends', False)
    check('empty', True)
    check('compress', False)
    check('unique', False)

    check('delete', ())
    check('ignore', None)

    check('flavor', 'exact')

    # check that there are no left over options
    assert sorted(processed) == sorted(Options.__annotations__)


def test_matcher_cache():
    source = [term.blue('hello'), '', 'world']
    # keep colors and empty lines
    matcher = LineMatcher.parse(source, color=True, empty=True)

    stack = matcher._stack

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

    with matcher.override(color=False):
        assert len(stack) == 2
        assert stack[0] is cached
        assert stack[1] is None

        assert matcher.lines() == ('hello', '', 'world')
        assert len(stack) == 2
        assert stack[1] == ('hello', '', 'world')


def test_matcher_find():
    lines = ['hello', 'world', 'yay', '!', '!', '!']
    matcher = LineMatcher.parse(lines, flavor='exact')
    assert matcher.find({'hello', 'yay'}) == [('hello', 0), ('yay', 2)]


def test_matcher_find_blocks():
    lines = ['hello', 'world', 'yay', 'hello', 'world', '!', 'yay']
    matcher = LineMatcher.parse(lines)
    assert matcher.find_blocks(['hello', 'world']) == [
        [('hello', 0), ('world', 1)],
        [('hello', 3), ('world', 4)],
    ]


@pytest.mark.parametrize(
    ('lines', 'flavor', 'pattern', 'expect'),
    [
        (['1', 'b', '3', 'a', '5', '!'], 'exact', ('a', 'b'), [('b', 1), ('a', 3)]),
        (['blbl', 'yay', 'hihi', '^o^'], 'fnmatch', '*[ao]*', [('yay', 1), ('^o^', 3)]),
        (['111', 'hello', 'world', '222'], 're', r'\d+', [('111', 0), ('222', 3)]),
    ],
)
def test_matcher_flavor(
    lines: list[str],
    flavor: Flavor,
    pattern: Sequence[LinePattern],
    expect: Sequence[tuple[str, int]],
) -> None:
    matcher = LineMatcher.parse(lines, flavor=flavor)
    assert matcher.find(pattern) == expect


def test_assert_match():
    matcher = LineMatcher.parse(['a', 'b', 'c', 'd'])
    matcher.assert_match('.+', flavor='re')
    matcher.assert_match('[abcd]', flavor='fnmatch')


def test_assert_match_debug():
    pass


def test_assert_no_match():
    pass


def test_assert_no_match_debug():
    pass


@pytest.mark.parametrize('dedup', range(3))
@pytest.mark.parametrize(('maxsize', 'start', 'count'), [(10, 3, 4)])
def test_assert_lines(maxsize, start, count, dedup):
    # 'maxsize' might be smaller than start + (dedup +  1) * count
    # but it is fine since stop indices are clamped internally
    source = Source(maxsize, start, count, dedup=dedup)
    matcher = LineMatcher(source.text)

    # the main block is matched exactly once
    matcher.assert_lines(source.main, count=1)
    assert source.base * source.ncopy == source.main
    matcher.assert_lines(source.base, count=source.ncopy)

    for subidx in range(1, count + 1):
        # check that the sub-blocks are matched correctly
        subblock = [Source.block_line(start + i) for i in range(subidx)]
        matcher.assert_lines(subblock, count=source.ncopy)


@pytest.mark.parametrize(
    ('pattern', 'count', 'expect'),
    [
        (
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
        (['a', 'b'], 2, None),
        (
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
def test_assert_lines_debug(pattern, count, expect):
    lines = ['a', 'b', 'c', 'a', 'b', 'd']
    matcher = LineMatcher.parse(lines)

    if expect is None:
        matcher.assert_lines(pattern, count=count)
        return

    with pytest.raises(_pytest.outcomes.Failed, match='.*') as exc_info:
        matcher.assert_lines(pattern, count=count)

    actual = exc_info.value.msg
    assert actual is not None
    assert actual.splitlines() == expect


# fmt: off
@pytest.mark.parametrize(('maxsize', 'start', 'count'), [
    # combinations of integers (a, b, c) such that c >= 1 and a >= b + c
    (1, 0, 1),
    (2, 0, 1), (2, 0, 2), (2, 1, 1),
    (3, 0, 1), (3, 0, 2), (3, 0, 3), (3, 1, 1), (3, 1, 2), (3, 2, 1),
])
# fmt: on
@pytest.mark.parametrize('dedup', range(3))
def test_assert_no_lines(maxsize, start, count, dedup):
    # 'maxsize' might be smaller than start + (dedup +  1) * count
    # but it is fine since stop indices are clamped internally
    source = Source(maxsize, start, count, dedup=dedup)
    matcher = LineMatcher(source.text)
    # do not use 'match' with pytest.raises() since the diff
    # output is hard to parse, but use == with lists instead
    with pytest.raises(_pytest.outcomes.Failed, match='.*') as exc_info:
        matcher.assert_no_lines(source.main, context=0)

    actual = exc_info.value.msg
    assert actual is not None

    expect: list[str] = ['block pattern', '']
    expect.extend(util.indent_lines(source.main))
    expect.extend(['', 'found in', ''])
    expect.extend(util.indent_lines(source.main, highlight=True))
    assert actual.splitlines() == expect


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
def test_assert_no_lines_debug(
    maxsize, start, count, dedup, omit_prev, omit_next, context_size
):
    source = Source(maxsize, start, count, dedup=dedup)
    matcher = LineMatcher(source.text)
    # do not use 'match' with pytest.raises() since the diff
    # output is hard to parse, but use == with lists instead
    with pytest.raises(_pytest.outcomes.Failed, match='.*') as exc_info:
        matcher.assert_no_lines(source.main, context=context_size)

    actual = exc_info.value.msg
    assert actual is not None

    expect: list[str] = ['block pattern', '']
    expect.extend(util.indent_lines(source.main))
    expect.extend(['', 'found in', ''])
    expect.extend(make_debug_context(
        source.main,
        source.peek_prev(context_size), omit_prev,
        source.peek_next(context_size), omit_next,
        context_size=context_size, indent=4,
    ))
    assert actual.splitlines() == expect
