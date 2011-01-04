# -*- coding: utf-8 -*-
"""
    test_i18n
    ~~~~~~~~~

    Test locale features.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import *


@with_app(confoverrides={'language': 'de'})
def test_i18n(app):
    app.builder.build_all()
