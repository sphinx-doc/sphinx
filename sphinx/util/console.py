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
    def green(text: str) -> str: ...  # NoQA: E704
    def yellow(text: str) -> str: ...  # NoQA: E704
    def blue(text: str) -> str: ...  # NoQA: E704
    def fuchsia(text: str) -> str: ...  # NoQA: E704
    def teal(text: str) -> str: ...  # NoQA: E704

    def darkgray(text: str) -> str: ...  # NoQA: E704
    def lightgray(text: str) -> str: ...  # NoQA: E704
    def darkred(text: str) -> str: ...  # NoQA: E704
    def darkgreen(text: str) -> str: ...  # NoQA: E704
    def brown(text: str) -> str: ...  # NoQA: E704
    def darkblue(text: str) -> str: ...  # NoQA: E704
    def purple(text: str) -> str: ...  # NoQA: E704
    def turquoise(text: str) -> str: ...  # NoQA: E704
    # fmt: on

try:
    # check if colorama is installed to support color on Windows
    import colorama
except ImportError:
    colorama = None


_CSI = re.escape('\x1b[')  # 'ESC [': Control Sequence Introducer
_ansi_re: re.Pattern[str] = re.compile(
    _CSI
    + r"""
    (
      (\d\d;){0,2}\d\dm  # ANSI colour code
    |
      \dK                # ANSI Erase in Line
    )""",
    re.VERBOSE | re.ASCII,
)
_ansi_color_re: Final[re.Pattern[str]] = re.compile('\x1b.*?m')

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
    return _ansi_color_re.sub('', s)


def _strip_escape_sequences(s: str) -> str:
    return _ansi_re.sub('', s)


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
