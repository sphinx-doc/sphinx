# -*- coding: utf-8 -*-
"""
    test_build_qthelp
    ~~~~~~~~~~~~~~~~~

    Test the Qt Help builder and check its output.  We don't need to
    test the HTML itself; that's already handled by
    :file:`test_build_html.py`.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('qthelp', testroot='basic')
def test_qthelp_basic(app, status, warning):
    app.builder.build_all()

    qhcp = (app.outdir / 'Python.qhcp').text()
    assert '<title>Python  documentation</title>' in qhcp
    assert '<homePage>qthelp://org.sphinx.python/doc/index.html</homePage>' in qhcp
    assert '<startPage>qthelp://org.sphinx.python/doc/index.html</startPage>' in qhcp
    assert '<input>Python.qhp</input>' in qhcp
    assert '<output>Python.qch</output>' in qhcp
    assert '<file>Python.qch</file>' in qhcp


@pytest.mark.sphinx('qthelp', testroot='basic')
def test_qthelp_namespace(app, status, warning):
    # default namespace
    app.builder.build_all()

    qhp = (app.outdir / 'Python.qhp').text()
    assert '<namespace>org.sphinx.python</namespace>' in qhp

    qhcp = (app.outdir / 'Python.qhcp').text()
    assert '<homePage>qthelp://org.sphinx.python/doc/index.html</homePage>' in qhcp
    assert '<startPage>qthelp://org.sphinx.python/doc/index.html</startPage>' in qhcp

    # give a namespace
    app.config.qthelp_namespace = 'org.sphinx-doc.sphinx'
    app.builder.build_all()

    qhp = (app.outdir / 'Python.qhp').text()
    assert '<namespace>org.sphinxdoc.sphinx</namespace>' in qhp

    qhcp = (app.outdir / 'Python.qhcp').text()
    assert '<homePage>qthelp://org.sphinxdoc.sphinx/doc/index.html</homePage>' in qhcp
    assert '<startPage>qthelp://org.sphinxdoc.sphinx/doc/index.html</startPage>' in qhcp


@pytest.mark.sphinx('qthelp', testroot='basic')
def test_qthelp_title(app, status, warning):
    # default title
    app.builder.build_all()

    qhp = (app.outdir / 'Python.qhp').text()
    assert '<section title="Python  documentation" ref="index.html">' in qhp

    qhcp = (app.outdir / 'Python.qhcp').text()
    assert '<title>Python  documentation</title>' in qhcp

    # give a title
    app.config.html_title = 'Sphinx <b>"full"</b> title'
    app.config.html_short_title = 'Sphinx <b>"short"</b> title'
    app.builder.build_all()

    qhp = (app.outdir / 'Python.qhp').text()
    assert '<section title="Sphinx &lt;b&gt;"full"&lt;/b&gt; title" ref="index.html">' in qhp

    qhcp = (app.outdir / 'Python.qhcp').text()
    assert '<title>Sphinx &lt;b&gt;"short"&lt;/b&gt; title</title>' in qhcp
