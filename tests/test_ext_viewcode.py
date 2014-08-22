# -*- coding: utf-8 -*-
"""
    test_ext_viewcode
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.viewcode extension.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
from StringIO import StringIO

from util import test_roots, with_app


warnfile = StringIO()
root = test_roots / 'test-ext-viewcode'
doctreedir = root / '_build' / 'doctree'


def teardown_module():
    (root / '_build').rmtree(True)


@with_app(srcdir=root, warning=warnfile)
def test_simple(app):
    app.builder.build_all()

    warnings = re.sub(r'\\+', '/', warnfile.getvalue())
    assert re.findall(
        r"index.rst:\d+: WARNING: Object named 'func1' not found in include " +
        r"file .*/spam/__init__.py'",
        warnings
    )

    result = (app.outdir / 'index.html').text(encoding='utf-8')
    assert result.count('href="_modules/spam/mod1.html#func1"') == 2
    assert result.count('href="_modules/spam/mod2.html#func2"') == 2
