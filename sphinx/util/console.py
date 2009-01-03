# -*- coding: utf-8 -*-
"""
    sphinx.util.console
    ~~~~~~~~~~~~~~~~~~~

    Format colored console output.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

codes = {}

def get_terminal_width():
    """Borrowed from the py lib."""
    try:
        import os, termios, fcntl, struct
        call = fcntl.ioctl(0, termios.TIOCGWINSZ, "\000"*8)
        height, width = struct.unpack("hhhh", call)[:2]
        terminal_width = width
    except (SystemExit, KeyboardInterrupt):
        raise
    except:
        # FALLBACK
        terminal_width = int(os.environ.get('COLUMNS', 80))-1
    return terminal_width

_tw = get_terminal_width()

def print_and_backspace(text, func):
    if not codes:
        # if no coloring, don't output fancy backspaces
        func(text)
    else:
        func(text.ljust(_tw) + _tw * "\b")

def color_terminal():
    if 'COLORTERM' in os.environ:
        return True
    term = os.environ.get('TERM', 'dumb').lower()
    if 'xterm' in term or 'color' in term:
        return True
    return False


def nocolor():
    codes.clear()

def coloron():
    codes.update(_orig_codes)

def colorize(name, text):
    return codes.get(name, '') + text + codes.get('reset', '')

def create_color_func(name):
    def inner(text):
        return colorize(name, text)
    globals()[name] = inner

_attrs = {
    'reset':     '39;49;00m',
    'bold':      '01m',
    'faint':     '02m',
    'standout':  '03m',
    'underline': '04m',
    'blink':     '05m',
}

for _name, _value in _attrs.items():
    codes[_name] = '\x1b[' + _value

_colors = [
    ('black',     'darkgray'),
    ('darkred',   'red'),
    ('darkgreen', 'green'),
    ('brown',     'yellow'),
    ('darkblue',  'blue'),
    ('purple',    'fuchsia'),
    ('turquoise', 'teal'),
    ('lightgray', 'white'),
]

for i, (dark, light) in enumerate(_colors):
    codes[dark] = '\x1b[%im' % (i+30)
    codes[light] = '\x1b[%i;01m' % (i+30)

_orig_codes = codes.copy()

for _name in codes:
    create_color_func(_name)
