from __future__ import annotations

import contextlib
import itertools
import operator
import re
from typing import TYPE_CHECKING

import pytest

from sphinx.testing._matcher.buffer import Block, Line

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from sphinx.testing._matcher.buffer import SourceView


@pytest.mark.parametrize('cls', [Line, Block])
def test_offset_value(cls: type[SourceView[Any]]) -> None:
    with pytest.raises(TypeError, match=re.escape('offset must be an integer, got: None')):
        cls('', None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=re.escape('offset must be >= 0, got: -1')):
        cls('', -1)


def test_line_comparison_operators():
    assert Line('a', 1) == 'a'
    assert Line('a', 1) == ('a', 1)
    assert Line('a', 1) == ['a', 1]
    assert Line('a', 1) == Line('a', 1)

    assert Line('a', 2) != 'b'
    assert Line('a', 2) != ('a', 1)
    assert Line('a', 2) != ('b', 2)
    assert Line('a', 2) != ['a', 1]
    assert Line('a', 2) != ['b', 2]
    assert Line('a', 2) != Line('a', 1)
    assert Line('a', 2) != Line('b', 2)

    # order
    assert Line('ab', 1) > 'a'
    assert Line('ab', 1) > ('a', 1)
    assert Line('ab', 1) > ['a', 1]
    assert Line('ab', 1) > Line('a', 1)

    assert Line('a', 1) < 'ab'
    assert Line('a', 1) < ('ab', 1)
    assert Line('a', 1) < ['ab', 1]
    assert Line('a', 1) < Line('ab', 1)

    assert Line('ab', 1) >= 'ab'
    assert Line('ab', 1) >= ('ab', 1)
    assert Line('ab', 1) >= ['ab', 1]
    assert Line('ab', 1) >= Line('ab', 1)

    assert Line('ab', 1) <= 'ab'
    assert Line('ab', 1) <= ('ab', 1)
    assert Line('ab', 1) <= ['ab', 1]
    assert Line('ab', 1) <= Line('ab', 1)


def test_empty_line():
    assert Line() == ''
    assert Line() == ['', 0]

    assert Line() != ['', 1]
    assert Line() != ['a']
    assert Line() != ['a', 0]
    assert Line() != object()

    assert Line() <= ''
    assert Line() <= 'a'
    assert Line() <= ['a', 0]
    assert Line() <= Line('a', 0)

    assert Line() < 'a'
    assert Line() < ['a', 0]
    assert Line() < Line('a', 0)

    # do not simplify these expressions
    assert not operator.__lt__(Line(), '')
    assert not operator.__lt__(Line(), ['', 0])
    assert not operator.__lt__(Line(), Line())

    assert not operator.__gt__(Line(), '')
    assert not operator.__gt__(Line(), ['', 0])
    assert not operator.__gt__(Line(), Line())


@pytest.mark.parametrize('operand', [[], [Line()], [Line(), 0], [[chr(1), chr(2)], 0]])
def test_line_unsupported_operators(operand):
    for dispatcher in [operator.__lt__, operator.__le__, operator.__ge__, operator.__gt__]:
        pytest.raises(TypeError, dispatcher, Line(), operand)

    assert Line() != operand


def test_line_startswith():
    line = Line('abac')
    assert line.startswith('a')
    assert line.startswith('ab')
    assert not line.startswith('no')

    line = Line('ab bb c')
    assert line.startswith(' ', 2)
    assert line.startswith(' bb', 2)
    assert not line.startswith('a', 2)


def test_line_endswith():
    line = Line('ab1ac')
    assert line.endswith('c')
    assert line.endswith('ac')
    assert not line.endswith('no')

    line = Line('ab 4b 3c ')
    assert line.endswith(' ', 2)
    assert line.endswith('3c ', 2)
    assert not line.endswith('b 3c ', 0, 4)


def test_line_type_errors():
    line = Line()
    pytest.raises(TypeError, line.count, 2)
    pytest.raises(TypeError, line.index, 2)
    pytest.raises(TypeError, line.find, 2)


def test_line_count_substrings():
    line = Line('abac')
    assert line.count('no') == 0
    assert line.count('a') == 2

    line = Line(''.join(('a', 'b', ' ', 'b', 'b', ' ', 'a', 'c', ' ', 'c', 'c')))
    assert line.count(re.compile(r'^\Z')) == 0
    assert line.count(re.compile(r'a[bc]')) == 2


@pytest.mark.parametrize(
    ('line', 'data'),
    [
        (
            Line('abaz'),
            [
                ('a', (), 0),
                ('a', (1,), 2),
                ('not_found', (), -1),
                ('z', (0, 2), -1),  # do not include last character
            ],
        ),
        (
            #            -11  -10   -9   -8   -7   -6   -5   -4   -3   -2   -1
            #              0    1    2    3    4    5    6    7    8    9   10
            Line(''.join(('a', 'b', ' ', 'b', 'b', ' ', 'x', 'c', ' ', 'c', 'c'))),
            [
                (re.compile(r'a\w'), (), 0),
                (re.compile(r'\bx'), (2,), 6),
                *itertools.product(
                    [re.compile(r'\s+')],
                    [(3,), (-8,)],
                    [5],
                ),
                *itertools.product(
                    [re.compile(r'c ')],
                    [(6, 9), (6, -2), (-5, -2), (-5, 9)],  # all equivalent to (6, 9)
                    [7],
                ),
                *itertools.product(
                    [re.compile(r'^bb')],
                    [(3, 8), (3, -3), (-8, -3), (-8, -3)],  # all equivalent to (3, 8)
                    [3],
                ),
                (re.compile(r'^\Z'), (), -1),
                *itertools.product(
                    [re.compile(r'c[cd]')],
                    [(0, 5), (-6, 5)],
                    [-1],
                ),
            ],
        ),
    ],
)
def test_line_find(line: Line, data: list[tuple[str, tuple[int, ...], int]]) -> None:
    for target, args, expect in data:
        actual = line.find(target, *args)

        if expect == -1:
            assert actual == expect, (line.buffer, target, args)
            with pytest.raises(ValueError, match=re.escape(str(target))):
                line.index(target, *args)
        else:
            assert actual == expect, (line.buffer, target, args)
            assert line.index(target, *args) == expect


def test_block_constructor():
    empty = Block()
    assert empty.buffer == ()
    assert empty.offset == 0

    match = re.escape('expecting a native string, got: 1234')
    with pytest.raises(TypeError, match=match):
        Block([1234])  # type: ignore[list-item]


def test_empty_block():
    assert Block() == []
    assert Block() == [[], 0]

    assert Block() != [[], 1]
    assert Block() != ['a']
    assert Block() != [['a'], 0]
    assert Block() != object()

    assert Block() <= []
    assert Block() <= ['a']
    assert Block() <= [['a'], 0]
    assert Block() <= [[Line('a', 0)], 0]

    assert Block() < ['a']
    assert Block() < [['a'], 0]
    assert Block() < [[Line('a', 0)], 0]

    # do not simplify these expressions
    assert not operator.__lt__(Block(), [])
    assert not operator.__lt__(Block(), [[], 0])

    assert not operator.__gt__(Block(), [])
    assert not operator.__gt__(Block(), ['a'])
    assert not operator.__gt__(Block(), [['a'], 0])
    assert not operator.__gt__(Block(), [[('a', 0)], 0])
    assert not operator.__gt__(Block(), [[Line('a', 0)], 0])


@pytest.mark.parametrize(
    ('lines', 'foreign', 'expect'),
    [
        (['a', 'b', 'c'], 'd', ('a', 'b', 'c')),
        (['a', 'b', 'c'], 'd', ('a', ('b', 2), Line('c', 3))),
        (['a', 'b', 'c'], 'd', ('a', ['b', 2], Line('c', 3))),
    ],
)
def test_block_comparison_operators(
    lines: list[str], foreign: str, expect: Sequence[str | tuple[str, int] | Line]
) -> None:
    assert Block(lines, 1) == expect
    assert Block(lines, 1) == [expect, 1]

    assert Block(lines, 1) != [*expect, foreign]
    assert Block(lines, 1) != [expect, 2]

    assert Block(lines, 1) <= expect
    assert Block(lines, 1) <= [expect, 1]

    assert Block(lines[:2], 1) <= expect
    assert Block(lines[:2], 1) <= [expect, 1]

    assert Block(lines[:2], 1) < expect
    assert Block(lines[:2], 1) < [expect, 1]

    assert Block(lines, 1) >= expect
    assert Block(lines, 1) >= [expect, 1]

    assert Block([*lines, foreign], 1) > expect
    assert Block([*lines, foreign], 1) > [expect, 1]

    assert Block([foreign, *lines, foreign], 1) > expect
    assert Block([foreign, *lines, foreign], 1) > [expect, 1]


@pytest.mark.parametrize(
    'operand',
    [
        [],
        [[], 0],
        ['L1'],
        [Line()],
        ['L1', 'L2'],
        ['L1', Line()],
        ['L1', 'L2', 'L3'],
        ['L1', 'L2', Line()],
        [['L1'], 0],
        [[Line()], 0],
        [['L1', 'L2'], 0],
        [['L1', Line()], 0],
    ],
)
def test_block_supported_operators(operand):
    with contextlib.nullcontext():
        for dispatcher in [operator.__lt__, operator.__le__, operator.__ge__, operator.__gt__]:
            dispatcher(Block(), operand)


@pytest.mark.parametrize(
    'operand',
    [
        object(),  # bad lines
        ['L1', object(), 'L3'],  # bad lines (no offset)
        [['a', object()], 1],  # bad lines (with offset)
        ['L1', 1],  # single line + offset not allowed
        [[], object()],  # no lines + bad offset
        [['L1', 'L2'], object()],  # ok lines + bad offset
        [[object(), object()], object()],  # bad lines + bad offset
    ],
)
def test_block_unsupported_operators(operand):
    for dispatcher in [operator.__lt__, operator.__le__, operator.__ge__, operator.__gt__]:
        pytest.raises(TypeError, dispatcher, Block(), operand)

    assert Block() != operand


def test_block_slice_context():
    assert Block(['a', 'b'], 1).context(delta=4, limit=5) == (slice(0, 1), slice(3, 5))
    assert Block(['a', 'b'], 3).context(delta=2, limit=9) == (slice(1, 3), slice(5, 7))


def test_block_count_lines():
    block = Block(['a', 'b', 'a', 'c'])
    assert block.count('no') == 0
    assert block.count('a') == 2

    block = Block(['ab', 'bb', 'ac'])
    # this also tests the predicate-based implementation
    assert block.count(re.compile(r'^\Z')) == 0
    assert block.count(re.compile(r'a\w')) == 2


@pytest.mark.parametrize(
    ('block', 'data'),
    [
        (
            Block(['a', 'b', 'a', 'end']),
            [
                ('a', (), 0),
                ('a', (1,), 2),
                ('not_found', (), -1),
                ('end', (0, 2), -1),  # do not include last line
            ],
        ),
        (
            #      -11   -10   -9    -8    -7   -6    -5    -4   -3    -2    -1
            #        0     1    2     3     4    5     6     7    8     9    10
            Block(('a0', 'b1', ' ', 'b3', 'b4', ' ', '6a', 'a7', ' ', 'cc', 'c?')),
            [
                (re.compile(r'a\d'), (), 0),
                (re.compile(r'a\d'), (1,), 7),
                *itertools.product(
                    [re.compile(r'\d\w')],  # '6a'
                    [(3, 9), (3, -2), (-8, 9), (-8, -2)],  # all equivalent to (3, 9)
                    [6],
                ),
                *itertools.product(
                    [re.compile(r'^\s+')],
                    [(5, 8), (5, -3), (-6, 8), (-6, -3)],  # all equivalent to (5, 8)
                    [5],
                ),
                (re.compile(r'^\Z'), (), -1),
                *itertools.product(
                    [re.compile(r'c\?')],
                    [(0, 4), (-7, 9)],
                    [-1],
                ),
            ],
        ),
    ],
)
def test_block_find(block: Block, data: list[tuple[str, tuple[int, ...], int]]) -> None:
    for target, args, expect in data:
        actual = block.find(target, *args)

        if expect == -1:
            assert actual == expect, (block.buffer, target, args)
            with pytest.raises(ValueError, match=re.escape(str(target))):
                block.index(target, *args)
        else:
            assert actual == expect, (block.buffer, target, args)
            assert block.index(target, *args) == expect
