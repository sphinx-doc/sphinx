"""Test smart quotes."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.testing.util import etree_parse

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from sphinx.testing.fixtures import _app_params
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


@pytest.mark.parametrize(
    ('first_builder', 'second_builder', 'expected', 'rereads'),
    [
        (
            'text',
            'xml',
            '<paragraph>This is a line with a quote, isn’t it?</paragraph>',
            True,
        ),
        ('xml', 'text', "This is a line with a quote, isn't it?", True),
        (
            'html',
            'xml',
            '<paragraph>This is a line with a quote, isn’t it?</paragraph>',
            False,
        ),
        ('text', 'man', r'isn\(aqt it?', False),
    ],
)
@pytest.mark.sphinx(testroot='smartquotes-cache', srcdir='smartquotes-cache')
def test_smartquotes_when_reusing_doctrees_across_builders(
    make_app: Callable[..., SphinxTestApp],
    app_params: _app_params,
    first_builder: str,
    second_builder: str,
    expected: str,
    rereads: bool,
    tmp_path: Path,
) -> None:
    _args, kwargs = app_params
    kwargs = {**kwargs, 'builddir': tmp_path / '_build'}
    first_app = make_app(first_builder, freshenv=True, **kwargs)
    first_app.build()

    second_app = make_app(second_builder, **kwargs)
    assert second_app.fresh_env_used is False
    assert second_app.doctreedir == first_app.doctreedir
    read_doctrees: list[object] = []
    second_app.connect(
        'doctree-read', lambda _app, doctree: read_doctrees.append(doctree)
    )
    second_app.build()

    assert len(read_doctrees) == int(rereads)
    if second_builder == 'man':
        output_file = next(second_app.outdir.glob('*.1'))
    else:
        filename = 'index.xml' if second_builder == 'xml' else 'index.txt'
        output_file = second_app.outdir / filename
    content = output_file.read_text(encoding='utf8')
    assert expected in content
    title = second_app.env.titles['index'].astext()
    assert ('“quoted”' in title) == (second_builder == 'xml')
    toc = second_app.env.tocs['index'].astext()
    assert ('“quoted”' in toc) == (second_builder == 'xml')


@pytest.mark.sphinx(testroot='smartquotes-cache', srcdir='smartquotes-cache')
def test_smartquotes_cache_after_same_state_builder(
    make_app: Callable[..., SphinxTestApp],
    app_params: _app_params,
    tmp_path: Path,
) -> None:
    _args, kwargs = app_params
    kwargs = {**kwargs, 'builddir': tmp_path / '_build'}

    html_app = make_app('html', freshenv=True, **kwargs)
    html_app.build()
    assert 'isn’t it?' in (html_app.outdir / 'index.html').read_text(encoding='utf8')

    xml_app = make_app('xml', **kwargs)
    assert xml_app.fresh_env_used is False
    assert xml_app.env._smartquotes_enabled is True
    xml_reads: list[object] = []
    xml_app.connect('doctree-read', lambda _app, doctree: xml_reads.append(doctree))
    xml_app.build()
    assert xml_reads == []
    assert 'isn’t it?' in (xml_app.outdir / 'index.xml').read_text(encoding='utf8')

    text_app = make_app('text', **kwargs)
    assert text_app.fresh_env_used is False
    assert text_app.env._smartquotes_enabled is True
    text_reads: list[object] = []
    text_app.connect('doctree-read', lambda _app, doctree: text_reads.append(doctree))
    text_app.build()
    assert len(text_reads) == 1
    assert "isn't it?" in (text_app.outdir / 'index.txt').read_text(encoding='utf8')


@pytest.mark.parametrize(
    ('first_builder', 'second_builder', 'expected'),
    [
        ('html', 'xml-no-smartquotes', "isn't it?"),
        ('xml-no-smartquotes', 'html', 'isn’t it?'),
    ],
)
@pytest.mark.sphinx(testroot='smartquotes-cache', srcdir='smartquotes-cache')
def test_smartquotes_cache_with_builder_override(
    make_app: Callable[..., SphinxTestApp],
    app_params: _app_params,
    first_builder: str,
    second_builder: str,
    expected: str,
    tmp_path: Path,
) -> None:
    _args, kwargs = app_params
    kwargs = {**kwargs, 'builddir': tmp_path / '_build'}

    first_app = make_app(first_builder, freshenv=True, **kwargs)
    first_app.build()

    second_app = make_app(second_builder, **kwargs)
    assert second_app.fresh_env_used is False
    assert second_app.doctreedir == first_app.doctreedir
    read_doctrees: list[object] = []
    second_app.connect(
        'doctree-read', lambda _app, doctree: read_doctrees.append(doctree)
    )
    second_app.build()

    suffix = 'html' if second_builder == 'html' else 'xml'
    content = (second_app.outdir / f'index.{suffix}').read_text(encoding='utf8')
    assert expected in content
    assert len(read_doctrees) == 1
