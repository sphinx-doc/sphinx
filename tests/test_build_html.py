"""
    test_build_html
    ~~~~~~~~~~~~~~~

    Test the HTML builder and check output against XPath.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
from distutils.version import LooseVersion
from itertools import chain, cycle
from unittest.mock import ANY, call, patch

import pygments
import pytest
from html5lib import HTMLParser

from sphinx.builders.html import validate_html_extra_path, validate_html_static_path
from sphinx.errors import ConfigError
from sphinx.testing.util import strip_escseq
from sphinx.util import docutils, md5
from sphinx.util.inventory import InventoryFile

if docutils.__version_info__ < (0, 17):
    FIGURE_CAPTION = ".//div[@class='figure align-default']/p[@class='caption']"
else:
    FIGURE_CAPTION = ".//figure/figcaption/p"


ENV_WARNINGS = """\
%(root)s/autodoc_fodder.py:docstring of autodoc_fodder.MarkupError:\\d+: \
WARNING: Explicit markup ends without a blank line; unexpected unindent.
%(root)s/index.rst:\\d+: WARNING: Encoding 'utf-8-sig' used for reading included \
file '%(root)s/wrongenc.inc' seems to be wrong, try giving an :encoding: option
%(root)s/index.rst:\\d+: WARNING: invalid single index entry ''
%(root)s/index.rst:\\d+: WARNING: image file not readable: foo.png
%(root)s/index.rst:\\d+: WARNING: download file not readable: %(root)s/nonexisting.png
%(root)s/undecodable.rst:\\d+: WARNING: undecodable source characters, replacing \
with "\\?": b?'here: >>>(\\\\|/)xbb<<<((\\\\|/)r)?'
"""

HTML_WARNINGS = ENV_WARNINGS + """\
%(root)s/index.rst:\\d+: WARNING: unknown option: &option
%(root)s/index.rst:\\d+: WARNING: citation not found: missing
%(root)s/index.rst:\\d+: WARNING: a suitable image for html builder not found: foo.\\*
%(root)s/index.rst:\\d+: WARNING: Could not lex literal_block as "c". Highlighting skipped.
"""


etree_cache = {}


@pytest.fixture(scope='module')
def cached_etree_parse():
    def parse(fname):
        if fname in etree_cache:
            return etree_cache[fname]
        with (fname).open('rb') as fp:
            etree = HTMLParser(namespaceHTMLElements=False).parse(fp)
            etree_cache.clear()
            etree_cache[fname] = etree
            return etree
    yield parse
    etree_cache.clear()


def flat_dict(d):
    return chain.from_iterable(
        [
            zip(cycle([fname]), values)
            for fname, values in d.items()
        ]
    )


def tail_check(check):
    rex = re.compile(check)

    def checker(nodes):
        for node in nodes:
            if node.tail and rex.search(node.tail):
                return True
        assert False, '%r not found in tail of any nodes %s' % (check, nodes)
    return checker


def check_xpath(etree, fname, path, check, be_found=True):
    nodes = list(etree.findall(path))
    if check is None:
        assert nodes == [], ('found any nodes matching xpath '
                             '%r in file %s' % (path, fname))
        return
    else:
        assert nodes != [], ('did not find any node matching xpath '
                             '%r in file %s' % (path, fname))
    if hasattr(check, '__call__'):
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

        assert False, ('%r not found in any node matching '
                       'path %s in %s: %r' % (check, path, fname,
                                              [node.text for node in nodes]))


@pytest.mark.sphinx('html', testroot='warnings')
def test_html_warnings(app, warning):
    app.build()
    html_warnings = strip_escseq(re.sub(re.escape(os.sep) + '{1,2}', '/', warning.getvalue()))
    html_warnings_exp = HTML_WARNINGS % {
        'root': re.escape(app.srcdir.replace(os.sep, '/'))}
    assert re.match(html_warnings_exp + '$', html_warnings), \
        'Warnings don\'t match:\n' + \
        '--- Expected (regex):\n' + html_warnings_exp + \
        '--- Got:\n' + html_warnings


@pytest.mark.sphinx('html', confoverrides={'html4_writer': True})
def test_html4_output(app, status, warning):
    app.build()


@pytest.mark.parametrize("fname,expect", flat_dict({
    'images.html': [
        (".//img[@src='_images/img.png']", ''),
        (".//img[@src='_images/img1.png']", ''),
        (".//img[@src='_images/simg.png']", ''),
        (".//img[@src='_images/svgimg.svg']", ''),
        (".//a[@href='_sources/images.txt']", ''),
    ],
    'subdir/images.html': [
        (".//img[@src='../_images/img1.png']", ''),
        (".//img[@src='../_images/rimg.png']", ''),
    ],
    'subdir/includes.html': [
        (".//a[@class='reference download internal']", ''),
        (".//img[@src='../_images/img.png']", ''),
        (".//p", 'This is an include file.'),
        (".//pre/span", 'line 1'),
        (".//pre/span", 'line 2'),
    ],
    'includes.html': [
        (".//pre", 'Max Strauß'),
        (".//a[@class='reference download internal']", ''),
        (".//pre/span", '"quotes"'),
        (".//pre/span", "'included'"),
        (".//pre/span[@class='s2']", 'üöä'),
        (".//div[@class='inc-pyobj1 highlight-text notranslate']//pre",
         r'^class Foo:\n    pass\n\s*$'),
        (".//div[@class='inc-pyobj2 highlight-text notranslate']//pre",
         r'^    def baz\(\):\n        pass\n\s*$'),
        (".//div[@class='inc-lines highlight-text notranslate']//pre",
         r'^class Foo:\n    pass\nclass Bar:\n$'),
        (".//div[@class='inc-startend highlight-text notranslate']//pre",
         '^foo = "Including Unicode characters: üöä"\\n$'),
        (".//div[@class='inc-preappend highlight-text notranslate']//pre",
         r'(?m)^START CODE$'),
        (".//div[@class='inc-pyobj-dedent highlight-python notranslate']//span",
         r'def'),
        (".//div[@class='inc-tab3 highlight-text notranslate']//pre",
         r'-| |-'),
        (".//div[@class='inc-tab8 highlight-python notranslate']//pre/span",
         r'-|      |-'),
    ],
    'autodoc.html': [
        (".//dl[@class='py class']/dt[@id='autodoc_target.Class']", ''),
        (".//dl[@class='py function']/dt[@id='autodoc_target.function']/em/span/span", r'\*\*'),
        (".//dl[@class='py function']/dt[@id='autodoc_target.function']/em/span/span", r'kwds'),
        (".//dd/p", r'Return spam\.'),
    ],
    'extapi.html': [
        (".//strong", 'from class: Bar'),
    ],
    'markup.html': [
        (".//title", 'set by title directive'),
        (".//p/em", 'Section author: Georg Brandl'),
        (".//p/em", 'Module author: Georg Brandl'),
        # created by the meta directive
        (".//meta[@name='author'][@content='Me']", ''),
        (".//meta[@name='keywords'][@content='docs, sphinx']", ''),
        # a label created by ``.. _label:``
        (".//div[@id='label']", ''),
        # code with standard code blocks
        (".//pre", '^some code$'),
        # an option list
        (".//span[@class='option']", '--help'),
        # admonitions
        (".//p[@class='admonition-title']", 'My Admonition'),
        (".//div[@class='admonition note']/p", 'Note text.'),
        (".//div[@class='admonition warning']/p", 'Warning text.'),
        # inline markup
        (".//li/p/strong", r'^command\\n$'),
        (".//li/p/strong", r'^program\\n$'),
        (".//li/p/em", r'^dfn\\n$'),
        (".//li/p/kbd", r'^kbd\\n$'),
        (".//li/p/span", 'File \N{TRIANGULAR BULLET} Close'),
        (".//li/p/code/span[@class='pre']", '^a/$'),
        (".//li/p/code/em/span[@class='pre']", '^varpart$'),
        (".//li/p/code/em/span[@class='pre']", '^i$'),
        (".//a[@href='https://www.python.org/dev/peps/pep-0008']"
         "[@class='pep reference external']/strong", 'PEP 8'),
        (".//a[@href='https://www.python.org/dev/peps/pep-0008']"
         "[@class='pep reference external']/strong",
         'Python Enhancement Proposal #8'),
        (".//a[@href='https://tools.ietf.org/html/rfc1.html']"
         "[@class='rfc reference external']/strong", 'RFC 1'),
        (".//a[@href='https://tools.ietf.org/html/rfc1.html']"
         "[@class='rfc reference external']/strong", 'Request for Comments #1'),
        (".//a[@href='objects.html#envvar-HOME']"
         "[@class='reference internal']/code/span[@class='pre']", 'HOME'),
        (".//a[@href='#with']"
         "[@class='reference internal']/code/span[@class='pre']", '^with$'),
        (".//a[@href='#grammar-token-try_stmt']"
         "[@class='reference internal']/code/span", '^statement$'),
        (".//a[@href='#some-label'][@class='reference internal']/span", '^here$'),
        (".//a[@href='#some-label'][@class='reference internal']/span", '^there$'),
        (".//a[@href='subdir/includes.html']"
         "[@class='reference internal']/span", 'Including in subdir'),
        (".//a[@href='objects.html#cmdoption-python-c']"
         "[@class='reference internal']/code/span[@class='pre']", '-c'),
        # abbreviations
        (".//abbr[@title='abbreviation']", '^abbr$'),
        # version stuff
        (".//div[@class='versionadded']/p/span", 'New in version 0.6: '),
        (".//div[@class='versionadded']/p/span",
         tail_check('First paragraph of versionadded')),
        (".//div[@class='versionchanged']/p/span",
         tail_check('First paragraph of versionchanged')),
        (".//div[@class='versionchanged']/p",
         'Second paragraph of versionchanged'),
        # footnote reference
        (".//a[@class='footnote-reference brackets']", r'1'),
        # created by reference lookup
        (".//a[@href='index.html#ref1']", ''),
        # ``seealso`` directive
        (".//div/p[@class='admonition-title']", 'See also'),
        # a ``hlist`` directive
        (".//table[@class='hlist']/tbody/tr/td/ul/li/p", '^This$'),
        # a ``centered`` directive
        (".//p[@class='centered']/strong", 'LICENSE'),
        # a glossary
        (".//dl/dt[@id='term-boson']", 'boson'),
        (".//dl/dt[@id='term-boson']/a", '¶'),
        # a production list
        (".//pre/strong", 'try_stmt'),
        (".//pre/a[@href='#grammar-token-try1_stmt']/code/span", 'try1_stmt'),
        # tests for ``only`` directive
        (".//p", 'A global substitution!'),
        (".//p", 'In HTML.'),
        (".//p", 'In both.'),
        (".//p", 'Always present'),
        # tests for ``any`` role
        (".//a[@href='#with']/span", 'headings'),
        (".//a[@href='objects.html#func_without_body']/code/span", 'objects'),
        # tests for numeric labels
        (".//a[@href='#id1'][@class='reference internal']/span", 'Testing various markup'),
        # tests for smartypants
        (".//li/p", 'Smart “quotes” in English ‘text’.'),
        (".//li/p", 'Smart — long and – short dashes.'),
        (".//li/p", 'Ellipsis…'),
        (".//li/p/code/span[@class='pre']", 'foo--"bar"...'),
        (".//p", 'Этот «абзац» должен использовать „русские“ кавычки.'),
        (".//p", 'Il dit : « C’est “super” ! »'),
    ],
    'objects.html': [
        (".//dt[@id='mod.Cls.meth1']", ''),
        (".//dt[@id='errmod.Error']", ''),
        (".//dt/span[@class='sig-name descname']/span[@class='pre']", r'long\(parameter,'),
        (".//dt/span[@class='sig-name descname']/span[@class='pre']", r'list\)'),
        (".//dt/span[@class='sig-name descname']/span[@class='pre']", 'another'),
        (".//dt/span[@class='sig-name descname']/span[@class='pre']", 'one'),
        (".//a[@href='#mod.Cls'][@class='reference internal']", ''),
        (".//dl[@class='std userdesc']", ''),
        (".//dt[@id='userdesc-myobj']", ''),
        (".//a[@href='#userdesc-myobj'][@class='reference internal']", ''),
        # docfields
        (".//a[@class='reference internal'][@href='#TimeInt']/em", 'TimeInt'),
        (".//a[@class='reference internal'][@href='#Time']", 'Time'),
        (".//a[@class='reference internal'][@href='#errmod.Error']/strong", 'Error'),
        # C references
        (".//span[@class='pre']", 'CFunction()'),
        (".//a[@href='#c.Sphinx_DoSomething']", ''),
        (".//a[@href='#c.SphinxStruct.member']", ''),
        (".//a[@href='#c.SPHINX_USE_PYTHON']", ''),
        (".//a[@href='#c.SphinxType']", ''),
        (".//a[@href='#c.sphinx_global']", ''),
        # test global TOC created by toctree()
        (".//ul[@class='current']/li[@class='toctree-l1 current']/a[@href='#']",
         'Testing object descriptions'),
        (".//li[@class='toctree-l1']/a[@href='markup.html']",
         'Testing various markup'),
        # test unknown field names
        (".//dt[@class='field-odd']", 'Field_name'),
        (".//dt[@class='field-even']", 'Field_name all lower'),
        (".//dt[@class='field-odd']", 'FIELD_NAME'),
        (".//dt[@class='field-even']", 'FIELD_NAME ALL CAPS'),
        (".//dt[@class='field-odd']", 'Field_Name'),
        (".//dt[@class='field-even']", 'Field_Name All Word Caps'),
        (".//dt[@class='field-odd']", 'Field_name'),
        (".//dt[@class='field-even']", 'Field_name First word cap'),
        (".//dt[@class='field-odd']", 'FIELd_name'),
        (".//dt[@class='field-even']", 'FIELd_name PARTial caps'),
        # custom sidebar
        (".//h4", 'Custom sidebar'),
        # docfields
        (".//dd[@class='field-odd']/p/strong", '^moo$'),
        (".//dd[@class='field-odd']/p/strong", tail_check(r'\(Moo\) .* Moo')),
        (".//dd[@class='field-odd']/ul/li/p/strong", '^hour$'),
        (".//dd[@class='field-odd']/ul/li/p/em", '^DuplicateType$'),
        (".//dd[@class='field-odd']/ul/li/p/em", tail_check(r'.* Some parameter')),
        # others
        (".//a[@class='reference internal'][@href='#cmdoption-perl-arg-p']/code/span",
         'perl'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-arg-p']/code/span",
         '\\+p'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-ObjC']/code/span",
         '--ObjC\\+\\+'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-plugin.option']/code/span",
         '--plugin.option'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-arg-create-auth-token']"
         "/code/span",
         'create-auth-token'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-arg-arg']/code/span",
         'arg'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-j']/code/span",
         '-j'),
        (".//a[@class='reference internal'][@href='#cmdoption-hg-arg-commit']/code/span",
         'hg'),
        (".//a[@class='reference internal'][@href='#cmdoption-hg-arg-commit']/code/span",
         'commit'),
        (".//a[@class='reference internal'][@href='#cmdoption-git-commit-p']/code/span",
         'git'),
        (".//a[@class='reference internal'][@href='#cmdoption-git-commit-p']/code/span",
         'commit'),
        (".//a[@class='reference internal'][@href='#cmdoption-git-commit-p']/code/span",
         '-p'),
    ],
    'index.html': [
        (".//meta[@name='hc'][@content='hcval']", ''),
        (".//meta[@name='hc_co'][@content='hcval_co']", ''),
        (".//dt[@class='label']/span[@class='brackets']", r'Ref1'),
        (".//dt[@class='label']", ''),
        (".//li[@class='toctree-l1']/a", 'Testing various markup'),
        (".//li[@class='toctree-l2']/a", 'Inline markup'),
        (".//title", 'Sphinx <Tests>'),
        (".//div[@class='footer']", 'Georg Brandl & Team'),
        (".//a[@href='http://python.org/']"
         "[@class='reference external']", ''),
        (".//li/p/a[@href='genindex.html']/span", 'Index'),
        (".//li/p/a[@href='py-modindex.html']/span", 'Module Index'),
        # custom sidebar only for contents
        (".//h4", 'Contents sidebar'),
        # custom JavaScript
        (".//script[@src='file://moo.js']", ''),
        # URL in contents
        (".//a[@class='reference external'][@href='http://sphinx-doc.org/']",
         'http://sphinx-doc.org/'),
        (".//a[@class='reference external'][@href='http://sphinx-doc.org/latest/']",
         'Latest reference'),
        # Indirect hyperlink targets across files
        (".//a[@href='markup.html#some-label'][@class='reference internal']/span",
         '^indirect hyperref$'),
    ],
    'bom.html': [
        (".//title", " File with UTF-8 BOM"),
    ],
    'extensions.html': [
        (".//a[@href='http://python.org/dev/']", "http://python.org/dev/"),
        (".//a[@href='http://bugs.python.org/issue1000']", "issue 1000"),
        (".//a[@href='http://bugs.python.org/issue1042']", "explicit caption"),
    ],
    'genindex.html': [
        # index entries
        (".//a/strong", "Main"),
        (".//a/strong", "[1]"),
        (".//a/strong", "Other"),
        (".//a", "entry"),
        (".//li/a", "double"),
    ],
    'footnote.html': [
        (".//a[@class='footnote-reference brackets'][@href='#id9'][@id='id1']", r"1"),
        (".//a[@class='footnote-reference brackets'][@href='#id10'][@id='id2']", r"2"),
        (".//a[@class='footnote-reference brackets'][@href='#foo'][@id='id3']", r"3"),
        (".//a[@class='reference internal'][@href='#bar'][@id='id4']/span", r"\[bar\]"),
        (".//a[@class='reference internal'][@href='#baz-qux'][@id='id5']/span", r"\[baz_qux\]"),
        (".//a[@class='footnote-reference brackets'][@href='#id11'][@id='id6']", r"4"),
        (".//a[@class='footnote-reference brackets'][@href='#id12'][@id='id7']", r"5"),
        (".//a[@class='fn-backref'][@href='#id1']", r"1"),
        (".//a[@class='fn-backref'][@href='#id2']", r"2"),
        (".//a[@class='fn-backref'][@href='#id3']", r"3"),
        (".//a[@class='fn-backref'][@href='#id4']", r"bar"),
        (".//a[@class='fn-backref'][@href='#id5']", r"baz_qux"),
        (".//a[@class='fn-backref'][@href='#id6']", r"4"),
        (".//a[@class='fn-backref'][@href='#id7']", r"5"),
        (".//a[@class='fn-backref'][@href='#id8']", r"6"),
    ],
    'otherext.html': [
        (".//h1", "Generated section"),
        (".//a[@href='_sources/otherext.foo.txt']", ''),
    ]
}))
@pytest.mark.sphinx('html', tags=['testtag'],
                    confoverrides={'html_context.hckey_co': 'hcval_co'})
@pytest.mark.test_params(shared_result='test_build_html_output')
def test_html5_output(app, cached_etree_parse, fname, expect):
    app.build()
    print(app.outdir / fname)
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx('html', parallel=2)
def test_html_parallel(app):
    app.build()


@pytest.mark.sphinx('html')
@pytest.mark.test_params(shared_result='test_build_html_output')
def test_html_download(app):
    app.build()

    # subdir/includes.html
    result = (app.outdir / 'subdir' / 'includes.html').read_text()
    pattern = ('<a class="reference download internal" download="" '
               'href="../(_downloads/.*/img.png)">')
    matched = re.search(pattern, result)
    assert matched
    assert (app.outdir / matched.group(1)).exists()
    filename = matched.group(1)

    # includes.html
    result = (app.outdir / 'includes.html').read_text()
    pattern = ('<a class="reference download internal" download="" '
               'href="(_downloads/.*/img.png)">')
    matched = re.search(pattern, result)
    assert matched
    assert (app.outdir / matched.group(1)).exists()
    assert matched.group(1) == filename


@pytest.mark.sphinx('html', testroot='roles-download')
def test_html_download_role(app, status, warning):
    app.build()
    digest = md5(b'dummy.dat').hexdigest()
    assert (app.outdir / '_downloads' / digest / 'dummy.dat').exists()
    digest_another = md5(b'another/dummy.dat').hexdigest()
    assert (app.outdir / '_downloads' / digest_another / 'dummy.dat').exists()

    content = (app.outdir / 'index.html').read_text()
    assert (('<li><p><a class="reference download internal" download="" '
             'href="_downloads/%s/dummy.dat">'
             '<code class="xref download docutils literal notranslate">'
             '<span class="pre">dummy.dat</span></code></a></p></li>' % digest)
            in content)
    assert (('<li><p><a class="reference download internal" download="" '
             'href="_downloads/%s/dummy.dat">'
             '<code class="xref download docutils literal notranslate">'
             '<span class="pre">another/dummy.dat</span></code></a></p></li>' %
             digest_another) in content)
    assert ('<li><p><code class="xref download docutils literal notranslate">'
            '<span class="pre">not_found.dat</span></code></p></li>' in content)
    assert ('<li><p><a class="reference download external" download="" '
            'href="http://www.sphinx-doc.org/en/master/_static/sphinxheader.png">'
            '<code class="xref download docutils literal notranslate">'
            '<span class="pre">Sphinx</span> <span class="pre">logo</span>'
            '</code></a></p></li>' in content)


@pytest.mark.sphinx('html', testroot='build-html-translator')
def test_html_translator(app):
    app.build()
    assert app.builder.docwriter.visitor.depart_with_node == 10


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
        (".//li[@class='toctree-l3']/a", '1.1.1. Foo A1', True),
        (".//li[@class='toctree-l3']/a", '1.2.1. Foo B1', True),
        (".//li[@class='toctree-l3']/a", '2.1.1. Bar A1', False),
        (".//li[@class='toctree-l3']/a", '2.2.1. Bar B1', False),
    ],
    'foo.html': [
        (".//h1", 'Foo', True),
        (".//h2", 'Foo A', True),
        (".//h3", 'Foo A1', True),
        (".//h2", 'Foo B', True),
        (".//h3", 'Foo B1', True),

        (".//h1//span[@class='section-number']", '1. ', True),
        (".//h2//span[@class='section-number']", '1.1. ', True),
        (".//h3//span[@class='section-number']", '1.1.1. ', True),
        (".//h2//span[@class='section-number']", '1.2. ', True),
        (".//h3//span[@class='section-number']", '1.2.1. ', True),

        (".//div[@class='sphinxsidebarwrapper']//li/a", '1.1. Foo A', True),
        (".//div[@class='sphinxsidebarwrapper']//li/a", '1.1.1. Foo A1', True),
        (".//div[@class='sphinxsidebarwrapper']//li/a", '1.2. Foo B', True),
        (".//div[@class='sphinxsidebarwrapper']//li/a", '1.2.1. Foo B1', True),
    ],
    'bar.html': [
        (".//h1", 'Bar', True),
        (".//h2", 'Bar A', True),
        (".//h2", 'Bar B', True),
        (".//h3", 'Bar B1', True),
        (".//h1//span[@class='section-number']", '2. ', True),
        (".//h2//span[@class='section-number']", '2.1. ', True),
        (".//h2//span[@class='section-number']", '2.2. ', True),
        (".//h3//span[@class='section-number']", '2.2.1. ', True),
        (".//div[@class='sphinxsidebarwrapper']//li/a", '2. Bar', True),
        (".//div[@class='sphinxsidebarwrapper']//li/a", '2.1. Bar A', True),
        (".//div[@class='sphinxsidebarwrapper']//li/a", '2.2. Bar B', True),
        (".//div[@class='sphinxsidebarwrapper']//li/a", '2.2.1. Bar B1', False),
    ],
    'baz.html': [
        (".//h1", 'Baz A', True),
        (".//h1//span[@class='section-number']", '2.1.1. ', True),
    ],
}))
@pytest.mark.sphinx('html', testroot='tocdepth')
@pytest.mark.test_params(shared_result='test_build_html_tocdepth')
def test_tocdepth(app, cached_etree_parse, fname, expect):
    app.build()
    # issue #1251
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
        (".//li[@class='toctree-l3']/a", '1.1.1. Foo A1', True),
        (".//li[@class='toctree-l3']/a", '1.2.1. Foo B1', True),
        (".//li[@class='toctree-l3']/a", '2.1.1. Bar A1', False),
        (".//li[@class='toctree-l3']/a", '2.2.1. Bar B1', False),

        # index.rst
        (".//h1", 'test-tocdepth', True),

        # foo.rst
        (".//h2", 'Foo', True),
        (".//h3", 'Foo A', True),
        (".//h4", 'Foo A1', True),
        (".//h3", 'Foo B', True),
        (".//h4", 'Foo B1', True),
        (".//h2//span[@class='section-number']", '1. ', True),
        (".//h3//span[@class='section-number']", '1.1. ', True),
        (".//h4//span[@class='section-number']", '1.1.1. ', True),
        (".//h3//span[@class='section-number']", '1.2. ', True),
        (".//h4//span[@class='section-number']", '1.2.1. ', True),

        # bar.rst
        (".//h2", 'Bar', True),
        (".//h3", 'Bar A', True),
        (".//h3", 'Bar B', True),
        (".//h4", 'Bar B1', True),
        (".//h2//span[@class='section-number']", '2. ', True),
        (".//h3//span[@class='section-number']", '2.1. ', True),
        (".//h3//span[@class='section-number']", '2.2. ', True),
        (".//h4//span[@class='section-number']", '2.2.1. ', True),

        # baz.rst
        (".//h4", 'Baz A', True),
        (".//h4//span[@class='section-number']", '2.1.1. ', True),
    ],
}))
@pytest.mark.sphinx('singlehtml', testroot='tocdepth')
@pytest.mark.test_params(shared_result='test_build_html_tocdepth')
def test_tocdepth_singlehtml(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx('html', testroot='numfig')
@pytest.mark.test_params(shared_result='test_build_html_numfig')
def test_numfig_disabled_warn(app, warning):
    app.build()
    warnings = warning.getvalue()
    assert 'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.' in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' not in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' not in warnings


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", None, True),
        (".//table/caption/span[@class='caption-number']", None, True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", None, True),
        (".//li/p/code/span", '^fig1$', True),
        (".//li/p/code/span", '^Figure%s$', True),
        (".//li/p/code/span", '^table-1$', True),
        (".//li/p/code/span", '^Table:%s$', True),
        (".//li/p/code/span", '^CODE_1$', True),
        (".//li/p/code/span", '^Code-%s$', True),
        (".//li/p/a/span", '^Section 1$', True),
        (".//li/p/a/span", '^Section 2.1$', True),
        (".//li/p/code/span", '^Fig.{number}$', True),
        (".//li/p/a/span", '^Sect.1 Foo$', True),
    ],
    'foo.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", None, True),
        (".//table/caption/span[@class='caption-number']", None, True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", None, True),
    ],
    'bar.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", None, True),
        (".//table/caption/span[@class='caption-number']", None, True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", None, True),
    ],
    'baz.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", None, True),
        (".//table/caption/span[@class='caption-number']", None, True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", None, True),
    ],
}))
@pytest.mark.sphinx('html', testroot='numfig')
@pytest.mark.test_params(shared_result='test_build_html_numfig')
def test_numfig_disabled(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx(
    'html', testroot='numfig',
    srcdir='test_numfig_without_numbered_toctree_warn',
    confoverrides={'numfig': True})
def test_numfig_without_numbered_toctree_warn(app, warning):
    app.build()
    # remove :numbered: option
    index = (app.srcdir / 'index.rst').read_text()
    index = re.sub(':numbered:.*', '', index)
    (app.srcdir / 'index.rst').write_text(index)
    app.builder.build_all()

    warnings = warning.getvalue()
    assert 'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.' not in warnings
    assert 'index.rst:55: WARNING: Failed to create a cross reference. Any number is not assigned: index' in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' in warnings


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 9 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 10 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 9 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 10 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 9 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 10 $', True),
        (".//li/p/a/span", '^Fig. 9$', True),
        (".//li/p/a/span", '^Figure6$', True),
        (".//li/p/a/span", '^Table 9$', True),
        (".//li/p/a/span", '^Table:6$', True),
        (".//li/p/a/span", '^Listing 9$', True),
        (".//li/p/a/span", '^Code-6$', True),
        (".//li/p/code/span", '^foo$', True),
        (".//li/p/code/span", '^bar_a$', True),
        (".//li/p/a/span", '^Fig.9 should be Fig.1$', True),
        (".//li/p/code/span", '^Sect.{number}$', True),
    ],
    'foo.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 4 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 3 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 4 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 3 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 4 $', True),
    ],
    'bar.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 5 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 7 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 8 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 5 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 7 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 8 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 5 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 7 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 8 $', True),
    ],
    'baz.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 6 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 6 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 6 $', True),
    ],
}))
@pytest.mark.sphinx(
    'html', testroot='numfig',
    srcdir='test_numfig_without_numbered_toctree',
    confoverrides={'numfig': True})
def test_numfig_without_numbered_toctree(app, cached_etree_parse, fname, expect):
    # remove :numbered: option
    index = (app.srcdir / 'index.rst').read_text()
    index = re.sub(':numbered:.*', '', index)
    (app.srcdir / 'index.rst').write_text(index)

    if not app.outdir.listdir():
        app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx('html', testroot='numfig', confoverrides={'numfig': True})
@pytest.mark.test_params(shared_result='test_build_html_numfig_on')
def test_numfig_with_numbered_toctree_warn(app, warning):
    app.build()
    warnings = warning.getvalue()
    assert 'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.' not in warnings
    assert 'index.rst:55: WARNING: Failed to create a cross reference. Any number is not assigned: index' in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' in warnings


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2 $', True),
        (".//li/p/a/span", '^Fig. 1$', True),
        (".//li/p/a/span", '^Figure2.2$', True),
        (".//li/p/a/span", '^Table 1$', True),
        (".//li/p/a/span", '^Table:2.2$', True),
        (".//li/p/a/span", '^Listing 1$', True),
        (".//li/p/a/span", '^Code-2.2$', True),
        (".//li/p/a/span", '^Section.1$', True),
        (".//li/p/a/span", '^Section.2.1$', True),
        (".//li/p/a/span", '^Fig.1 should be Fig.1$', True),
        (".//li/p/a/span", '^Sect.1 Foo$', True),
    ],
    'foo.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.2 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.4 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.3 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.4 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.3 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.4 $', True),
    ],
    'bar.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.4 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.3 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.4 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.3 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.4 $', True),
    ],
    'baz.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.2 $', True),
    ],
}))
@pytest.mark.sphinx('html', testroot='numfig', confoverrides={'numfig': True})
@pytest.mark.test_params(shared_result='test_build_html_numfig_on')
def test_numfig_with_numbered_toctree(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx('html', testroot='numfig', confoverrides={
    'numfig': True,
    'numfig_format': {'figure': 'Figure:%s',
                      'table': 'Tab_%s',
                      'code-block': 'Code-%s',
                      'section': 'SECTION-%s'}})
@pytest.mark.test_params(shared_result='test_build_html_numfig_format_warn')
def test_numfig_with_prefix_warn(app, warning):
    app.build()
    warnings = warning.getvalue()
    assert 'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.' not in warnings
    assert 'index.rst:55: WARNING: Failed to create a cross reference. Any number is not assigned: index' in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' in warnings


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-2 $', True),
        (".//li/p/a/span", '^Figure:1$', True),
        (".//li/p/a/span", '^Figure2.2$', True),
        (".//li/p/a/span", '^Tab_1$', True),
        (".//li/p/a/span", '^Table:2.2$', True),
        (".//li/p/a/span", '^Code-1$', True),
        (".//li/p/a/span", '^Code-2.2$', True),
        (".//li/p/a/span", '^SECTION-1$', True),
        (".//li/p/a/span", '^SECTION-2.1$', True),
        (".//li/p/a/span", '^Fig.1 should be Fig.1$', True),
        (".//li/p/a/span", '^Sect.1 Foo$', True),
    ],
    'foo.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:1.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:1.2 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:1.3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:1.4 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_1.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_1.2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_1.3 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_1.4 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-1.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-1.2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-1.3 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-1.4 $', True),
    ],
    'bar.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:2.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:2.3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:2.4 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_2.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_2.3 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_2.4 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-2.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-2.3 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-2.4 $', True),
    ],
    'baz.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Figure:2.2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Tab_2.2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Code-2.2 $', True),
    ],
}))
@pytest.mark.sphinx('html', testroot='numfig',
                    confoverrides={'numfig': True,
                                   'numfig_format': {'figure': 'Figure:%s',
                                                     'table': 'Tab_%s',
                                                     'code-block': 'Code-%s',
                                                     'section': 'SECTION-%s'}})
@pytest.mark.test_params(shared_result='test_build_html_numfig_format_warn')
def test_numfig_with_prefix(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx('html', testroot='numfig',
                    confoverrides={'numfig': True, 'numfig_secnum_depth': 2})
@pytest.mark.test_params(shared_result='test_build_html_numfig_depth_2')
def test_numfig_with_secnum_depth_warn(app, warning):
    app.build()
    warnings = warning.getvalue()
    assert 'index.rst:47: WARNING: numfig is disabled. :numref: is ignored.' not in warnings
    assert 'index.rst:55: WARNING: Failed to create a cross reference. Any number is not assigned: index' in warnings
    assert 'index.rst:56: WARNING: invalid numfig_format: invalid' in warnings
    assert 'index.rst:57: WARNING: invalid numfig_format: Fig %s %s' in warnings


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2 $', True),
        (".//li/p/a/span", '^Fig. 1$', True),
        (".//li/p/a/span", '^Figure2.1.2$', True),
        (".//li/p/a/span", '^Table 1$', True),
        (".//li/p/a/span", '^Table:2.1.2$', True),
        (".//li/p/a/span", '^Listing 1$', True),
        (".//li/p/a/span", '^Code-2.1.2$', True),
        (".//li/p/a/span", '^Section.1$', True),
        (".//li/p/a/span", '^Section.2.1$', True),
        (".//li/p/a/span", '^Fig.1 should be Fig.1$', True),
        (".//li/p/a/span", '^Sect.1 Foo$', True),
    ],
    'foo.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.1.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.1.2 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.2.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.1.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.1.2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.2.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.1.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.1.2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.2.1 $', True),
    ],
    'bar.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.1.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.1.3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.2.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.1.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.1.3 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.2.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.1.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.1.3 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.2.1 $', True),
    ],
    'baz.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.1.2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.1.2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.1.2 $', True),
    ],
}))
@pytest.mark.sphinx('html', testroot='numfig',
                    confoverrides={'numfig': True,
                                   'numfig_secnum_depth': 2})
@pytest.mark.test_params(shared_result='test_build_html_numfig_depth_2')
def test_numfig_with_secnum_depth(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2 $', True),
        (".//li/p/a/span", '^Fig. 1$', True),
        (".//li/p/a/span", '^Figure2.2$', True),
        (".//li/p/a/span", '^Table 1$', True),
        (".//li/p/a/span", '^Table:2.2$', True),
        (".//li/p/a/span", '^Listing 1$', True),
        (".//li/p/a/span", '^Code-2.2$', True),
        (".//li/p/a/span", '^Section.1$', True),
        (".//li/p/a/span", '^Section.2.1$', True),
        (".//li/p/a/span", '^Fig.1 should be Fig.1$', True),
        (".//li/p/a/span", '^Sect.1 Foo$', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.2 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 1.4 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.3 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 1.4 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.3 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 1.4 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.1 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.3 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.4 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.1 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.3 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.4 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.1 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.3 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.4 $', True),
        (FIGURE_CAPTION + "/span[@class='caption-number']", '^Fig. 2.2 $', True),
        (".//table/caption/span[@class='caption-number']",
         '^Table 2.2 $', True),
        (".//div[@class='code-block-caption']/"
         "span[@class='caption-number']", '^Listing 2.2 $', True),
    ],
}))
@pytest.mark.sphinx('singlehtml', testroot='numfig', confoverrides={'numfig': True})
@pytest.mark.test_params(shared_result='test_build_html_numfig_on')
def test_numfig_with_singlehtml(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
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
    ],
}))
@pytest.mark.sphinx('html', testroot='add_enumerable_node',
                    srcdir='test_enumerable_node')
def test_enumerable_node(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx('html', testroot='html_assets')
def test_html_assets(app):
    app.builder.build_all()

    # exclude_path and its family
    assert not (app.outdir / 'static' / 'index.html').exists()
    assert not (app.outdir / 'extra' / 'index.html').exists()

    # html_static_path
    assert not (app.outdir / '_static' / '.htaccess').exists()
    assert not (app.outdir / '_static' / '.htpasswd').exists()
    assert (app.outdir / '_static' / 'API.html').exists()
    assert (app.outdir / '_static' / 'API.html').read_text() == 'Sphinx-1.4.4'
    assert (app.outdir / '_static' / 'css' / 'style.css').exists()
    assert (app.outdir / '_static' / 'js' / 'custom.js').exists()
    assert (app.outdir / '_static' / 'rimg.png').exists()
    assert not (app.outdir / '_static' / '_build' / 'index.html').exists()
    assert (app.outdir / '_static' / 'background.png').exists()
    assert not (app.outdir / '_static' / 'subdir' / '.htaccess').exists()
    assert not (app.outdir / '_static' / 'subdir' / '.htpasswd').exists()

    # html_extra_path
    assert (app.outdir / '.htaccess').exists()
    assert not (app.outdir / '.htpasswd').exists()
    assert (app.outdir / 'API.html_t').exists()
    assert (app.outdir / 'css/style.css').exists()
    assert (app.outdir / 'rimg.png').exists()
    assert not (app.outdir / '_build' / 'index.html').exists()
    assert (app.outdir / 'background.png').exists()
    assert (app.outdir / 'subdir' / '.htaccess').exists()
    assert not (app.outdir / 'subdir' / '.htpasswd').exists()

    # html_css_files
    content = (app.outdir / 'index.html').read_text()
    assert '<link rel="stylesheet" type="text/css" href="_static/css/style.css" />' in content
    assert ('<link media="print" rel="stylesheet" title="title" type="text/css" '
            'href="https://example.com/custom.css" />' in content)

    # html_js_files
    assert '<script src="_static/js/custom.js"></script>' in content
    assert ('<script async="async" src="https://example.com/script.js">'
            '</script>' in content)


@pytest.mark.sphinx('html', testroot='html_assets')
def test_assets_order(app):
    app.add_css_file('normal.css')
    app.add_css_file('early.css', priority=100)
    app.add_css_file('late.css', priority=750)
    app.add_css_file('lazy.css', priority=900)
    app.add_js_file('normal.js')
    app.add_js_file('early.js', priority=100)
    app.add_js_file('late.js', priority=750)
    app.add_js_file('lazy.js', priority=900)

    app.builder.build_all()
    content = (app.outdir / 'index.html').read_text()

    # css_files
    expected = ['_static/early.css', '_static/pygments.css', '_static/alabaster.css',
                'https://example.com/custom.css', '_static/normal.css', '_static/late.css',
                '_static/css/style.css', '_static/lazy.css']
    pattern = '.*'.join('href="%s"' % f for f in expected)
    assert re.search(pattern, content, re.S)

    # js_files
    expected = ['_static/early.js', '_static/jquery.js', '_static/underscore.js',
                '_static/doctools.js', 'https://example.com/script.js', '_static/normal.js',
                '_static/late.js', '_static/js/custom.js', '_static/lazy.js']
    pattern = '.*'.join('src="%s"' % f for f in expected)
    assert re.search(pattern, content, re.S)


@pytest.mark.sphinx('html', testroot='basic', confoverrides={'html_copy_source': False})
def test_html_copy_source(app):
    app.builder.build_all()
    assert not (app.outdir / '_sources' / 'index.rst.txt').exists()


@pytest.mark.sphinx('html', testroot='basic', confoverrides={'html_sourcelink_suffix': '.txt'})
def test_html_sourcelink_suffix(app):
    app.builder.build_all()
    assert (app.outdir / '_sources' / 'index.rst.txt').exists()


@pytest.mark.sphinx('html', testroot='basic', confoverrides={'html_sourcelink_suffix': '.rst'})
def test_html_sourcelink_suffix_same(app):
    app.builder.build_all()
    assert (app.outdir / '_sources' / 'index.rst').exists()


@pytest.mark.sphinx('html', testroot='basic', confoverrides={'html_sourcelink_suffix': ''})
def test_html_sourcelink_suffix_empty(app):
    app.builder.build_all()
    assert (app.outdir / '_sources' / 'index.rst').exists()


@pytest.mark.sphinx('html', testroot='html_entity')
def test_html_entity(app):
    app.builder.build_all()
    valid_entities = {'amp', 'lt', 'gt', 'quot', 'apos'}
    content = (app.outdir / 'index.html').read_text()
    for entity in re.findall(r'&([a-z]+);', content, re.M):
        assert entity not in valid_entities


@pytest.mark.sphinx('html', testroot='basic')
@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_html_inventory(app):
    app.builder.build_all()
    with open(app.outdir / 'objects.inv', 'rb') as f:
        invdata = InventoryFile.load(f, 'https://www.google.com', os.path.join)
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
    app.builder.build_all()
    content = (app.outdir / 'index.html').read_text()
    if docutils.__version_info__ < (0, 17):
        assert ('<p class="caption"><span class="caption-text">The caption of pic</span>'
                '<a class="headerlink" href="#id1" title="Permalink to this image">¶</a></p>'
                in content)
    else:
        assert ('<figcaption>\n<p><span class="caption-text">The caption of pic</span>'
                '<a class="headerlink" href="#id1" title="Permalink to this image">¶</a></p>\n</figcaption>'
                in content)


@pytest.mark.sphinx('html', testroot='directives-raw')
def test_html_raw_directive(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'index.html').read_text()

    # standard case
    assert 'standalone raw directive (HTML)' in result
    assert 'standalone raw directive (LaTeX)' not in result

    # with substitution
    assert '<p>HTML: abc def ghi</p>' in result
    assert '<p>LaTeX: abc  ghi</p>' in result


@pytest.mark.parametrize("fname,expect", flat_dict({
    'index.html': [
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
    ],
}))
@pytest.mark.sphinx('html', testroot='stylesheets')
def test_alternate_stylesheets(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx('html', testroot='html_style')
def test_html_style(app, status, warning):
    app.build()
    result = (app.outdir / 'index.html').read_text()
    assert '<link rel="stylesheet" type="text/css" href="_static/default.css" />' in result
    assert ('<link rel="stylesheet" type="text/css" href="_static/alabaster.css" />'
            not in result)


@pytest.mark.sphinx('html', testroot='images')
def test_html_remote_images(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'index.html').read_text()
    assert ('<img alt="https://www.python.org/static/img/python-logo.png" '
            'src="https://www.python.org/static/img/python-logo.png" />' in result)
    assert not (app.outdir / 'python-logo.png').exists()


@pytest.mark.sphinx('html', testroot='remote-logo')
def test_html_remote_logo(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'index.html').read_text()
    assert ('<img class="logo" src="https://www.python.org/static/img/python-logo.png" alt="Logo"/>' in result)
    assert ('<link rel="shortcut icon" href="https://www.python.org/static/favicon.ico"/>' in result)
    assert not (app.outdir / 'python-logo.png').exists()


@pytest.mark.sphinx('html', testroot='basic')
def test_html_sidebar(app, status, warning):
    ctx = {}

    # default for alabaster
    app.builder.build_all()
    result = (app.outdir / 'index.html').read_text()
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
    app.builder.build_all()
    result = (app.outdir / 'index.html').read_text()
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
    app.builder.build_all()
    result = (app.outdir / 'index.html').read_text()
    assert ('<div class="sphinxsidebar" role="navigation" '
            'aria-label="main navigation">' not in result)
    assert '<h1 class="logo"><a href="#">Python</a></h1>' not in result
    assert '<h3>Navigation</h3>' not in result
    assert '<h3>Related Topics</h3>' not in result
    assert '<h3 id="searchlabel">Quick search</h3>' not in result

    app.builder.add_sidebars('index', ctx)
    assert ctx['sidebars'] == []


@pytest.mark.parametrize('fname,expect', flat_dict({
    'index.html': [(".//em/a[@href='https://example.com/man.1']", "", True),
                   (".//em/a[@href='https://example.com/ls.1']", "", True),
                   (".//em/a[@href='https://example.com/sphinx.']", "", True)]

}))
@pytest.mark.sphinx('html', testroot='manpage_url', confoverrides={
    'manpages_url': 'https://example.com/{page}.{section}'})
@pytest.mark.test_params(shared_result='test_build_html_manpage_url')
def test_html_manpage(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)


@pytest.mark.sphinx('html', testroot='toctree-glob',
                    confoverrides={'html_baseurl': 'https://example.com/'})
def test_html_baseurl(app, status, warning):
    app.build()

    result = (app.outdir / 'index.html').read_text()
    assert '<link rel="canonical" href="https://example.com/index.html" />' in result

    result = (app.outdir / 'qux' / 'index.html').read_text()
    assert '<link rel="canonical" href="https://example.com/qux/index.html" />' in result


@pytest.mark.sphinx('html', testroot='toctree-glob',
                    confoverrides={'html_baseurl': 'https://example.com/subdir',
                                   'html_file_suffix': '.htm'})
def test_html_baseurl_and_html_file_suffix(app, status, warning):
    app.build()

    result = (app.outdir / 'index.htm').read_text()
    assert '<link rel="canonical" href="https://example.com/subdir/index.htm" />' in result

    result = (app.outdir / 'qux' / 'index.htm').read_text()
    assert '<link rel="canonical" href="https://example.com/subdir/qux/index.htm" />' in result


@pytest.mark.sphinx('html', testroot='basic')
def test_default_html_math_renderer(app, status, warning):
    assert app.builder.math_renderer_name == 'mathjax'


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'extensions': ['sphinx.ext.mathjax']})
def test_html_math_renderer_is_mathjax(app, status, warning):
    assert app.builder.math_renderer_name == 'mathjax'


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'extensions': ['sphinx.ext.imgmath']})
def test_html_math_renderer_is_imgmath(app, status, warning):
    assert app.builder.math_renderer_name == 'imgmath'


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'extensions': ['sphinxcontrib.jsmath',
                                                  'sphinx.ext.imgmath']})
def test_html_math_renderer_is_duplicated(make_app, app_params):
    try:
        args, kwargs = app_params
        make_app(*args, **kwargs)
        assert False
    except ConfigError as exc:
        assert str(exc) == ('Many math_renderers are registered. '
                            'But no math_renderer is selected.')


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'extensions': ['sphinx.ext.imgmath',
                                                  'sphinx.ext.mathjax']})
def test_html_math_renderer_is_duplicated2(app, status, warning):
    # case of both mathjax and another math_renderer is loaded
    assert app.builder.math_renderer_name == 'imgmath'  # The another one is chosen


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'extensions': ['sphinxcontrib.jsmath',
                                                  'sphinx.ext.imgmath'],
                                   'html_math_renderer': 'imgmath'})
def test_html_math_renderer_is_chosen(app, status, warning):
    assert app.builder.math_renderer_name == 'imgmath'


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'extensions': ['sphinxcontrib.jsmath',
                                                  'sphinx.ext.mathjax'],
                                   'html_math_renderer': 'imgmath'})
def test_html_math_renderer_is_mismatched(make_app, app_params):
    try:
        args, kwargs = app_params
        make_app(*args, **kwargs)
        assert False
    except ConfigError as exc:
        assert str(exc) == "Unknown math_renderer 'imgmath' is given."


@pytest.mark.sphinx('html', testroot='basic')
def test_html_pygments_style_default(app):
    style = app.builder.highlighter.formatter_args.get('style')
    assert style.__name__ == 'Alabaster'


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'pygments_style': 'sphinx'})
def test_html_pygments_style_manually(app):
    style = app.builder.highlighter.formatter_args.get('style')
    assert style.__name__ == 'SphinxStyle'


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'html_theme': 'classic'})
def test_html_pygments_for_classic_theme(app):
    style = app.builder.highlighter.formatter_args.get('style')
    assert style.__name__ == 'SphinxStyle'


@pytest.mark.sphinx('html', testroot='basic')
def test_html_dark_pygments_style_default(app):
    assert app.builder.dark_highlighter is None


@pytest.mark.sphinx(testroot='basic', srcdir='validate_html_extra_path')
def test_validate_html_extra_path(app):
    (app.confdir / '_static').makedirs()
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
    (app.confdir / '_static').makedirs()
    app.config.html_static_path = [
        '/path/to/not_found',       # not found
        '_static',
        app.outdir,                 # outdir
        app.outdir / '_static',     # inside outdir
    ]
    validate_html_static_path(app, app.config)
    assert app.config.html_static_path == ['_static']


@pytest.mark.sphinx(testroot='html_scaled_image_link')
def test_html_scaled_image_link(app):
    app.build()
    context = (app.outdir / 'index.html').read_text()

    # no scaled parameters
    assert re.search('\n<img alt="_images/img.png" src="_images/img.png" />', context)

    # scaled_image_link
    assert re.search('\n<a class="reference internal image-reference" href="_images/img.png">'
                     '<img alt="_images/img.png" src="_images/img.png" style="[^"]+" /></a>',
                     context)

    # no-scaled-link class disables the feature
    assert re.search('\n<img alt="_images/img.png" class="no-scaled-link"'
                     ' src="_images/img.png" style="[^"]+" />',
                     context)


@pytest.mark.sphinx('html', testroot='reST-code-block',
                    confoverrides={'html_codeblock_linenos_style': 'table'})
def test_html_codeblock_linenos_style_table(app):
    app.build()
    content = (app.outdir / 'index.html').read_text()

    pygments_version = tuple(LooseVersion(pygments.__version__).version)
    if pygments_version >= (2, 8):
        assert ('<div class="linenodiv"><pre><span class="normal">1</span>\n'
                '<span class="normal">2</span>\n'
                '<span class="normal">3</span>\n'
                '<span class="normal">4</span></pre></div>') in content
    else:
        assert '<div class="linenodiv"><pre>1\n2\n3\n4</pre></div>' in content


@pytest.mark.sphinx('html', testroot='reST-code-block',
                    confoverrides={'html_codeblock_linenos_style': 'inline'})
def test_html_codeblock_linenos_style_inline(app):
    app.build()
    content = (app.outdir / 'index.html').read_text()

    pygments_version = tuple(LooseVersion(pygments.__version__).version)
    if pygments_version > (2, 7):
        assert '<span class="linenos">1</span>' in content
    else:
        assert '<span class="lineno">1 </span>' in content


@pytest.mark.sphinx('html', testroot='highlight_options')
def test_highlight_options(app):
    subject = app.builder.highlighter
    with patch.object(subject, 'highlight_block', wraps=subject.highlight_block) as highlight:
        app.build()

        call_args = highlight.call_args_list
        assert len(call_args) == 3
        assert call_args[0] == call(ANY, 'default', force=False, linenos=False,
                                    location=ANY, opts={'default_option': True})
        assert call_args[1] == call(ANY, 'python', force=False, linenos=False,
                                    location=ANY, opts={'python_option': True})
        assert call_args[2] == call(ANY, 'java', force=False, linenos=False,
                                    location=ANY, opts={})


@pytest.mark.sphinx('html', testroot='highlight_options',
                    confoverrides={'highlight_options': {'default_option': True}})
def test_highlight_options_old(app):
    subject = app.builder.highlighter
    with patch.object(subject, 'highlight_block', wraps=subject.highlight_block) as highlight:
        app.build()

        call_args = highlight.call_args_list
        assert len(call_args) == 3
        assert call_args[0] == call(ANY, 'default', force=False, linenos=False,
                                    location=ANY, opts={'default_option': True})
        assert call_args[1] == call(ANY, 'python', force=False, linenos=False,
                                    location=ANY, opts={})
        assert call_args[2] == call(ANY, 'java', force=False, linenos=False,
                                    location=ANY, opts={})


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'html_permalinks': False})
def test_html_permalink_disable(app):
    app.build()
    content = (app.outdir / 'index.html').read_text()

    assert '<h1>The basic Sphinx documentation for testing</h1>' in content


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'html_permalinks_icon': '<span>[PERMALINK]</span>'})
def test_html_permalink_icon(app):
    app.build()
    content = (app.outdir / 'index.html').read_text()

    assert ('<h1>The basic Sphinx documentation for testing<a class="headerlink" '
            'href="#the-basic-sphinx-documentation-for-testing" '
            'title="Permalink to this headline"><span>[PERMALINK]</span></a></h1>' in content)


@pytest.mark.sphinx('html', testroot='html_signaturereturn_icon')
def test_html_signaturereturn_icon(app):
    app.build()
    content = (app.outdir / 'index.html').read_text()

    assert ('<span class="sig-return-icon">&#x2192;</span>' in content)
