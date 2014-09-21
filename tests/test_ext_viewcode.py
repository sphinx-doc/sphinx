# -*- coding: utf-8 -*-
"""
    test_ext_viewcode
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.viewcode extension.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from util import with_app


@with_app(testroot='ext-viewcode')
def test_simple(app, status, warning):
    app.builder.build_all()

    warnings = re.sub(r'\\+', '/', warning.getvalue())
    assert re.findall(
        r"index.rst:\d+: WARNING: Object named 'func1' not found in include " +
        r"file .*/spam/__init__.py'",
        warnings
    )

    result = (app.outdir / 'index.html').text(encoding='utf-8')
    assert result.count('href="_modules/spam/mod1.html#func1"') == 2
    assert result.count('href="_modules/spam/mod2.html#func2"') == 2
    assert result.count('href="_modules/spam/mod1.html#Class1"') == 2
    assert result.count('href="_modules/spam/mod2.html#Class2"') == 2
