# -*- coding: utf-8 -*-
"""
    test_domain_js
    ~~~~~~~~~~~~~~

    Tests the JavaScript Domain

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""


from util import with_app


@with_app('html', testroot='domain-js')
def test_hidden_directive(app, status, warning):
    app.builder.build(['domain-js'])
    result = (app.outdir / 'index.html').text(encoding='utf-8')
    assert '<dt id="Foobar">' in result
    assert '<dt id="Foo">' not in result
    # js domain doesn't handle nested directives
    assert '<dt id="bar">' in result
