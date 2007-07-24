# -*- coding: utf-8 -*-
"""
    sphinx.util.console
    ~~~~~~~~~~~~~~~~~~~

    Format colored console output.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""

codes = {}

def nocolor():
    codes.clear()

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

for name, value in _attrs.items():
    codes[name] = '\x1b[' + value

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

for name in codes:
    create_color_func(name)
