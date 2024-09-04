"""Test the HTML builder and check output against XPath."""

from __future__ import annotations

import os
import posixpath
import re
from typing import TYPE_CHECKING

import pytest

from sphinx.builders.html import validate_html_extra_path, validate_html_static_path
from sphinx.deprecation import RemovedInSphinx90Warning
from sphinx.errors import ConfigError
from sphinx.util.console import strip_colors
from sphinx.util.inventory import InventoryFile

from tests.test_builders.xpath_data import FIGURE_CAPTION
from tests.test_builders.xpath_util import check_xpath

if TYPE_CHECKING:
    from typing import Any


def test_html_sidebars_error(make_app, tmp_path):
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


def test_html4_error(make_app, tmp_path):
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
def test_docutils_output(app, cached_etree_parse, fname, path, check):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check)


@pytest.mark.sphinx(
    'html',
    testroot='root',
    parallel=2,
)
def test_html_parallel(app):
    app.build()


@pytest.mark.sphinx('html', testroot='build-html-translator')
def test_html_translator(app):
    app.build()
    assert app.builder.docwriter.visitor.depart_with_node == 10


@pytest.mark.parametrize(
    'expect',
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
def test_enumerable_node(app, cached_etree_parse, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / 'index.html'), 'index.html', *expect)


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_copy_source': False},
)
def test_html_copy_source(app):
    app.build(force_all=True)
    assert not (app.outdir / '_sources' / 'index.rst.txt').exists()


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_sourcelink_suffix': '.txt'},
)
def test_html_sourcelink_suffix(app):
    app.build(force_all=True)
    assert (app.outdir / '_sources' / 'index.rst.txt').exists()


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_sourcelink_suffix': '.rst'},
)
def test_html_sourcelink_suffix_same(app):
    app.build(force_all=True)
    assert (app.outdir / '_sources' / 'index.rst').exists()


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_sourcelink_suffix': ''},
)
def test_html_sourcelink_suffix_empty(app):
    app.build(force_all=True)
    assert (app.outdir / '_sources' / 'index.rst').exists()


@pytest.mark.sphinx('html', testroot='html_entity')
def test_html_entity(app):
    app.build(force_all=True)
    valid_entities = {'amp', 'lt', 'gt', 'quot', 'apos'}
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    for entity in re.findall(r'&([a-z]+);', content, re.MULTILINE):
        assert entity not in valid_entities


@pytest.mark.sphinx('html', testroot='basic')
def test_html_inventory(app):
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
    assert invdata['std:label']['modindex'] == (
        'Project name not set',
        '',
        'https://www.google.com/py-modindex.html',
        'Module Index',
    )
    assert invdata['std:label']['py-modindex'] == (
        'Project name not set',
        '',
        'https://www.google.com/py-modindex.html',
        'Python Module Index',
    )
    assert invdata['std:label']['genindex'] == (
        'Project name not set',
        '',
        'https://www.google.com/genindex.html',
        'Index',
    )
    assert invdata['std:label']['search'] == (
        'Project name not set',
        '',
        'https://www.google.com/search.html',
        'Search Page',
    )
    assert set(invdata['std:doc'].keys()) == {'index'}
    assert invdata['std:doc']['index'] == (
        'Project name not set',
        '',
        'https://www.google.com/index.html',
        'The basic Sphinx documentation for testing',
    )


@pytest.mark.usefixtures('_http_teapot')
@pytest.mark.sphinx(
    'html',
    testroot='images',
    confoverrides={'html_sourcelink_suffix': ''},
)
def test_html_anchor_for_figure(app):
    app.build(force_all=True)
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<figcaption>\n<p><span class="caption-text">The caption of pic</span>'
        '<a class="headerlink" href="#id1" title="Link to this image">¶</a></p>\n</figcaption>'
    ) in content


@pytest.mark.sphinx('html', testroot='directives-raw')
def test_html_raw_directive(app):
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')

    # standard case
    assert 'standalone raw directive (HTML)' in result
    assert 'standalone raw directive (LaTeX)' not in result

    # with substitution
    assert '<p>HTML: abc def ghi</p>' in result
    assert '<p>LaTeX: abc  ghi</p>' in result


@pytest.mark.parametrize(
    'expect',
    [
        (".//link[@href='_static/persistent.css'][@rel='stylesheet']", '', True),
        (
            ".//link[@href='_static/default.css']"
            "[@rel='stylesheet']"
            "[@title='Default']",
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
            ".//link[@href='_static/more_alternate2.css']"
            "[@rel='alternate stylesheet']",
            '',
            True,
        ),
    ],
)
@pytest.mark.sphinx('html', testroot='stylesheets')
def test_alternate_stylesheets(app, cached_etree_parse, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / 'index.html'), 'index.html', *expect)


@pytest.mark.sphinx('html', testroot='html_style')
def test_html_style(app):
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
def test_html_sidebar(app):
    ctx: dict[str, Any] = {}

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

    app.builder.add_sidebars('index', ctx)
    assert ctx['sidebars'] == [
        'localtoc.html',
        'searchfield.html',
        'sourcelink.html',
    ]

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

    app.builder.add_sidebars('index', ctx)
    assert ctx['sidebars'] == ['sourcelink.html']

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

    app.builder.add_sidebars('index', ctx)
    assert ctx['sidebars'] == []


@pytest.mark.parametrize(
    ('fname', 'expect'),
    [
        ('index.html', (".//h1/em/a[@href='https://example.com/cp.1']", '', True)),
        ('index.html', (".//em/a[@href='https://example.com/man.1']", '', True)),
        ('index.html', (".//em/a[@href='https://example.com/ls.1']", '', True)),
        ('index.html', (".//em/a[@href='https://example.com/sphinx.']", '', True)),
    ],
)
@pytest.mark.sphinx(
    'html',
    testroot='manpage_url',
    confoverrides={'manpages_url': 'https://example.com/{page}.{section}'},
)
@pytest.mark.test_params(shared_result='test_build_html_manpage_url')
def test_html_manpage(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx(
    'html',
    testroot='toctree-glob',
    confoverrides={'html_baseurl': 'https://example.com/'},
)
def test_html_baseurl(app):
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
def test_html_baseurl_and_html_file_suffix(app):
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
def test_validate_html_extra_path(app):
    (app.confdir / '_static').mkdir(parents=True, exist_ok=True)
    app.config.html_extra_path = [
        '/path/to/not_found',    # not found
        '_static',
        app.outdir,              # outdir
        app.outdir / '_static',  # inside outdir
    ]  # fmt: skip
    with pytest.warns(
        RemovedInSphinx90Warning, match='Use "pathlib.Path" or "os.fspath" instead'
    ):
        validate_html_extra_path(app, app.config)
    assert app.config.html_extra_path == ['_static']


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    srcdir='validate_html_static_path',
)
def test_validate_html_static_path(app):
    (app.confdir / '_static').mkdir(parents=True, exist_ok=True)
    app.config.html_static_path = [
        '/path/to/not_found',    # not found
        '_static',
        app.outdir,              # outdir
        app.outdir / '_static',  # inside outdir
    ]  # fmt: skip
    with pytest.warns(
        RemovedInSphinx90Warning, match='Use "pathlib.Path" or "os.fspath" instead'
    ):
        validate_html_static_path(app, app.config)
    assert app.config.html_static_path == ['_static']


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_permalinks': False},
)
def test_html_permalink_disable(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert '<h1>The basic Sphinx documentation for testing</h1>' in content


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_permalinks_icon': '<span>[PERMALINK]</span>'},
)
def test_html_permalink_icon(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert (
        '<h1>The basic Sphinx documentation for testing<a class="headerlink" '
        'href="#the-basic-sphinx-documentation-for-testing" '
        'title="Link to this heading"><span>[PERMALINK]</span></a></h1>'
    ) in content


@pytest.mark.sphinx('html', testroot='html_signaturereturn_icon')
def test_html_signaturereturn_icon(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert '<span class="sig-return-icon">&#x2192;</span>' in content


@pytest.mark.sphinx(
    'html',
    testroot='root',
    srcdir=os.urandom(4).hex(),
)
def test_html_remove_sources_before_write_gh_issue_10786(app):
    # see:  https://github.com/sphinx-doc/sphinx/issues/10786
    target = app.srcdir / 'img.png'

    def handler(app):
        assert target.exists()
        target.unlink()
        return []

    app.connect('html-collect-pages', handler)
    assert target.exists()
    app.build()
    assert not target.exists()

    ws = strip_colors(app.warning.getvalue()).splitlines()
    assert len(ws) >= 1

    file = os.fsdecode(target)
    assert f"WARNING: cannot copy image file '{file}': {file} does not exist" == ws[-1]


@pytest.mark.sphinx(
    'html',
    testroot='domain-py-python_maximum_signature_line_length',
    confoverrides={'python_maximum_signature_line_length': 1},
)
def test_html_pep_695_one_type_per_line(app, cached_etree_parse):
    app.build()
    fname = app.outdir / 'index.html'
    etree = cached_etree_parse(fname)

    class chk:
        def __init__(self, expect: str) -> None:
            self.expect = expect

        def __call__(self, nodes):
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
