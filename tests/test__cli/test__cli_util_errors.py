from __future__ import annotations

import itertools
import operator
from typing import TYPE_CHECKING

from sphinx._cli.util.colour import blue, reset
from sphinx._cli.util.errors import strip_escape_sequences

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final

CURSOR_UP: Final[str] = '\x1b[2A'  # ignored ANSI code
ERASE_LINE: Final[str] = '\x1b[2K'  # supported ANSI code
TEXT: Final[str] = '\x07 ß Hello world!'


def test_strip_escape_sequences() -> None:
    # double ERASE_LINE so that the tested strings may have 2 of them
    ansi_base_blocks = [
        TEXT,
        blue(TEXT),
        reset(TEXT),
        ERASE_LINE,
        ERASE_LINE,
        CURSOR_UP,
    ]
    # :func:`strip_escape_sequences` strips ANSI codes known by Sphinx
    text_base_blocks = [
        TEXT,
        TEXT,
        TEXT,
        '',
        '',
        CURSOR_UP,
    ]

    assert len(text_base_blocks) == len(ansi_base_blocks)
    N = len(ansi_base_blocks)

    def next_ansi_blocks(choices: Sequence[str], n: int) -> Sequence[str]:
        # Get a list of *n* words from a cyclic sequence of *choices*.
        #
        # For instance ``next_ansi_blocks(['a', 'b'], 3) == ['a', 'b', 'a']``.
        stream = itertools.cycle(choices)
        return list(map(operator.itemgetter(0), zip(stream, range(n), strict=False)))

    # generate all permutations of length N
    for sigma in itertools.permutations(range(N), N):
        # apply the permutation on the blocks with ANSI codes
        ansi_blocks = list(map(ansi_base_blocks.__getitem__, sigma))
        # apply the permutation on the blocks with stripped codes
        text_blocks = list(map(text_base_blocks.__getitem__, sigma))

        for glue, n in itertools.product(['.', '\n', '\r\n'], range(4 * N)):
            ansi_strings = next_ansi_blocks(ansi_blocks, n)
            text_strings = next_ansi_blocks(text_blocks, n)
            assert len(ansi_strings) == len(text_strings) == n

            ansi_string = glue.join(ansi_strings)
            text_string = glue.join(text_strings)
            assert strip_escape_sequences(ansi_string) == text_string


def test_strip_ansi_short_forms() -> None:
    # In Sphinx, we always "normalize" the color codes so that they
    # match "\x1b\[(\d\d;){0,2}(\d\d)m" but it might happen that
    # some messages use '\x1b[0m' instead of ``reset(s)``, so we
    # test whether this alternative form is supported or not.

    for strip_function in strip_escape_sequences, strip_escape_sequences:
        # \x1b[m and \x1b[0m are equivalent to \x1b[00m
        assert strip_function('\x1b[m') == ''
        assert strip_function('\x1b[0m') == ''

        # \x1b[1m is equivalent to \x1b[01m
        assert strip_function('\x1b[1mbold\x1b[0m') == 'bold'

    # \x1b[K is equivalent to \x1b[0K
    assert strip_escape_sequences('\x1b[K') == ''
