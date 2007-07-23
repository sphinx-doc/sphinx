# -*- coding: utf-8 -*-
"""
    Console utils
    ~~~~~~~~~~~~~

    Format colored console output.

    :copyright: 1998-2004 by the Gentoo Foundation.
    :copyright: 2006-2007 by Georg Brandl.
    :license: GNU GPL.
"""

esc_seq = "\x1b["

codes = {}
codes["reset"]     = esc_seq + "39;49;00m"

codes["bold"]      = esc_seq + "01m"
codes["faint"]     = esc_seq + "02m"
codes["standout"]  = esc_seq + "03m"
codes["underline"] = esc_seq + "04m"
codes["blink"]     = esc_seq + "05m"
codes["overline"]  = esc_seq + "06m"  # Who made this up? Seriously.

ansi_color_codes = []
for x in xrange(30, 38):
    ansi_color_codes.append("%im" % x)
    ansi_color_codes.append("%i;01m" % x)

rgb_ansi_colors = [
    '0x000000', '0x555555', '0xAA0000', '0xFF5555',
    '0x00AA00', '0x55FF55', '0xAA5500', '0xFFFF55',
    '0x0000AA', '0x5555FF', '0xAA00AA', '0xFF55FF',
    '0x00AAAA', '0x55FFFF', '0xAAAAAA', '0xFFFFFF'
]

for x in xrange(len(rgb_ansi_colors)):
    codes[rgb_ansi_colors[x]] = esc_seq + ansi_color_codes[x]

del x

codes["black"]     = codes["0x000000"]
codes["darkgray"]  = codes["0x555555"]

codes["red"]       = codes["0xFF5555"]
codes["darkred"]   = codes["0xAA0000"]

codes["green"]     = codes["0x55FF55"]
codes["darkgreen"] = codes["0x00AA00"]

codes["yellow"]    = codes["0xFFFF55"]
codes["brown"]     = codes["0xAA5500"]

codes["blue"]      = codes["0x5555FF"]
codes["darkblue"]  = codes["0x0000AA"]

codes["fuchsia"]   = codes["0xFF55FF"]
codes["purple"]    = codes["0xAA00AA"]

codes["teal"]      = codes["0x00AAAA"]
codes["turquoise"] = codes["0x55FFFF"]

codes["white"]     = codes["0xFFFFFF"]
codes["lightgray"] = codes["0xAAAAAA"]

codes["darkteal"]   = codes["turquoise"]
codes["darkyellow"] = codes["brown"]
codes["fuscia"]     = codes["fuchsia"]
codes["white"]      = codes["bold"]

def nocolor():
    "turn off colorization"
    for code in codes:
        codes[code] = ""

def reset_color():
    return codes["reset"]

def colorize(color_key, text):
    return codes[color_key] + text + codes["reset"]

functions_colors = [
    "bold", "white", "teal", "turquoise", "darkteal",
    "fuscia", "fuchsia", "purple", "blue", "darkblue",
    "green", "darkgreen", "yellow", "brown",
    "darkyellow", "red", "darkred"
]

def create_color_func(color_key):
    """
    Return a function that formats its argument in the given color.
    """
    def derived_func(text):
        return colorize(color_key, text)
    return derived_func

ns = locals()
for c in functions_colors:
    ns[c] = create_color_func(c)

del c, ns
