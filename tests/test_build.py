# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test the entire build process with the test root.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
import difflib
import htmlentitydefs
from StringIO import StringIO
from subprocess import Popen, PIPE

from util import *
from etree13 import ElementTree as ET

try:
    import pygments
except ImportError:
    pygments = None

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder
from sphinx.writers.latex import LaTeXTranslator


def teardown_module():
    (test_root / '_build').rmtree(True)


html_warnfile = StringIO()
latex_warnfile = StringIO()

ENV_WARNINGS = """\
%(root)s/images.txt:9: WARNING: image file not readable: foo.png
%(root)s/images.txt:23: WARNING: nonlocal image URI found: \
http://www.python.org/logo.png
%(root)s/includes.txt:: (WARNING/2) Encoding 'utf-8-sig' used for reading \
included file u'wrongenc.inc' seems to be wrong, try giving an :encoding: option
%(root)s/includes.txt:4: WARNING: download file not readable: nonexisting.png
"""

HTML_WARNINGS = ENV_WARNINGS + """\
%(root)s/images.txt:20: WARNING: no matching candidate for image URI u'foo.*'
%(root)s/markup.txt:: WARNING: invalid index entry u''
%(root)s/markup.txt:: WARNING: invalid pair index entry u''
%(root)s/markup.txt:: WARNING: invalid pair index entry u'keyword; '
"""

LATEX_WARNINGS = ENV_WARNINGS + """\
None:None: WARNING: no matching candidate for image URI u'foo.*'
WARNING: invalid pair index entry u''
"""

HTML_XPATH = {
    'images.html': {
        ".//img[@src='_images/img.png']": '',
        ".//img[@src='_images/img1.png']": '',
        ".//img[@src='_images/simg.png']": '',
        ".//object[@data='_images/svgimg.svg']": '',
        ".//embed[@src='_images/svgimg.svg']": '',
    },
    'subdir/images.html': {
        ".//img[@src='../_images/img1.png']": '',
        ".//img[@src='../_images/rimg.png']": '',
    },
    'subdir/includes.html': {
        ".//a[@href='../_downloads/img.png']": '',
    },
    'includes.html': {
        ".//pre": u'Max Strauß',
        ".//a[@href='_downloads/img.png']": '',
        ".//a[@href='_downloads/img1.png']": '',
        ".//pre": u'"quotes"',
        ".//pre": u"'included'",
    },
    'autodoc.html': {
        ".//dt[@id='test_autodoc.Class']": '',
        ".//dt[@id='test_autodoc.function']/em": r'\*\*kwds',
        ".//dd": r'Return spam\.',
    },
    'markup.html': {
        ".//meta[@name='author'][@content='Me']": '',
        ".//meta[@name='keywords'][@content='docs, sphinx']": '',
        ".//a[@href='contents.html#ref1']": '',
        ".//div[@id='label']": '',
        ".//span[@class='option']": '--help',
        ".//p": 'A global substitution.',
        ".//p": 'In HTML.',
        ".//p": 'In both.',
        ".//p": 'Always present',
        ".//title": 'set by title directive',
        ".//span[@class='pre']": 'CFunction()',
    },
    'desc.html': {
        ".//dt[@id='mod.Cls.meth1']": '',
        ".//dt[@id='errmod.Error']": '',
        ".//a[@href='#mod.Cls']": '',
        ".//dl[@class='userdesc']": '',
        ".//dt[@id='userdescrole-myobj']": '',
        ".//a[@href='#userdescrole-myobj']": '',
    },
    'contents.html': {
        ".//meta[@name='hc'][@content='hcval']": '',
        ".//meta[@name='hc_co'][@content='hcval_co']": '',
        ".//meta[@name='testopt'][@content='testoverride']": '',
        #".//td[@class='label']": r'\[Ref1\]',   # docutils 0.5 only
        ".//td[@class='label']": '',
        ".//li[@class='toctree-l1']/a": 'Testing various markup',
        ".//li[@class='toctree-l2']/a": 'Admonitions',
        ".//title": 'Sphinx <Tests>',
        ".//div[@class='footer']": 'Georg Brandl & Team',
        ".//a[@href='http://python.org/']": '',
    },
    'bom.html': {
        ".//title": " File with UTF-8 BOM",
    },
    '_static/statictmpl.html': {
        ".//project": 'Sphinx <Tests>',
    },
}

if pygments:
    HTML_XPATH['includes.html'].update({
        ".//pre/span[@class='s']": u'üöä',
        ".//div[@class='inc-pyobj1 highlight-text']/div/pre":
            r'^class Foo:\n    pass\n\s*$',
        ".//div[@class='inc-pyobj2 highlight-text']/div/pre":
            r'^    def baz\(\):\n        pass\n\s*$',
        ".//div[@class='inc-lines highlight-text']/div/pre":
            r'^class Foo:\n    pass\nclass Bar:\n$',
        ".//div[@class='inc-startend highlight-text']/div/pre":
            ur'^foo = u"Including Unicode characters: üöä"\n$',
        ".//div[@class='inc-pyobj-dedent highlight-python']/div/pre/span":
            r'def',
    })
    HTML_XPATH['subdir/includes.html'].update({
        ".//pre/span": 'line 1',
        ".//pre/span": 'line 2',
    })

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

@gen_with_app(buildername='html', warning=html_warnfile, cleanenv=True,
              confoverrides={'html_context.hckey_co': 'hcval_co'},
              tags=['testtag'])
def test_html(app):
    app.builder.build_all()
    html_warnings = html_warnfile.getvalue().replace(os.sep, '/')
    html_warnings_exp = HTML_WARNINGS % {'root': app.srcdir}
    assert html_warnings == html_warnings_exp, 'Warnings don\'t match:\n' + \
           '\n'.join(difflib.ndiff(html_warnings_exp.splitlines(),
                                   html_warnings.splitlines()))

    for fname, paths in HTML_XPATH.iteritems():
        parser = NslessParser()
        parser.entity.update(htmlentitydefs.entitydefs)
        etree = ET.parse(os.path.join(app.outdir, fname), parser)
        for path, check in paths.iteritems():
            yield check_xpath, etree, fname, path, check


@with_app(buildername='latex', warning=latex_warnfile, cleanenv=True)
def test_latex(app):
    LaTeXTranslator.ignore_missing_images = True
    app.builder.build_all()
    latex_warnings = latex_warnfile.getvalue().replace(os.sep, '/')
    latex_warnings_exp = LATEX_WARNINGS % {'root': app.srcdir}
    assert latex_warnings == latex_warnings_exp, 'Warnings don\'t match:\n' + \
           '\n'.join(difflib.ndiff(latex_warnings_exp.splitlines(),
                                   latex_warnings.splitlines()))
    # file from latex_additional_files
    assert (app.outdir / 'svgimg.svg').isfile()

    # only run latex if all needed packages are there
    def kpsetest(filename):
        try:
            p = Popen(['kpsewhich', filename], stdout=PIPE)
        except OSError, err:
            # no kpsewhich... either no tex distribution is installed or it is
            # a "strange" one -- don't bother running latex
            return None
        else:
            p.communicate()
            if p.returncode != 0:
                # not found
                return False
            # found
            return True

    if kpsetest('article.sty') is None:
        print >>sys.stderr, \
              'info: not running latex, it doesn\'t seem to be installed'
        return
    for filename in ['fancyhdr.sty', 'fancybox.sty', 'titlesec.sty',
                     'amsmath.sty', 'framed.sty', 'color.sty', 'fancyvrb.sty',
                     'threeparttable.sty']:
        if not kpsetest(filename):
            print >>sys.stderr, \
                  'info: not running latex, the %s package doesn\'t ' \
                  'seem to be installed' % filename
            return

    # now, try to run latex over it
    cwd = os.getcwd()
    os.chdir(app.outdir)
    try:
        try:
            p = Popen(['pdflatex', '--interaction=nonstopmode',
                       'SphinxTests.tex'], stdout=PIPE, stderr=PIPE)
        except OSError, err:
            pass  # most likely pdflatex was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print stdout
                del app.cleanup_trees[:]
                assert False, 'latex exited with error'
    finally:
        os.chdir(cwd)

# just let the remaining ones run for now

@with_app(buildername='pickle')
def test_pickle(app):
    app.builder.build_all()

@with_app(buildername='linkcheck')
def test_linkcheck(app):
    app.builder.build_all()

@with_app(buildername='text')
def test_text(app):
    app.builder.build_all()

@with_app(buildername='htmlhelp')
def test_htmlhelp(app):
    app.builder.build_all()

@with_app(buildername='qthelp')
def test_qthelp(app):
    app.builder.build_all()

@with_app(buildername='changes', cleanenv=True)
def test_changes(app):
    app.builder.build_all()
