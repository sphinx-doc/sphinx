# -*- coding: utf-8 -*-
"""
    test_python_memaddr
    ~~~~~~~~~~~~~~~~~~~

    Tests that memory addresses are not shown in python code documentation.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app


@with_app('html', testroot='python-memaddr')
def test_memory_address(app, status, warning):
    app.builder.build_all()
    for f in ['index.html','searchindex.js']:
        t = (app.outdir / f).text()
        refs = t.count("0x")
        assert refs == 0, "A memory address was found %d times in the file %s." % (refs, f)

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
