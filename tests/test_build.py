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
from StringIO import StringIO
from subprocess import Popen, PIPE

from sphinx.builders.latex import LaTeXBuilder
from sphinx.writers.latex import LaTeXTranslator

from util import *


def teardown_module():
    (test_root / '_build').rmtree(True)


latex_warnfile = StringIO()

ENV_WARNINGS = """\
%(root)s/images.txt:9: WARNING: image file not readable: foo.png
%(root)s/images.txt:23: WARNING: nonlocal image URI found: \
http://www.python.org/logo.png
%(root)s/includes.txt:: (WARNING/2) Encoding 'utf-8-sig' used for reading \
included file u'wrongenc.inc' seems to be wrong, try giving an :encoding: option
%(root)s/includes.txt:4: WARNING: download file not readable: nonexisting.png
"""

LATEX_WARNINGS = ENV_WARNINGS + """\
None:None: WARNING: no matching candidate for image URI u'foo.*'
WARNING: invalid pair index entry u''
"""


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

@with_app(buildername='epub')
def test_epub(app):
    app.builder.build_all()

@with_app(buildername='changes')
def test_changes(app):
    app.builder.build_all()

@with_app(buildername='singlehtml', cleanenv=True)
def test_singlehtml(app):
    app.builder.build_all()
