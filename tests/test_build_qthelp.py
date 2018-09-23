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

from sphinx.testing.util import etree_parse


@pytest.mark.sphinx('qthelp', testroot='basic')
def test_qthelp_basic(app, status, warning):
    app.builder.build_all()

    qhp = (app.outdir / 'Python.qhp').text()
    assert '<customFilter name="Python ">' in qhp
    assert '<filterAttribute>Python</filterAttribute>' in qhp
    assert '<filterAttribute></filterAttribute>' in qhp
    assert '<section title="Python  documentation" ref="index.html">' in qhp
    assert '<file>genindex.html</file>' in qhp
    assert '<file>index.html</file>' in qhp
    assert '<file>_static/basic.css</file>' in qhp
    assert '<file>_static/down.png</file>' in qhp

    qhcp = (app.outdir / 'Python.qhcp').text()
    assert '<title>Python  documentation</title>' in qhcp
    assert '<homePage>qthelp://org.sphinx.python/doc/index.html</homePage>' in qhcp
    assert '<startPage>qthelp://org.sphinx.python/doc/index.html</startPage>' in qhcp
    assert '<input>Python.qhp</input>' in qhcp
    assert '<output>Python.qch</output>' in qhcp
    assert '<file>Python.qch</file>' in qhcp


@pytest.mark.sphinx('qthelp', testroot='need-escaped')
def test_qthelp_escaped(app, status, warning):
    app.builder.build_all()

    et = etree_parse(app.outdir / 'needbescapedbproject.qhp')
    customFilter = et.find('.//customFilter')
    assert len(customFilter) == 2
    assert customFilter.attrib == {'name': 'need <b>"escaped"</b> project '}
    assert customFilter[0].text == 'needbescapedbproject'
    assert customFilter[1].text is None

    toc = et.find('.//toc')
    assert len(toc) == 1
    assert toc[0].attrib == {'title': 'need <b>"escaped"</b> project  documentation',
                             'ref': 'index.html'}
    assert len(toc[0]) == 4
    assert toc[0][0].attrib == {'title': '<foo>', 'ref': 'foo.html'}
    assert toc[0][0][0].attrib == {'title': 'quux', 'ref': 'quux.html'}
    assert toc[0][0][1].attrib == {'title': 'foo "1"', 'ref': 'foo.html#foo-1'}
    assert toc[0][0][1][0].attrib == {'title': 'foo.1-1', 'ref': 'foo.html#foo-1-1'}
    assert toc[0][0][2].attrib == {'title': 'foo.2', 'ref': 'foo.html#foo-2'}
    assert toc[0][1].attrib == {'title': 'bar', 'ref': 'bar.html'}
    assert toc[0][2].attrib == {'title': 'http://sphinx-doc.org/',
                                'ref': 'http://sphinx-doc.org/'}
    assert toc[0][3].attrib == {'title': 'baz', 'ref': 'baz.html'}

    keywords = et.find('.//keywords')
    assert len(keywords) == 2
    assert keywords[0].attrib == {'name': '<subsection>', 'ref': 'index.html#index-0'}
    assert keywords[1].attrib == {'name': '"subsection"', 'ref': 'index.html#index-0'}


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
    assert '<namespace>org.sphinx-doc.sphinx</namespace>' in qhp

    qhcp = (app.outdir / 'Python.qhcp').text()
    assert '<homePage>qthelp://org.sphinx-doc.sphinx/doc/index.html</homePage>' in qhcp
    assert '<startPage>qthelp://org.sphinx-doc.sphinx/doc/index.html</startPage>' in qhcp


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
    assert ('<section title="Sphinx &lt;b&gt;&#34;full&#34;&lt;/b&gt; title" ref="index.html">'
            in qhp)

    qhcp = (app.outdir / 'Python.qhcp').text()
    assert '<title>Sphinx &lt;b&gt;&#34;short&#34;&lt;/b&gt; title</title>' in qhcp
