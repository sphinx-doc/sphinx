from __future__ import annotations

import itertools
import operator
from typing import TYPE_CHECKING

import pytest

from sphinx.util.console import blue, reset, strip_colors, strip_escape_sequences

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Final, TypeVar

    _T = TypeVar('_T')

ERASE_IN_LINE: Final[str] = '\x1b[2K'
BELL_TEXT: Final[str] = '\x07 Hello world!'


@pytest.mark.parametrize(
    ('strip_function', 'ansi_base_blocks', 'text_base_blocks'),
    [
        (
            strip_colors,
            # double ERASE_IN_LINE so that the tested strings may have 2 of them
            [BELL_TEXT, blue(BELL_TEXT), reset(BELL_TEXT), ERASE_IN_LINE, ERASE_IN_LINE],
            # :func:`strip_colors` removes color codes but keep ERASE_IN_LINE
            [BELL_TEXT, BELL_TEXT, BELL_TEXT, ERASE_IN_LINE, ERASE_IN_LINE],
        ),
        (
            strip_escape_sequences,
            # double ERASE_IN_LINE so that the tested strings may have 2 of them
            [BELL_TEXT, blue(BELL_TEXT), reset(BELL_TEXT), ERASE_IN_LINE, ERASE_IN_LINE],
            # :func:`strip_escape_sequences` strips ANSI codes known by Sphinx
            [BELL_TEXT, BELL_TEXT, BELL_TEXT, '', ''],
        ),
    ],
    ids=[strip_colors.__name__, strip_escape_sequences.__name__],
)
def test_strip_ansi(
    strip_function: Callable[[str], str],
    ansi_base_blocks: Sequence[str],
    text_base_blocks: Sequence[str],
) -> None:
    assert callable(strip_function)
    assert len(text_base_blocks) == len(ansi_base_blocks)
    N = len(ansi_base_blocks)

    def next_ansi_blocks(choices: Sequence[str], n: int) -> Sequence[str]:
        stream = itertools.cycle(choices)
        return list(map(operator.itemgetter(0), zip(stream, range(n))))

    for sigma in itertools.permutations(range(N), N):
        ansi_blocks = list(map(ansi_base_blocks.__getitem__, sigma))
        text_blocks = list(map(text_base_blocks.__getitem__, sigma))

        for glue, n in itertools.product(['.', '\n', '\r\n'], range(4 * N)):
            ansi_strings = next_ansi_blocks(ansi_blocks, n)
            text_strings = next_ansi_blocks(text_blocks, n)
            assert len(ansi_strings) == len(text_strings) == n

            ansi_string = glue.join(ansi_strings)
            text_string = glue.join(text_strings)
            assert strip_function(ansi_string) == text_string


def test_strip_ansi_short_forms():
    # In Sphinx, we always "normalize" the color codes so that they
    # match "\x1b\[(\d\d;){0,2}(\d\d)m" but it might happen that
    # some messages use '\x1b[0m' instead of ``reset(s)``, so we
    # test whether this alternative form is supported or not.

    for strip_function in [strip_colors, strip_escape_sequences]:
        # \x1b[m and \x1b[0m are equivalent to \x1b[00m
        assert strip_function('\x1b[m') == ''
        assert strip_function('\x1b[0m') == ''

        # \x1b[1m is equivalent to \x1b[01m
        assert strip_function('\x1b[1mbold\x1b[0m') == 'bold'

    # \x1b[K is equivalent to \x1b[0K
    assert strip_escape_sequences('\x1b[K') == ''
