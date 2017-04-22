# -*- coding: utf-8 -*-
"""
    test_websupport
    ~~~~~~~~~~~~~~~

    Test the Web Support Package

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.websupport import WebSupport
try:
    sqlalchemy_missing = False
except ImportError:
    sqlalchemy_missing = True

import pytest
from util import rootdir, tempdir


@pytest.mark.skipif(sqlalchemy_missing, reason='needs sqlalchemy')
def test_build(request):
    settings = {
        'srcdir': rootdir / 'roots' / 'test-basic',
        # to use same directory for 'builddir' in each 'support' fixture, using
        # 'tempdir' (static) value instead of 'tempdir' fixture value.
        # each test expect result of db value at previous test case.
        'builddir': tempdir / 'websupport'
    }
    marker = request.node.get_marker('support')
    if marker:
        settings.update(marker.kwargs)

    support = WebSupport(**settings)
    support.build()
