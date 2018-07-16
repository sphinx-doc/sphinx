# -*- coding: utf-8 -*-
"""
    test_websupport
    ~~~~~~~~~~~~~~~

    Test the Web Support Package

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from sphinx.websupport import WebSupport
try:
    sqlalchemy_missing = False
    import sqlalchemy  # NOQA
except ImportError:
    sqlalchemy_missing = True


@pytest.mark.skipif(sqlalchemy_missing, reason='needs sqlalchemy')
def test_build(request, rootdir, sphinx_test_tempdir):
    settings = {
        'srcdir': rootdir / 'test-basic',
        # to use same directory for 'builddir' in each 'support' fixture, using
        # 'sphinx_test_tempdir' (static) value instead of 'tempdir' fixture value.
        # each test expect result of db value at previous test case.
        'builddir': sphinx_test_tempdir / 'websupport'
    }
    marker = request.node.get_marker('support')
    if marker:
        settings.update(marker.kwargs)

    support = WebSupport(**settings)
    support.build()
