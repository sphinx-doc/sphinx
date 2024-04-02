from __future__ import annotations

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


@pytest.mark.parametrize('operand', [{1, 2, 3}])
def test_block_unsupported_operators(operand):
    for dispatcher in [operator.__lt__, operator.__le__, operator.__ge__, operator.__gt__]:
        pytest.raises(TypeError, dispatcher, Block(), operand)

    assert Block() != operand


def test_block_slice_context():
    assert Block(['a', 'b'], 1).context(delta=4, limit=5) == (slice(0, 1), slice(3, 5))
    assert Block(['a', 'b'], 3).context(delta=2, limit=9) == (slice(1, 3), slice(5, 7))
