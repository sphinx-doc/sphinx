# -*- coding: utf-8 -*-
"""
    test_build_latex
    ~~~~~~~~~~~~~~~~

    Test the build process with LaTeX builder with the test root.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import re
from itertools import product
from subprocess import Popen, PIPE

from six import PY3

from sphinx.errors import SphinxError
from sphinx.util.osutil import cd, ensuredir
from sphinx.writers.latex import LaTeXTranslator

from util import SkipTest, remove_unicode_literals, with_app, strip_escseq
from test_build_html import ENV_WARNINGS


LATEX_ENGINES = ['pdflatex', 'lualatex', 'xelatex']
DOCCLASSES = ['howto', 'manual']
STYLEFILES = ['article.sty', 'fancyhdr.sty', 'titlesec.sty', 'amsmath.sty',
              'framed.sty', 'color.sty', 'fancyvrb.sty', 'fncychap.sty',
              'threeparttable.sty', 'geometry.sty']

LATEX_WARNINGS = ENV_WARNINGS + """\
%(root)s/index.rst:\\d+: WARNING: unknown option: &option
%(root)s/index.rst:\\d+: WARNING: citation not found: missing
%(root)s/index.rst:\\d+: WARNING: no matching candidate for image URI u'foo.\\*'
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
        return None
    else:
        p.communicate()
        if p.returncode != 0:
            # not found
            return False
        # found
        return True


def test_latex():
    if kpsetest(*STYLEFILES) is False:
        raise SkipTest('not running latex, the required styles doesn\'t seem to be installed')

    for engine, docclass in product(LATEX_ENGINES, DOCCLASSES):
        yield build_latex_doc, engine, docclass


@with_app(buildername='latex')
def build_latex_doc(app, status, warning, engine, docclass):
    app.config.latex_engine = engine
    app.config.latex_documents[0] = app.config.latex_documents[0][:4] + (docclass,)

    LaTeXTranslator.ignore_missing_images = True
    app.builder.build_all()

    # file from latex_additional_files
    assert (app.outdir / 'svgimg.svg').isfile()

    # now, try to run latex over it
    with cd(app.outdir):
        try:
            ensuredir(engine)
            p = Popen([engine, '--interaction=nonstopmode',
                       '-output-directory=%s' % engine, 'SphinxTests.tex'],
                      stdout=PIPE, stderr=PIPE)
        except OSError:  # most likely the latex executable was not found
            raise SkipTest
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print(stdout)
                print(stderr)
                assert False, '%s exited with return code %s' % (
                    engine, p.returncode)


@with_app(buildername='latex')
def test_writer(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')

    assert ('\\begin{sphinxfigure-in-table}\n\\centering\n\\capstart\n'
            '\\noindent\\sphinxincludegraphics{{img}.png}\n'
            '\\sphinxfigcaption{figure in table}\\label{markup:id7}'
            '\\end{sphinxfigure-in-table}\\relax' in result)

    assert ('\\begin{wrapfigure}{r}{0pt}\n\\centering\n'
            '\\noindent\\sphinxincludegraphics{{rimg}.png}\n'
            '\\caption{figure with align option}\\label{markup:id8}'
            '\\end{wrapfigure}' in result)

    assert ('\\begin{wrapfigure}{r}{0.500\\linewidth}\n\\centering\n'
            '\\noindent\\sphinxincludegraphics{{rimg}.png}\n'
            '\\caption{figure with align \\& figwidth option}\\label{markup:id9}'
            '\\end{wrapfigure}' in result)

    assert ('\\begin{wrapfigure}{r}{3cm}\n\\centering\n'
            '\\noindent\\sphinxincludegraphics[width=3cm]{{rimg}.png}\n'
            '\\caption{figure with align \\& width option}\\label{markup:id10}'
            '\\end{wrapfigure}' in result)


@with_app(buildername='latex', testroot='warnings', freshenv=True)
def test_latex_warnings(app, status, warning):
    app.builder.build_all()

    warnings = strip_escseq(warning.getvalue().replace(os.sep, '/'))
    warnings_exp = LATEX_WARNINGS % {
        'root': re.escape(app.srcdir.replace(os.sep, '/'))}
    assert re.match(warnings_exp + '$', warnings), \
        'Warnings don\'t match:\n' + \
        '--- Expected (regex):\n' + warnings_exp + \
        '--- Got:\n' + warnings


@with_app(buildername='latex', testroot='numfig',
          confoverrides={'numfig': True})
def test_numref(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Fig.\\@ }}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Table }}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\literalblockname}{Listing }}' in result
    assert '\\hyperref[index:fig1]{Fig.\\@ \\ref{index:fig1}}' in result
    assert '\\hyperref[baz:fig22]{Figure\\ref{baz:fig22}}' in result
    assert '\\hyperref[index:table-1]{Table \\ref{index:table-1}}' in result
    assert '\\hyperref[baz:table22]{Table:\\ref{baz:table22}}' in result
    assert '\\hyperref[index:code-1]{Listing \\ref{index:code-1}}' in result
    assert '\\hyperref[baz:code22]{Code-\\ref{baz:code22}}' in result
    assert '\\hyperref[foo:foo]{Section \\ref{foo:foo}}' in result
    assert '\\hyperref[bar:bar-a]{Section \\ref{bar:bar-a}}' in result
    assert '\\hyperref[index:fig1]{Fig.\\ref{index:fig1} \\nameref{index:fig1}}' in result
    assert '\\hyperref[foo:foo]{Sect.\\ref{foo:foo} \\nameref{foo:foo}}' in result


@with_app(buildername='latex', testroot='numfig',
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
    assert '\\hyperref[foo:foo]{SECTION-\\ref{foo:foo}}' in result
    assert '\\hyperref[bar:bar-a]{SECTION-\\ref{bar:bar-a}}' in result
    assert '\\hyperref[index:fig1]{Fig.\\ref{index:fig1} \\nameref{index:fig1}}' in result
    assert '\\hyperref[foo:foo]{Sect.\\ref{foo:foo} \\nameref{foo:foo}}' in result


@with_app(buildername='latex', testroot='numfig',
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
    assert '\\def\\fnum@figure{\\figurename\\thefigure.\\@}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Tab\\_}}' in result
    assert '\\def\\fnum@table{\\tablename\\thetable:}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\literalblockname}{Code-}}' in result
    assert '\\hyperref[index:fig1]{Figure:\\ref{index:fig1}.\\@}' in result
    assert '\\hyperref[baz:fig22]{Figure\\ref{baz:fig22}}' in result
    assert '\\hyperref[index:table-1]{Tab\\_\\ref{index:table-1}:}' in result
    assert '\\hyperref[baz:table22]{Table:\\ref{baz:table22}}' in result
    assert '\\hyperref[index:code-1]{Code-\\ref{index:code-1} \\textbar{} }' in result
    assert '\\hyperref[baz:code22]{Code-\\ref{baz:code22}}' in result
    assert '\\hyperref[foo:foo]{SECTION\\_\\ref{foo:foo}\\_}' in result
    assert '\\hyperref[bar:bar-a]{SECTION\\_\\ref{bar:bar-a}\\_}' in result
    assert '\\hyperref[index:fig1]{Fig.\\ref{index:fig1} \\nameref{index:fig1}}' in result
    assert '\\hyperref[foo:foo]{Sect.\\ref{foo:foo} \\nameref{foo:foo}}' in result


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
    assert '\\renewcommand{\\literalblockname}{LIST }' in result
    assert u'\\hyperref[index:fig1]{\u56f3 \\ref{index:fig1}}' in result
    assert '\\hyperref[baz:fig22]{Figure\\ref{baz:fig22}}' in result
    assert '\\hyperref[index:table-1]{TABLE \\ref{index:table-1}}' in result
    assert '\\hyperref[baz:table22]{Table:\\ref{baz:table22}}' in result
    assert '\\hyperref[index:code-1]{LIST \\ref{index:code-1}}' in result
    assert '\\hyperref[baz:code22]{Code-\\ref{baz:code22}}' in result
    assert '\\hyperref[foo:foo]{Section \\ref{foo:foo}}' in result
    assert '\\hyperref[bar:bar-a]{Section \\ref{bar:bar-a}}' in result
    assert '\\hyperref[index:fig1]{Fig.\\ref{index:fig1} \\nameref{index:fig1}}' in result
    assert '\\hyperref[foo:foo]{Sect.\\ref{foo:foo} \\nameref{foo:foo}}' in result


@with_app(buildername='latex')
def test_latex_add_latex_package(app, status, warning):
    app.add_latex_package('foo')
    app.add_latex_package('bar', 'baz')
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')
    assert '\\usepackage{foo}' in result
    assert '\\usepackage[baz]{bar}' in result


@with_app(buildername='latex', testroot='latex-babel')
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
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Fig.\\@ }}\n' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Table.\\@ }}\n' in result
    assert '\\addto\\extrasenglish{\\def\\pageautorefname{page}}\n' in result
    assert '\\shorthandoff' not in result


@with_app(buildername='latex', testroot='latex-babel',
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
    assert '\\addto\\captionsngerman{\\renewcommand{\\figurename}{Fig.\\@ }}\n' in result
    assert '\\addto\\captionsngerman{\\renewcommand{\\tablename}{Table.\\@ }}\n' in result
    assert '\\addto\\extrasngerman{\\def\\pageautorefname{page}}\n' in result
    assert '\\shorthandoff{"}' in result


@with_app(buildername='latex', testroot='latex-babel',
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
    assert '\\addto\\captionsrussian{\\renewcommand{\\figurename}{Fig.\\@ }}\n' in result
    assert '\\addto\\captionsrussian{\\renewcommand{\\tablename}{Table.\\@ }}\n' in result
    assert '\\addto\\extrasrussian{\\def\\pageautorefname{page}}\n' in result
    assert '\\shorthandoff' not in result


@with_app(buildername='latex', testroot='latex-babel',
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
    assert '\\addto\\captionsturkish{\\renewcommand{\\figurename}{Fig.\\@ }}\n' in result
    assert '\\addto\\captionsturkish{\\renewcommand{\\tablename}{Table.\\@ }}\n' in result
    assert '\\addto\\extrasturkish{\\def\\pageautorefname{sayfa}}\n' in result
    assert '\\shorthandoff{=}' in result


@with_app(buildername='latex', testroot='latex-babel',
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
    assert '\\renewcommand{\\figurename}{Fig.\\@ }\n' in result
    assert '\\renewcommand{\\tablename}{Table.\\@ }\n' in result
    assert u'\\def\\pageautorefname{ページ}\n' in result
    assert '\\shorthandoff' not in result


@with_app(buildername='latex', testroot='latex-babel',
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
    assert '\\addto\\captionsenglish{\\renewcommand{\\figurename}{Fig.\\@ }}\n' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Table.\\@ }}\n' in result
    assert '\\addto\\extrasenglish{\\def\\pageautorefname{page}}\n' in result
    assert '\\shorthandoff' not in result

    assert "WARNING: no Babel option known for language 'unknown'" in warning.getvalue()


@with_app(buildername='latex')
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
    assert '{\\hyperref[footnote:bar]{\\sphinxcrossref{{[}bar{]}}}}' in result
    assert '\\bibitem[bar]{bar}{\\phantomsection\\label{footnote:bar} ' in result
    assert '\\bibitem[bar]{bar}{\\phantomsection\\label{footnote:bar} \ncite' in result
    assert '\\bibitem[bar]{bar}{\\phantomsection\\label{footnote:bar} \ncite\n}' in result
    assert '\\caption{Table caption \\sphinxfootnotemark[4]' in result
    assert 'name \\sphinxfootnotemark[5]' in result
    assert ('\\end{threeparttable}\n\n%\n'
            '\\begin{footnotetext}[4]\sphinxAtStartFootnote\n'
            'footnotes in table caption\n%\n\\end{footnotetext}%\n'
            '\\begin{footnotetext}[5]\sphinxAtStartFootnote\n'
            'footnotes in table\n%\n\\end{footnotetext}') in result


@with_app(buildername='latex', testroot='footnotes')
def test_reference_in_caption_and_codeblock_in_footnote(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\caption{This is the figure caption with a reference to \\label{index:id2}'
            '{\\hyperref[index:authoryear]{\\sphinxcrossref{{[}AuthorYear{]}}}}.}' in result)
    assert '\\chapter{The section with a reference to {[}AuthorYear{]}}' in result
    assert '\\caption{The table title with a reference to {[}AuthorYear{]}}' in result
    assert '\\paragraph{The rubric title with a reference to {[}AuthorYear{]}}' in result
    assert ('\\chapter{The section with a reference to \\sphinxfootnotemark[4]}\n'
            '\\label{index:the-section-with-a-reference-to}'
            '%\n\\begin{footnotetext}[4]\\sphinxAtStartFootnote\n'
            'Footnote in section\n%\n\\end{footnotetext}') in result
    assert ('\\caption{This is the figure caption with a footnote to '
            '\\sphinxfootnotemark[6].}\label{index:id27}\end{figure}\n'
            '%\n\\begin{footnotetext}[6]\\sphinxAtStartFootnote\n'
            'Footnote in caption\n%\n\\end{footnotetext}')in result
    assert ('\\caption{footnote \\sphinxfootnotemark[7] '
            'in caption of normal table}\\label{index:id28}') in result
    assert ('\\caption{footnote \\sphinxfootnotemark[8] '
            'in caption \sphinxfootnotemark[9] of longtable}') in result
    assert ('\end{longtable}\n\n%\n\\begin{footnotetext}[8]'
            '\sphinxAtStartFootnote\n'
            'Foot note in longtable\n%\n\\end{footnotetext}' in result)
    assert ('This is a reference to the code-block in the footnote:\n'
            '{\hyperref[index:codeblockinfootnote]{\\sphinxcrossref{\\DUrole'
            '{std,std-ref}{I am in a footnote}}}}') in result
    assert ('&\nThis is one more footnote with some code in it '
            '\\sphinxfootnotemark[10].\n\\\\') in result
    assert '\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]' in result


@with_app(buildername='latex', testroot='footnotes',
          confoverrides={'latex_show_urls': 'inline'})
def test_latex_show_urls_is_inline(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in bar\n%\n\\end{footnote} in bar.rst' in result)
    assert ('Auto footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in baz\n%\n\\end{footnote} in baz.rst' in result)
    assert ('\\phantomsection\\label{index:id30}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to\\string-authoryear]'
            '{\\sphinxcrossref{The section with a reference to '
            '\\phantomsection\\label{index:id1}'
            '{\\hyperref[index:authoryear]{\\sphinxcrossref{{[}AuthorYear{]}}}}}}}' in result)
    assert ('\\phantomsection\\label{index:id31}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to]'
            '{\\sphinxcrossref{The section with a reference to }}}' in result)
    assert ('First footnote: %\n\\begin{footnote}[2]\\sphinxAtStartFootnote\n'
           'First\n%\n\\end{footnote}') in result
    assert ('Second footnote: %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
           'Second\n%\n\\end{footnote}') in result
    assert '\\href{http://sphinx-doc.org/}{Sphinx} (http://sphinx-doc.org/)' in result
    assert ('Third footnote: %\n\\begin{footnote}[3]\\sphinxAtStartFootnote\n'
           'Third\n%\n\\end{footnote}') in result
    assert ('\\href{http://sphinx-doc.org/~test/}{URL including tilde} '
            '(http://sphinx-doc.org/\\textasciitilde{}test/)' in result)
    assert ('\\item[{\\href{http://sphinx-doc.org/}{URL in term} (http://sphinx-doc.org/)}] '
            '\\leavevmode\nDescription' in result)
    assert ('\\item[{Footnote in term \\sphinxfootnotemark[5]}] '
            '\\leavevmode%\n\\begin{footnotetext}[5]\\sphinxAtStartFootnote\n'
            'Footnote in term\n%\n\\end{footnotetext}\nDescription' in result)
    assert ('\\item[{\\href{http://sphinx-doc.org/}{Term in deflist} '
            '(http://sphinx-doc.org/)}] \\leavevmode\nDescription' in result)
    assert ('\\url{https://github.com/sphinx-doc/sphinx}\n' in result)
    assert ('\\href{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx-dev@googlegroups.com}' in result)


@with_app(buildername='latex', testroot='footnotes',
          confoverrides={'latex_show_urls': 'footnote'})
def test_latex_show_urls_is_footnote(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in bar\n%\n\\end{footnote} in bar.rst' in result)
    assert ('Auto footnote number %\n\\begin{footnote}[2]\\sphinxAtStartFootnote\n'
            'footnote in baz\n%\n\\end{footnote} in baz.rst' in result)
    assert ('\\phantomsection\\label{index:id30}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to\\string-authoryear]'
            '{\\sphinxcrossref{The section with a reference '
            'to \\phantomsection\\label{index:id1}'
            '{\\hyperref[index:authoryear]{\\sphinxcrossref{{[}AuthorYear{]}}}}}}}' in result)
    assert ('\\phantomsection\\label{index:id31}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to]'
            '{\\sphinxcrossref{The section with a reference to }}}' in result)
    assert ('First footnote: %\n\\begin{footnote}[3]\\sphinxAtStartFootnote\n'
           'First\n%\n\\end{footnote}') in result
    assert ('Second footnote: %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
           'Second\n%\n\\end{footnote}') in result
    assert ('\\href{http://sphinx-doc.org/}{Sphinx}'
            '%\n\\begin{footnote}[4]\\sphinxAtStartFootnote\n'
            '\\nolinkurl{http://sphinx-doc.org/}\n%\n\\end{footnote}') in result
    assert ('Third footnote: %\n\\begin{footnote}[6]\\sphinxAtStartFootnote\n'
            'Third\n%\n\\end{footnote}') in result
    assert ('\\href{http://sphinx-doc.org/~test/}{URL including tilde}'
            '%\n\\begin{footnote}[5]\\sphinxAtStartFootnote\n'
            '\\nolinkurl{http://sphinx-doc.org/~test/}\n%\n\\end{footnote}') in result
    assert ('\\item[{\\href{http://sphinx-doc.org/}{URL in term}\\sphinxfootnotemark[8]}] '
            '\\leavevmode%\n\\begin{footnotetext}[8]\\sphinxAtStartFootnote\n'
            '\\nolinkurl{http://sphinx-doc.org/}\n%\n'
            '\\end{footnotetext}\nDescription') in result
    assert ('\\item[{Footnote in term \\sphinxfootnotemark[10]}] '
            '\\leavevmode%\n\\begin{footnotetext}[10]\\sphinxAtStartFootnote\n'
            'Footnote in term\n%\n\\end{footnotetext}\nDescription') in result
    assert ('\\item[{\\href{http://sphinx-doc.org/}{Term in deflist}'
            '\\sphinxfootnotemark[9]}] '
            '\\leavevmode%\n\\begin{footnotetext}[9]\\sphinxAtStartFootnote\n'
            '\\nolinkurl{http://sphinx-doc.org/}\n%\n'
            '\\end{footnotetext}\nDescription') in result
    assert ('\\url{https://github.com/sphinx-doc/sphinx}\n' in result)
    assert ('\\href{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx-dev@googlegroups.com}\n') in result


@with_app(buildername='latex', testroot='footnotes',
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
    assert ('\\phantomsection\\label{index:id30}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to\\string-authoryear]'
            '{\\sphinxcrossref{The section with a reference '
            'to \\phantomsection\\label{index:id1}'
            '{\\hyperref[index:authoryear]{\\sphinxcrossref{{[}AuthorYear{]}}}}}}}') in result
    assert ('\\phantomsection\\label{index:id31}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to]'
            '{\\sphinxcrossref{The section with a reference to }}}' in result)
    assert ('First footnote: %\n\\begin{footnote}[2]\\sphinxAtStartFootnote\n'
           'First\n%\n\\end{footnote}') in result
    assert ('Second footnote: %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
           'Second\n%\n\\end{footnote}') in result
    assert '\\href{http://sphinx-doc.org/}{Sphinx}' in result
    assert ('Third footnote: %\n\\begin{footnote}[3]\\sphinxAtStartFootnote\n'
           'Third\n%\n\\end{footnote}') in result
    assert '\\href{http://sphinx-doc.org/~test/}{URL including tilde}' in result
    assert ('\\item[{\\href{http://sphinx-doc.org/}{URL in term}}] '
            '\\leavevmode\nDescription') in result
    assert ('\\item[{Footnote in term \\sphinxfootnotemark[5]}] '
            '\\leavevmode%\n\\begin{footnotetext}[5]\\sphinxAtStartFootnote\n'
            'Footnote in term\n%\n\\end{footnotetext}\nDescription') in result
    assert ('\\item[{\\href{http://sphinx-doc.org/}{Term in deflist}}] '
            '\\leavevmode\nDescription') in result
    assert ('\\url{https://github.com/sphinx-doc/sphinx}\n' in result)
    assert ('\\href{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx-dev@googlegroups.com}\n') in result


@with_app(buildername='latex', testroot='image-in-section')
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


@with_app(buildername='latex', confoverrides={'latex_logo': 'notfound.jpg'})
def test_latex_logo_if_not_found(app, status, warning):
    try:
        app.builder.build_all()
        assert False  # SphinxError not raised
    except Exception as exc:
        assert isinstance(exc, SphinxError)


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'latex_documents': [
              ('index', 'SphinxTests.tex', 'Sphinx Tests Documentation',
               'Georg Brandl', 'manual'),
          ]})
def test_toctree_maxdepth_manual(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}{1}' in result
    assert '\\setcounter{secnumdepth}' not in result


@with_app(buildername='latex', testroot='toctree-maxdepth',
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


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'master_doc': 'foo'})
def test_toctree_not_found(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}' not in result
    assert '\\setcounter{secnumdepth}' not in result


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'master_doc': 'bar'})
def test_toctree_without_maxdepth(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}' not in result
    assert '\\setcounter{secnumdepth}' not in result


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'master_doc': 'qux'})
def test_toctree_with_deeper_maxdepth(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}{3}' in result
    assert '\\setcounter{secnumdepth}{3}' in result


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'latex_toplevel_sectioning': None})
def test_latex_toplevel_sectioning_is_None(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\chapter{Foo}' in result


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'latex_toplevel_sectioning': 'part'})
def test_latex_toplevel_sectioning_is_part(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\part{Foo}' in result


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'latex_toplevel_sectioning': 'chapter'})
def test_latex_toplevel_sectioning_is_chapter(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\chapter{Foo}' in result


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'latex_toplevel_sectioning': 'section'})
def test_latex_toplevel_sectioning_is_section(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\section{Foo}' in result
