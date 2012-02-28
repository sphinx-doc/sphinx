# -*- coding: utf-8 -*-
"""
    test_build_html
    ~~~~~~~~~~~~~~~

    Test the HTML builder and check output against XPath.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
import htmlentitydefs
from StringIO import StringIO

try:
    import pygments
except ImportError:
    pygments = None

from sphinx import __version__
from util import *
from etree13 import ElementTree as ET


def teardown_module():
    (test_root / '_build').rmtree(True)


html_warnfile = StringIO()

ENV_WARNINGS = """\
%(root)s/autodoc_fodder.py:docstring of autodoc_fodder\\.MarkupError:2: \
WARNING: Explicit markup ends without a blank line; unexpected \
unindent\\.\\n?
%(root)s/images.txt:9: WARNING: image file not readable: foo.png
%(root)s/images.txt:23: WARNING: nonlocal image URI found: \
http://www.python.org/logo.png
%(root)s/includes.txt:\\d*: WARNING: Encoding 'utf-8-sig' used for \
reading included file u'.*?wrongenc.inc' seems to be wrong, try giving an \
:encoding: option\\n?
%(root)s/includes.txt:4: WARNING: download file not readable: .*?nonexisting.png
%(root)s/objects.txt:\\d*: WARNING: using old C markup; please migrate to \
new-style markup \(e.g. c:function instead of cfunction\), see \
http://sphinx.pocoo.org/domains.html
"""

HTML_WARNINGS = ENV_WARNINGS + """\
%(root)s/images.txt:20: WARNING: no matching candidate for image URI u'foo.\\*'
%(root)s/markup.txt:: WARNING: invalid single index entry u''
%(root)s/markup.txt:: WARNING: invalid pair index entry u''
%(root)s/markup.txt:: WARNING: invalid pair index entry u'keyword; '
"""

if sys.version_info >= (3, 0):
    ENV_WARNINGS = remove_unicode_literals(ENV_WARNINGS)
    HTML_WARNINGS = remove_unicode_literals(HTML_WARNINGS)


def tail_check(check):
    rex = re.compile(check)
    def checker(nodes):
        for node in nodes:
            if node.tail and rex.search(node.tail):
                return True
        assert False, '%r not found in tail of any nodes %s' % (check, nodes)
    return checker


HTML_XPATH = {
    'images.html': [
        (".//img[@src='_images/img.png']", ''),
        (".//img[@src='_images/img1.png']", ''),
        (".//img[@src='_images/simg.png']", ''),
        (".//img[@src='_images/svgimg.svg']", ''),
    ],
    'subdir/images.html': [
        (".//img[@src='../_images/img1.png']", ''),
        (".//img[@src='../_images/rimg.png']", ''),
    ],
    'subdir/includes.html': [
        (".//a[@href='../_downloads/img.png']", ''),
        (".//img[@src='../_images/img.png']", ''),
        (".//p", 'This is an include file.'),
    ],
    'includes.html': [
        (".//pre", u'Max Strauß'),
        (".//a[@href='_downloads/img.png']", ''),
        (".//a[@href='_downloads/img1.png']", ''),
        (".//pre", u'"quotes"'),
        (".//pre", u"'included'"),
    ],
    'autodoc.html': [
        (".//dt[@id='test_autodoc.Class']", ''),
        (".//dt[@id='test_autodoc.function']/em", r'\*\*kwds'),
        (".//dd/p", r'Return spam\.'),
    ],
    'extapi.html': [
        (".//strong", 'from function: Foo'),
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
        (".//p[@class='first admonition-title']", 'My Admonition'),
        (".//p[@class='last']", 'Note text.'),
        (".//p[@class='last']", 'Warning text.'),
        # inline markup
        (".//li/strong", r'^command\\n$'),
        (".//li/strong", r'^program\\n$'),
        (".//li/em", r'^dfn\\n$'),
        (".//li/tt/span[@class='pre']", r'^kbd\\n$'),
        (".//li/em", u'File \N{TRIANGULAR BULLET} Close'),
        (".//li/tt/span[@class='pre']", '^a/$'),
        (".//li/tt/em/span[@class='pre']", '^varpart$'),
        (".//li/tt/em/span[@class='pre']", '^i$'),
        (".//a[@href='http://www.python.org/dev/peps/pep-0008']"
            "[@class='pep reference external']/strong", 'PEP 8'),
        (".//a[@href='http://tools.ietf.org/html/rfc1.html']"
            "[@class='rfc reference external']/strong", 'RFC 1'),
        (".//a[@href='objects.html#envvar-HOME']"
            "[@class='reference internal']/tt/span[@class='pre']", 'HOME'),
        (".//a[@href='#with']"
            "[@class='reference internal']/tt/span[@class='pre']", '^with$'),
        (".//a[@href='#grammar-token-try_stmt']"
            "[@class='reference internal']/tt/span", '^statement$'),
        (".//a[@href='subdir/includes.html']"
            "[@class='reference internal']/em", 'Including in subdir'),
        (".//a[@href='objects.html#cmdoption-python-c']"
            "[@class='reference internal']/em", 'Python -c option'),
        # abbreviations
        (".//abbr[@title='abbreviation']", '^abbr$'),
        # version stuff
        (".//span[@class='versionmodified']", 'New in version 0.6'),
        # footnote reference
        (".//a[@class='footnote-reference']", r'\[1\]'),
        # created by reference lookup
        (".//a[@href='contents.html#ref1']", ''),
        # ``seealso`` directive
        (".//div/p[@class='first admonition-title']", 'See also'),
        # a ``hlist`` directive
        (".//table[@class='hlist']/tr/td/ul/li", '^This$'),
        # a ``centered`` directive
        (".//p[@class='centered']/strong", 'LICENSE'),
        # a glossary
        (".//dl/dt[@id='term-boson']", 'boson'),
        # a production list
        (".//pre/strong", 'try_stmt'),
        (".//pre/a[@href='#grammar-token-try1_stmt']/tt/span", 'try1_stmt'),
        # tests for ``only`` directive
        (".//p", 'A global substitution.'),
        (".//p", 'In HTML.'),
        (".//p", 'In both.'),
        (".//p", 'Always present'),
    ],
    'objects.html': [
        (".//dt[@id='mod.Cls.meth1']", ''),
        (".//dt[@id='errmod.Error']", ''),
        (".//dt/tt", r'long\(parameter,\s* list\)'),
        (".//dt/tt", 'another one'),
        (".//a[@href='#mod.Cls'][@class='reference internal']", ''),
        (".//dl[@class='userdesc']", ''),
        (".//dt[@id='userdesc-myobj']", ''),
        (".//a[@href='#userdesc-myobj'][@class='reference internal']", ''),
        # C references
        (".//span[@class='pre']", 'CFunction()'),
        (".//a[@href='#Sphinx_DoSomething']", ''),
        (".//a[@href='#SphinxStruct.member']", ''),
        (".//a[@href='#SPHINX_USE_PYTHON']", ''),
        (".//a[@href='#SphinxType']", ''),
        (".//a[@href='#sphinx_global']", ''),
        # reference from old C markup extension
        (".//a[@href='#Sphinx_Func']", ''),
        # test global TOC created by toctree()
        (".//ul[@class='current']/li[@class='toctree-l1 current']/a[@href='']",
            'Testing object descriptions'),
        (".//li[@class='toctree-l1']/a[@href='markup.html']",
            'Testing various markup'),
        # custom sidebar
        (".//h4", 'Custom sidebar'),
        # docfields
        (".//td[@class='field-body']/strong", '^moo$'),
        (".//td[@class='field-body']/strong",
             tail_check(r'\(Moo\) .* Moo')),
        (".//td[@class='field-body']/ul/li/strong", '^hour$'),
        (".//td[@class='field-body']/ul/li/em", '^DuplicateType$'),
        (".//td[@class='field-body']/ul/li/em",
             tail_check(r'.* Some parameter')),
    ],
    'contents.html': [
        (".//meta[@name='hc'][@content='hcval']", ''),
        (".//meta[@name='hc_co'][@content='hcval_co']", ''),
        (".//meta[@name='testopt'][@content='testoverride']", ''),
        (".//td[@class='label']", r'\[Ref1\]'),
        (".//td[@class='label']", ''),
        (".//li[@class='toctree-l1']/a", 'Testing various markup'),
        (".//li[@class='toctree-l2']/a", 'Inline markup'),
        (".//title", 'Sphinx <Tests>'),
        (".//div[@class='footer']", 'Georg Brandl & Team'),
        (".//a[@href='http://python.org/']"
            "[@class='reference external']", ''),
        (".//li/a[@href='genindex.html']/em", 'Index'),
        (".//li/a[@href='py-modindex.html']/em", 'Module Index'),
        (".//li/a[@href='search.html']/em", 'Search Page'),
        # custom sidebar only for contents
        (".//h4", 'Contents sidebar'),
        # custom JavaScript
        (".//script[@src='file://moo.js']", ''),
    ],
    'bom.html': [
        (".//title", " File with UTF-8 BOM"),
    ],
    'extensions.html': [
        (".//a[@href='http://python.org/dev/']", "http://python.org/dev/"),
        (".//a[@href='http://bugs.python.org/issue1000']", "issue 1000"),
        (".//a[@href='http://bugs.python.org/issue1042']", "explicit caption"),
    ],
    '_static/statictmpl.html': [
        (".//project", 'Sphinx <Tests>'),
    ],
    'genindex.html': [
        # index entries
        (".//a/strong", "Main"),
        (".//a/strong", "[1]"),
        (".//a/strong", "Other"),
        (".//a", "entry"),
        (".//dt/a", "double"),
    ]
}

if pygments:
    HTML_XPATH['includes.html'].extend([
        (".//pre/span[@class='s']", u'üöä'),
        (".//div[@class='inc-pyobj1 highlight-text']//pre",
            r'^class Foo:\n    pass\n\s*$'),
        (".//div[@class='inc-pyobj2 highlight-text']//pre",
            r'^    def baz\(\):\n        pass\n\s*$'),
        (".//div[@class='inc-lines highlight-text']//pre",
            r'^class Foo:\n    pass\nclass Bar:\n$'),
        (".//div[@class='inc-startend highlight-text']//pre",
            ur'^foo = "Including Unicode characters: üöä"\n$'),
        (".//div[@class='inc-preappend highlight-text']//pre",
            r'(?m)^START CODE$'),
        (".//div[@class='inc-pyobj-dedent highlight-python']//span",
            r'def'),
        (".//div[@class='inc-tab3 highlight-text']//pre",
            r'-| |-'),
        (".//div[@class='inc-tab8 highlight-python']//pre/span",
            r'-|      |-'),
    ])
    HTML_XPATH['subdir/includes.html'].extend([
        (".//pre/span", 'line 1'),
        (".//pre/span", 'line 2'),
    ])

class NslessParser(ET.XMLParser):
    """XMLParser that throws away namespaces in tag names."""

    def _fixname(self, key):
        try:
            return self._names[key]
        except KeyError:
            name = key
            br = name.find('}')
            if br > 0:
                name = name[br+1:]
            self._names[key] = name = self._fixtext(name)
            return name


def check_xpath(etree, fname, path, check):
    nodes = list(etree.findall(path))
    assert nodes != [], ('did not find any node matching xpath '
                         '%r in file %s' % (path, fname))
    if hasattr(check, '__call__'):
        check(nodes)
    elif not check:
        # only check for node presence
        pass
    else:
        rex = re.compile(check)
        for node in nodes:
            if node.text and rex.search(node.text):
                break
        else:
            assert False, ('%r not found in any node matching '
                           'path %s in %s: %r' % (check, path, fname,
                           [node.text for node in nodes]))

def check_static_entries(outdir):
    staticdir = outdir / '_static'
    assert staticdir.isdir()
    # a file from a directory entry in html_static_path
    assert (staticdir / 'README').isfile()
    # a directory from a directory entry in html_static_path
    assert (staticdir / 'subdir' / 'foo.css').isfile()
    # a file from a file entry in html_static_path
    assert (staticdir / 'templated.css').isfile()
    assert (staticdir / 'templated.css').text().splitlines()[1] == __version__
    # a file from _static, but matches exclude_patterns
    assert not (staticdir / 'excluded.css').exists()

@gen_with_app(buildername='html', warning=html_warnfile, cleanenv=True,
              confoverrides={'html_context.hckey_co': 'hcval_co'},
              tags=['testtag'])
def test_html(app):
    app.builder.build_all()
    html_warnings = html_warnfile.getvalue().replace(os.sep, '/')
    html_warnings_exp = HTML_WARNINGS % {'root': re.escape(app.srcdir)}
    assert re.match(html_warnings_exp + '$', html_warnings), \
           'Warnings don\'t match:\n' + \
           '--- Expected (regex):\n' + html_warnings_exp + \
           '--- Got:\n' + html_warnings

    for fname, paths in HTML_XPATH.iteritems():
        parser = NslessParser()
        parser.entity.update(htmlentitydefs.entitydefs)
        fp = open(os.path.join(app.outdir, fname))
        try:
            etree = ET.parse(fp, parser)
        finally:
            fp.close()
        for path, check in paths:
            yield check_xpath, etree, fname, path, check

    check_static_entries(app.builder.outdir)
