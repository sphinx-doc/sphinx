# -*- coding: utf-8 -*-
"""
    test_doctest
    ~~~~~~~~~~~~

    Test the doctest extension.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import StringIO

from util import *

status = StringIO.StringIO()

@with_app(buildername='doctest', status=status)
def test_build(app):
    app.builder.build_all()
    if app.statuscode != 0:
        print >>sys.stderr, status.getvalue()
        assert False, 'failures in doctests'
