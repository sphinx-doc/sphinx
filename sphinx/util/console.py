"""Format colored console output."""

from __future__ import annotations

import os
import re
import shutil
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final

    # fmt: off
    def reset(text: str) -> str: ...  # NoQA: E704
    def bold(text: str) -> str: ...  # NoQA: E704
    def faint(text: str) -> str: ...  # NoQA: E704
    def standout(text: str) -> str: ...  # NoQA: E704
    def underline(text: str) -> str: ...  # NoQA: E704
    def blink(text: str) -> str: ...  # NoQA: E704

    def black(text: str) -> str: ...  # NoQA: E704
    def white(text: str) -> str: ...  # NoQA: E704
    def red(text: str) -> str: ...  # NoQA: E704
    def yellow(text: str) -> str: ...  # NoQA: E704
    def blue(text: str) -> str: ...  # NoQA: E704
    def purple(text: str) -> str: ...  # NoQA: E704
    def turquoise(text: str) -> str: ...  # NoQA: E704

    def darkgray(text: str) -> str: ...  # NoQA: E704
    def lightgray(text: str) -> str: ...  # NoQA: E704
    def darkred(text: str) -> str: ...  # NoQA: E704
    def brown(text: str) -> str: ...  # NoQA: E704
    def darkblue(text: str) -> str: ...  # NoQA: E704
    def fuchsia(text: str) -> str: ...  # NoQA: E704
    def teal(text: str) -> str: ...  # NoQA: E704
    # fmt: on

try:
    # check if colorama is installed to support color on Windows
    import colorama
except ImportError:
    colorama = None

_CSI: Final[str] = re.escape('\x1b[')  # 'ESC [': Control Sequence Introducer
_OSC: Final[str] = re.escape('\x1b]')  # 'ESC ]': Operating System Command
_BELL: Final[str] = re.escape('\x07')  # bell command

# ANSI escape sequences for colors
_ansi_color_re: Final[re.Pattern[str]] = re.compile('\x1b.*?m')

# ANSI escape sequences supported by vt100 terminal (non-colors)
_ansi_other_re: Final[re.Pattern[str]] = re.compile(
    _CSI
    + r"""(?:
        H                   # HOME
        |\?\d+[hl]          # enable/disable features (e.g., cursor, mouse, etc)
        |[1-6] q            # cursor shape (e.g., blink) (note the space before 'q')
        |2?J                # erase down (J) or clear screen (2J)
        |\d*[ABCD]          # cursor up/down/forward/backward
        |\d+G               # move to column
        |(?:\d;)?\d+;\d+H   # move to (x, y)
        |\dK                # erase in line
    ) | """
    + _OSC
    + r"""(?:
        \d;.*?\x07          # set window title
    ) | """
    + _BELL,
    re.VERBOSE | re.ASCII,
)

# ANSI escape sequences
_ansi_re: Final[re.Pattern[str]] = re.compile(
    ' | '.join((_ansi_color_re.pattern, _ansi_other_re.pattern)),
    re.VERBOSE | re.ASCII,
)

codes: dict[str, str] = {}


def terminal_safe(s: str) -> str:
    """Safely encode a string for printing to the terminal."""
    return s.encode('ascii', 'backslashreplace').decode('ascii')


def get_terminal_width() -> int:
    """Return the width of the terminal in columns."""
    return shutil.get_terminal_size().columns - 1


_tw: int = get_terminal_width()


def term_width_line(text: str) -> str:
    if not codes:
        # if no coloring, don't output fancy backspaces
        return text + '\n'
    else:
        # codes are not displayed, this must be taken into account
        return text.ljust(_tw + len(text) - len(_ansi_re.sub('', text))) + '\r'


def color_terminal() -> bool:
    if 'NO_COLOR' in os.environ:
        return False
    if sys.platform == 'win32' and colorama is not None:
        colorama.init()
        return True
    if 'FORCE_COLOR' in os.environ:
        return True
    if not hasattr(sys.stdout, 'isatty'):
        return False
    if not sys.stdout.isatty():
        return False
    if 'COLORTERM' in os.environ:
        return True
    term = os.environ.get('TERM', 'dumb').lower()
    return term in ('xterm', 'linux') or 'color' in term


def nocolor() -> None:
    if sys.platform == 'win32' and colorama is not None:
        colorama.deinit()
    codes.clear()


def coloron() -> None:
    codes.update(_orig_codes)


def colorize(name: str, text: str, input_mode: bool = False) -> str:
    def escseq(name: str) -> str:
        # Wrap escape sequence with ``\1`` and ``\2`` to let readline know
        # it is non-printable characters
        # ref: https://tiswww.case.edu/php/chet/readline/readline.html
        #
        # Note: This hack does not work well in Windows (see #5059)
        escape = codes.get(name, '')
        if input_mode and escape and sys.platform != 'win32':
            return '\1' + escape + '\2'
        else:
            return escape

    return escseq(name) + text + escseq('reset')


def strip_colors(s: str) -> str:
    """Strip all color escape sequences from *s*."""
    # TODO: deprecate parameter *s* in favor of a positional-only parameter *text*
    return _ansi_color_re.sub('', s)


def strip_control_sequences(text: str, /) -> str:
    """Strip non-color escape sequences from *text*."""
    return _ansi_other_re.sub('', text)


def strip_escape_sequences(text: str, /) -> str:
    """Strip all control sequences from *text*."""
    # Remove control sequences first so that text of the form
    #
    #   '\x1b[94m' + '\x1bA' + TEXT + '\x1b[0m'
    #
    # is cleaned to TEXT and not '' (otherwise '[94m\x1bAabc\x1b[0'
    # is considered by :data:`_ansi_color_re` and removed altogther).
    return strip_colors(strip_control_sequences(text))


def create_color_func(name: str) -> None:
    def inner(text: str) -> str:
        return colorize(name, text)

    globals()[name] = inner


_attrs = {
    'reset': '39;49;00m',
    'bold': '01m',
    'faint': '02m',
    'standout': '03m',
    'underline': '04m',
    'blink': '05m',
}

for _name, _value in _attrs.items():
    codes[_name] = '\x1b[' + _value

_colors = [
    ('black', 'darkgray'),
    ('darkred', 'red'),
    ('darkgreen', 'green'),
    ('brown', 'yellow'),
    ('darkblue', 'blue'),
    ('purple', 'fuchsia'),
    ('turquoise', 'teal'),
    ('lightgray', 'white'),
]

for i, (dark, light) in enumerate(_colors, 30):
    codes[dark] = '\x1b[%im' % i
    codes[light] = '\x1b[%im' % (i + 60)

_orig_codes = codes.copy()

for _name in codes:
    create_color_func(_name)
