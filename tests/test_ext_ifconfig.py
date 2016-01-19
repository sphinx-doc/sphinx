# -*- coding: utf-8 -*-
"""
    test_ext_ifconfig
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.ifconfig extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from util import with_app


@with_app(testroot='ext-ifconfig')
def test_ifconfig(app, status, warning):
    app.builder.build_all()
