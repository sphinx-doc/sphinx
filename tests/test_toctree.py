# -*- coding: utf-8 -*-
"""
    test_toctree
    ~~~~~~~~~~~~

    Test the HTML builder and check output against XPath.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app


@with_app(testroot='toctree-glob')
def test_relations(app, status, warning):
    app.builder.build_all()
    assert app.builder.relations['index'] == [None, None, 'foo']
    assert app.builder.relations['foo'] == ['index', 'index', 'bar/index']
    assert app.builder.relations['bar/index'] == ['index', 'foo', 'bar/bar_1']
    assert app.builder.relations['bar/bar_1'] == ['bar/index', 'bar/index', 'bar/bar_2']
    assert app.builder.relations['bar/bar_2'] == ['bar/index', 'bar/bar_1', 'bar/bar_3']
    assert app.builder.relations['bar/bar_3'] == ['bar/index', 'bar/bar_2', 'baz']
    assert app.builder.relations['baz'] == ['index', 'bar/bar_3', None]
