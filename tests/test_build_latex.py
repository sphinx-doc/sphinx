# -*- coding: utf-8 -*-
"""
    test_build_latex
    ~~~~~~~~~~~~~~~~

    Test the build process with LaTeX builder with the test root.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
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


@with_app(buildername='latex',
          confoverrides={'latex_documents': [
              ('contents', 'SphinxTests.tex', 'Sphinx Tests Documentation',
               'Georg Brandl \\and someone else', 'howto'),
          ]},
          srcdir='latex_howto')
def test_latex_howto(app, status, warning):
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
                app.cleanup()
                assert False, 'latex exited with return code %s' % p.returncode
    finally:
        os.chdir(cwd)


@with_app(buildername='latex', testroot='numfig',
          confoverrides={'numfig': True})
def test_numref(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Fig. }}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Table }}' in result
    assert '\\floatname{literal-block}{Listing }' in result
    assert '\\hyperref[index:fig1]{Fig. \\ref{index:fig1}}' in result
    assert '\\hyperref[baz:fig22]{Figure\\ref{baz:fig22}}' in result
    assert '\\hyperref[index:table-1]{Table \\ref{index:table-1}}' in result
    assert '\\hyperref[baz:table22]{Table:\\ref{baz:table22}}' in result
    assert '\\hyperref[index:code-1]{Listing \\ref{index:code-1}}' in result
    assert '\\hyperref[baz:code22]{Code-\\ref{baz:code22}}' in result


@with_app(buildername='latex', testroot='numfig',
          confoverrides={'numfig': True,
                         'numfig_format': {'figure': 'Figure:%s',
                                           'table': 'Tab_%s',
                                           'code-block': 'Code-%s'}})
def test_numref_with_prefix1(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Figure:}}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Tab\\_}}' in result
    assert '\\floatname{literal-block}{Code-}' in result
    assert '\\ref{index:fig1}' in result
    assert '\\ref{baz:fig22}' in result
    assert '\\ref{index:table-1}' in result
    assert '\\ref{baz:table22}' in result
    assert '\\ref{index:code-1}' in result
    assert '\\ref{baz:code22}' in result
    assert '\\hyperref[index:fig1]{Figure:\\ref{index:fig1}}' in result
    assert '\\hyperref[baz:fig22]{Figure\\ref{baz:fig22}}' in result
    assert '\\hyperref[index:table-1]{Tab\\_\\ref{index:table-1}}' in result
    assert '\\hyperref[baz:table22]{Table:\\ref{baz:table22}}' in result
    assert '\\hyperref[index:code-1]{Code-\\ref{index:code-1}}' in result
    assert '\\hyperref[baz:code22]{Code-\\ref{baz:code22}}' in result


@with_app(buildername='latex', testroot='numfig',
          confoverrides={'numfig': True,
                         'numfig_format': {'figure': 'Figure:%s.',
                                           'table': 'Tab_%s:',
                                           'code-block': 'Code-%s | '}})
def test_numref_with_prefix2(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Figure:}}' in result
    assert '\\def\\fnum@figure{\\figurename\\thefigure.}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Tab\\_}}' in result
    assert '\\def\\fnum@table{\\tablename\\thetable:}' in result
    assert '\\floatname{literal-block}{Code-}' in result
    assert '\\hyperref[index:fig1]{Figure:\\ref{index:fig1}.}' in result
    assert '\\hyperref[baz:fig22]{Figure\\ref{baz:fig22}}' in result
    assert '\\hyperref[index:table-1]{Tab\\_\\ref{index:table-1}:}' in result
    assert '\\hyperref[baz:table22]{Table:\\ref{baz:table22}}' in result
    assert '\\hyperref[index:code-1]{Code-\\ref{index:code-1} \\textbar{} }' in result
    assert '\\hyperref[baz:code22]{Code-\\ref{baz:code22}}' in result


@with_app(buildername='latex', testroot='numfig',
          confoverrides={'numfig': True, 'language': 'el'})
def test_numref_with_language_el(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\addto\\captionsgreek{\\renewcommand{\\figurename}{Fig. }}' in result
    assert '\\addto\\captionsgreek{\\renewcommand{\\tablename}{Table }}' in result
    assert '\\floatname{literal-block}{Listing }' in result
    assert '\\hyperref[index:fig1]{Fig. \\ref{index:fig1}}' in result
    assert '\\hyperref[baz:fig22]{Figure\\ref{baz:fig22}}' in result
    assert '\\hyperref[index:table-1]{Table \\ref{index:table-1}}' in result
    assert '\\hyperref[baz:table22]{Table:\\ref{baz:table22}}' in result
    assert '\\hyperref[index:code-1]{Listing \\ref{index:code-1}}' in result
    assert '\\hyperref[baz:code22]{Code-\\ref{baz:code22}}' in result


@with_app(buildername='latex', testroot='numfig',
          confoverrides={'numfig': True, 'language': 'ja'})
def test_numref_with_language_ja(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert u'\\renewcommand{\\figurename}{\u56f3 }' in result
    assert '\\renewcommand{\\tablename}{TABLE }' in result
    assert '\\floatname{literal-block}{LIST }' in result
    assert u'\\hyperref[index:fig1]{\u56f3 \\ref{index:fig1}}' in result
    assert '\\hyperref[baz:fig22]{Figure\\ref{baz:fig22}}' in result
    assert '\\hyperref[index:table-1]{TABLE \\ref{index:table-1}}' in result
    assert '\\hyperref[baz:table22]{Table:\\ref{baz:table22}}' in result
    assert '\\hyperref[index:code-1]{LIST \\ref{index:code-1}}' in result
    assert '\\hyperref[baz:code22]{Code-\\ref{baz:code22}}' in result


@with_app(buildername='latex')
def test_latex_add_latex_package(app, status, warning):
    app.add_latex_package('foo')
    app.add_latex_package('bar', 'baz')
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')
    assert '\\usepackage{foo}' in result
    assert '\\usepackage[baz]{bar}' in result


@with_app(buildername='latex', testroot='contentsname')
def test_contentsname(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\addto\\captionsenglish{\\renewcommand{\\contentsname}{Table of content}}'
            in result)


@with_app(buildername='latex', testroot='contentsname',
          confoverrides={'language': 'ja'})
def test_contentsname_with_language_ja(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\renewcommand{\\contentsname}{Table of content}' in result


@with_app(buildername='latex')
def test_footnote(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\footnote[1]{\nnumbered\n}' in result
    assert '\\footnote[2]{\nauto numbered\n}' in result
    assert '\\footnote[3]{\nnamed\n}' in result
    assert '{\\hyperref[footnote:bar]{\\emph{{[}bar{]}}}}' in result
    assert '\\bibitem[bar]{bar}{\\phantomsection\\label{footnote:bar} ' in result
    assert '\\bibitem[bar]{bar}{\\phantomsection\\label{footnote:bar} \ncite' in result
    assert '\\bibitem[bar]{bar}{\\phantomsection\\label{footnote:bar} \ncite\n}' in result
    assert 'name \\footnotemark[5]' in result
    assert '\\end{threeparttable}\n\n\\footnotetext[5]{\nfootnotes in table\n}' in result
