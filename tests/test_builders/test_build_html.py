"""Test the HTML builder and check output against XPath."""

import os
import posixpath
import re

import pytest

from sphinx.builders.html import validate_html_extra_path, validate_html_static_path
from sphinx.errors import ConfigError
from sphinx.testing.util import strip_escseq
from sphinx.util.inventory import InventoryFile

FIGURE_CAPTION = ".//figure/figcaption/p"


ENV_WARNINGS = """\
{root}/autodoc_fodder.py:docstring of autodoc_fodder.MarkupError:\\d+: \
WARNING: Explicit markup ends without a blank line; unexpected unindent.
{root}/index.rst:\\d+: WARNING: Encoding 'utf-8-sig' used for reading included \
file '{root}/wrongenc.inc' seems to be wrong, try giving an :encoding: option
{root}/index.rst:\\d+: WARNING: invalid single index entry ''
{root}/index.rst:\\d+: WARNING: image file not readable: foo.png
{root}/index.rst:\\d+: WARNING: download file not readable: {root}/nonexisting.png
{root}/undecodable.rst:\\d+: WARNING: undecodable source characters, replacing \
with "\\?": b?'here: >>>(\\\\|/)xbb<<<((\\\\|/)r)?'
"""

HTML_WARNINGS = ENV_WARNINGS + """\
{root}/index.rst:\\d+: WARNING: unknown option: '&option'
{root}/index.rst:\\d+: WARNING: citation not found: missing
{root}/index.rst:\\d+: WARNING: a suitable image for html builder not found: foo.\\*
{root}/index.rst:\\d+: WARNING: Lexing literal_block ".*" as "c" resulted in an error at token: ".*". Retrying in relaxed mode.
"""


def check_xpath(etree, fname, path, check, be_found=True):
    nodes = list(etree.findall(path))
    if check is None:
        assert nodes == [], ('found any nodes matching xpath '
                             f'{path!r} in file {fname}')
        return
    else:
        assert nodes != [], ('did not find any node matching xpath '
                             f'{path!r} in file {fname}')
    if callable(check):
        check(nodes)
    elif not check:
        # only check for node presence
        pass
    else:
        def get_text(node):
            if node.text is not None:
                # the node has only one text
                return node.text
            else:
                # the node has tags and text; gather texts just under the node
                return ''.join(n.tail or '' for n in node)

        rex = re.compile(check)
        if be_found:
            if any(rex.search(get_text(node)) for node in nodes):
                return
        else:
            if all(not rex.search(get_text(node)) for node in nodes):
                return

        msg = (f'{check!r} not found in any node matching '
               f'{path!r} in file {fname}: {[node.text for node in nodes]!r}')
        raise AssertionError(msg)


@pytest.mark.sphinx('html', testroot='warnings', freshenv=True)
def test_html_warnings(app, warning):
    app.build(force_all=True)
    warnings = strip_escseq(re.sub(re.escape(os.sep) + '{1,2}', '/', warning.getvalue()))
    warnings_exp = HTML_WARNINGS.format(root=re.escape(app.srcdir.as_posix()))
    assert re.match(warnings_exp + '$', warnings), (
        "Warnings don't match:\n"
        + f'--- Expected (regex):\n{warnings_exp}\n'
        + f'--- Got:\n{warnings}'
    )


def test_html4_error(make_app, tmp_path):
    (tmp_path / 'conf.py').write_text('', encoding='utf-8')
    with pytest.raises(
        ConfigError,
        match='HTML 4 is no longer supported by Sphinx',
    ):
        make_app(
            buildername='html',
            srcdir=tmp_path,
            confoverrides={'html4_writer': True},
        )


@pytest.mark.parametrize(("fname", "path", "check"), [
    ('index.html', ".//div[@class='citation']/span", r'Ref1'),
    ('index.html', ".//div[@class='citation']/span", r'Ref_1'),

    ('footnote.html', ".//a[@class='footnote-reference brackets'][@href='#id9'][@id='id1']", r"1"),
    ('footnote.html', ".//a[@class='footnote-reference brackets'][@href='#id10'][@id='id2']", r"2"),
    ('footnote.html', ".//a[@class='footnote-reference brackets'][@href='#foo'][@id='id3']", r"3"),
    ('footnote.html', ".//a[@class='reference internal'][@href='#bar'][@id='id4']/span", r"\[bar\]"),
    ('footnote.html', ".//a[@class='reference internal'][@href='#baz-qux'][@id='id5']/span", r"\[baz_qux\]"),
    ('footnote.html', ".//a[@class='footnote-reference brackets'][@href='#id11'][@id='id6']", r"4"),
    ('footnote.html', ".//a[@class='footnote-reference brackets'][@href='#id12'][@id='id7']", r"5"),
    ('footnote.html', ".//aside[@class='footnote brackets']/span/a[@href='#id1']", r"1"),
    ('footnote.html', ".//aside[@class='footnote brackets']/span/a[@href='#id2']", r"2"),
    ('footnote.html', ".//aside[@class='footnote brackets']/span/a[@href='#id3']", r"3"),
    ('footnote.html', ".//div[@class='citation']/span/a[@href='#id4']", r"bar"),
    ('footnote.html', ".//div[@class='citation']/span/a[@href='#id5']", r"baz_qux"),
    ('footnote.html', ".//aside[@class='footnote brackets']/span/a[@href='#id6']", r"4"),
    ('footnote.html', ".//aside[@class='footnote brackets']/span/a[@href='#id7']", r"5"),
    ('footnote.html', ".//aside[@class='footnote brackets']/span/a[@href='#id8']", r"6"),
])
@pytest.mark.sphinx('html')
@pytest.mark.test_params(shared_result='test_build_html_output_docutils18')
def test_docutils_output(app, cached_etree_parse, fname, path, check):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check)


@pytest.mark.sphinx('html', parallel=2)
def test_html_parallel(app):
    app.build()


@pytest.mark.sphinx('html', testroot='build-html-translator')
def test_html_translator(app):
    app.build()
    assert app.builder.docwriter.visitor.depart_with_node == 10


@pytest.mark.parametrize("expect", [
    (FIGURE_CAPTION + "//span[@class='caption-number']", "Fig. 1", True),
    (FIGURE_CAPTION + "//span[@class='caption-number']", "Fig. 2", True),
    (FIGURE_CAPTION + "//span[@class='caption-number']", "Fig. 3", True),
    (".//div//span[@class='caption-number']", "No.1 ", True),
    (".//div//span[@class='caption-number']", "No.2 ", True),
    (".//li/p/a/span", 'Fig. 1', True),
    (".//li/p/a/span", 'Fig. 2', True),
    (".//li/p/a/span", 'Fig. 3', True),
    (".//li/p/a/span", 'No.1', True),
    (".//li/p/a/span", 'No.2', True),
])
@pytest.mark.sphinx('html', testroot='add_enumerable_node',
                    srcdir='test_enumerable_node')
def test_enumerable_node(app, cached_etree_parse, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / 'index.html'), 'index.html', *expect)


@pytest.mark.sphinx('html', testroot='basic', confoverrides={'html_copy_source': False})
def test_html_copy_source(app):
    app.build(force_all=True)
    assert not (app.outdir / '_sources' / 'index.rst.txt').exists()


@pytest.mark.sphinx('html', testroot='basic', confoverrides={'html_sourcelink_suffix': '.txt'})
def test_html_sourcelink_suffix(app):
    app.build(force_all=True)
    assert (app.outdir / '_sources' / 'index.rst.txt').exists()


@pytest.mark.sphinx('html', testroot='basic', confoverrides={'html_sourcelink_suffix': '.rst'})
def test_html_sourcelink_suffix_same(app):
    app.build(force_all=True)
    assert (app.outdir / '_sources' / 'index.rst').exists()


@pytest.mark.sphinx('html', testroot='basic', confoverrides={'html_sourcelink_suffix': ''})
def test_html_sourcelink_suffix_empty(app):
    app.build(force_all=True)
    assert (app.outdir / '_sources' / 'index.rst').exists()


@pytest.mark.sphinx('html', testroot='html_entity')
def test_html_entity(app):
    app.build(force_all=True)
    valid_entities = {'amp', 'lt', 'gt', 'quot', 'apos'}
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    for entity in re.findall(r'&([a-z]+);', content, re.M):
        assert entity not in valid_entities


@pytest.mark.sphinx('html', testroot='basic')
def test_html_inventory(app):
    app.build(force_all=True)

    with app.outdir.joinpath('objects.inv').open('rb') as f:
        invdata = InventoryFile.load(f, 'https://www.google.com', posixpath.join)

    assert set(invdata.keys()) == {'std:label', 'std:doc'}
    assert set(invdata['std:label'].keys()) == {'modindex',
                                                'py-modindex',
                                                'genindex',
                                                'search'}
    assert invdata['std:label']['modindex'] == ('Python',
                                                '',
                                                'https://www.google.com/py-modindex.html',
                                                'Module Index')
    assert invdata['std:label']['py-modindex'] == ('Python',
                                                   '',
                                                   'https://www.google.com/py-modindex.html',
                                                   'Python Module Index')
    assert invdata['std:label']['genindex'] == ('Python',
                                                '',
                                                'https://www.google.com/genindex.html',
                                                'Index')
    assert invdata['std:label']['search'] == ('Python',
                                              '',
                                              'https://www.google.com/search.html',
                                              'Search Page')
    assert set(invdata['std:doc'].keys()) == {'index'}
    assert invdata['std:doc']['index'] == ('Python',
                                           '',
                                           'https://www.google.com/index.html',
                                           'The basic Sphinx documentation for testing')


@pytest.mark.sphinx('html', testroot='images', confoverrides={'html_sourcelink_suffix': ''})
def test_html_anchor_for_figure(app):
    app.build(force_all=True)
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert ('<figcaption>\n<p><span class="caption-text">The caption of pic</span>'
            '<a class="headerlink" href="#id1" title="Link to this image">¶</a></p>\n</figcaption>'
            in content)


@pytest.mark.sphinx('html', testroot='directives-raw')
def test_html_raw_directive(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')

    # standard case
    assert 'standalone raw directive (HTML)' in result
    assert 'standalone raw directive (LaTeX)' not in result

    # with substitution
    assert '<p>HTML: abc def ghi</p>' in result
    assert '<p>LaTeX: abc  ghi</p>' in result


@pytest.mark.parametrize("expect", [
    (".//link[@href='_static/persistent.css']"
     "[@rel='stylesheet']", '', True),
    (".//link[@href='_static/default.css']"
     "[@rel='stylesheet']"
     "[@title='Default']", '', True),
    (".//link[@href='_static/alternate1.css']"
     "[@rel='alternate stylesheet']"
     "[@title='Alternate']", '', True),
    (".//link[@href='_static/alternate2.css']"
     "[@rel='alternate stylesheet']", '', True),
    (".//link[@href='_static/more_persistent.css']"
     "[@rel='stylesheet']", '', True),
    (".//link[@href='_static/more_default.css']"
     "[@rel='stylesheet']"
     "[@title='Default']", '', True),
    (".//link[@href='_static/more_alternate1.css']"
     "[@rel='alternate stylesheet']"
     "[@title='Alternate']", '', True),
    (".//link[@href='_static/more_alternate2.css']"
     "[@rel='alternate stylesheet']", '', True),
])
@pytest.mark.sphinx('html', testroot='stylesheets')
def test_alternate_stylesheets(app, cached_etree_parse, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / 'index.html'), 'index.html', *expect)


@pytest.mark.sphinx('html', testroot='html_style')
def test_html_style(app, status, warning):
    app.build()
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<link rel="stylesheet" type="text/css" href="_static/default.css" />' in result
    assert ('<link rel="stylesheet" type="text/css" href="_static/alabaster.css" />'
            not in result)


@pytest.mark.sphinx('html', testroot='basic')
def test_html_sidebar(app, status, warning):
    ctx = {}

    # default for alabaster
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert ('<div class="sphinxsidebar" role="navigation" '
            'aria-label="main navigation">' in result)
    assert '<h1 class="logo"><a href="#">Python</a></h1>' in result
    assert '<h3>Navigation</h3>' in result
    assert '<h3>Related Topics</h3>' in result
    assert '<h3 id="searchlabel">Quick search</h3>' in result

    app.builder.add_sidebars('index', ctx)
    assert ctx['sidebars'] == ['about.html', 'navigation.html', 'relations.html',
                               'searchbox.html', 'donate.html']

    # only relations.html
    app.config.html_sidebars = {'**': ['relations.html']}
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert ('<div class="sphinxsidebar" role="navigation" '
            'aria-label="main navigation">' in result)
    assert '<h1 class="logo"><a href="#">Python</a></h1>' not in result
    assert '<h3>Navigation</h3>' not in result
    assert '<h3>Related Topics</h3>' in result
    assert '<h3 id="searchlabel">Quick search</h3>' not in result

    app.builder.add_sidebars('index', ctx)
    assert ctx['sidebars'] == ['relations.html']

    # no sidebars
    app.config.html_sidebars = {'**': []}
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert ('<div class="sphinxsidebar" role="navigation" '
            'aria-label="main navigation">' not in result)
    assert '<h1 class="logo"><a href="#">Python</a></h1>' not in result
    assert '<h3>Navigation</h3>' not in result
    assert '<h3>Related Topics</h3>' not in result
    assert '<h3 id="searchlabel">Quick search</h3>' not in result

    app.builder.add_sidebars('index', ctx)
    assert ctx['sidebars'] == []


@pytest.mark.sphinx('html', testroot='toctree-glob',
                    confoverrides={'html_baseurl': 'https://example.com/'})
def test_html_baseurl(app, status, warning):
    app.build()

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<link rel="canonical" href="https://example.com/index.html" />' in result

    result = (app.outdir / 'qux' / 'index.html').read_text(encoding='utf8')
    assert '<link rel="canonical" href="https://example.com/qux/index.html" />' in result


@pytest.mark.sphinx('html', testroot='toctree-glob',
                    confoverrides={'html_baseurl': 'https://example.com/subdir',
                                   'html_file_suffix': '.htm'})
def test_html_baseurl_and_html_file_suffix(app, status, warning):
    app.build()

    result = (app.outdir / 'index.htm').read_text(encoding='utf8')
    assert '<link rel="canonical" href="https://example.com/subdir/index.htm" />' in result

    result = (app.outdir / 'qux' / 'index.htm').read_text(encoding='utf8')
    assert '<link rel="canonical" href="https://example.com/subdir/qux/index.htm" />' in result


@pytest.mark.sphinx(testroot='basic', srcdir='validate_html_extra_path')
def test_validate_html_extra_path(app):
    (app.confdir / '_static').mkdir(parents=True, exist_ok=True)
    app.config.html_extra_path = [
        '/path/to/not_found',       # not found
        '_static',
        app.outdir,                 # outdir
        app.outdir / '_static',     # inside outdir
    ]
    validate_html_extra_path(app, app.config)
    assert app.config.html_extra_path == ['_static']


@pytest.mark.sphinx(testroot='basic', srcdir='validate_html_static_path')
def test_validate_html_static_path(app):
    (app.confdir / '_static').mkdir(parents=True, exist_ok=True)
    app.config.html_static_path = [
        '/path/to/not_found',       # not found
        '_static',
        app.outdir,                 # outdir
        app.outdir / '_static',     # inside outdir
    ]
    validate_html_static_path(app, app.config)
    assert app.config.html_static_path == ['_static']


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'html_permalinks': False})
def test_html_permalink_disable(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert '<h1>The basic Sphinx documentation for testing</h1>' in content


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'html_permalinks_icon': '<span>[PERMALINK]</span>'})
def test_html_permalink_icon(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert ('<h1>The basic Sphinx documentation for testing<a class="headerlink" '
            'href="#the-basic-sphinx-documentation-for-testing" '
            'title="Link to this heading"><span>[PERMALINK]</span></a></h1>' in content)


@pytest.mark.sphinx('html', testroot='html_signaturereturn_icon')
def test_html_signaturereturn_icon(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert ('<span class="sig-return-icon">&#x2192;</span>' in content)
