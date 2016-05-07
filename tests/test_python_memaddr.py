# -*- coding: utf-8 -*-
"""
    test_python_memaddr
    ~~~~~~~~~~~~~~~~~~~

    Tests that memory addresses are not shown in python code documentation.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app
from six import iteritems


@with_app('html', testroot='python-memaddr')
def test_memory_address(app, status, warning):
    app.builder.build_all()
    for f, refs_manual in iteritems({'index.html': 3, 'searchindex.js': -1}):
        t = (app.outdir / f).text()
        refs_ok = t.count("0xabcdef")
        if refs_manual >= 0:
            assert refs_ok == refs_manual, \
                ("%s memory addresses were deleted from file %s."
                 % (refs_manual-refs_ok, f))
        refs = t.count("0x") - refs_ok
        assert refs == 0, "File %s contained %d memory addresses." % (f, refs)


def the_same(x):
    return(x)


class MyClass(object):
    """A test class."""

    functions = {'TheSame': the_same}

    def __init__(self):
        pass

    def get_a(self):
        """Get a value"""
        pass

    def set_a(self, func=the_same, x=3):
        """Set a value."""
        pass

    def set_ah(self, opts={'func': the_same, 'x': 3}):
        """Set a value, with opts."""
        pass
