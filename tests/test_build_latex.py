# -*- coding: utf-8 -*-
"""
    test_build_latex
    ~~~~~~~~~~~~~~~~

    Test the build process with LaTeX builder with the test root.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import re
from subprocess import Popen, PIPE

from six import PY3

from sphinx.writers.latex import LaTeXTranslator

from util import SkipTest, remove_unicode_literals, with_app
from test_build_html import ENV_WARNINGS


LATEX_WARNINGS = ENV_WARNINGS + """\
None:None: WARNING: citation not found: missing
None:None: WARNING: no matching candidate for image URI u'foo.\\*'
WARNING: invalid pair index entry u''
WARNING: invalid pair index entry u'keyword; '
"""

if PY3:
    LATEX_WARNINGS = remove_unicode_literals(LATEX_WARNINGS)


@with_app(buildername='latex')
def test_latex(app, status, warning):
    LaTeXTranslator.ignore_missing_images = True
    app.builder.build_all()
    latex_warnings = warning.getvalue().replace(os.sep, '/')
    latex_warnings_exp = LATEX_WARNINGS % {
        'root': re.escape(app.srcdir.replace(os.sep, '/'))}
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
        raise SkipTest('not running latex, it doesn\'t seem to be installed')
    for filename in ['fancyhdr.sty', 'fancybox.sty', 'titlesec.sty',
                     'amsmath.sty', 'framed.sty', 'color.sty', 'fancyvrb.sty',
                     'threeparttable.sty']:
        if not kpsetest(filename):
            raise SkipTest('not running latex, the %s package doesn\'t '
                           'seem to be installed' % filename)

    # now, try to run latex over it
    cwd = os.getcwd()
    os.chdir(app.outdir)
    try:
        try:
            p = Popen(['pdflatex', '--interaction=nonstopmode',
                       'SphinxTests.tex'], stdout=PIPE, stderr=PIPE)
        except OSError:
            raise SkipTest  # most likely pdflatex was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print(stdout)
                print(stderr)
                del app.cleanup_trees[:]
                assert False, 'latex exited with return code %s' % p.returncode
    finally:
        os.chdir(cwd)


@with_app(buildername='latex')
def test_latex_add_latex_package(app, status, warning):
    app.add_latex_package('foo')
    app.add_latex_package('bar', 'baz')
    app.builder.build_all()
    assert '\\usepackage{foo}' in (app.outdir / 'SphinxTests.tex').text()
    assert '\\usepackage[baz]{bar}' in (app.outdir / 'SphinxTests.tex').text()
