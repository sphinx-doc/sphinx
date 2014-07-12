# -*- coding: utf-8 -*-
"""
    test_py_domain
    ~~~~~~~~~~~~~~

    Tests the Python Domain

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx import addnodes
from sphinx.domains.python import py_sig_re, _pseudo_parse_arglist


def parse(sig):
    m = py_sig_re.match(sig)
    if m is None:
        raise ValueError
    name_prefix, name, arglist, retann = m.groups()
    signode = addnodes.desc_signature(sig, '')
    _pseudo_parse_arglist(signode, arglist)
    return signode.astext()


def test_function_signatures():

    rv = parse('func(a=1) -> int object')
    assert unicode(rv) == u'a=1'

    rv = parse('func(a=1, [b=None])')
    assert unicode(rv) == u'a=1, [b=None]'

    rv = parse('func(a=1[, b=None])')
    assert unicode(rv) == u'a=1, [b=None]'

    rv = parse("compile(source : string, filename, symbol='file')")
    assert unicode(rv) == u"source : string, filename, symbol='file'"

    rv = parse('func(a=[], [b=None])')
    assert unicode(rv) == u'a=[], [b=None]'

    rv = parse('func(a=[][, b=None])')
    assert unicode(rv) == u'a=[], [b=None]'
