"""Test the HTML builder and check output against XPath."""

from __future__ import annotations

import os
import posixpath
import re
from typing import TYPE_CHECKING

import pytest
from docutils import nodes
from docutils.parsers import rst
from docutils.readers import standalone
from docutils.writers import html5_polyglot

from sphinx import addnodes
from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.builders.html import (
    StandaloneHTMLBuilder,
    validate_html_extra_path,
    validate_html_static_path,
)
from sphinx.errors import ConfigError
from sphinx.testing.util import etree_parse
from sphinx.util.docutils import _get_settings, new_document
from sphinx.util.inventory import InventoryFile, _InventoryItem
from sphinx.writers.html5 import HTML5Translator

from tests.test_builders.xpath_data import FIGURE_CAPTION
from tests.test_builders.xpath_util import check_xpath

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path
    from typing import Any
    from xml.etree.ElementTree import Element, ElementTree

    from sphinx.testing.util import SphinxTestApp


def test_html_sidebars_error(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    (tmp_path / 'conf.py').touch()
    with pytest.raises(
        ConfigError,
        match="Values in 'html_sidebars' must be a list of strings. "
        "At least one pattern has a string value: 'index'. "
        r"Change to `html_sidebars = \{'index': \['searchbox.html'\]\}`.",
    ):
        make_app(
            'html',
            srcdir=tmp_path,
            confoverrides={'html_sidebars': {'index': 'searchbox.html'}},
        )


def test_html4_error(make_app: Callable[..., SphinxTestApp], tmp_path: Path) -> None:
    (tmp_path / 'conf.py').touch()
    with pytest.raises(
        ConfigError,
        match='HTML 4 is no longer supported by Sphinx',
    ):
        make_app(
            'html',
            srcdir=tmp_path,
            confoverrides={'html4_writer': True},
        )


@pytest.mark.parametrize(
    ('fname', 'path', 'check'),
    [
        ('index.html', ".//div[@class='citation']/span", r'Ref1'),
        ('index.html', ".//div[@class='citation']/span", r'Ref_1'),
        (
            'footnote.html',
            ".//a[@class='footnote-reference brackets'][@href='#id9'][@id='id1']",
            r'1',
        ),
        (
            'footnote.html',
            ".//a[@class='footnote-reference brackets'][@href='#id10'][@id='id2']",
            r'2',
        ),
        (
            'footnote.html',
            ".//a[@class='footnote-reference brackets'][@href='#foo'][@id='id3']",
            r'3',
        ),
        (
            'footnote.html',
            ".//a[@class='reference internal'][@href='#bar'][@id='id4']/span",
            r'\[bar\]',
        ),
        (
            'footnote.html',
            ".//a[@class='reference internal'][@href='#baz-qux'][@id='id5']/span",
            r'\[baz_qux\]',
        ),
        (
            'footnote.html',
            ".//a[@class='footnote-reference brackets'][@href='#id11'][@id='id6']",
            r'4',
        ),
        (
            'footnote.html',
            ".//a[@class='footnote-reference brackets'][@href='#id12'][@id='id7']",
            r'5',
        ),
        (
            'footnote.html',
            ".//aside[@class='footnote brackets']/span/a[@href='#id1']",
            r'1',
        ),
        (
            'footnote.html',
            ".//aside[@class='footnote brackets']/span/a[@href='#id2']",
            r'2',
        ),
        (
            'footnote.html',
            ".//aside[@class='footnote brackets']/span/a[@href='#id3']",
            r'3',
        ),
        ('footnote.html', ".//div[@class='citation']/span/a[@href='#id4']", r'bar'),
        ('footnote.html', ".//div[@class='citation']/span/a[@href='#id5']", r'baz_qux'),
        (
            'footnote.html',
            ".//aside[@class='footnote brackets']/span/a[@href='#id6']",
            r'4',
        ),
        (
            'footnote.html',
            ".//aside[@class='footnote brackets']/span/a[@href='#id7']",
            r'5',
        ),
        (
            'footnote.html',
            ".//aside[@class='footnote brackets']/span/a[@href='#id8']",
            r'6',
        ),
    ],
)
@pytest.mark.sphinx('html', testroot='root')
@pytest.mark.test_params(shared_result='test_build_html_output_docutils18')
def test_docutils_output(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    fname: str,
    path: str,
    check: str,
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check)


@pytest.mark.sphinx(
    'html',
    testroot='root',
    parallel=2,
)
def test_html_parallel(app: SphinxTestApp) -> None:
    app.build()


class ConfHTMLTranslator(HTML5Translator):
    depart_with_node = 0

    def depart_admonition(self, node: nodes.Element | None = None) -> None:
        if node is not None:
            self.depart_with_node += 1
        super().depart_admonition(node)


@pytest.mark.sphinx('html', testroot='_blank')
def test_html_translator(app: SphinxTestApp) -> None:
    settings = _get_settings(
        standalone.Reader, rst.Parser, html5_polyglot.Writer, defaults={}
    )
    doctree = new_document(__file__, settings)
    doctree.append(addnodes.seealso('test', nodes.Text('test')))
    doctree.append(nodes.note('test', nodes.Text('test')))
    doctree.append(nodes.warning('test', nodes.Text('test')))
    doctree.append(nodes.attention('test', nodes.Text('test')))
    doctree.append(nodes.caution('test', nodes.Text('test')))
    doctree.append(nodes.danger('test', nodes.Text('test')))
    doctree.append(nodes.error('test', nodes.Text('test')))
    doctree.append(nodes.hint('test', nodes.Text('test')))
    doctree.append(nodes.important('test', nodes.Text('test')))
    doctree.append(nodes.tip('test', nodes.Text('test')))

    visitor = ConfHTMLTranslator(doctree, app.builder)
    assert isinstance(visitor, ConfHTMLTranslator)
    assert isinstance(visitor, HTML5Translator)
    doctree.walkabout(visitor)

    assert visitor.depart_with_node == 10


@pytest.mark.parametrize(
    ('path', 'check', 'be_found'),
    [
        (FIGURE_CAPTION + "//span[@class='caption-number']", 'Fig. 1', True),
        (FIGURE_CAPTION + "//span[@class='caption-number']", 'Fig. 2', True),
        (FIGURE_CAPTION + "//span[@class='caption-number']", 'Fig. 3', True),
        (".//div//span[@class='caption-number']", 'No.1 ', True),
        (".//div//span[@class='caption-number']", 'No.2 ', True),
        ('.//li/p/a/span', 'Fig. 1', True),
        ('.//li/p/a/span', 'Fig. 2', True),
        ('.//li/p/a/span', 'Fig. 3', True),
        ('.//li/p/a/span', 'No.1', True),
        ('.//li/p/a/span', 'No.2', True),
    ],
)
@pytest.mark.sphinx(
    'html',
    testroot='add_enumerable_node',
    srcdir='test_enumerable_node',
)
def test_enumerable_node(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    path: str,
    check: str,
    be_found: bool,
) -> None:
    app.build()
    check_xpath(
        cached_etree_parse(app.outdir / 'index.html'),
        'index.html',
        path,
        check,
        be_found,
    )


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_copy_source': False},
)
def test_html_copy_source(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert not (app.outdir / '_sources' / 'index.rst.txt').exists()


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_sourcelink_suffix': '.txt'},
)
def test_html_sourcelink_suffix(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert (app.outdir / '_sources' / 'index.rst.txt').exists()


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_sourcelink_suffix': '.rst'},
)
def test_html_sourcelink_suffix_same(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert (app.outdir / '_sources' / 'index.rst').exists()


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_sourcelink_suffix': ''},
)
def test_html_sourcelink_suffix_empty(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert (app.outdir / '_sources' / 'index.rst').exists()


@pytest.mark.sphinx('html', testroot='html_entity')
def test_html_entity(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    valid_entities = {'amp', 'lt', 'gt', 'quot', 'apos'}
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    for entity in re.findall(r'&([a-z]+);', content, re.MULTILINE):
        assert entity not in valid_entities


@pytest.mark.sphinx('html', testroot='basic')
def test_html_inventory(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    with app.outdir.joinpath('objects.inv').open('rb') as f:
        invdata = InventoryFile.load(f, 'https://www.google.com', posixpath.join)

    assert set(invdata.keys()) == {'std:label', 'std:doc'}
    assert set(invdata['std:label'].keys()) == {
        'modindex',
        'py-modindex',
        'genindex',
        'search',
    }
    assert invdata['std:label']['modindex'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='https://www.google.com/py-modindex.html',
        display_name='Module Index',
    )
    assert invdata['std:label']['py-modindex'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='https://www.google.com/py-modindex.html',
        display_name='Python Module Index',
    )
    assert invdata['std:label']['genindex'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='https://www.google.com/genindex.html',
        display_name='Index',
    )
    assert invdata['std:label']['search'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='https://www.google.com/search.html',
        display_name='Search Page',
    )
    assert set(invdata['std:doc'].keys()) == {'index'}
    assert invdata['std:doc']['index'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='https://www.google.com/index.html',
        display_name='The basic Sphinx documentation for testing',
    )


@pytest.mark.usefixtures('_http_teapot')
@pytest.mark.sphinx(
    'html',
    testroot='images',
    confoverrides={'html_sourcelink_suffix': ''},
)
def test_html_anchor_for_figure(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<figcaption>\n<p><span class="caption-text">The caption of pic</span>'
        '<a class="headerlink" href="#id1" title="Link to this image">¶</a></p>\n</figcaption>'
    ) in content


@pytest.mark.sphinx('html', testroot='directives-raw')
def test_html_raw_directive(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')

    # standard case
    assert 'standalone raw directive (HTML)' in result
    assert 'standalone raw directive (LaTeX)' not in result

    # with substitution
    assert '<p>HTML: abc def ghi</p>' in result
    assert '<p>LaTeX: abc  ghi</p>' in result


@pytest.mark.parametrize(
    ('path', 'check', 'be_found'),
    [
        (".//link[@href='_static/persistent.css'][@rel='stylesheet']", '', True),
        (
            ".//link[@href='_static/default.css'][@rel='stylesheet'][@title='Default']",
            '',
            True,
        ),
        (
            ".//link[@href='_static/alternate1.css']"
            "[@rel='alternate stylesheet']"
            "[@title='Alternate']",
            '',
            True,
        ),
        (
            ".//link[@href='_static/alternate2.css'][@rel='alternate stylesheet']",
            '',
            True,
        ),
        (
            ".//link[@href='_static/more_persistent.css'][@rel='stylesheet']",
            '',
            True,
        ),
        (
            ".//link[@href='_static/more_default.css']"
            "[@rel='stylesheet']"
            "[@title='Default']",
            '',
            True,
        ),
        (
            ".//link[@href='_static/more_alternate1.css']"
            "[@rel='alternate stylesheet']"
            "[@title='Alternate']",
            '',
            True,
        ),
        (
            ".//link[@href='_static/more_alternate2.css'][@rel='alternate stylesheet']",
            '',
            True,
        ),
    ],
)
@pytest.mark.sphinx('html', testroot='stylesheets')
def test_alternate_stylesheets(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    path: str,
    check: str,
    be_found: bool,
) -> None:
    app.build()
    check_xpath(
        cached_etree_parse(app.outdir / 'index.html'),
        'index.html',
        path,
        check,
        be_found,
    )


@pytest.mark.sphinx('html', testroot='html_style')
def test_html_style(app: SphinxTestApp) -> None:
    app.build()
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<link rel="stylesheet" type="text/css" href="_static/default.css" />'
    ) in result
    assert (
        '<link rel="stylesheet" type="text/css" href="_static/alabaster.css" />'
    ) not in result


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={
        'html_sidebars': {
            '**': [
                'localtoc.html',
                'searchfield.html',
                'sourcelink.html',
            ]
        }
    },
)
def test_html_sidebar(app: SphinxTestApp) -> None:
    # default for alabaster
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    # layout.html
    assert '<div class="sphinxsidebar" role="navigation" aria-label="Main">' in result
    assert '<h1>The basic Sphinx documentation for testing' in result
    assert '<h3>Navigation</h3>' in result
    # localtoc.html
    assert '<h3><a href="#">Table of Contents</a></h3>' in result
    # searchfield.html
    assert '<div class="searchformwrapper">' in result
    # sourcelink.html
    assert '<h3>This Page</h3>' in result

    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    sidebars = app.builder._get_sidebars('index')
    assert sidebars == (
        'localtoc.html',
        'searchfield.html',
        'sourcelink.html',
    )

    # only sourcelink.html
    app.config.html_sidebars = {'**': ['sourcelink.html']}
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    # layout.html
    assert '<div class="sphinxsidebar" role="navigation" aria-label="Main">' in result
    assert '<h1>The basic Sphinx documentation for testing' in result
    assert '<h3>Navigation</h3>' in result
    # localtoc.html
    assert '<h3><a href="#">Table of Contents</a></h3>' not in result
    # searchfield.html
    assert '<div class="searchformwrapper">' not in result
    # sourcelink.html
    assert '<h3>This Page</h3>' in result

    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    sidebars = app.builder._get_sidebars('index')
    assert sidebars == ('sourcelink.html',)

    # no sidebars
    app.config.html_sidebars = {'**': []}
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    # layout.html
    assert (
        '<div class="sphinxsidebar" role="navigation" aria-label="Main">'
    ) not in result
    assert '<h1>The basic Sphinx documentation for testing' in result
    assert '<h3>Navigation</h3>' in result
    # localtoc.html
    assert '<h3><a href="#">Table of Contents</a></h3>' not in result
    # searchfield.html
    assert '<div class="searchformwrapper">' not in result
    # sourcelink.html
    assert '<h3>This Page</h3>' not in result

    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    sidebars = app.builder._get_sidebars('index')
    assert sidebars == ()


@pytest.mark.parametrize(
    ('fname', 'path', 'check', 'be_found'),
    [
        ('index.html', ".//h1/em/a[@href='https://example.com/cp.1']", '', True),
        ('index.html', ".//em/a[@href='https://example.com/man.1']", '', True),
        ('index.html', ".//em/a[@href='https://example.com/ls.1']", '', True),
        ('index.html', ".//em/a[@href='https://example.com/sphinx.']", '', True),
    ],
)
@pytest.mark.sphinx(
    'html',
    testroot='manpage_url',
    confoverrides={'manpages_url': 'https://example.com/{page}.{section}'},
)
@pytest.mark.test_params(shared_result='test_build_html_manpage_url')
def test_html_manpage(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    fname: str,
    path: str,
    check: str,
    be_found: bool,
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check, be_found)


@pytest.mark.sphinx(
    'html',
    testroot='toctree-glob',
    confoverrides={'html_baseurl': 'https://example.com/'},
)
def test_html_baseurl(app: SphinxTestApp) -> None:
    app.build()

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<link rel="canonical" href="https://example.com/index.html" />' in result

    result = (app.outdir / 'qux' / 'index.html').read_text(encoding='utf8')
    assert (
        '<link rel="canonical" href="https://example.com/qux/index.html" />'
    ) in result


@pytest.mark.sphinx(
    'html',
    testroot='toctree-glob',
    confoverrides={
        'html_baseurl': 'https://example.com/subdir',
        'html_file_suffix': '.htm',
    },
)
def test_html_baseurl_and_html_file_suffix(app: SphinxTestApp) -> None:
    app.build()

    result = (app.outdir / 'index.htm').read_text(encoding='utf8')
    assert (
        '<link rel="canonical" href="https://example.com/subdir/index.htm" />'
    ) in result

    result = (app.outdir / 'qux' / 'index.htm').read_text(encoding='utf8')
    assert (
        '<link rel="canonical" href="https://example.com/subdir/qux/index.htm" />'
    ) in result


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    srcdir='validate_html_extra_path',
)
def test_validate_html_extra_path(app: SphinxTestApp) -> None:
    (app.confdir / '_static').mkdir(parents=True, exist_ok=True)
    app.config.html_extra_path = [
        '/path/to/not_found',    # not found
        '_static',
        app.outdir,              # outdir
        app.outdir / '_static',  # inside outdir
    ]  # fmt: skip

    validate_html_extra_path(app, app.config)
    assert app.config.html_extra_path == ['_static']

    warnings = strip_escape_sequences(app.warning.getvalue()).splitlines()
    assert "html_extra_path entry '/path/to/not_found' does not exist" in warnings[0]
    assert warnings[1].endswith(' is placed inside outdir')
    assert warnings[2].endswith(' does not exist')
    assert len(warnings) == 3


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    srcdir='validate_html_static_path',
)
def test_validate_html_static_path(app: SphinxTestApp) -> None:
    (app.confdir / '_static').mkdir(parents=True, exist_ok=True)
    app.config.html_static_path = [
        '/path/to/not_found',    # not found
        '_static',
        app.outdir,              # outdir
        app.outdir / '_static',  # inside outdir
    ]  # fmt: skip

    validate_html_static_path(app, app.config)
    assert app.config.html_static_path == ['_static']

    warnings = strip_escape_sequences(app.warning.getvalue()).splitlines()
    assert "html_static_path entry '/path/to/not_found' does not exist" in warnings[0]
    assert warnings[1].endswith(' is placed inside outdir')
    assert warnings[2].endswith(' does not exist')
    assert len(warnings) == 3


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_permalinks': False},
)
def test_html_permalink_disable(app: SphinxTestApp) -> None:
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert '<h1>The basic Sphinx documentation for testing</h1>' in content


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_permalinks_icon': '<span>[PERMALINK]</span>'},
)
def test_html_permalink_icon(app: SphinxTestApp) -> None:
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert (
        '<h1>The basic Sphinx documentation for testing<a class="headerlink" '
        'href="#the-basic-sphinx-documentation-for-testing" '
        'title="Link to this heading"><span>[PERMALINK]</span></a></h1>'
    ) in content


@pytest.mark.sphinx('html', testroot='html_signaturereturn_icon')
def test_html_signaturereturn_icon(app: SphinxTestApp) -> None:
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert '<span class="sig-return-icon">&#x2192;</span>' in content


@pytest.mark.sphinx(
    'html',
    testroot='root',
    srcdir=os.urandom(4).hex(),
)
def test_html_remove_sources_before_write_gh_issue_10786(app: SphinxTestApp) -> None:
    # See: https://github.com/sphinx-doc/sphinx/issues/10786
    target = app.srcdir / 'img.png'

    def handler(app: SphinxTestApp) -> list[tuple[str, dict[str, Any], str]]:
        assert target.exists()
        target.unlink()
        return []

    app.connect('html-collect-pages', handler)
    assert target.exists()
    app.build()
    assert not target.exists()

    ws = strip_escape_sequences(app.warning.getvalue()).splitlines()
    assert len(ws) >= 1

    file = os.fsdecode(target)
    assert f"WARNING: cannot copy image file '{file}': {file} does not exist" == ws[-1]


@pytest.mark.sphinx(
    'html',
    testroot='domain-py-python_maximum_signature_line_length',
    confoverrides={'python_maximum_signature_line_length': 1},
)
def test_html_pep_695_one_type_per_line(
    app: SphinxTestApp, cached_etree_parse: Callable[[Path], ElementTree]
) -> None:
    app.build()
    fname = app.outdir / 'index.html'
    etree = cached_etree_parse(fname)

    class chk:
        def __init__(self, expect: str) -> None:
            self.expect = expect

        def __call__(self, nodes: Sequence[Element]) -> None:
            assert len(nodes) == 1, nodes
            objnode = ''.join(nodes[0].itertext()).replace('\n\n', '')
            objnode = objnode.rstrip(chr(182))  # remove '¶' symbol
            objnode = objnode.strip('\n')  # remove surrounding new lines
            assert objnode == self.expect

    # each signature has a dangling ',' at the end of its parameters lists
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="generic_foo"][1]',
        chk('generic_foo[\nT,\n]()'),
    )
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="generic_bar"][1]',
        chk('generic_bar[\nT,\n](\nx: list[T],\n)'),
    )
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="generic_ret"][1]',
        chk('generic_ret[\nR,\n]() → R'),
    )
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="MyGenericClass"][1]',
        chk('class MyGenericClass[\nX,\n]'),
    )
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="MyList"][1]',
        chk('class MyList[\nT,\n](list[T])'),
    )


@pytest.mark.sphinx(
    'html',
    testroot='domain-py-python_maximum_signature_line_length',
    confoverrides={
        'python_maximum_signature_line_length': 1,
        'python_trailing_comma_in_multi_line_signatures': False,
    },
)
def test_html_pep_695_trailing_comma_in_multi_line_signatures(
    app: SphinxTestApp,
) -> None:
    app.build()
    fname = app.outdir / 'index.html'
    etree = etree_parse(fname)

    class chk:
        def __init__(self, expect: str) -> None:
            self.expect = expect

        def __call__(self, nodes: Sequence[Element]) -> None:
            assert len(nodes) == 1, nodes
            objnode = ''.join(nodes[0].itertext()).replace('\n\n', '')
            objnode = objnode.rstrip(chr(182))  # remove '¶' symbol
            objnode = objnode.strip('\n')  # remove surrounding new lines
            assert objnode == self.expect

    # each signature has a dangling ',' at the end of its parameters lists
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="generic_foo"][1]',
        chk('generic_foo[\nT\n]()'),
    )
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="generic_bar"][1]',
        chk('generic_bar[\nT\n](\nx: list[T]\n)'),
    )
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="generic_ret"][1]',
        chk('generic_ret[\nR\n]() → R'),
    )
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="MyGenericClass"][1]',
        chk('class MyGenericClass[\nX\n]'),
    )
    check_xpath(
        etree,
        fname,
        r'.//dt[@id="MyList"][1]',
        chk('class MyList[\nT\n](list[T])'),
    )


@pytest.mark.sphinx('html', testroot='directives-admonition-collapse')
def test_html_admonition_collapse(app: SphinxTestApp) -> None:
    app.build()
    fname = app.outdir / 'index.html'
    etree = etree_parse(fname)

    def _create_check(text: str, open: bool) -> Callable[[Sequence[Element]], None]:
        def _check(els: Sequence[Element]) -> None:
            assert len(els) == 1
            el = els[0]
            if open:
                assert el.attrib['open'] == 'open'
            else:
                assert 'open' not in el.attrib
            p = el.find('p')
            assert p is not None
            assert p.text == text

        return _check

    check_xpath(
        etree,
        fname,
        r'.//div[@class="standard admonition note"]//p',
        'This is a standard note.',
    )
    check_xpath(
        etree,
        fname,
        r'.//details[@class="admonition note"]',
        _create_check('This note is collapsible, and initially open by default.', True),
    )
    check_xpath(
        etree,
        fname,
        r'.//details[@class="admonition-example admonition"]',
        _create_check('This example is collapsible, and initially open.', True),
    )
    check_xpath(
        etree,
        fname,
        r'.//details[@class="admonition hint"]',
        _create_check('This hint is collapsible, but initially closed.', False),
    )
