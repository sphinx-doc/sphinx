"""Test the HTML builder and check output against XPath."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from sphinx.builders.html import StandaloneHTMLBuilder

from tests.test_builders.xpath_html_util import _intradocument_hyperlink_check
from tests.test_builders.xpath_util import check_xpath

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path
    from xml.etree.ElementTree import Element, ElementTree

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='toctree-glob')
def test_relations(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    assert app.builder.relations['index'] == [None, None, 'foo']
    assert app.builder.relations['foo'] == ['index', 'index', 'bar/index']
    assert app.builder.relations['bar/index'] == ['index', 'foo', 'bar/bar_1']
    assert app.builder.relations['bar/bar_1'] == ['bar/index', 'bar/index', 'bar/bar_2']
    assert app.builder.relations['bar/bar_2'] == ['bar/index', 'bar/bar_1', 'bar/bar_3']
    assert app.builder.relations['bar/bar_3'] == [
        'bar/index',
        'bar/bar_2',
        'bar/bar_4/index',
    ]
    assert app.builder.relations['bar/bar_4/index'] == ['bar/index', 'bar/bar_3', 'baz']
    assert app.builder.relations['baz'] == ['index', 'bar/bar_4/index', 'qux/index']
    assert app.builder.relations['qux/index'] == ['index', 'baz', 'qux/qux_1']
    assert app.builder.relations['qux/qux_1'] == ['qux/index', 'qux/index', 'qux/qux_2']
    assert app.builder.relations['qux/qux_2'] == ['qux/index', 'qux/qux_1', None]
    assert 'quux' not in app.builder.relations


@pytest.mark.sphinx('singlehtml', testroot='toctree-empty')
def test_singlehtml_toctree(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    try:
        app.builder._get_local_toctree('index')
    except AttributeError:
        pytest.fail('Unexpected AttributeError in app.builder.fix_refuris')


@pytest.mark.sphinx(
    'html',
    testroot='toctree',
    srcdir='numbered-toctree',
)
def test_numbered_toctree(app: SphinxTestApp) -> None:
    # give argument to :numbered: option
    index = (app.srcdir / 'index.rst').read_text(encoding='utf8')
    index = re.sub(':numbered:.*', ':numbered: 1', index)
    (app.srcdir / 'index.rst').write_text(index, encoding='utf8')
    app.build(force_all=True)


@pytest.mark.parametrize(
    'expect',
    [
        # internal references should be same-document; external should not
        (".//a[@class='reference internal']", _intradocument_hyperlink_check),
        (".//a[@class='reference external']", r'https?://'),
    ],
)
@pytest.mark.sphinx('singlehtml', testroot='toctree')
def test_singlehtml_hyperlinks(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    expect: tuple[str, str | Callable[[Sequence[Element]], None]],
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / 'index.html'), 'index.html', *expect)


@pytest.mark.sphinx(
    'html',
    testroot='toctree-multiple-parents',
    confoverrides={'html_theme': 'alabaster'},
)
def test_toctree_multiple_parents(
    app: SphinxTestApp, cached_etree_parse: Callable[[Path], ElementTree]
) -> None:
    # The lexicographically greatest parent of the document in global toctree
    # should be chosen, regardless of the order in which files are read
    with patch.object(app.builder, '_read_serial') as m:
        # Read files in reversed order
        _read_serial = type(app.builder)._read_serial
        m.side_effect = lambda docnames: _read_serial(app.builder, docnames[::-1])
        app.build()
        # Check if charlie is a child of delta in charlie.html
        xpath_delta_children = (
            ".//ul[@class='current']//a[@href='delta.html']/../ul/li//a"
        )
        etree = cached_etree_parse(app.outdir / 'charlie.html')
        check_xpath(etree, 'charlie.html', xpath=xpath_delta_children, check='Charlie')


@pytest.mark.sphinx(
    'html',
    testroot='_blank',
    srcdir='titleless-pages',
    confoverrides={'html_title': 'Project & docs', 'html_theme': 'basic'},
)
def test_titleless_pages(app: SphinxTestApp) -> None:
    (app.srcdir / 'index.rst').write_text(
        'Home\n====\n\n.. toctree::\n\n'
        '   Landing page <landing>\n'
        '   Named page <named>\n',
        encoding='utf-8',
    )
    (app.srcdir / 'landing.rst').write_text('Landing content.\n', encoding='utf-8')
    (app.srcdir / 'named.rst').write_text(
        '.. title:: Custom & title\n\nNamed content.\n', encoding='utf-8'
    )
    app.build()
    assert app.warning.getvalue() == ''
    index = (app.outdir / 'index.html').read_text(encoding='utf-8')
    assert 'href="landing.html">Landing page</a>' in index
    assert 'href="named.html">Named page</a>' in index
    landing = (app.outdir / 'landing.html').read_text(encoding='utf-8')
    assert '<title>Project &amp; docs</title>' in landing
    assert '<h1' not in landing
    named = (app.outdir / 'named.html').read_text(encoding='utf-8')
    assert '<title>Custom &amp; title &#8212; Project &amp; docs</title>' in named
    assert '<h1' not in named
    assert '<title>Home &#8212; Project &amp; docs</title>' in index
    assert not app.env.tocs['landing'].children
    assert app.env.titles['landing'].astext() == '<no title>'

    # A newly added heading replaces the fallback on an incremental build.
    (app.srcdir / 'landing.rst').write_text(
        'New heading\n===========\n\nLanding content.\n', encoding='utf-8'
    )
    app.env.all_docs['landing'] = 0
    app.build()
    landing = (app.outdir / 'landing.html').read_text(encoding='utf-8')
    assert '<title>New heading &#8212; Project &amp; docs</title>' in landing
    assert 'missing_title' not in app.env.longtitles['landing']
    assert app.warning.getvalue() == ''


@pytest.mark.sphinx('html', testroot='_blank', srcdir='titleless-no-label')
def test_titleless_page_without_explicit_toctree_title(app: SphinxTestApp) -> None:
    (app.srcdir / 'index.rst').write_text(
        'Home\n====\n\n.. toctree::\n\n   landing\n', encoding='utf-8'
    )
    (app.srcdir / 'landing.rst').write_text('Landing content.\n', encoding='utf-8')
    app.build()
    assert "doesn't have a title: no link will be generated" in app.warning.getvalue()
