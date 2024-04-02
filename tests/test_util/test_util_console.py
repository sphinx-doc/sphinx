from __future__ import annotations

from typing import TYPE_CHECKING

import sphinx.util.console as term
from sphinx.util.console import strip_colors, strip_escape_sequences

if TYPE_CHECKING:
    from typing import TypeVar

    _T = TypeVar('_T')

ERASE_IN_LINE = '\x1b[2K'


def test_strip_colors():
    s = 'hello world -  '
    assert strip_colors(s) == s, s
    assert strip_colors(term.blue(s)) == s
    assert strip_colors(term.blue(s) + ERASE_IN_LINE) == s + ERASE_IN_LINE

    t = s + term.blue(s)
    assert strip_colors(t + ERASE_IN_LINE) == s * 2 + ERASE_IN_LINE

    # this fails but this shouldn't :(
    # assert strip_colors('a' + term.blue('b') + ERASE_IN_LINE + 'c' + term.blue('d')) == 'abcd'


def test_strip_escape_sequences():
    s = 'hello world -  '
    assert strip_escape_sequences(s) == s, s
    assert strip_escape_sequences(term.blue(s)) == s
    assert strip_escape_sequences(term.blue(s) + ERASE_IN_LINE) == s

    t = s + term.blue(s)
    assert strip_escape_sequences(t + ERASE_IN_LINE) == s * 2
    assert strip_escape_sequences(t + ERASE_IN_LINE + t + ERASE_IN_LINE) == s * 4
