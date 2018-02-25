# -*- coding: utf-8 -*-
"""
    test_smartquotes
    ~~~~~~~~~~~~~~~~

    Test smart quotes.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from sphinx.util import docutils


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True)
def test_basic(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').text()
    assert u'<p>– “Sphinx” is a tool that makes it easy …</p>' in content


@pytest.mark.sphinx(buildername='text', testroot='smartquotes', freshenv=True)
def test_text_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'index.txt').text()
    assert u'-- "Sphinx" is a tool that makes it easy ...' in content


@pytest.mark.sphinx(buildername='man', testroot='smartquotes', freshenv=True)
def test_man_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'python.1').text()
    assert u'\\-\\- "Sphinx" is a tool that makes it easy ...' in content


@pytest.mark.sphinx(buildername='latex', testroot='smartquotes', freshenv=True)
def test_latex_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'test.tex').text()
    assert u'\\textendash{} “Sphinx” is a tool that makes it easy …' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'language': 'ja'})
def test_ja_html_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').text()
    assert u'<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'smartquotes': False})
def test_smartquotes_disabled(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').text()
    assert u'<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.skipif(docutils.__version_info__ < (0, 14),
                    reason='docutils-0.14 or above is required')
@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'smartquotes_action': 'q'})
def test_smartquotes_action(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').text()
    assert u'<p>-- “Sphinx” is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'language': 'ja', 'smartquotes_excludes': {}})
def test_smartquotes_excludes_language(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').text()
    assert u'<p>– 「Sphinx」 is a tool that makes it easy …</p>' in content


@pytest.mark.sphinx(buildername='man', testroot='smartquotes', freshenv=True,
                    confoverrides={'smartquotes_excludes': {}})
def test_smartquotes_excludes_builders(app, status, warning):
    app.build()

    content = (app.outdir / 'python.1').text()
    assert u'– “Sphinx” is a tool that makes it easy …' in content
