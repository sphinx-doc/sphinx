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
from subprocess import Popen, PIPE

from six import PY3

from sphinx.errors import SphinxError
from sphinx.writers.latex import LaTeXTranslator

from util import SkipTest, remove_unicode_literals, with_app
from test_build_html import ENV_WARNINGS


LATEX_WARNINGS = ENV_WARNINGS + """\
%(root)s/markup.txt:\\d+: WARNING: unknown option: &option
%(root)s/footnote.txt:\\d+: WARNING: citation not found: missing
%(root)s/images.txt:\\d+: WARNING: no matching candidate for image URI u'foo.\\*'
%(root)s/markup.txt:\\d+: WARNING: Could not lex literal_block as "c". Highlighting skipped.
"""

if PY3:
    LATEX_WARNINGS = remove_unicode_literals(LATEX_WARNINGS)


def run_latex(outdir):
    """Run pdflatex, xelatex, and lualatex in the outdir"""
    cwd = os.getcwd()
    os.chdir(outdir)
    try:
        latexes = ('pdflatex', 'xelatex', 'lualatex')
        available_latexes = len(latexes)
        for latex in latexes:
            try:
                os.mkdir(latex)
                p = Popen([latex, '--interaction=nonstopmode',
                        '-output-directory=%s' % latex, 'SphinxTests.tex'],
                        stdout=PIPE, stderr=PIPE)
            except OSError:  # most likely the latex executable was not found
                available_latexes -= 1
            else:
                stdout, stderr = p.communicate()
                if p.returncode != 0:
                    print(stdout)
                    print(stderr)
                    assert False, '%s exited with return code %s' % (
                        latex, p.returncode)
    finally:
        os.chdir(cwd)

    if available_latexes == 0: # no latex is available, skip the test
        raise SkipTest

@with_app(buildername='latex', freshenv=True)  # use freshenv to check warnings
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
    run_latex(app.outdir)


@with_app(buildername='latex')
def test_writer(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.tex').text(encoding='utf8')

    assert ('\\begin{figure-in-table}\n\\centering\n\\capstart\n'
            '\\includegraphics{{img}.png}\n'
            '\\figcaption{figure in table}\\label{markup:id7}\\end{figure-in-table}' in result)

    assert ('\\begin{wrapfigure}{r}{0pt}\n\\centering\n'
            '\\includegraphics{{rimg}.png}\n\\caption{figure with align option}'
            '\\label{markup:id8}\\end{wrapfigure}' in result)

    assert ('\\begin{wrapfigure}{r}{0.500\\linewidth}\n\\centering\n'
            '\\includegraphics{{rimg}.png}\n\\caption{figure with align \\& figwidth option}'
            '\\label{markup:id9}\\end{wrapfigure}' in result)

    assert ('\\begin{wrapfigure}{r}{3cm}\n\\centering\n'
            '\\includegraphics[width=3cm]{{rimg}.png}\n'
            '\\caption{figure with align \\& width option}'
            '\\label{markup:id10}\\end{wrapfigure}' in result)


@with_app(buildername='latex', freshenv=True,  # use freshenv to check warnings
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
    run_latex(app.outdir)


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
    assert '\\SetupFloatingEnvironment{literal-block}{name=Listing }' in result
    assert '\\hyperref[index:fig1]{Fig.\\@ \\ref{index:fig1}}' in result
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
    assert '\\SetupFloatingEnvironment{literal-block}{name=Code-}' in result
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
    assert '\\def\\fnum@figure{\\figurename\\thefigure.\\@}' in result
    assert '\\addto\\captionsenglish{\\renewcommand{\\tablename}{Tab\\_}}' in result
    assert '\\def\\fnum@table{\\tablename\\thetable:}' in result
    assert '\\SetupFloatingEnvironment{literal-block}{name=Code-}' in result
    assert '\\hyperref[index:fig1]{Figure:\\ref{index:fig1}.\\@}' in result
    assert '\\hyperref[baz:fig22]{Figure\\ref{baz:fig22}}' in result
    assert '\\hyperref[index:table-1]{Tab\\_\\ref{index:table-1}:}' in result
    assert '\\hyperref[baz:table22]{Table:\\ref{baz:table22}}' in result
    assert '\\hyperref[index:code-1]{Code-\\ref{index:code-1} \\textbar{} }' in result
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
    assert '\\SetupFloatingEnvironment{literal-block}{name=LIST }' in result
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
    assert '\\footnote[1]{\sphinxAtStartFootnote%\nnumbered\n}' in result
    assert '\\footnote[2]{\sphinxAtStartFootnote%\nauto numbered\n}' in result
    assert '\\footnote[3]{\sphinxAtStartFootnote%\nnamed\n}' in result
    assert '{\\hyperref[footnote:bar]{\\crossref{{[}bar{]}}}}' in result
    assert '\\bibitem[bar]{bar}{\\phantomsection\\label{footnote:bar} ' in result
    assert '\\bibitem[bar]{bar}{\\phantomsection\\label{footnote:bar} \ncite' in result
    assert '\\bibitem[bar]{bar}{\\phantomsection\\label{footnote:bar} \ncite\n}' in result
    assert '\\capstart\\caption{Table caption \\protect\\footnotemark[4]}' in result
    assert 'name \\protect\\footnotemark[5]' in result
    assert ('\\end{threeparttable}\n\n'
            '\\footnotetext[4]{\sphinxAtStartFootnote%\nfootnotes in table caption\n}'
            '\\footnotetext[5]{\sphinxAtStartFootnote%\nfootnotes in table\n}' in result)


@with_app(buildername='latex', testroot='footnotes')
def test_reference_in_caption(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\caption{This is the figure caption with a reference to \\label{index:id2}'
            '{\\hyperref[index:authoryear]{\\crossref{{[}AuthorYear{]}}}}.}' in result)
    assert '\\chapter{The section with a reference to {[}AuthorYear{]}}' in result
    assert '\\caption{The table title with a reference to {[}AuthorYear{]}}' in result
    assert '\\paragraph{The rubric title with a reference to {[}AuthorYear{]}}' in result
    assert ('\\chapter{The section with a reference to \\protect\\footnotemark[4]}\n'
            '\\label{index:the-section-with-a-reference-to}'
            '\\footnotetext[4]{\sphinxAtStartFootnote%\nFootnote in section\n}' in result)
    assert ('\\caption{This is the figure caption with a footnote to '
            '\\protect\\footnotemark[6].}\label{index:id23}\end{figure}\n'
            '\\footnotetext[6]{\sphinxAtStartFootnote%\nFootnote in caption\n}')in result
    assert ('\\caption{footnote \\protect\\footnotemark[7] '
            'in caption of normal table}') in result
    assert ('\\end{threeparttable}\n\n\\footnotetext[7]{\sphinxAtStartFootnote%\n'
            'Foot note in table\n}' in result)
    assert ('\\caption{footnote \\protect\\footnotemark[8] in caption of longtable}'
            in result)
    assert ('\end{longtable}\n\n\\footnotetext[8]{\sphinxAtStartFootnote%\n'
            'Foot note in longtable\n}' in result)


@with_app(buildername='latex', testroot='footnotes',
          confoverrides={'latex_show_urls': 'inline'})
def test_latex_show_urls_is_inline(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number \\footnote[1]{\sphinxAtStartFootnote%\n'
            'footnote in bar\n} in bar.rst' in result)
    assert ('Auto footnote number \\footnote[1]{\sphinxAtStartFootnote%\n'
            'footnote in baz\n} in baz.rst' in result)
    assert ('\\phantomsection\\label{index:id26}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to\\string-authoryear]'
            '{\\crossref{The section with a reference to \\phantomsection\\label{index:id1}'
            '{\\hyperref[index:authoryear]{\\crossref{{[}AuthorYear{]}}}}}}}' in result)
    assert ('\\phantomsection\\label{index:id27}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to]'
            '{\\crossref{The section with a reference to }}}' in result)
    assert 'First footnote: \\footnote[2]{\sphinxAtStartFootnote%\nFirst\n}' in result
    assert 'Second footnote: \\footnote[1]{\sphinxAtStartFootnote%\nSecond\n}' in result
    assert '\\href{http://sphinx-doc.org/}{Sphinx} (http://sphinx-doc.org/)' in result
    assert 'Third footnote: \\footnote[3]{\sphinxAtStartFootnote%\nThird\n}' in result
    assert ('\\href{http://sphinx-doc.org/~test/}{URL including tilde} '
            '(http://sphinx-doc.org/\\textasciitilde{}test/)' in result)
    assert ('\\item[{\\href{http://sphinx-doc.org/}{URL in term} (http://sphinx-doc.org/)}] '
            '\\leavevmode\nDescription' in result)
    assert ('\\item[{Footnote in term \\protect\\footnotemark[5]}] '
            '\\leavevmode\\footnotetext[5]{\sphinxAtStartFootnote%\n'
            'Footnote in term\n}\nDescription' in result)
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
    assert ('Same footnote number \\footnote[1]{\sphinxAtStartFootnote%\n'
            'footnote in bar\n} in bar.rst' in result)
    assert ('Auto footnote number \\footnote[2]{\sphinxAtStartFootnote%\n'
            'footnote in baz\n} in baz.rst' in result)
    assert ('\\phantomsection\\label{index:id26}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to\\string-authoryear]'
            '{\\crossref{The section with a reference to \\phantomsection\\label{index:id1}'
            '{\\hyperref[index:authoryear]{\\crossref{{[}AuthorYear{]}}}}}}}' in result)
    assert ('\\phantomsection\\label{index:id27}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to]'
            '{\\crossref{The section with a reference to }}}' in result)
    assert 'First footnote: \\footnote[3]{\sphinxAtStartFootnote%\nFirst\n}' in result
    assert 'Second footnote: \\footnote[1]{\sphinxAtStartFootnote%\nSecond\n}' in result
    assert ('\\href{http://sphinx-doc.org/}{Sphinx}'
            '\\footnote[4]{\sphinxAtStartFootnote%\n'
            '\\nolinkurl{http://sphinx-doc.org/}\n}' in result)
    assert 'Third footnote: \\footnote[6]{\sphinxAtStartFootnote%\nThird\n}' in result
    assert ('\\href{http://sphinx-doc.org/~test/}{URL including tilde}'
            '\\footnote[5]{\sphinxAtStartFootnote%\n'
            '\\nolinkurl{http://sphinx-doc.org/~test/}\n}' in result)
    assert ('\\item[{\\href{http://sphinx-doc.org/}{URL in term}\\protect\\footnotemark[8]}] '
            '\\leavevmode\\footnotetext[8]{\sphinxAtStartFootnote%\n'
            '\\nolinkurl{http://sphinx-doc.org/}\n}\nDescription' in result)
    assert ('\\item[{Footnote in term \\protect\\footnotemark[10]}] '
            '\\leavevmode\\footnotetext[10]{\sphinxAtStartFootnote%\n'
            'Footnote in term\n}\nDescription' in result)
    assert ('\\item[{\\href{http://sphinx-doc.org/}{Term in deflist}\\protect'
            '\\footnotemark[9]}] '
            '\\leavevmode\\footnotetext[9]{\sphinxAtStartFootnote%\n'
            '\\nolinkurl{http://sphinx-doc.org/}\n}\nDescription' in result)
    assert ('\\url{https://github.com/sphinx-doc/sphinx}\n' in result)
    assert ('\\href{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx-dev@googlegroups.com}\n' in result)


@with_app(buildername='latex', testroot='footnotes',
          confoverrides={'latex_show_urls': 'no'})
def test_latex_show_urls_is_no(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number \\footnote[1]{\sphinxAtStartFootnote%\n'
            'footnote in bar\n} in bar.rst' in result)
    assert ('Auto footnote number \\footnote[1]{\sphinxAtStartFootnote%\n'
            'footnote in baz\n} in baz.rst' in result)
    assert ('\\phantomsection\\label{index:id26}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to\\string-authoryear]'
            '{\\crossref{The section with a reference to \\phantomsection\\label{index:id1}'
            '{\\hyperref[index:authoryear]{\\crossref{{[}AuthorYear{]}}}}}}}' in result)
    assert ('\\phantomsection\\label{index:id27}{\\hyperref[index:the\\string-section'
            '\\string-with\\string-a\\string-reference\\string-to]'
            '{\\crossref{The section with a reference to }}}' in result)
    assert 'First footnote: \\footnote[2]{\sphinxAtStartFootnote%\nFirst\n}' in result
    assert 'Second footnote: \\footnote[1]{\sphinxAtStartFootnote%\nSecond\n}' in result
    assert '\\href{http://sphinx-doc.org/}{Sphinx}' in result
    assert 'Third footnote: \\footnote[3]{\sphinxAtStartFootnote%\nThird\n}' in result
    assert '\\href{http://sphinx-doc.org/~test/}{URL including tilde}' in result
    assert ('\\item[{\\href{http://sphinx-doc.org/}{URL in term}}] '
            '\\leavevmode\nDescription' in result)
    assert ('\\item[{Footnote in term \\protect\\footnotemark[5]}] '
            '\\leavevmode\\footnotetext[5]{\sphinxAtStartFootnote%\n'
            'Footnote in term\n}\nDescription' in result)
    assert ('\\item[{\\href{http://sphinx-doc.org/}{Term in deflist}}] '
            '\\leavevmode\nDescription' in result)
    assert ('\\url{https://github.com/sphinx-doc/sphinx}\n' in result)
    assert ('\\href{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx-dev@googlegroups.com}\n' in result)


@with_app(buildername='latex', testroot='image-in-section')
def test_image_in_section(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\chapter[Test section]'
            '{\includegraphics[width=15pt,height=15pt]{{pic}.png} Test section}'
            in result)
    assert ('\chapter[Other {[}blah{]} section]{Other {[}blah{]} '
            '\includegraphics[width=15pt,height=15pt]{{pic}.png} section}' in result)
    assert ('\chapter{Another section}' in result)


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


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'master_doc': 'foo'})
def test_toctree_not_found(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}' not in result


@with_app(buildername='latex', testroot='toctree-maxdepth',
          confoverrides={'master_doc': 'bar'})
def test_toctree_without_maxdepth(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'Python.tex').text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}' not in result


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
