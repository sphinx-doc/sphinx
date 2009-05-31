# -*- coding: utf-8 -*-
"""
    test_autosummary
    ~~~~~~~~~~~~~~~~

    Test the autosummary extension.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import string

from util import *

from sphinx.ext.autosummary import mangle_signature


def test_mangle_signature():
    TEST = """
    () :: ()
    (a, b, c, d, e) :: (a, b, c, d, e)
    (a, b, c=1, d=2, e=3) :: (a, b[, c, d, e])
    (a, b, aaa=1, bbb=1, ccc=1, eee=1, fff=1, ggg=1, hhh=1, iii=1, jjj=1)\
    :: (a, b[, aaa, bbb, ccc, ...])
    (a, b, c=(), d=<foo>) :: (a, b[, c, d])
    (a, b, c='foobar()', d=123) :: (a, b[, c, d])
    """

    TEST = [map(string.strip, x.split("::")) for x in TEST.split("\n")
            if '::' in x]
    for inp, outp in TEST:
        res = mangle_signature(inp).strip().replace(u"\u00a0", " ")
        assert res == outp, (u"'%s' -> '%s' != '%s'" % (inp, res, outp))
