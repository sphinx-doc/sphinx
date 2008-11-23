# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test the entire build process with the test root.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

import os
import sys
import difflib
import htmlentitydefs
from StringIO import StringIO
from subprocess import Popen, PIPE

from util import *
from etree13 import ElementTree as ET

from sphinx.builder import StandaloneHTMLBuilder, LaTeXBuilder
from sphinx.latexwriter import LaTeXTranslator


html_warnfile = StringIO()
latex_warnfile = StringIO()

ENV_WARNINGS = """\
WARNING: %(root)s/images.txt:9: Image file not readable: foo.png
WARNING: %(root)s/images.txt:21: Nonlocal image URI found: http://www.python.org/logo.png
WARNING: %(root)s/includes.txt:: (WARNING/2) Encoding 'utf-8' used for reading included \
file u'wrongenc.inc' seems to be wrong, try giving an :encoding: option
"""

HTML_WARNINGS = ENV_WARNINGS + """\
WARNING: %(root)s/images.txt:: no matching candidate for image URI u'foo.*'
"""

LATEX_WARNINGS = ENV_WARNINGS + """\
WARNING: None:: no matching candidate for image URI u'foo.*'
"""

HTML_XPATH = {
    'images.html': {
        ".//img[@src='_images/img.png']": '',
        ".//img[@src='_images/img1.png']": '',
        ".//img[@src='_images/simg.png']": '',
    },
    'includes.html': {
        ".//pre/span[@class='s']": u'üöä',
        ".//pre": u'Max Strauß',
    },
    'autodoc.html': {
        ".//dt[@id='test_autodoc.Class']": '',
        ".//dt[@id='test_autodoc.function']/em": '**kwds',
        ".//dd": 'Return spam.',
    },
    'markup.html': {
        ".//meta[@name='author'][@content='Me']": '',
        ".//meta[@name='keywords'][@content='docs, sphinx']": '',
        ".//a[@href='contents.html#ref1']": '',
        ".//div[@id='label']": '',
        ".//span[@class='option']": '--help',
    },
    'desc.html': {
        ".//dt[@id='mod.Cls.meth1']": '',
        ".//dt[@id='errmod.Error']": '',
        ".//a[@href='#mod.Cls']": '',
    },
    'contents.html': {
        ".//meta[@name='hc'][@content='hcval']": '',
        ".//td[@class='label']": '[Ref1]',
        ".//li[@class='toctree-l1']/a": 'Testing various markup',
        ".//li[@class='toctree-l2']/a": 'Admonitions',
        ".//title": 'Sphinx <Tests>',
        ".//div[@class='footer']": 'Georg Brandl & Team',
    },
}

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


@with_app(buildername='html', warning=html_warnfile)
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
        for path, text in paths.iteritems():
            nodes = list(etree.findall(path))
            assert nodes != []
            if not text:
                # only check for node presence
                continue
            for node in nodes:
                if node.text and text in node.text:
                    break
            else:
                assert False, ('%r not found in any node matching '
                               'path %s in %s' % (text, path, fname))


@with_app(buildername='latex', warning=latex_warnfile)
def test_latex(app):
    LaTeXTranslator.ignore_missing_images = True
    app.builder.build_all()
    latex_warnings = latex_warnfile.getvalue().replace(os.sep, '/')
    latex_warnings_exp = LATEX_WARNINGS % {'root': app.srcdir}
    assert latex_warnings == latex_warnings_exp, 'Warnings don\'t match:\n' + \
           '\n'.join(difflib.ndiff(latex_warnings_exp.splitlines(),
                                   latex_warnings.splitlines()))

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
        print >>sys.stderr, 'info: not running latex, it doesn\'t seem to be installed'
        return
    for filename in ['fancyhdr.sty', 'fancybox.sty', 'titlesec.sty', 'amsmath.sty',
                     'framed.sty', 'color.sty', 'fancyvrb.sty', 'threeparttable.sty']:
        if not kpsetest(filename):
            print >>sys.stderr, 'info: not running latex, the %s package doesn\'t ' \
                  'seem to be installed' % filename
            return

    # now, try to run latex over it
    cwd = os.getcwd()
    os.chdir(app.outdir)
    try:
        try:
            p = Popen(['pdflatex', '--interaction=nonstopmode', 'SphinxTests.tex'],
                      stdout=PIPE, stderr=PIPE)
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

@with_app(buildername='linkcheck')
def test_linkcheck(app):
    app.builder.build_all()

@with_app(buildername='text')
def test_text(app):
    app.builder.build_all()

@with_app(buildername='changes', cleanenv=True)
def test_changes(app):
    app.builder.build_all()
