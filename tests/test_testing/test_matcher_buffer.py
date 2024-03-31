from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

from sphinx.testing._matcher.buffer import Block, Line

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from sphinx.testing._matcher.buffer import TextView


@pytest.mark.parametrize('cls', [Line, Block])
def test_offset_value(cls: type[TextView[Any]]) -> None:
    with pytest.raises(TypeError, match=re.escape('offset must be an integer, got: None')):
        cls('', None)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match=re.escape('offset must be >= 0, got: -1')):
        cls('', -1)


def test_line_constructor():
    empty = Line()
    assert empty.buffer == ''
    assert empty.offset == 0


    with pytest.raises(TypeError, match=re.escape('expecting a native string, got: 0')):
        Line(0, 1)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match=re.escape('expecting a native string, got: %r' % '')):
        Line(type('', (str,), {})(), 1)


def test_line_arithmetic():
    l1, l2 = Line('a', 1), Line('b', 1)
    assert l1 + l2 == Line('ab', 1)

    match = re.escape('cannot concatenate lines with different offsets')
    with pytest.raises(ValueError, match=match):
        Line('a', 1) + Line('b', 2)

    assert Line('a', 1) * 3 == Line('aaa', 1)
    with pytest.raises(TypeError):
        Line() * object()


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


@pytest.mark.parametrize('bad_line', [1234, type('', (str,), {})()])
def test_block_constructor(bad_line):
    empty = Block()
    assert empty.buffer == ()
    assert empty.offset == 0

    match = re.escape(f'expecting a native string, got: {bad_line!r}')
    with pytest.raises(TypeError, match=match):
        Block([bad_line])


@pytest.mark.parametrize(
    ('lines', 'foreign', 'expect'),
    [
        (['a', 'b', 'c'], 'd', ('a', 'b', 'c')),
        (['a', 'b', 'c'], 'd', ('a', ('b', 2), Line('c', 3))),
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


def test_block_slice_context():
    assert Block(['a', 'b'], 1).context(delta=4, limit=5) == (slice(0, 1), slice(3, 5))
    assert Block(['a', 'b'], 3).context(delta=2, limit=9) == (slice(1, 3), slice(5, 7))
