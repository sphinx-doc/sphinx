# -*- coding: utf-8 -*-
"""
    test_doctest
    ~~~~~~~~~~~~

    Test the doctest extension.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import StringIO

from util import *

status = StringIO.StringIO()
cleanup_called = 0

@with_app(buildername='doctest', status=status)
def test_build(app):
    global cleanup_called
    cleanup_called = 0
    app.builder.build_all()
    if app.statuscode != 0:
        print >>sys.stderr, status.getvalue()
        assert False, 'failures in doctests'
    # in doctest.txt, there are two named groups and the default group,
    # so the cleanup function must be called three times
    assert cleanup_called == 3, 'testcleanup did not get executed enough times'

def cleanup_call():
    global cleanup_called
    cleanup_called += 1
