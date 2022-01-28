"""
    test_smartquotes
    ~~~~~~~~~~~~~~~~

    Test smart quotes.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
from html5lib import HTMLParser

from sphinx.util import docutils


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True)
def test_basic(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text()
    assert '<p>– “Sphinx” is a tool that makes it easy …</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True)
def test_literals(app, status, warning):
    app.build()

    with (app.outdir / 'literals.html').open() as html_file:
        etree = HTMLParser(namespaceHTMLElements=False).parse(html_file)

    for code_element in etree.iter('code'):
        code_text = ''.join(code_element.itertext())

        if code_text.startswith('code role'):
            assert "'quotes'" in code_text
        elif code_text.startswith('{'):
            assert code_text == "{'code': 'role', 'with': 'quotes'}"
        elif code_text.startswith('literal'):
            assert code_text == "literal with 'quotes'"


@pytest.mark.sphinx(buildername='text', testroot='smartquotes', freshenv=True)
def test_text_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'index.txt').read_text()
    assert '-- "Sphinx" is a tool that makes it easy ...' in content


@pytest.mark.sphinx(buildername='man', testroot='smartquotes', freshenv=True)
def test_man_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'python.1').read_text()
    if docutils.__version_info__ > (0, 18):
        assert r'\-\- \(dqSphinx\(dq is a tool that makes it easy ...' in content
    else:
        assert r'\-\- "Sphinx" is a tool that makes it easy ...' in content


@pytest.mark.sphinx(buildername='latex', testroot='smartquotes', freshenv=True)
def test_latex_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'python.tex').read_text()
    assert '\\textendash{} “Sphinx” is a tool that makes it easy …' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'language': 'ja'})
def test_ja_html_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text()
    assert '<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'smartquotes': False})
def test_smartquotes_disabled(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text()
    assert '<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'smartquotes_action': 'q'})
def test_smartquotes_action(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text()
    assert '<p>-- “Sphinx” is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'language': 'ja', 'smartquotes_excludes': {}})
def test_smartquotes_excludes_language(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text()
    assert '<p>– 「Sphinx」 is a tool that makes it easy …</p>' in content


@pytest.mark.sphinx(buildername='man', testroot='smartquotes', freshenv=True,
                    confoverrides={'smartquotes_excludes': {}})
def test_smartquotes_excludes_builders(app, status, warning):
    app.build()

    content = (app.outdir / 'python.1').read_text()
    assert '– “Sphinx” is a tool that makes it easy …' in content
