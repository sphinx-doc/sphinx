"""Test smart quotes."""

import docutils
import pytest
from html5lib import HTMLParser


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True)
def test_basic(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>– “Sphinx” is a tool that makes it easy …</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True)
def test_literals(app, status, warning):
    app.build()

    with (app.outdir / 'literals.html').open(encoding='utf-8') as html_file:
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

    content = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert '-- "Sphinx" is a tool that makes it easy ...' in content


@pytest.mark.sphinx(buildername='man', testroot='smartquotes', freshenv=True)
def test_man_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'python.1').read_text(encoding='utf8')
    if docutils.__version_info__ > (0, 18):
        assert r'\-\- \(dqSphinx\(dq is a tool that makes it easy ...' in content
    else:
        assert r'\-\- "Sphinx" is a tool that makes it easy ...' in content


@pytest.mark.sphinx(buildername='latex', testroot='smartquotes', freshenv=True)
def test_latex_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert '\\textendash{} “Sphinx” is a tool that makes it easy …' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'language': 'ja'})
def test_ja_html_builder(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'smartquotes': False})
def test_smartquotes_disabled(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'smartquotes_action': 'q'})
def test_smartquotes_action(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>-- “Sphinx” is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(buildername='html', testroot='smartquotes', freshenv=True,
                    confoverrides={'language': 'ja', 'smartquotes_excludes': {}})
def test_smartquotes_excludes_language(app, status, warning):
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>– 「Sphinx」 is a tool that makes it easy …</p>' in content


@pytest.mark.sphinx(buildername='man', testroot='smartquotes', freshenv=True,
                    confoverrides={'smartquotes_excludes': {}})
def test_smartquotes_excludes_builders(app, status, warning):
    app.build()

    content = (app.outdir / 'python.1').read_text(encoding='utf8')
    assert '– “Sphinx” is a tool that makes it easy …' in content
