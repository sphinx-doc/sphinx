# -*- coding: utf-8 -*-
"""
    test_domain_py
    ~~~~~~~~~~~~~~

    Tests the Python Domain

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import text_type

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
    assert text_type(rv) == u'a=1'

    rv = parse('func(a=1, [b=None])')
    assert text_type(rv) == u'a=1, [b=None]'

    rv = parse('func(a=1[, b=None])')
    assert text_type(rv) == u'a=1, [b=None]'

    rv = parse("compile(source : string, filename, symbol='file')")
    assert text_type(rv) == u"source : string, filename, symbol='file'"

    rv = parse('func(a=[], [b=None])')
    assert text_type(rv) == u'a=[], [b=None]'

    rv = parse('func(a=[][, b=None])')
    assert text_type(rv) == u'a=[], [b=None]'
