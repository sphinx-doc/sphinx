# -*- coding: utf-8 -*-
"""
    test_toctree
    ~~~~~~~~~~~~

    Test the HTML builder and check output against XPath.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import re

import pytest


@pytest.mark.sphinx(testroot='toctree-glob')
def test_relations(app, status, warning):
    app.builder.build_all()
    assert app.builder.relations['index'] == [None, None, 'foo']
    assert app.builder.relations['foo'] == ['index', 'index', 'bar/index']
    assert app.builder.relations['bar/index'] == ['index', 'foo', 'bar/bar_1']
    assert app.builder.relations['bar/bar_1'] == ['bar/index', 'bar/index', 'bar/bar_2']
    assert app.builder.relations['bar/bar_2'] == ['bar/index', 'bar/bar_1', 'bar/bar_3']
    assert app.builder.relations['bar/bar_3'] == ['bar/index', 'bar/bar_2', 'bar/bar_4/index']
    assert app.builder.relations['bar/bar_4/index'] == ['bar/index', 'bar/bar_3', 'baz']
    assert app.builder.relations['baz'] == ['index', 'bar/bar_4/index', 'qux/index']
    assert app.builder.relations['qux/index'] == ['index', 'baz', 'qux/qux_1']
    assert app.builder.relations['qux/qux_1'] == ['qux/index', 'qux/index', 'qux/qux_2']
    assert app.builder.relations['qux/qux_2'] == ['qux/index', 'qux/qux_1', None]
    assert 'quux' not in app.builder.relations


@pytest.mark.sphinx('singlehtml', testroot='toctree-empty')
def test_singlehtml_toctree(app, status, warning):
    app.builder.build_all()
    try:
        app.builder._get_local_toctree('index')
    except AttributeError:
        pytest.fail('Unexpected AttributeError in app.builder.fix_refuris')


@pytest.mark.sphinx(testroot='toctree', srcdir="numbered-toctree")
def test_numbered_toctree(app, status, warning):
    # give argument to :numbered: option
    index = (app.srcdir / 'index.rst').text()
    index = re.sub(':numbered:.*', ':numbered: 1', index)
    (app.srcdir / 'index.rst').write_text(index, encoding='utf-8')
    app.builder.build_all()
