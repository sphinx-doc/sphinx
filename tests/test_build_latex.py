# -*- coding: utf-8 -*-
"""
    test_build_latex
    ~~~~~~~~~~~~~~~~

    Test the build process with LaTeX builder with the test root.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import re
from itertools import product
from shutil import copyfile
from subprocess import Popen, PIPE

import pytest
from six import PY3
from test_build_html import ENV_WARNINGS

from sphinx.errors import SphinxError
from sphinx.testing.util import remove_unicode_literals, strip_escseq
from sphinx.util import docutils
from sphinx.util.osutil import cd, ensuredir
from sphinx.writers.latex import LaTeXTranslator


LATEX_ENGINES = ['pdflatex', 'lualatex', 'xelatex']
DOCCLASSES = ['howto', 'manual']
STYLEFILES = ['article.cls', 'fancyhdr.sty', 'titlesec.sty', 'amsmath.sty',
              'framed.sty', 'color.sty', 'fancyvrb.sty',
              'fncychap.sty', 'geometry.sty', 'kvoptions.sty', 'hyperref.sty']

LATEX_WARNINGS = ENV_WARNINGS + """\
%(root)s/index.rst:\\d+: WARNING: unknown option: &option
%(root)s/index.rst:\\d+: WARNING: citation not found: missing
%(root)s/index.rst:\\d+: WARNING: a suitable image for latex builder not found: foo.\\*
%(root)s/index.rst:\\d+: WARNING: Could not lex literal_block as "c". Highlighting skipped.
"""

if PY3:
    LATEX_WARNINGS = remove_unicode_literals(LATEX_WARNINGS)


# only run latex if all needed packages are there
def kpsetest(*filenames):
    try:
        p = Popen(['kpsewhich'] + list(filenames), stdout=PIPE)
    except OSError:
        # no kpsewhich... either no tex distribution is installed or it is
        # a "strange" one -- don't bother running latex
        return False
    else:
        p.communicate()
        if p.returncode != 0:
            # not found
            return False
        # found
        return True


# compile latex document with app.config.latex_engine
def compile_latex_document(app):
    # now, try to run latex over it
    with cd(app.outdir):
        try:
            ensuredir(app.config.latex_engine)
            # keep a copy of latex file for this engine in case test fails
            copyfile('SphinxTests.tex',
                     app.config.latex_engine + '/SphinxTests.tex')
            p = Popen([app.config.latex_engine,
                       '--interaction=nonstopmode',
                       '-output-directory=%s' % app.config.latex_engine,
                       'SphinxTests.tex'],
                      stdout=PIPE, stderr=PIPE)
        except OSError:  # most likely the latex executable was not found
            raise pytest.skip.Exception
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print(stdout)
                print(stderr)
                assert False, '%s exited with return code %s' % (
                    app.config.latex_engine, p.returncode)


def skip_if_requested(testfunc):
    if 'SKIP_LATEX_BUILD' in os.environ:
        msg = 'Skip LaTeX builds because SKIP_LATEX_BUILD is set'
        return pytest.mark.skipif(True, reason=msg)(testfunc)
    else:
        return testfunc


def skip_if_stylefiles_notfound(testfunc):
    if kpsetest(*STYLEFILES) is False:
        msg = 'not running latex, the required styles do not seem to be installed'
        return pytest.mark.skipif(True, reason=msg)(testfunc)
    else:
        return testfunc


@skip_if_requested
@skip_if_stylefiles_notfound
@pytest.mark.parametrize(
    "engine,docclass",
    product(LATEX_ENGINES, DOCCLASSES),
)
@pytest.mark.sphinx('latex')
def test_build_latex_doc(app, status, warning, engine, docclass):
    app.config.latex_engine = engine
    app.config.latex_documents[0] = app.config.latex_documents[0][:4] + (docclass,)

    LaTeXTranslator.ignore_missing_images = True
    app.builder.build_all()

    # file from latex_additional_files
    assert (app.outdir / 'svgimg.svg').isfile()

    compile_latex_document(app)


@pytest.mark.sphinx('latex')
def test_writer(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')

    assert ('\\begin{sphinxfigure-in-table}\n\\centering\n\\capstart\n'
            '\\noindent\\sphinxincludegraphics{{img}.png}\n'
            '\\sphinxfigcaption{figure in table}\\label{\\detokenize{markup:id8}}'
            '\\end{sphinxfigure-in-table}\\relax' in result)

    assert ('\\begin{wrapfigure}{r}{0pt}\n\\centering\n'
            '\\noindent\\sphinxincludegraphics{{rimg}.png}\n'
            '\\caption{figure with align option}\\label{\\detokenize{markup:id9}}'
            '\\end{wrapfigure}' in result)

    assert ('\\begin{wrapfigure}{r}{0.500\\linewidth}\n\\centering\n'
            '\\noindent\\sphinxincludegraphics{{rimg}.png}\n'
            '\\caption{figure with align \\& figwidth option}'
            '\\label{\\detokenize{markup:id10}}'
            '\\end{wrapfigure}' in result)

    assert ('\\begin{wrapfigure}{r}{3cm}\n\\centering\n'
            '\\noindent\\sphinxincludegraphics[width=3cm]{{rimg}.png}\n'
            '\\caption{figure with align \\& width option}'
            '\\label{\\detokenize{markup:id11}}'
            '\\end{wrapfigure}' in result)


@pytest.mark.sphinx('latex', testroot='warnings', freshenv=True)
def test_latex_warnings(app, status, warning):
    app.builder.build_all()

    warnings = strip_escseq(re.sub(re.escape(os.sep) + '{1,2}', '/', warning.getvalue()))
    warnings_exp = LATEX_WARNINGS % {
        'root': re.escape(app.srcdir.replace(os.sep, '/'))}
    assert re.match(warnings_exp + '$', warnings), \
        'Warnings don\'t match:\n' + \
        '--- Expected (regex):\n' + warnings_exp + \
        '--- Got:\n' + warnings


@pytest.mark.sphinx('latex', testroot='basic')
def test_latex_basic(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'test.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert r'\title{The basic Sphinx documentation for testing}' in result
    assert r'\release{}' in result
    assert r'\renewcommand{\releasename}{}' in result


@pytest.mark.sphinx('latex', testroot='latex-title')
def test_latex_title_after_admonitions(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'test.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\title{test-latex-title}' in result


@pytest.mark.sphinx('latex', testroot='basic',
                    confoverrides={'release': '1.0'})
def test_latex_release(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'test.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert r'\release{1.0}' in result
    assert r'\renewcommand{\releasename}{Release}' in result


@pytest.mark.sphinx('latex', testroot='numfig',
                    confoverrides={'numfig': True})
def test_numref(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Fig.}}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Table}}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\literalblockname}{Listing}}' in result
    assert ('\\hyperref[\\detokenize{index:fig1}]'
            '{Fig.\\@ \\ref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:fig22}]'
            '{Figure\\ref{\\detokenize{baz:fig22}}}') in result
    assert ('\\hyperref[\\detokenize{index:table-1}]'
            '{Table \\ref{\\detokenize{index:table-1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:table22}]'
            '{Table:\\ref{\\detokenize{baz:table22}}}') in result
    assert ('\\hyperref[\\detokenize{index:code-1}]'
            '{Listing \\ref{\\detokenize{index:code-1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:code22}]'
            '{Code-\\ref{\\detokenize{baz:code22}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]'
            '{Section \\ref{\\detokenize{foo:foo}}}') in result
    assert ('\\hyperref[\\detokenize{bar:bar-a}]'
            '{Section \\ref{\\detokenize{bar:bar-a}}}') in result
    assert ('\\hyperref[\\detokenize{index:fig1}]{Fig.\\ref{\\detokenize{index:fig1}} '
            '\\nameref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]{Sect.\\ref{\\detokenize{foo:foo}} '
            '\\nameref{\\detokenize{foo:foo}}}') in result


@pytest.mark.sphinx(
    'latex', testroot='numfig',
    confoverrides={'numfig': True,
                   'numfig_format': {'figure': 'Figure:%s',
                                     'table': 'Tab_%s',
                                     'code-block': 'Code-%s',
                                     'section': 'SECTION-%s'}})
def test_numref_with_prefix1(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Figure:}}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Tab\\_}}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\literalblockname}{Code-}}' in result
    assert '\\ref{\\detokenize{index:fig1}}' in result
    assert '\\ref{\\detokenize{baz:fig22}}' in result
    assert '\\ref{\\detokenize{index:table-1}}' in result
    assert '\\ref{\\detokenize{baz:table22}}' in result
    assert '\\ref{\\detokenize{index:code-1}}' in result
    assert '\\ref{\\detokenize{baz:code22}}' in result
    assert ('\\hyperref[\\detokenize{index:fig1}]'
            '{Figure:\\ref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:fig22}]'
            '{Figure\\ref{\\detokenize{baz:fig22}}}') in result
    assert ('\\hyperref[\\detokenize{index:table-1}]'
            '{Tab\\_\\ref{\\detokenize{index:table-1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:table22}]'
            '{Table:\\ref{\\detokenize{baz:table22}}}') in result
    assert ('\\hyperref[\\detokenize{index:code-1}]'
            '{Code-\\ref{\\detokenize{index:code-1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:code22}]'
            '{Code-\\ref{\\detokenize{baz:code22}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]'
            '{SECTION-\\ref{\\detokenize{foo:foo}}}') in result
    assert ('\\hyperref[\\detokenize{bar:bar-a}]'
            '{SECTION-\\ref{\\detokenize{bar:bar-a}}}') in result
    assert ('\\hyperref[\\detokenize{index:fig1}]{Fig.\\ref{\\detokenize{index:fig1}} '
            '\\nameref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]{Sect.\\ref{\\detokenize{foo:foo}} '
            '\\nameref{\\detokenize{foo:foo}}}') in result


@pytest.mark.sphinx(
    'latex', testroot='numfig',
    confoverrides={'numfig': True,
                   'numfig_format': {'figure': 'Figure:%s.',
                                     'table': 'Tab_%s:',
                                     'code-block': 'Code-%s | ',
                                     'section': 'SECTION_%s_'}})
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
    assert '\\addto\\captionsenglish{\\renewcommand{\\literalblockname}{Code-}}' in result
    assert ('\\hyperref[\\detokenize{index:fig1}]'
            '{Figure:\\ref{\\detokenize{index:fig1}}.\\@}') in result
    assert ('\\hyperref[\\detokenize{baz:fig22}]'
            '{Figure\\ref{\\detokenize{baz:fig22}}}') in result
    assert ('\\hyperref[\\detokenize{index:table-1}]'
            '{Tab\\_\\ref{\\detokenize{index:table-1}}:}') in result
    assert ('\\hyperref[\\detokenize{baz:table22}]'
            '{Table:\\ref{\\detokenize{baz:table22}}}') in result
    assert ('\\hyperref[\\detokenize{index:code-1}]{Code-\\ref{\\detokenize{index:code-1}} '
            '\\textbar{} }') in result
    assert ('\\hyperref[\\detokenize{baz:code22}]'
            '{Code-\\ref{\\detokenize{baz:code22}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]'
            '{SECTION\\_\\ref{\\detokenize{foo:foo}}\\_}') in result
    assert ('\\hyperref[\\detokenize{bar:bar-a}]'
            '{SECTION\\_\\ref{\\detokenize{bar:bar-a}}\\_}') in result
    assert ('\\hyperref[\\detokenize{index:fig1}]{Fig.\\ref{\\detokenize{index:fig1}} '
            '\\nameref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]{Sect.\\ref{\\detokenize{foo:foo}} '
            '\\nameref{\\detokenize{foo:foo}}}') in result


@pytest.mark.sphinx(
    'latex', testroot='numfig',
    confoverrides={'numfig': True, 'language': 'ja'})
def test_numref_with_language_ja(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert u'\\renewcommand{\\figurename}{\u56f3}' in result  # 図
    assert u'\\renewcommand{\\tablename}{\u8868}' in result  # 表
    assert u'\\renewcommand{\\literalblockname}{\u30ea\u30b9\u30c8}' in result  # リスト
    assert (u'\\hyperref[\\detokenize{index:fig1}]'
            u'{\u56f3 \\ref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:fig22}]'
            '{Figure\\ref{\\detokenize{baz:fig22}}}') in result
    assert (u'\\hyperref[\\detokenize{index:table-1}]'
            u'{\u8868 \\ref{\\detokenize{index:table-1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:table22}]'
            '{Table:\\ref{\\detokenize{baz:table22}}}') in result
    assert (u'\\hyperref[\\detokenize{index:code-1}]'
            u'{\u30ea\u30b9\u30c8 \\ref{\\detokenize{index:code-1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:code22}]'
            '{Code-\\ref{\\detokenize{baz:code22}}}') in result
    assert (u'\\hyperref[\\detokenize{foo:foo}]'
            u'{\\ref{\\detokenize{foo:foo}} \u7ae0}') in result
    assert (u'\\hyperref[\\detokenize{bar:bar-a}]'
            u'{\\ref{\\detokenize{bar:bar-a}} \u7ae0}') in result
    assert ('\\hyperref[\\detokenize{index:fig1}]{Fig.\\ref{\\detokenize{index:fig1}} '
            '\\nameref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]{Sect.\\ref{\\detokenize{foo:foo}} '
            '\\nameref{\\detokenize{foo:foo}}}') in result


@pytest.mark.sphinx('latex', testroot='latex-numfig')
def test_latex_obey_numfig_is_false(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'SphinxManual.tex').text(encoding='utf8')
    assert '\\usepackage{sphinx}' in result

    result = (app.outdir / 'SphinxHowTo.tex').text(encoding='utf8')
    assert '\\usepackage{sphinx}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-numfig',
    confoverrides={'numfig': True, 'numfig_secnum_depth': 0})
def test_latex_obey_numfig_secnum_depth_is_zero(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'SphinxManual.tex').text(encoding='utf8')
    assert '\\usepackage[,nonumfigreset,mathnumfig]{sphinx}' in result

    result = (app.outdir / 'SphinxHowTo.tex').text(encoding='utf8')
    assert '\\usepackage[,nonumfigreset,mathnumfig]{sphinx}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-numfig',
    confoverrides={'numfig': True, 'numfig_secnum_depth': 2})
def test_latex_obey_numfig_secnum_depth_is_two(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'SphinxManual.tex').text(encoding='utf8')
    assert '\\usepackage[,numfigreset=2,mathnumfig]{sphinx}' in result

    result = (app.outdir / 'SphinxHowTo.tex').text(encoding='utf8')
    assert '\\usepackage[,numfigreset=3,mathnumfig]{sphinx}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-numfig',
    confoverrides={'numfig': True, 'math_numfig': False})
def test_latex_obey_numfig_but_math_numfig_false(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'SphinxManual.tex').text(encoding='utf8')
    assert '\\usepackage[,numfigreset=1]{sphinx}' in result

    result = (app.outdir / 'SphinxHowTo.tex').text(encoding='utf8')
    assert '\\usepackage[,numfigreset=2]{sphinx}' in result


@pytest.mark.sphinx('latex')
def test_latex_add_latex_package(app, status, warning):
    app.add_latex_package('foo')
    app.add_latex_package('bar', 'baz')
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')
    assert '\\usepackage{foo}' in result
    assert '\\usepackage[baz]{bar}' in result


@pytest.mark.sphinx('latex', testroot='latex-babel')
def test_babel_with_no_language_settings(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,english]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{times}' in result
    assert '\\usepackage[Bjarne]{fncychap}' in result
    assert ('\\addto\\captionsenglish{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Fig.}}\n' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Table.}}\n' in result
    assert '\\addto\\extrasenglish{\\def\\pageautorefname{page}}\n' in result
    assert '\\shorthandoff' not in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'de'})
def test_babel_with_language_de(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,ngerman]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{times}' in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsngerman{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\addto\\captionsngerman{\\renewcommand{\\figurename}{Fig.}}\n' in result
    assert '\\addto\\captionsngerman{\\renewcommand{\\tablename}{Table.}}\n' in result
    assert '\\addto\\extrasngerman{\\def\\pageautorefname{Seite}}\n' in result
    assert '\\shorthandoff{"}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'ru'})
def test_babel_with_language_ru(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,russian]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{times}' not in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsrussian{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\addto\\captionsrussian{\\renewcommand{\\figurename}{Fig.}}\n' in result
    assert '\\addto\\captionsrussian{\\renewcommand{\\tablename}{Table.}}\n' in result
    assert (u'\\addto\\extrasrussian{\\def\\pageautorefname'
            u'{\u0441\u0442\u0440\u0430\u043d\u0438\u0446\u0430}}\n' in result)
    assert '\\shorthandoff{"}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'tr'})
def test_babel_with_language_tr(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,turkish]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{times}' in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsturkish{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\addto\\captionsturkish{\\renewcommand{\\figurename}{Fig.}}\n' in result
    assert '\\addto\\captionsturkish{\\renewcommand{\\tablename}{Table.}}\n' in result
    assert '\\addto\\extrasturkish{\\def\\pageautorefname{sayfa}}\n' in result
    assert '\\shorthandoff{=}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'ja'})
def test_babel_with_language_ja(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,dvipdfmx]{sphinxmanual}' in result
    assert '\\usepackage{babel}' not in result
    assert '\\usepackage{times}' in result
    assert '\\usepackage[Sonny]{fncychap}' not in result
    assert '\\renewcommand{\\contentsname}{Table of content}\n' in result
    assert '\\renewcommand{\\figurename}{Fig.}\n' in result
    assert '\\renewcommand{\\tablename}{Table.}\n' in result
    assert u'\\def\\pageautorefname{ページ}\n' in result
    assert '\\shorthandoff' not in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'unknown'})
def test_babel_with_unknown_language(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,english]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{times}' in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsenglish{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Fig.}}\n' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Table.}}\n' in result
    assert '\\addto\\extrasenglish{\\def\\pageautorefname{page}}\n' in result
    assert '\\shorthandoff' in result

    assert "WARNING: no Babel option known for language 'unknown'" in warning.getvalue()


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'de', 'latex_engine': 'lualatex'})
def test_polyglossia_with_language_de(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,german]{sphinxmanual}' in result
    assert '\\usepackage{polyglossia}' in result
    assert '\\setmainlanguage[spelling=new]{german}' in result
    assert '\\usepackage{times}' not in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsgerman{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\addto\\captionsgerman{\\renewcommand{\\figurename}{Fig.}}\n' in result
    assert '\\addto\\captionsgerman{\\renewcommand{\\tablename}{Table.}}\n' in result
    assert '\\def\\pageautorefname{Seite}\n' in result
    assert '\\shorthandoff' not in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'de-1901', 'latex_engine': 'lualatex'})
def test_polyglossia_with_language_de_1901(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,german]{sphinxmanual}' in result
    assert '\\usepackage{polyglossia}' in result
    assert '\\setmainlanguage[spelling=old]{german}' in result
    assert '\\usepackage{times}' not in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsgerman{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\addto\\captionsgerman{\\renewcommand{\\figurename}{Fig.}}\n' in result
    assert '\\addto\\captionsgerman{\\renewcommand{\\tablename}{Table.}}\n' in result
    assert '\\def\\pageautorefname{page}\n' in result
    assert '\\shorthandoff' not in result


@pytest.mark.sphinx('latex')
def test_footnote(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\begin{footnote}[1]\\sphinxAtStartFootnote\nnumbered\n%\n'
            '\\end{footnote}') in result
    assert ('\\begin{footnote}[2]\\sphinxAtStartFootnote\nauto numbered\n%\n'
            '\\end{footnote}') in result
    assert '\\begin{footnote}[3]\\sphinxAtStartFootnote\nnamed\n%\n\\end{footnote}' in result
    assert '\\sphinxcite{footnote:bar}' in result
    assert ('\\bibitem[bar]{footnote:bar}\ncite\n') in result
    assert '\\sphinxcaption{Table caption \\sphinxfootnotemark[4]' in result
    assert ('\\hline%\n\\begin{footnotetext}[4]\\sphinxAtStartFootnote\n'
            'footnote in table caption\n%\n\\end{footnotetext}\\ignorespaces %\n'
            '\\begin{footnotetext}[5]\\sphinxAtStartFootnote\n'
            'footnote in table header\n%\n\\end{footnotetext}\\ignorespaces \n'
            'VIDIOC\\_CROPCAP\n&\n') in result
    assert ('Information about VIDIOC\\_CROPCAP %\n'
            '\\begin{footnote}[6]\\sphinxAtStartFootnote\n'
            'footnote in table not in header\n%\n\\end{footnote}\n\\\\\n\\hline\n'
            '\\end{tabulary}\n'
            '\\par\n\\sphinxattableend\\end{savenotes}\n') in result


@pytest.mark.sphinx('latex', testroot='footnotes')
def test_reference_in_caption_and_codeblock_in_footnote(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\caption{This is the figure caption with a reference to '
            '\\sphinxcite{index:authoryear}.}' in result)
    assert '\\chapter{The section with a reference to {[}AuthorYear{]}}' in result
    assert ('\\sphinxcaption{The table title with a reference'
            ' to {[}AuthorYear{]}}' in result)
    assert '\\subsubsection*{The rubric title with a reference to {[}AuthorYear{]}}' in result
    assert ('\\chapter{The section with a reference to \\sphinxfootnotemark[5]}\n'
            '\\label{\\detokenize{index:the-section-with-a-reference-to}}'
            '%\n\\begin{footnotetext}[5]\\sphinxAtStartFootnote\n'
            'Footnote in section\n%\n\\end{footnotetext}') in result
    assert ('\\caption{This is the figure caption with a footnote to '
            '\\sphinxfootnotemark[7].}\\label{\\detokenize{index:id29}}\\end{figure}\n'
            '%\n\\begin{footnotetext}[7]\\sphinxAtStartFootnote\n'
            'Footnote in caption\n%\n\\end{footnotetext}')in result
    assert ('\\sphinxcaption{footnote \\sphinxfootnotemark[8] in '
            'caption of normal table}\\label{\\detokenize{index:id30}}') in result
    assert ('\\caption{footnote \\sphinxfootnotemark[9] '
            'in caption \\sphinxfootnotemark[10] of longtable\\strut}') in result
    assert ('\\endlastfoot\n%\n\\begin{footnotetext}[9]\\sphinxAtStartFootnote\n'
            'Foot note in longtable\n%\n\\end{footnotetext}\\ignorespaces %\n'
            '\\begin{footnotetext}[10]\\sphinxAtStartFootnote\n'
            'Second footnote in caption of longtable\n') in result
    assert ('This is a reference to the code-block in the footnote:\n'
            '{\\hyperref[\\detokenize{index:codeblockinfootnote}]'
            '{\\sphinxcrossref{\\DUrole{std,std-ref}{I am in a footnote}}}}') in result
    assert ('&\nThis is one more footnote with some code in it %\n'
            '\\begin{footnote}[11]\\sphinxAtStartFootnote\n'
            'Third footnote in longtable\n') in result
    assert ('\\end{sphinxVerbatim}\n%\n\\end{footnote}.\n') in result
    assert '\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]' in result


@pytest.mark.sphinx(
    'latex', testroot='footnotes',
    confoverrides={'latex_show_urls': 'inline'})
def test_latex_show_urls_is_inline(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in bar\n%\n\\end{footnote} in bar.rst') in result
    assert ('Auto footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in baz\n%\n\\end{footnote} in baz.rst') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id32}}'
            '{\\hyperref[\\detokenize{index:the-section'
            '-with-a-reference-to-authoryear}]'
            '{\\sphinxcrossref{The section with a reference to '
            '\\sphinxcite{index:authoryear}}}}') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id33}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to}]'
            '{\\sphinxcrossref{The section with a reference to }}}' in result)
    assert ('First footnote: %\n\\begin{footnote}[2]\\sphinxAtStartFootnote\n'
            'First\n%\n\\end{footnote}') in result
    assert ('Second footnote: %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'Second\n%\n\\end{footnote}') in result
    assert '\\sphinxhref{http://sphinx-doc.org/}{Sphinx} (http://sphinx-doc.org/)' in result
    assert ('Third footnote: %\n\\begin{footnote}[3]\\sphinxAtStartFootnote\n'
            'Third \\sphinxfootnotemark[4]\n%\n\\end{footnote}%\n'
            '\\begin{footnotetext}[4]\\sphinxAtStartFootnote\n'
            'Footnote inside footnote\n%\n\\end{footnotetext}\\ignorespaces') in result
    assert ('\\sphinxhref{http://sphinx-doc.org/~test/}{URL including tilde} '
            '(http://sphinx-doc.org/\\textasciitilde{}test/)') in result
    assert ('\\item[{\\sphinxhref{http://sphinx-doc.org/}{URL in term} '
            '(http://sphinx-doc.org/)}] \\leavevmode\nDescription' in result)
    assert ('\\item[{Footnote in term \\sphinxfootnotemark[6]}] '
            '\\leavevmode%\n\\begin{footnotetext}[6]\\sphinxAtStartFootnote\n'
            'Footnote in term\n%\n\\end{footnotetext}\\ignorespaces \n'
            'Description') in result
    assert ('\\item[{\\sphinxhref{http://sphinx-doc.org/}{Term in deflist} '
            '(http://sphinx-doc.org/)}] \\leavevmode\nDescription') in result
    assert '\\sphinxurl{https://github.com/sphinx-doc/sphinx}\n' in result
    assert ('\\sphinxhref{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx-dev@googlegroups.com}') in result


@pytest.mark.sphinx(
    'latex', testroot='footnotes',
    confoverrides={'latex_show_urls': 'footnote'})
def test_latex_show_urls_is_footnote(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in bar\n%\n\\end{footnote} in bar.rst') in result
    assert ('Auto footnote number %\n\\begin{footnote}[2]\\sphinxAtStartFootnote\n'
            'footnote in baz\n%\n\\end{footnote} in baz.rst') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id32}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to-authoryear}]'
            '{\\sphinxcrossref{The section with a reference '
            'to \\sphinxcite{index:authoryear}}}}') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id33}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to}]'
            '{\\sphinxcrossref{The section with a reference to }}}') in result
    assert ('First footnote: %\n\\begin{footnote}[3]\\sphinxAtStartFootnote\n'
            'First\n%\n\\end{footnote}') in result
    assert ('Second footnote: %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'Second\n%\n\\end{footnote}') in result
    assert ('\\sphinxhref{http://sphinx-doc.org/}{Sphinx}'
            '%\n\\begin{footnote}[4]\\sphinxAtStartFootnote\n'
            '\\sphinxnolinkurl{http://sphinx-doc.org/}\n%\n\\end{footnote}') in result
    assert ('Third footnote: %\n\\begin{footnote}[6]\\sphinxAtStartFootnote\n'
            'Third \\sphinxfootnotemark[7]\n%\n\\end{footnote}%\n'
            '\\begin{footnotetext}[7]\\sphinxAtStartFootnote\n'
            'Footnote inside footnote\n%\n'
            '\\end{footnotetext}\\ignorespaces') in result
    assert ('\\sphinxhref{http://sphinx-doc.org/~test/}{URL including tilde}'
            '%\n\\begin{footnote}[5]\\sphinxAtStartFootnote\n'
            '\\sphinxnolinkurl{http://sphinx-doc.org/~test/}\n%\n\\end{footnote}') in result
    assert ('\\item[{\\sphinxhref{http://sphinx-doc.org/}'
            '{URL in term}\\sphinxfootnotemark[9]}] '
            '\\leavevmode%\n\\begin{footnotetext}[9]\\sphinxAtStartFootnote\n'
            '\\sphinxnolinkurl{http://sphinx-doc.org/}\n%\n'
            '\\end{footnotetext}\\ignorespaces \nDescription') in result
    assert ('\\item[{Footnote in term \\sphinxfootnotemark[11]}] '
            '\\leavevmode%\n\\begin{footnotetext}[11]\\sphinxAtStartFootnote\n'
            'Footnote in term\n%\n\\end{footnotetext}\\ignorespaces \n'
            'Description') in result
    assert ('\\item[{\\sphinxhref{http://sphinx-doc.org/}{Term in deflist}'
            '\\sphinxfootnotemark[10]}] '
            '\\leavevmode%\n\\begin{footnotetext}[10]\\sphinxAtStartFootnote\n'
            '\\sphinxnolinkurl{http://sphinx-doc.org/}\n%\n'
            '\\end{footnotetext}\\ignorespaces \nDescription') in result
    assert ('\\sphinxurl{https://github.com/sphinx-doc/sphinx}\n' in result)
    assert ('\\sphinxhref{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx-dev@googlegroups.com}\n') in result


@pytest.mark.sphinx(
    'latex', testroot='footnotes',
    confoverrides={'latex_show_urls': 'no'})
def test_latex_show_urls_is_no(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in bar\n%\n\\end{footnote} in bar.rst') in result
    assert ('Auto footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in baz\n%\n\\end{footnote} in baz.rst') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id32}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to-authoryear}]'
            '{\\sphinxcrossref{The section with a reference '
            'to \\sphinxcite{index:authoryear}}}}') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id33}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to}]'
            '{\\sphinxcrossref{The section with a reference to }}}' in result)
    assert ('First footnote: %\n\\begin{footnote}[2]\\sphinxAtStartFootnote\n'
            'First\n%\n\\end{footnote}') in result
    assert ('Second footnote: %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'Second\n%\n\\end{footnote}') in result
    assert '\\sphinxhref{http://sphinx-doc.org/}{Sphinx}' in result
    assert ('Third footnote: %\n\\begin{footnote}[3]\\sphinxAtStartFootnote\n'
            'Third \\sphinxfootnotemark[4]\n%\n\\end{footnote}%\n'
            '\\begin{footnotetext}[4]\\sphinxAtStartFootnote\n'
            'Footnote inside footnote\n%\n\\end{footnotetext}\\ignorespaces') in result
    assert '\\sphinxhref{http://sphinx-doc.org/~test/}{URL including tilde}' in result
    assert ('\\item[{\\sphinxhref{http://sphinx-doc.org/}{URL in term}}] '
            '\\leavevmode\nDescription') in result
    assert ('\\item[{Footnote in term \\sphinxfootnotemark[6]}] '
            '\\leavevmode%\n\\begin{footnotetext}[6]\\sphinxAtStartFootnote\n'
            'Footnote in term\n%\n\\end{footnotetext}\\ignorespaces \n'
            'Description') in result
    assert ('\\item[{\\sphinxhref{http://sphinx-doc.org/}{Term in deflist}}] '
            '\\leavevmode\nDescription') in result
    assert ('\\sphinxurl{https://github.com/sphinx-doc/sphinx}\n' in result)
    assert ('\\sphinxhref{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx-dev@googlegroups.com}\n') in result


@pytest.mark.sphinx(
    'latex', testroot='footnotes',
    confoverrides={'latex_show_urls': 'footnote',
                   'rst_prolog': '.. |URL| replace:: `text <http://www.example.com/>`__'})
def test_latex_show_urls_footnote_and_substitutions(app, status, warning):
    # hyperlinks in substitutions should not effect to make footnotes (refs: #4784)
    test_latex_show_urls_is_footnote(app, status, warning)


@pytest.mark.sphinx('latex', testroot='image-in-section')
def test_image_in_section(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\chapter[Test section]{\\lowercase{\\sphinxincludegraphics'
            '[width=15bp,height=15bp]}{{pic}.png} Test section}'
            in result)
    assert ('\\chapter[Other {[}blah{]} section]{Other {[}blah{]} '
            '\\lowercase{\\sphinxincludegraphics[width=15bp,height=15bp]}'
            '{{pic}.png} section}' in result)
    assert ('\\chapter{Another section}' in result)


@pytest.mark.sphinx('latex', testroot='basic',
                    confoverrides={'latex_logo': 'notfound.jpg'})
def test_latex_logo_if_not_found(app, status, warning):
    try:
        app.builder.build_all()
        assert False  # SphinxError not raised
    except Exception as exc:
        assert isinstance(exc, SphinxError)


@pytest.mark.sphinx('latex', testroot='toctree-maxdepth')
def test_toctree_maxdepth_manual(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}{1}' in result
    assert '\\setcounter{secnumdepth}' not in result
    assert '\\chapter{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_documents': [
        ('index', 'SphinxTests.tex', 'Sphinx Tests Documentation',
         'Georg Brandl', 'howto'),
    ]})
def test_toctree_maxdepth_howto(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}{2}' in result
    assert '\\setcounter{secnumdepth}' not in result
    assert '\\section{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'master_doc': 'foo'})
def test_toctree_not_found(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}' not in result
    assert '\\setcounter{secnumdepth}' not in result
    assert '\\chapter{Foo A}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'master_doc': 'bar'})
def test_toctree_without_maxdepth(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}' not in result
    assert '\\setcounter{secnumdepth}' not in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'master_doc': 'qux'})
def test_toctree_with_deeper_maxdepth(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}{3}' in result
    assert '\\setcounter{secnumdepth}{3}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': None})
def test_latex_toplevel_sectioning_is_None(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\chapter{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': 'part'})
def test_latex_toplevel_sectioning_is_part(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\part{Foo}' in result
    assert '\\chapter{Foo A}' in result
    assert '\\chapter{Foo B}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': 'part',
                   'latex_documents': [
                       ('index', 'Python.tex', 'Sphinx Tests Documentation',
                        'Georg Brandl', 'howto')
                   ]})
def test_latex_toplevel_sectioning_is_part_with_howto(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\part{Foo}' in result
    assert '\\section{Foo A}' in result
    assert '\\section{Foo B}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': 'chapter'})
def test_latex_toplevel_sectioning_is_chapter(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\chapter{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': 'chapter',
                   'latex_documents': [
                       ('index', 'Python.tex', 'Sphinx Tests Documentation',
                        'Georg Brandl', 'howto')
                   ]})
def test_latex_toplevel_sectioning_is_chapter_with_howto(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\section{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': 'section'})
def test_latex_toplevel_sectioning_is_section(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\section{Foo}' in result


@skip_if_stylefiles_notfound
@pytest.mark.sphinx('latex', testroot='maxlistdepth')
def test_maxlistdepth_at_ten(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    compile_latex_document(app)


@pytest.mark.skipif(docutils.__version_info__ < (0, 13),
                    reason='docutils-0.13 or above is required')
@pytest.mark.sphinx('latex', testroot='latex-table')
@pytest.mark.test_params(shared_result='latex-table')
def test_latex_table_tabulars(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'test.tex').text(encoding='utf8')
    tables = {}
    for chap in re.split(r'\\(?:section|chapter){', result)[1:]:
        sectname, content = chap.split('}', 1)
        tables[sectname] = content.strip()

    def get_expected(name):
        return (app.srcdir / 'expects' / (name + '.tex')).text().strip()

    # simple_table
    actual = tables['simple table']
    expected = get_expected('simple_table')
    assert actual == expected

    # table having :widths: option
    actual = tables['table having :widths: option']
    expected = get_expected('table_having_widths')
    assert actual == expected

    # table having :align: option (tabulary)
    actual = tables['table having :align: option (tabulary)']
    expected = get_expected('tabulary_having_widths')
    assert actual == expected

    # table having :align: option (tabular)
    actual = tables['table having :align: option (tabular)']
    expected = get_expected('tabular_having_widths')
    assert actual == expected

    # table with tabularcolumn
    actual = tables['table with tabularcolumn']
    expected = get_expected('tabularcolumn')
    assert actual == expected

    # table with cell in first column having three paragraphs
    actual = tables['table with cell in first column having three paragraphs']
    expected = get_expected('table_having_threeparagraphs_cell_in_first_col')
    assert actual == expected

    # table having caption
    actual = tables['table having caption']
    expected = get_expected('table_having_caption')
    assert actual == expected

    # table having verbatim
    actual = tables['table having verbatim']
    expected = get_expected('table_having_verbatim')
    assert actual == expected

    # table having problematic cell
    actual = tables['table having problematic cell']
    expected = get_expected('table_having_problematic_cell')
    assert actual == expected

    # table having both :widths: and problematic cell
    actual = tables['table having both :widths: and problematic cell']
    expected = get_expected('table_having_widths_and_problematic_cell')
    assert actual == expected

    # table having both stub columns and problematic cell
    actual = tables['table having both stub columns and problematic cell']
    expected = get_expected('table_having_stub_columns_and_problematic_cell')
    assert actual == expected


@pytest.mark.skipif(docutils.__version_info__ < (0, 13),
                    reason='docutils-0.13 or above is required')
@pytest.mark.sphinx('latex', testroot='latex-table')
@pytest.mark.test_params(shared_result='latex-table')
def test_latex_table_longtable(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'test.tex').text(encoding='utf8')
    tables = {}
    for chap in re.split(r'\\(?:section|chapter){', result)[1:]:
        sectname, content = chap.split('}', 1)
        tables[sectname] = content.strip()

    def get_expected(name):
        return (app.srcdir / 'expects' / (name + '.tex')).text().strip()

    # longtable
    actual = tables['longtable']
    expected = get_expected('longtable')
    assert actual == expected

    # longtable having :widths: option
    actual = tables['longtable having :widths: option']
    expected = get_expected('longtable_having_widths')
    assert actual == expected

    # longtable having :align: option
    actual = tables['longtable having :align: option']
    expected = get_expected('longtable_having_align')
    assert actual == expected

    # longtable with tabularcolumn
    actual = tables['longtable with tabularcolumn']
    expected = get_expected('longtable_with_tabularcolumn')
    assert actual == expected

    # longtable having caption
    actual = tables['longtable having caption']
    expected = get_expected('longtable_having_caption')
    assert actual == expected

    # longtable having verbatim
    actual = tables['longtable having verbatim']
    expected = get_expected('longtable_having_verbatim')
    assert actual == expected

    # longtable having problematic cell
    actual = tables['longtable having problematic cell']
    expected = get_expected('longtable_having_problematic_cell')
    assert actual == expected

    # longtable having both :widths: and problematic cell
    actual = tables['longtable having both :widths: and problematic cell']
    expected = get_expected('longtable_having_widths_and_problematic_cell')
    assert actual == expected

    # longtable having both stub columns and problematic cell
    actual = tables['longtable having both stub columns and problematic cell']
    expected = get_expected('longtable_having_stub_columns_and_problematic_cell')
    assert actual == expected


@pytest.mark.skipif(docutils.__version_info__ < (0, 13),
                    reason='docutils-0.13 or above is required')
@pytest.mark.sphinx('latex', testroot='latex-table')
@pytest.mark.test_params(shared_result='latex-table')
def test_latex_table_complex_tables(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'test.tex').text(encoding='utf8')
    tables = {}
    for chap in re.split(r'\\(?:section|renewcommand){', result)[1:]:
        sectname, content = chap.split('}', 1)
        tables[sectname] = content.strip()

    def get_expected(name):
        return (app.srcdir / 'expects' / (name + '.tex')).text().strip()

    # grid table
    actual = tables['grid table']
    expected = get_expected('gridtable')
    assert actual == expected

    # complex spanning cell
    actual = tables['complex spanning cell']
    expected = get_expected('complex_spanning_cell')
    assert actual == expected


@pytest.mark.sphinx('latex', testroot='latex-table',
                    confoverrides={'templates_path': ['_mytemplates/latex']})
def test_latex_table_custom_template_caseA(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'test.tex').text(encoding='utf8')
    assert 'SALUT LES COPAINS' in result


@pytest.mark.sphinx('latex', testroot='latex-table',
                    confoverrides={'templates_path': ['_mytemplates']})
def test_latex_table_custom_template_caseB(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'test.tex').text(encoding='utf8')
    assert 'SALUT LES COPAINS' not in result


@pytest.mark.sphinx('latex', testroot='latex-table')
@pytest.mark.test_params(shared_result='latex-table')
def test_latex_table_custom_template_caseC(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'test.tex').text(encoding='utf8')
    assert 'SALUT LES COPAINS' not in result


@pytest.mark.sphinx('latex', testroot='directives-raw')
def test_latex_raw_directive(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')

    # standard case
    assert 'standalone raw directive (HTML)' not in result
    assert ('\\label{\\detokenize{index:id1}}\n'
            'standalone raw directive (LaTeX)' in result)

    # with substitution
    assert 'HTML: abc  ghi' in result
    assert 'LaTeX: abc def ghi' in result


@pytest.mark.sphinx('latex', testroot='images')
def test_latex_remote_images(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    assert '\\sphinxincludegraphics{{python-logo}.png}' in result
    assert (app.outdir / 'python-logo.png').exists()
    assert '\\sphinxincludegraphics{{NOT_EXIST}.PNG}' not in result
    assert ('WARNING: Could not fetch remote image: '
            'http://example.com/NOT_EXIST.PNG [404]' in warning.getvalue())


@pytest.mark.sphinx('latex', testroot='latex-index')
def test_latex_index(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    assert 'A \\index{famous}famous \\index{equation}equation:\n' in result
    assert '\n\\index{Einstein}\\index{relativity}\\ignorespaces \nand' in result
    assert '\n\\index{main \\sphinxleftcurlybrace{}}\\ignorespaces ' in result


@pytest.mark.sphinx('latex', testroot='latex-equations')
def test_latex_equations(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    expected = (app.srcdir / 'expects' / 'latex-equations.tex').text().strip()

    assert expected in result


@pytest.mark.sphinx('latex', testroot='image-in-parsed-literal')
def test_latex_image_in_parsed_literal(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    assert ('{\\sphinxunactivateextrasandspace \\raisebox{-0.5\\height}'
            '{\\scalebox{2.000000}{\\sphinxincludegraphics[height=1cm]{{pic}.png}}}'
            '}AFTER') in result


@pytest.mark.sphinx('latex', testroot='nested-enumerated-list')
def test_latex_nested_enumerated_list(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'test.tex').text(encoding='utf8')
    assert ('\\def\\theenumi{\\arabic{enumi}}\n'
            '\\def\\labelenumi{\\theenumi .}\n'
            '\\makeatletter\\def\\p@enumii{\\p@enumi \\theenumi .}\\makeatother\n'
            '\\setcounter{enumi}{4}\n' in result)
    assert ('\\def\\theenumii{\\alph{enumii}}\n'
            '\\def\\labelenumii{\\theenumii .}\n'
            '\\makeatletter\\def\\p@enumiii{\\p@enumii \\theenumii .}\\makeatother\n'
            '\\setcounter{enumii}{3}\n' in result)
    assert ('\\def\\theenumiii{\\arabic{enumiii}}\n'
            '\\def\\labelenumiii{\\theenumiii )}\n'
            '\\makeatletter\\def\\p@enumiv{\\p@enumiii \\theenumiii )}\\makeatother\n'
            '\\setcounter{enumiii}{9}\n' in result)
    assert ('\\def\\theenumiv{\\arabic{enumiv}}\n'
            '\\def\\labelenumiv{(\\theenumiv )}\n'
            '\\makeatletter\\def\\p@enumv{\\p@enumiv (\\theenumiv )}\\makeatother\n'
            '\\setcounter{enumiv}{23}\n' in result)
    assert ('\\def\\theenumii{\\roman{enumii}}\n'
            '\\def\\labelenumii{\\theenumii .}\n'
            '\\makeatletter\\def\\p@enumiii{\\p@enumii \\theenumii .}\\makeatother\n'
            '\\setcounter{enumii}{2}\n' in result)


@pytest.mark.sphinx('latex', testroot='footnotes')
def test_latex_thebibliography(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    assert ('\\begin{sphinxthebibliography}{AuthorYe}\n'
            '\\bibitem[AuthorYear]{index:authoryear}\n'
            'Author, Title, Year\n'
            '\\end{sphinxthebibliography}\n' in result)
    assert '\\sphinxcite{index:authoryear}' in result


@pytest.mark.sphinx('latex', testroot='glossary')
def test_latex_glossary(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'test.tex').text(encoding='utf8')
    assert (u'\\item[{änhlich\\index{änhlich|textbf}\\phantomsection'
            r'\label{\detokenize{index:term-anhlich}}}] \leavevmode' in result)
    assert (r'\item[{boson\index{boson|textbf}\phantomsection'
            r'\label{\detokenize{index:term-boson}}}] \leavevmode' in result)
    assert (r'\item[{\sphinxstyleemphasis{fermion}\index{fermion|textbf}'
            r'\phantomsection'
            r'\label{\detokenize{index:term-fermion}}}] \leavevmode' in result)
    assert (r'\item[{tauon\index{tauon|textbf}\phantomsection'
            r'\label{\detokenize{index:term-tauon}}}] \leavevmode'
            r'\item[{myon\index{myon|textbf}\phantomsection'
            r'\label{\detokenize{index:term-myon}}}] \leavevmode'
            r'\item[{electron\index{electron|textbf}\phantomsection'
            r'\label{\detokenize{index:term-electron}}}] \leavevmode' in result)
    assert (u'\\item[{über\\index{über|textbf}\\phantomsection'
            r'\label{\detokenize{index:term-uber}}}] \leavevmode' in result)


@pytest.mark.sphinx('latex', testroot='latex-labels')
def test_latex_labels(app, status, warning):
    app.builder.build_all()

    result = (app.outdir / 'test.tex').text(encoding='utf8')

    # figures
    assert (r'\caption{labeled figure}'
            r'\label{\detokenize{index:id1}}'
            r'\label{\detokenize{index:figure2}}'
            r'\label{\detokenize{index:figure1}}'
            r'\end{figure}' in result)
    assert (r'\caption{labeled figure}'
            r'\label{\detokenize{index:figure3}}'
            r'\end{figure}' in result)

    # code-blocks
    assert (r'\def\sphinxLiteralBlockLabel{'
            r'\label{\detokenize{index:codeblock2}}'
            r'\label{\detokenize{index:codeblock1}}}' in result)
    assert (r'\def\sphinxLiteralBlockLabel{'
            r'\label{\detokenize{index:codeblock3}}}' in result)

    # tables
    assert (r'\sphinxcaption{table caption}'
            r'\label{\detokenize{index:id2}}'
            r'\label{\detokenize{index:table2}}'
            r'\label{\detokenize{index:table1}}' in result)
    assert (r'\sphinxcaption{table caption}'
            r'\label{\detokenize{index:table3}}' in result)

    # sections
    assert ('\\chapter{subsection}\n'
            r'\label{\detokenize{index:subsection}}'
            r'\label{\detokenize{index:section2}}'
            r'\label{\detokenize{index:section1}}' in result)
    assert ('\\section{subsubsection}\n'
            r'\label{\detokenize{index:subsubsection}}'
            r'\label{\detokenize{index:section3}}' in result)
    assert ('\\subsection{otherdoc}\n'
            r'\label{\detokenize{otherdoc:otherdoc}}'
            r'\label{\detokenize{otherdoc::doc}}' in result)
