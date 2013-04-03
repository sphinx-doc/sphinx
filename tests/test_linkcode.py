# -*- coding: utf-8 -*-
"""
    test_linkcode
    ~~~~~~~~~~~~~

    Test the sphinx.ext.linkcode extension.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from util import with_app

@with_app(srcdir='(temp)', buildername='html', tags=['test_linkcode'])
def test_html(app):
    app.builder.build_all()

    fp = open(os.path.join(app.outdir, 'objects.html'), 'r')
    try:
        stuff = fp.read()
    finally:
        fp.close()

    assert 'http://foobar/source/foolib.py' in stuff
    assert 'http://foobar/js/' in stuff
    assert 'http://foobar/c/' in stuff
    assert 'http://foobar/cpp/' in stuff
