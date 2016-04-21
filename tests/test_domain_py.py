# -*- coding: utf-8 -*-
"""
    test_domain_py
    ~~~~~~~~~~~~~~

    Tests the Python Domain

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import text_type

from util import with_app

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

@with_app('html', testroot='domain-py')
def test_memory_address(app, status, warning):
    app.builder.build_all()
    g_refs = 0
    for f in ['index.html','searchindex.js']:
        t = (app.outdir / f).text()
        refs = t.count("0x")
        g_refs += refs
        if refs>0:
            print("A memory address was found %d times in the %s file." % (refs,f))
    if g_refs>0:
        assert False

def the_same(x):
    return(x)

class MyClass(object):
    """A test class."""

    functions = { 'TheSame': the_same }

    def __init__(self):
        self.a=1

    def get_a(self):
        """Get a value"""
        return(self.a)
    
    def set_a(self,func=the_same,x=3):
        """Set a value.

        :param func: a function to be called
        :param x: value to be passed to the function"""
        self.a=the_same(x)

    def set_ah(self,opts={'func': the_same, 'x': 3}):
        """Set a value, with opts."""
        self.set_a(opts['func'],opts['x'])


