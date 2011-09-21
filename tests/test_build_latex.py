# -*- coding: utf-8 -*-
"""
    test_build_latex
    ~~~~~~~~~~~~~~~~

    Test the build process with LaTeX builder with the test root.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
from StringIO import StringIO
from subprocess import Popen, PIPE

from sphinx.writers.latex import LaTeXTranslator

from util import *
from test_build_html import ENV_WARNINGS


def teardown_module():
    (test_root / '_build').rmtree(True)


latex_warnfile = StringIO()

LATEX_WARNINGS = ENV_WARNINGS + """\
None:None: WARNING: no matching candidate for image URI u'foo.\\*'
WARNING: invalid pair index entry u''
WARNING: invalid pair index entry u'keyword; '
"""

if sys.version_info >= (3, 0):
    LATEX_WARNINGS = remove_unicode_literals(LATEX_WARNINGS)


@with_app(buildername='latex', warning=latex_warnfile, cleanenv=True)
def test_latex(app):
    LaTeXTranslator.ignore_missing_images = True
    app.builder.build_all()
    latex_warnings = latex_warnfile.getvalue().replace(os.sep, '/')
    latex_warnings_exp = LATEX_WARNINGS % {'root': re.escape(app.srcdir)}
    assert re.match(latex_warnings_exp + '$', latex_warnings), \
           'Warnings don\'t match:\n' + \
           '--- Expected (regex):\n' + latex_warnings_exp + \
           '--- Got:\n' + latex_warnings

    # file from latex_additional_files
    assert (app.outdir / 'svgimg.svg').isfile()

    # only run latex if all needed packages are there
    def kpsetest(filename):
        try:
            p = Popen(['kpsewhich', filename], stdout=PIPE)
        except OSError:
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
        except OSError:
            pass  # most likely pdflatex was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print stdout
                print stderr
                del app.cleanup_trees[:]
                assert False, 'latex exited with return code %s' % p.returncode
    finally:
        os.chdir(cwd)
