# -*- coding: utf-8 -*-
"""
    sphinx.util.texescape
    ~~~~~~~~~~~~~~~~~~~~~

    TeX escaping helper.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

tex_replacements = [
    # map TeX special chars
    (u'$', ur'\$'),
    (u'%', ur'\%'),
    (u'&', ur'\&'),
    (u'#', ur'\#'),
    (u'_', ur'\_'),
    (u'{', ur'\{'),
    (u'}', ur'\}'),
    (u'[', ur'{[}'),
    (u']', ur'{]}'),
    (u'`', ur'{}`'),
    (u'\\',ur'\textbackslash{}'),
    (u'~', ur'\textasciitilde{}'),
    (u'<', ur'\textless{}'),
    (u'>', ur'\textgreater{}'),
    (u'^', ur'\textasciicircum{}'),
    # map special Unicode characters to TeX commands
    (u'¶', ur'\P{}'),
    (u'§', ur'\S{}'),
    (u'€', ur'\texteuro{}'),
    (u'∞', ur'\(\infty\)'),
    (u'±', ur'\(\pm\)'),
    (u'→', ur'\(\rightarrow\)'),
    (u'‣', ur'\(\rightarrow\)'),
    # used to separate -- in options
    (u'﻿', ur'{}'),
    # map some special Unicode characters to similar ASCII ones
    (u'─', ur'-'),
    (u'⎽', ur'\_'),
    (u'╲', ur'\textbackslash{}'),
    (u'|', ur'\textbar{}'),
    (u'│', ur'\textbar{}'),
    (u'ℯ', ur'e'),
    (u'ⅈ', ur'i'),
    (u'₁', ur'1'),
    (u'₂', ur'2'),
    # map Greek alphabet
    (u'α', ur'\(\alpha\)'),
    (u'β', ur'\(\beta\)'),
    (u'γ', ur'\(\gamma\)'),
    (u'δ', ur'\(\delta\)'),
    (u'ε', ur'\(\epsilon\)'),
    (u'ζ', ur'\(\zeta\)'),
    (u'η', ur'\(\eta\)'),
    (u'θ', ur'\(\theta\)'),
    (u'ι', ur'\(\iota\)'),
    (u'κ', ur'\(\kappa\)'),
    (u'λ', ur'\(\lambda\)'),
    (u'μ', ur'\(\mu\)'),
    (u'ν', ur'\(\nu\)'),
    (u'ξ', ur'\(\xi\)'),
    (u'ο', ur'o'),
    (u'π', ur'\(\pi\)'),
    (u'ρ', ur'\(\rho\)'),
    (u'σ', ur'\(\sigma\)'),
    (u'τ', ur'\(\tau\)'),
    (u'υ', u'\\(\\upsilon\\)'),
    (u'φ', ur'\(\phi\)'),
    (u'χ', ur'\(\chi\)'),
    (u'ψ', ur'\(\psi\)'),
    (u'ω', ur'\(\omega\)'),
    (u'Α', ur'A'),
    (u'Β', ur'B'),
    (u'Γ', ur'\(\Gamma\)'),
    (u'Δ', ur'\(\Delta\)'),
    (u'Ε', ur'E'),
    (u'Ζ', ur'Z'),
    (u'Η', ur'H'),
    (u'Θ', ur'\(\Theta\)'),
    (u'Ι', ur'I'),
    (u'Κ', ur'K'),
    (u'Λ', ur'\(\Lambda\)'),
    (u'Μ', ur'M'),
    (u'Ν', ur'N'),
    (u'Ξ', ur'\(\Xi\)'),
    (u'Ο', ur'O'),
    (u'Π', ur'\(\Pi\)'),
    (u'Ρ', ur'P'),
    (u'Σ', ur'\(\Sigma\)'),
    (u'Τ', ur'T'),
    (u'Υ', u'\\(\\Upsilon\\)'),
    (u'Φ', ur'\(\Phi\)'),
    (u'Χ', ur'X'),
    (u'Ψ', ur'\(\Psi\)'),
    (u'Ω', ur'\(\Omega\)'),
    (u'Ω', ur'\(\Omega\)'),
]

tex_escape_map = {}
tex_replace_map = {}
tex_hl_escape_map_new = {}

def init():
    for a, b in tex_replacements:
        tex_escape_map[ord(a)] = b
        tex_replace_map[ord(a)] = u'_'

    for a, b in tex_replacements:
        if a in u'[]{}\\': continue
        tex_hl_escape_map_new[ord(a)] = b
