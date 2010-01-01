# -*- coding: utf-8 -*-
"""
    sphinx.locale
    ~~~~~~~~~~~~~

    Locale utilities.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

_ = lambda x: x

admonitionlabels = {
    'attention': _('Attention'),
    'caution':   _('Caution'),
    'danger':    _('Danger'),
    'error':     _('Error'),
    'hint':      _('Hint'),
    'important': _('Important'),
    'note':      _('Note'),
    'seealso':   _('See Also'),
    'tip':       _('Tip'),
    'warning':   _('Warning'),
}

versionlabels = {
    'versionadded':   _('New in version %s'),
    'versionchanged': _('Changed in version %s'),
    'deprecated':     _('Deprecated since version %s'),
}

pairindextypes = {
    'module':    _('module'),
    'keyword':   _('keyword'),
    'operator':  _('operator'),
    'object':    _('object'),
    'exception': _('exception'),
    'statement': _('statement'),
    'builtin':   _('built-in function'),
}

del _

def init():
    for dct in (admonitionlabels, versionlabels, pairindextypes):
        for key in dct:
            dct[key] = _(dct[key])
