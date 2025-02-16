"""Test smart quotes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.testing.util import etree_parse

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx(
    'html',
    testroot='smartquotes',
    freshenv=True,
)
def test_basic(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>– “Sphinx” is a tool that makes it easy …</p>' in content


@pytest.mark.sphinx(
    'html',
    testroot='smartquotes',
    freshenv=True,
)
def test_literals(app: SphinxTestApp) -> None:
    app.build()

    etree = etree_parse(app.outdir / 'literals.html')
    for code_element in etree.iter('code'):
        code_text = ''.join(code_element.itertext())

        if code_text.startswith('code role'):
            assert "'quotes'" in code_text
        elif code_text.startswith('{'):
            assert code_text == "{'code': 'role', 'with': 'quotes'}"
        elif code_text.startswith('literal'):
            assert code_text == "literal with 'quotes'"


@pytest.mark.sphinx(
    'text',
    testroot='smartquotes',
    freshenv=True,
)
def test_text_builder(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert '-- "Sphinx" is a tool that makes it easy ...' in content


@pytest.mark.sphinx(
    'man',
    testroot='smartquotes',
    freshenv=True,
)
def test_man_builder(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'projectnamenotset.1').read_text(encoding='utf8')
    assert r'\-\- \(dqSphinx\(dq is a tool that makes it easy ...' in content


@pytest.mark.sphinx(
    'latex',
    testroot='smartquotes',
    freshenv=True,
)
def test_latex_builder(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')
    assert '\\textendash{} “Sphinx” is a tool that makes it easy …' in content


@pytest.mark.sphinx(
    'html',
    testroot='smartquotes',
    freshenv=True,
    confoverrides={'language': 'ja'},
)
def test_ja_html_builder(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(
    'html',
    testroot='smartquotes',
    freshenv=True,
    confoverrides={'language': 'zh_CN'},
)
def test_zh_cn_html_builder(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(
    'html',
    testroot='smartquotes',
    freshenv=True,
    confoverrides={'language': 'zh_TW'},
)
def test_zh_tw_html_builder(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(
    'html',
    testroot='smartquotes',
    freshenv=True,
    confoverrides={'smartquotes': False},
)
def test_smartquotes_disabled(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>-- &quot;Sphinx&quot; is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(
    'html',
    testroot='smartquotes',
    freshenv=True,
    confoverrides={'smartquotes_action': 'q'},
)
def test_smartquotes_action(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>-- “Sphinx” is a tool that makes it easy ...</p>' in content


@pytest.mark.sphinx(
    'html',
    testroot='smartquotes',
    freshenv=True,
    confoverrides={'language': 'ja', 'smartquotes_excludes': {}},
)
def test_smartquotes_excludes_language(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p>– 「Sphinx」 is a tool that makes it easy …</p>' in content


@pytest.mark.sphinx(
    'man',
    testroot='smartquotes',
    freshenv=True,
    confoverrides={'smartquotes_excludes': {}},
)
def test_smartquotes_excludes_builders(app: SphinxTestApp) -> None:
    app.build()

    content = (app.outdir / 'projectnamenotset.1').read_text(encoding='utf8')
    assert '– “Sphinx” is a tool that makes it easy …' in content
