# -*- coding: utf-8 -*-
"""
    test_linkcode
    ~~~~~~~~~~~~~

    Test the sphinx.ext.linkcode extension.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app


@with_app('html', tags=['test_linkcode'])
def test_html(app, status, warning):
    app.builder.build(['objects'])

    stuff = (app.outdir / 'objects.html').text(encoding='utf-8')

    assert 'http://foobar/source/foolib.py' in stuff
    assert 'http://foobar/js/' in stuff
    assert 'http://foobar/c/' in stuff
    assert 'http://foobar/cpp/' in stuff
