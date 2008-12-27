# -*- coding: utf-8 -*-
"""
    test_i18n
    ~~~~~~~~~

    Test locale features.

    :copyright: 2008 by Georg Brandl.
    :license: BSD, see LICENSE for details.
"""

from util import *


@with_app(confoverrides={'language': 'de'})
def test_i18n(app):
    app.builder.build_all()
