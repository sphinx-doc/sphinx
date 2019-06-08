"""
    sphinx.util.texescape
    ~~~~~~~~~~~~~~~~~~~~~

    TeX escaping helper.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
from typing import Dict

tex_replacements = [
    # map TeX special chars
    ('$', r'\$'),
    ('%', r'\%'),
    ('&', r'\&'),
    ('#', r'\#'),
    ('_', r'\_'),
    ('{', r'\{'),
    ('}', r'\}'),
    ('[', r'{[}'),
    (']', r'{]}'),
    ('`', r'{}`'),
    ('\\', r'\textbackslash{}'),
    ('~', r'\textasciitilde{}'),
    ('<', r'\textless{}'),
    ('>', r'\textgreater{}'),
    ('^', r'\textasciicircum{}'),
    # map special Unicode characters to TeX commands
    ('¶', r'\P{}'),
    ('§', r'\S{}'),
    ('€', r'\texteuro{}'),
    ('∞', r'\(\infty\)'),
    ('±', r'\(\pm\)'),
    ('→', r'\(\rightarrow\)'),
    ('‣', r'\(\rightarrow\)'),
    ('✓', r'\(\checkmark\)'),
    ('✔', r'\(\pmb{\checkmark}\)'),
    # used to separate -- in options
    ('﻿', r'{}'),
    # map some special Unicode characters to similar ASCII ones
    ('⎽', r'\_'),
    ('–', r'\textendash{}'),
    ('|', r'\textbar{}'),
    ('ℯ', r'e'),
    ('ⅈ', r'i'),
    ('⁰', r'\(\sp{\text{0}}\)'),
    ('¹', r'\(\sp{\text{1}}\)'),
    ('²', r'\(\sp{\text{2}}\)'),
    ('³', r'\(\sp{\text{3}}\)'),
    ('⁴', r'\(\sp{\text{4}}\)'),
    ('⁵', r'\(\sp{\text{5}}\)'),
    ('⁶', r'\(\sp{\text{6}}\)'),
    ('⁷', r'\(\sp{\text{7}}\)'),
    ('⁸', r'\(\sp{\text{8}}\)'),
    ('⁹', r'\(\sp{\text{9}}\)'),
    ('₀', r'\(\sb{\text{0}}\)'),
    ('₁', r'\(\sb{\text{1}}\)'),
    ('₂', r'\(\sb{\text{2}}\)'),
    ('₃', r'\(\sb{\text{3}}\)'),
    ('₄', r'\(\sb{\text{4}}\)'),
    ('₅', r'\(\sb{\text{5}}\)'),
    ('₆', r'\(\sb{\text{6}}\)'),
    ('₇', r'\(\sb{\text{7}}\)'),
    ('₈', r'\(\sb{\text{8}}\)'),
    ('₉', r'\(\sb{\text{9}}\)'),
    # Greek alphabet not escaped: pdflatex handles it via textalpha and inputenc
    # OHM SIGN U+2126 is handled by LaTeX textcomp package
]

tex_escape_map = {}  # type: Dict[int, str]
tex_replace_map = {}
tex_hl_escape_map_new = {}


def escape(s: str) -> str:
    """Escape text for LaTeX output."""
    return s.translate(tex_escape_map)


def escape_abbr(text: str) -> str:
    """Adjust spacing after abbreviations. Works with @ letter or other."""
    return re.sub(r'\.(?=\s|$)', r'.\@{}', text)


def init() -> None:
    for a, b in tex_replacements:
        tex_escape_map[ord(a)] = b
        tex_replace_map[ord(a)] = '_'

    for a, b in tex_replacements:
        if a in '[]{}\\':
            continue
        tex_hl_escape_map_new[ord(a)] = b
