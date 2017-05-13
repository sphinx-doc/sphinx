# -*- coding: utf-8 -*-
"""
    test_ext_l10nfigures
    ~~~~~~~~~~~~~~~~~~~~

    Test the l10nfigures extension.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app

from sphinx.ext.l10nfigures import replace_spans

@with_app(testroot='ext-l10nfigures')
def test_l10nfigures(app, status, warning):
    app.builder.build_all()


def test_replace_spans0():
    s = ''.join(s for s in replace_spans('0123456789', []))
    assert s == '0123456789'


def test_replace_spans1():
    s = ''.join(s for s in replace_spans('0123456789', [((3, 6), 'abcd')]))
    assert s == '012abcd6789', s

def test_replace_spans_more():
    s = ''.join(s for s in replace_spans('0123456789' * 5,
        [((3, 6), 'abcd'),((9, 10), 'abc'), ((25, 35), 'a')]
    ))
    assert s == '012abcd678abc012345678901234a567890123456789', s

