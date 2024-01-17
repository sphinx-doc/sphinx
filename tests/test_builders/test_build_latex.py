"""Test the build process with LaTeX builder with the test root."""

import os
import re
import subprocess
from itertools import chain, product
from pathlib import Path
from shutil import copyfile
from subprocess import CalledProcessError

import pytest

from sphinx.builders.latex import default_latex_documents
from sphinx.config import Config
from sphinx.errors import SphinxError
from sphinx.ext.intersphinx import load_mappings, normalize_intersphinx_mapping
from sphinx.ext.intersphinx import setup as intersphinx_setup
from sphinx.testing.util import strip_escseq
from sphinx.util.osutil import ensuredir
from sphinx.writers.latex import LaTeXTranslator

from tests.test_builders.test_build_html import ENV_WARNINGS

try:
    from contextlib import chdir
except ImportError:
    from sphinx.util.osutil import _chdir as chdir

LATEX_ENGINES = ['pdflatex', 'lualatex', 'xelatex']
DOCCLASSES = ['manual', 'howto']
STYLEFILES = ['article.cls', 'fancyhdr.sty', 'titlesec.sty', 'amsmath.sty',
              'framed.sty', 'color.sty', 'fancyvrb.sty',
              'fncychap.sty', 'geometry.sty', 'kvoptions.sty', 'hyperref.sty',
              'booktabs.sty']

LATEX_WARNINGS = ENV_WARNINGS + """\
{root}/index.rst:\\d+: WARNING: unknown option: '&option'
{root}/index.rst:\\d+: WARNING: citation not found: missing
{root}/index.rst:\\d+: WARNING: a suitable image for latex builder not found: foo.\\*
{root}/index.rst:\\d+: WARNING: Lexing literal_block ".*" as "c" resulted in an error at token: ".*". Retrying in relaxed mode.
"""


# only run latex if all needed packages are there
def kpsetest(*filenames):
    try:
        subprocess.run(['kpsewhich'] + list(filenames), capture_output=True, check=True)
        return True
    except (OSError, CalledProcessError):
        return False  # command not found or exit with non-zero


# compile latex document with app.config.latex_engine
def compile_latex_document(app, filename='python.tex', docclass='manual'):
    # now, try to run latex over it
    try:
        with chdir(app.outdir):
            # name latex output-directory according to both engine and docclass
            # to avoid reuse of auxiliary files by one docclass from another
            latex_outputdir = app.config.latex_engine + docclass
            ensuredir(latex_outputdir)
            # keep a copy of latex file for this engine in case test fails
            copyfile(filename, latex_outputdir + '/' + filename)
            args = [app.config.latex_engine,
                    '--halt-on-error',
                    '--interaction=nonstopmode',
                    '-output-directory=%s' % latex_outputdir,
                    filename]
            subprocess.run(args, capture_output=True, check=True)
    except OSError as exc:  # most likely the latex executable was not found
        raise pytest.skip.Exception from exc
    except CalledProcessError as exc:
        print(exc.stdout.decode('utf8'))
        print(exc.stderr.decode('utf8'))
        msg = f'{app.config.latex_engine} exited with return code {exc.returncode}'
        raise AssertionError(msg) from exc


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
    ('engine', 'docclass', 'python_maximum_signature_line_length'),
    # Only running test with `python_maximum_signature_line_length` not None with last
    # LaTeX engine to reduce testing time, as if this configuration does not fail with
    # one engine, it's almost impossible it would fail with another.
    chain(
        product(LATEX_ENGINES[:-1], DOCCLASSES, [None]),
        product([LATEX_ENGINES[-1]], DOCCLASSES, [1]),
    ),
)
@pytest.mark.sphinx('latex', freshenv=True)
def test_build_latex_doc(app, status, warning, engine, docclass, python_maximum_signature_line_length):
    app.config.python_maximum_signature_line_length = python_maximum_signature_line_length
    app.config.intersphinx_mapping = {
        'sphinx': ('https://www.sphinx-doc.org/en/master/', None),
    }
    intersphinx_setup(app)
    app.config.latex_engine = engine
    app.config.latex_documents = [app.config.latex_documents[0][:4] + (docclass,)]
    if engine == 'xelatex':
        app.config.latex_table_style = ['booktabs']
    elif engine == 'lualatex':
        app.config.latex_table_style = ['colorrows']
    normalize_intersphinx_mapping(app, app.config)
    load_mappings(app)
    app.builder.init()
    LaTeXTranslator.ignore_missing_images = True
    app.build(force_all=True)

    # file from latex_additional_files
    assert (app.outdir / 'svgimg.svg').is_file()

    compile_latex_document(app, 'sphinxtests.tex', docclass)


@pytest.mark.sphinx('latex')
def test_writer(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'sphinxtests.tex').read_text(encoding='utf8')

    assert ('\\begin{sphinxfigure-in-table}\n\\centering\n\\capstart\n'
            '\\noindent\\sphinxincludegraphics{{img}.png}\n'
            '\\sphinxfigcaption{figure in table}\\label{\\detokenize{markup:id8}}'
            '\\end{sphinxfigure-in-table}\\relax' in result)

    assert ('\\begin{wrapfigure}{r}{0pt}\n\\centering\n'
            '\\noindent\\sphinxincludegraphics{{rimg}.png}\n'
            '\\caption{figure with align option}\\label{\\detokenize{markup:id9}}'
            '\\end{wrapfigure}\n\n'
            '\\mbox{}\\par\\vskip-\\dimexpr\\baselineskip+\\parskip\\relax' in result)

    assert ('\\begin{wrapfigure}{r}{0.500\\linewidth}\n\\centering\n'
            '\\noindent\\sphinxincludegraphics{{rimg}.png}\n'
            '\\caption{figure with align \\& figwidth option}'
            '\\label{\\detokenize{markup:id10}}'
            '\\end{wrapfigure}\n\n'
            '\\mbox{}\\par\\vskip-\\dimexpr\\baselineskip+\\parskip\\relax' in result)

    assert ('\\begin{wrapfigure}{r}{3cm}\n\\centering\n'
            '\\noindent\\sphinxincludegraphics[width=3cm]{{rimg}.png}\n'
            '\\caption{figure with align \\& width option}'
            '\\label{\\detokenize{markup:id11}}'
            '\\end{wrapfigure}\n\n'
            '\\mbox{}\\par\\vskip-\\dimexpr\\baselineskip+\\parskip\\relax' in result)

    assert 'Footnotes' not in result

    assert ('\\begin{sphinxseealso}{See also:}\n\n'
            '\\sphinxAtStartPar\n'
            'something, something else, something more\n'
            '\\begin{description}\n'
            '\\sphinxlineitem{\\sphinxhref{https://www.google.com}{Google}}\n'
            '\\sphinxAtStartPar\n'
            'For everything.\n'
            '\n'
            '\\end{description}\n'
            '\n\n\\end{sphinxseealso}\n\n' in result)


@pytest.mark.sphinx('latex', testroot='warnings', freshenv=True)
def test_latex_warnings(app, status, warning):
    app.build(force_all=True)
    warnings = strip_escseq(re.sub(re.escape(os.sep) + '{1,2}', '/', warning.getvalue()))
    warnings_exp = LATEX_WARNINGS.format(root=re.escape(app.srcdir.as_posix()))
    assert re.match(warnings_exp + '$', warnings), (
        "Warnings don't match:\n"
        + f'--- Expected (regex):\n{warnings_exp}\n'
        + f'--- Got:\n{warnings}'
    )


@pytest.mark.sphinx('latex', testroot='basic')
def test_latex_basic(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert r'\title{The basic Sphinx documentation for testing}' in result
    assert r'\release{}' in result
    assert r'\renewcommand{\releasename}{}' in result


@pytest.mark.sphinx('latex', testroot='basic',
                    confoverrides={
                        'latex_documents': [('index', 'test.tex', 'title', 'author', 'manual')],
                    })
def test_latex_basic_manual(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    print(result)
    assert r'\def\sphinxdocclass{report}' in result
    assert r'\documentclass[letterpaper,10pt,english]{sphinxmanual}' in result


@pytest.mark.sphinx('latex', testroot='basic',
                    confoverrides={
                        'latex_documents': [('index', 'test.tex', 'title', 'author', 'howto')],
                    })
def test_latex_basic_howto(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    print(result)
    assert r'\def\sphinxdocclass{article}' in result
    assert r'\documentclass[letterpaper,10pt,english]{sphinxhowto}' in result


@pytest.mark.sphinx('latex', testroot='basic',
                    confoverrides={
                        'language': 'ja',
                        'latex_documents': [('index', 'test.tex', 'title', 'author', 'manual')],
                    })
def test_latex_basic_manual_ja(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    print(result)
    assert r'\def\sphinxdocclass{ujbook}' in result
    assert r'\documentclass[letterpaper,10pt,dvipdfmx]{sphinxmanual}' in result


@pytest.mark.sphinx('latex', testroot='basic',
                    confoverrides={
                        'language': 'ja',
                        'latex_documents': [('index', 'test.tex', 'title', 'author', 'howto')],
                    })
def test_latex_basic_howto_ja(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    print(result)
    assert r'\def\sphinxdocclass{ujreport}' in result
    assert r'\documentclass[letterpaper,10pt,dvipdfmx]{sphinxhowto}' in result


@pytest.mark.sphinx('latex', testroot='latex-theme')
def test_latex_theme(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    assert r'\def\sphinxdocclass{book}' in result
    assert r'\documentclass[a4paper,12pt,english]{sphinxbook}' in result


@pytest.mark.sphinx('latex', testroot='latex-theme',
                    confoverrides={'latex_elements': {'papersize': 'b5paper',
                                                      'pointsize': '9pt'}})
def test_latex_theme_papersize(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    assert r'\def\sphinxdocclass{book}' in result
    assert r'\documentclass[b5paper,9pt,english]{sphinxbook}' in result


@pytest.mark.sphinx('latex', testroot='latex-theme',
                    confoverrides={'latex_theme_options': {'papersize': 'b5paper',
                                                           'pointsize': '9pt'}})
def test_latex_theme_options(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    assert r'\def\sphinxdocclass{book}' in result
    assert r'\documentclass[b5paper,9pt,english]{sphinxbook}' in result


@pytest.mark.sphinx('latex', testroot='basic', confoverrides={'language': 'zh'})
def test_latex_additional_settings_for_language_code(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert r'\usepackage{xeCJK}' in result


@pytest.mark.sphinx('latex', testroot='basic', confoverrides={'language': 'el'})
def test_latex_additional_settings_for_greek(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\usepackage{polyglossia}\n\\setmainlanguage{greek}' in result
    assert '\\newfontfamily\\greekfonttt{FreeMono}' in result


@pytest.mark.sphinx('latex', testroot='latex-title')
def test_latex_title_after_admonitions(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\title{test\\sphinxhyphen{}latex\\sphinxhyphen{}title}' in result


@pytest.mark.sphinx('latex', testroot='basic',
                    confoverrides={'release': '1.0_0'})
def test_latex_release(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert r'\release{1.0\_0}' in result
    assert r'\renewcommand{\releasename}{Release}' in result


@pytest.mark.sphinx('latex', testroot='numfig',
                    confoverrides={'numfig': True})
def test_numref(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
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
            '{Code\\sphinxhyphen{}\\ref{\\detokenize{baz:code22}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]'
            '{Section \\ref{\\detokenize{foo:foo}}}') in result
    assert ('\\hyperref[\\detokenize{bar:bar-a}]'
            '{Section \\ref{\\detokenize{bar:bar-a}}}') in result
    assert ('\\hyperref[\\detokenize{index:fig1}]{Fig.\\ref{\\detokenize{index:fig1}} '
            '\\nameref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]{Sect.\\ref{\\detokenize{foo:foo}} '
            '\\nameref{\\detokenize{foo:foo}}}') in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\addto\captionsenglish{\renewcommand{\figurename}{Fig.\@{} }}' in result
    assert r'\addto\captionsenglish{\renewcommand{\tablename}{Table }}' in result
    assert r'\addto\captionsenglish{\renewcommand{\literalblockname}{Listing}}' in result


@pytest.mark.sphinx(
    'latex', testroot='numfig',
    confoverrides={'numfig': True,
                   'numfig_format': {'figure': 'Figure:%s',
                                     'table': 'Tab_%s',
                                     'code-block': 'Code-%s',
                                     'section': 'SECTION-%s'}})
def test_numref_with_prefix1(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
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
            '{Code\\sphinxhyphen{}\\ref{\\detokenize{index:code-1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:code22}]'
            '{Code\\sphinxhyphen{}\\ref{\\detokenize{baz:code22}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]'
            '{SECTION\\sphinxhyphen{}\\ref{\\detokenize{foo:foo}}}') in result
    assert ('\\hyperref[\\detokenize{bar:bar-a}]'
            '{SECTION\\sphinxhyphen{}\\ref{\\detokenize{bar:bar-a}}}') in result
    assert ('\\hyperref[\\detokenize{index:fig1}]{Fig.\\ref{\\detokenize{index:fig1}} '
            '\\nameref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]{Sect.\\ref{\\detokenize{foo:foo}} '
            '\\nameref{\\detokenize{foo:foo}}}') in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\addto\captionsenglish{\renewcommand{\figurename}{Figure:}}' in result
    assert r'\addto\captionsenglish{\renewcommand{\tablename}{Tab\_}}' in result
    assert r'\addto\captionsenglish{\renewcommand{\literalblockname}{Code-}}' in result


@pytest.mark.sphinx(
    'latex', testroot='numfig',
    confoverrides={'numfig': True,
                   'numfig_format': {'figure': 'Figure:%s.',
                                     'table': 'Tab_%s:',
                                     'code-block': 'Code-%s | ',
                                     'section': 'SECTION_%s_'}})
def test_numref_with_prefix2(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\hyperref[\\detokenize{index:fig1}]'
            '{Figure:\\ref{\\detokenize{index:fig1}}.\\@}') in result
    assert ('\\hyperref[\\detokenize{baz:fig22}]'
            '{Figure\\ref{\\detokenize{baz:fig22}}}') in result
    assert ('\\hyperref[\\detokenize{index:table-1}]'
            '{Tab\\_\\ref{\\detokenize{index:table-1}}:}') in result
    assert ('\\hyperref[\\detokenize{baz:table22}]'
            '{Table:\\ref{\\detokenize{baz:table22}}}') in result
    assert ('\\hyperref[\\detokenize{index:code-1}]{Code\\sphinxhyphen{}\\ref{\\detokenize{index:code-1}} '
            '| }') in result
    assert ('\\hyperref[\\detokenize{baz:code22}]'
            '{Code\\sphinxhyphen{}\\ref{\\detokenize{baz:code22}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]'
            '{SECTION\\_\\ref{\\detokenize{foo:foo}}\\_}') in result
    assert ('\\hyperref[\\detokenize{bar:bar-a}]'
            '{SECTION\\_\\ref{\\detokenize{bar:bar-a}}\\_}') in result
    assert ('\\hyperref[\\detokenize{index:fig1}]{Fig.\\ref{\\detokenize{index:fig1}} '
            '\\nameref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]{Sect.\\ref{\\detokenize{foo:foo}} '
            '\\nameref{\\detokenize{foo:foo}}}') in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\addto\captionsenglish{\renewcommand{\figurename}{Figure:}}' in result
    assert r'\def\fnum@figure{\figurename\thefigure{}.}' in result
    assert r'\addto\captionsenglish{\renewcommand{\tablename}{Tab\_}}' in result
    assert r'\def\fnum@table{\tablename\thetable{}:}' in result
    assert r'\addto\captionsenglish{\renewcommand{\literalblockname}{Code-}}' in result


@pytest.mark.sphinx(
    'latex', testroot='numfig',
    confoverrides={'numfig': True, 'language': 'ja'})
def test_numref_with_language_ja(app, status, warning):
    app.build()
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\hyperref[\\detokenize{index:fig1}]'
            '{\u56f3 \\ref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:fig22}]'
            '{Figure\\ref{\\detokenize{baz:fig22}}}') in result
    assert ('\\hyperref[\\detokenize{index:table-1}]'
            '{\u8868 \\ref{\\detokenize{index:table-1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:table22}]'
            '{Table:\\ref{\\detokenize{baz:table22}}}') in result
    assert ('\\hyperref[\\detokenize{index:code-1}]'
            '{\u30ea\u30b9\u30c8 \\ref{\\detokenize{index:code-1}}}') in result
    assert ('\\hyperref[\\detokenize{baz:code22}]'
            '{Code\\sphinxhyphen{}\\ref{\\detokenize{baz:code22}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]'
            '{\\ref{\\detokenize{foo:foo}} \u7ae0}') in result
    assert ('\\hyperref[\\detokenize{bar:bar-a}]'
            '{\\ref{\\detokenize{bar:bar-a}} \u7ae0}') in result
    assert ('\\hyperref[\\detokenize{index:fig1}]{Fig.\\ref{\\detokenize{index:fig1}} '
            '\\nameref{\\detokenize{index:fig1}}}') in result
    assert ('\\hyperref[\\detokenize{foo:foo}]{Sect.\\ref{\\detokenize{foo:foo}} '
            '\\nameref{\\detokenize{foo:foo}}}') in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert '\\@iden{\\renewcommand{\\figurename}{図 }}' in result
    assert '\\@iden{\\renewcommand{\\tablename}{表 }}' in result
    assert '\\@iden{\\renewcommand{\\literalblockname}{リスト}}' in result


@pytest.mark.sphinx('latex', testroot='latex-numfig')
def test_latex_obey_numfig_is_false(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'SphinxManual.tex').read_text(encoding='utf8')
    assert '\\usepackage{sphinx}' in result

    result = (app.outdir / 'SphinxHowTo.tex').read_text(encoding='utf8')
    assert '\\usepackage{sphinx}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-numfig',
    confoverrides={'numfig': True, 'numfig_secnum_depth': 0})
def test_latex_obey_numfig_secnum_depth_is_zero(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'SphinxManual.tex').read_text(encoding='utf8')
    assert '\\usepackage[,nonumfigreset,mathnumfig]{sphinx}' in result

    result = (app.outdir / 'SphinxHowTo.tex').read_text(encoding='utf8')
    assert '\\usepackage[,nonumfigreset,mathnumfig]{sphinx}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-numfig',
    confoverrides={'numfig': True, 'numfig_secnum_depth': 2})
def test_latex_obey_numfig_secnum_depth_is_two(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'SphinxManual.tex').read_text(encoding='utf8')
    assert '\\usepackage[,numfigreset=2,mathnumfig]{sphinx}' in result

    result = (app.outdir / 'SphinxHowTo.tex').read_text(encoding='utf8')
    assert '\\usepackage[,numfigreset=3,mathnumfig]{sphinx}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-numfig',
    confoverrides={'numfig': True, 'math_numfig': False})
def test_latex_obey_numfig_but_math_numfig_false(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'SphinxManual.tex').read_text(encoding='utf8')
    assert '\\usepackage[,numfigreset=1]{sphinx}' in result

    result = (app.outdir / 'SphinxHowTo.tex').read_text(encoding='utf8')
    assert '\\usepackage[,numfigreset=2]{sphinx}' in result


@pytest.mark.sphinx('latex', testroot='basic')
def test_latex_add_latex_package(app, status, warning):
    app.add_latex_package('foo')
    app.add_latex_package('bar', 'baz')
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    assert '\\usepackage{foo}' in result
    assert '\\usepackage[baz]{bar}' in result


@pytest.mark.sphinx('latex', testroot='latex-babel')
def test_babel_with_no_language_settings(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,english]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{tgtermes}' in result
    assert '\\usepackage[Bjarne]{fncychap}' in result
    assert ('\\addto\\captionsenglish{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\shorthandoff{"}' in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\def\pageautorefname{page}' in result
    assert r'\addto\captionsenglish{\renewcommand{\figurename}{Fig.\@{} }}' in result
    assert r'\addto\captionsenglish{\renewcommand{\tablename}{Table.\@{} }}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'de'})
def test_babel_with_language_de(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,ngerman]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{tgtermes}' in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsngerman{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\shorthandoff{"}' in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\def\pageautorefname{Seite}' in result
    assert r'\addto\captionsngerman{\renewcommand{\figurename}{Fig.\@{} }}' in result
    assert r'\addto\captionsngerman{\renewcommand{\tablename}{Table.\@{} }}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'ru'})
def test_babel_with_language_ru(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,russian]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{tgtermes}' not in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsrussian{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\shorthandoff{"}' in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\def\pageautorefname{страница}' in result
    assert r'\addto\captionsrussian{\renewcommand{\figurename}{Fig.\@{} }}' in result
    assert r'\addto\captionsrussian{\renewcommand{\tablename}{Table.\@{} }}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'tr'})
def test_babel_with_language_tr(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,turkish]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{tgtermes}' in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsturkish{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\shorthandoff{=}' in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\def\pageautorefname{sayfa}' in result
    assert r'\addto\captionsturkish{\renewcommand{\figurename}{Fig.\@{} }}' in result
    assert r'\addto\captionsturkish{\renewcommand{\tablename}{Table.\@{} }}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'ja'})
def test_babel_with_language_ja(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,dvipdfmx]{sphinxmanual}' in result
    assert '\\usepackage{babel}' not in result
    assert '\\usepackage{tgtermes}' in result
    assert '\\usepackage[Sonny]{fncychap}' not in result
    assert '\\renewcommand{\\contentsname}{Table of content}\n' in result
    assert '\\shorthandoff' not in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\def\pageautorefname{ページ}' in result
    assert '\\@iden{\\renewcommand{\\figurename}{Fig.\\@{} }}' in result
    assert '\\@iden{\\renewcommand{\\tablename}{Table.\\@{} }}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'unknown'})
def test_babel_with_unknown_language(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,english]{sphinxmanual}' in result
    assert '\\usepackage{babel}' in result
    assert '\\usepackage{tgtermes}' in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsenglish{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\shorthandoff' in result

    assert "WARNING: no Babel option known for language 'unknown'" in warning.getvalue()

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\def\pageautorefname{page}' in result
    assert r'\addto\captionsenglish{\renewcommand{\figurename}{Fig.\@{} }}' in result
    assert r'\addto\captionsenglish{\renewcommand{\tablename}{Table.\@{} }}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'de', 'latex_engine': 'lualatex'})
def test_polyglossia_with_language_de(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,german]{sphinxmanual}' in result
    assert '\\usepackage{polyglossia}' in result
    assert '\\setmainlanguage[spelling=new]{german}' in result
    assert '\\usepackage{tgtermes}' not in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsgerman{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\shorthandoff' not in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\def\pageautorefname{Seite}' in result
    assert r'\addto\captionsgerman{\renewcommand{\figurename}{Fig.\@{} }}' in result
    assert r'\addto\captionsgerman{\renewcommand{\tablename}{Table.\@{} }}' in result


@pytest.mark.sphinx(
    'latex', testroot='latex-babel',
    confoverrides={'language': 'de-1901', 'latex_engine': 'lualatex'})
def test_polyglossia_with_language_de_1901(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\documentclass[letterpaper,10pt,german]{sphinxmanual}' in result
    assert '\\usepackage{polyglossia}' in result
    assert '\\setmainlanguage[spelling=old]{german}' in result
    assert '\\usepackage{tgtermes}' not in result
    assert '\\usepackage[Sonny]{fncychap}' in result
    assert ('\\addto\\captionsgerman{\\renewcommand{\\contentsname}{Table of content}}\n'
            in result)
    assert '\\shorthandoff' not in result

    # sphinxmessages.sty
    result = (app.outdir / 'sphinxmessages.sty').read_text(encoding='utf8')
    print(result)
    assert r'\def\pageautorefname{page}' in result
    assert r'\addto\captionsgerman{\renewcommand{\figurename}{Fig.\@{} }}' in result
    assert r'\addto\captionsgerman{\renewcommand{\tablename}{Table.\@{} }}' in result


@pytest.mark.sphinx('latex')
def test_footnote(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'sphinxtests.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\sphinxAtStartPar\n%\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'numbered\n%\n\\end{footnote}') in result
    assert ('\\begin{footnote}[2]\\sphinxAtStartFootnote\nauto numbered\n%\n'
            '\\end{footnote}') in result
    assert '\\begin{footnote}[3]\\sphinxAtStartFootnote\nnamed\n%\n\\end{footnote}' in result
    assert '\\sphinxcite{footnote:bar}' in result
    assert ('\\bibitem[bar]{footnote:bar}\n\\sphinxAtStartPar\ncite\n') in result
    assert '\\sphinxcaption{Table caption \\sphinxfootnotemark[4]' in result
    assert ('\\sphinxmidrule\n\\sphinxtableatstartofbodyhook%\n'
            '\\begin{footnotetext}[4]\\sphinxAtStartFootnote\n'
            'footnote in table caption\n%\n\\end{footnotetext}\\ignorespaces %\n'
            '\\begin{footnotetext}[5]\\sphinxAtStartFootnote\n'
            'footnote in table header\n%\n\\end{footnotetext}\\ignorespaces '
            '\n\\sphinxAtStartPar\n'
            'VIDIOC\\_CROPCAP\n&\n\\sphinxAtStartPar\n') in result
    assert ('Information about VIDIOC\\_CROPCAP %\n'
            '\\begin{footnote}[6]\\sphinxAtStartFootnote\n'
            'footnote in table not in header\n%\n\\end{footnote}\n\\\\\n'
            '\\sphinxbottomrule\n\\end{tabulary}\n'
            '\\sphinxtableafterendhook\\par\n\\sphinxattableend\\end{savenotes}\n') in result


@pytest.mark.sphinx('latex', testroot='footnotes')
def test_reference_in_caption_and_codeblock_in_footnote(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('\\caption{This is the figure caption with a reference to '
            '\\sphinxcite{index:authoryear}.}' in result)
    assert '\\chapter{The section with a reference to {[}AuthorYear{]}}' in result
    assert ('\\sphinxcaption{The table title with a reference'
            ' to {[}AuthorYear{]}}' in result)
    assert '\\subsubsection*{The rubric title with a reference to {[}AuthorYear{]}}' in result
    assert ('\\chapter{The section with a reference to \\sphinxfootnotemark[6]}\n'
            '\\label{\\detokenize{index:the-section-with-a-reference-to}}'
            '%\n\\begin{footnotetext}[6]\\sphinxAtStartFootnote\n'
            'Footnote in section\n%\n\\end{footnotetext}') in result
    assert ('\\caption{This is the figure caption with a footnote to '
            '\\sphinxfootnotemark[8].}\\label{\\detokenize{index:id35}}\\end{figure}\n'
            '%\n\\begin{footnotetext}[8]\\sphinxAtStartFootnote\n'
            'Footnote in caption\n%\n\\end{footnotetext}') in result
    assert ('\\sphinxcaption{footnote \\sphinxfootnotemark[9] in '
            'caption of normal table}\\label{\\detokenize{index:id36}}') in result
    assert ('\\caption{footnote \\sphinxfootnotemark[10] '
            'in caption \\sphinxfootnotemark[11] of longtable\\strut}') in result
    assert ('\\endlastfoot\n\\sphinxtableatstartofbodyhook\n%\n'
            '\\begin{footnotetext}[10]\\sphinxAtStartFootnote\n'
            'Foot note in longtable\n%\n\\end{footnotetext}\\ignorespaces %\n'
            '\\begin{footnotetext}[11]\\sphinxAtStartFootnote\n'
            'Second footnote in caption of longtable\n') in result
    assert ('This is a reference to the code\\sphinxhyphen{}block in the footnote:\n'
            '{\\hyperref[\\detokenize{index:codeblockinfootnote}]'
            '{\\sphinxcrossref{\\DUrole{std,std-ref}{I am in a footnote}}}}') in result
    assert ('&\n\\sphinxAtStartPar\nThis is one more footnote with some code in it %\n'
            '\\begin{footnote}[12]\\sphinxAtStartFootnote\n'
            'Third footnote in longtable\n') in result
    assert ('\\end{sphinxVerbatim}\n%\n\\end{footnote}.\n') in result
    assert '\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]' in result


@pytest.mark.sphinx('latex', testroot='footnotes')
def test_footnote_referred_multiple_times(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())

    assert ('Explicitly numbered footnote: %\n'
            '\\begin{footnote}[100]'
            '\\sphinxAtStartFootnote\nNumbered footnote\n%\n'
            '\\end{footnote} \\sphinxfootnotemark[100]\n'
            in result)
    assert ('Named footnote: %\n'
            '\\begin{footnote}[13]'
            '\\sphinxAtStartFootnote\nNamed footnote\n%\n'
            '\\end{footnote} \\sphinxfootnotemark[13]\n'
            in result)


@pytest.mark.sphinx(
    'latex', testroot='footnotes',
    confoverrides={'latex_show_urls': 'inline'})
def test_latex_show_urls_is_inline(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number %\n'
            '\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in bar\n%\n\\end{footnote} in bar.rst') in result
    assert ('Auto footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in baz\n%\n\\end{footnote} in baz.rst') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id38}}'
            '{\\hyperref[\\detokenize{index:the-section'
            '-with-a-reference-to-authoryear}]'
            '{\\sphinxcrossref{The section with a reference to '
            '\\sphinxcite{index:authoryear}}}}') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id39}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to}]'
            '{\\sphinxcrossref{The section with a reference to }}}' in result)
    assert ('First footnote: %\n\\begin{footnote}[2]\\sphinxAtStartFootnote\n'
            'First\n%\n\\end{footnote}') in result
    assert ('Second footnote: %\n'
            '\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'Second\n%\n\\end{footnote}\n') in result
    assert '\\sphinxhref{https://sphinx-doc.org/}{Sphinx} (https://sphinx\\sphinxhyphen{}doc.org/)' in result
    assert ('Third footnote: %\n\\begin{footnote}[3]\\sphinxAtStartFootnote\n'
            'Third \\sphinxfootnotemark[4]\n%\n\\end{footnote}%\n'
            '\\begin{footnotetext}[4]\\sphinxAtStartFootnote\n'
            'Footnote inside footnote\n%\n\\end{footnotetext}\\ignorespaces') in result
    assert ('Fourth footnote: %\n\\begin{footnote}[5]\\sphinxAtStartFootnote\n'
            'Fourth\n%\n\\end{footnote}\n') in result
    assert ('\\sphinxhref{https://sphinx-doc.org/~test/}{URL including tilde} '
            '(https://sphinx\\sphinxhyphen{}doc.org/\\textasciitilde{}test/)') in result
    assert ('\\sphinxlineitem{\\sphinxhref{https://sphinx-doc.org/}{URL in term} '
            '(https://sphinx\\sphinxhyphen{}doc.org/)}\n'
            '\\sphinxAtStartPar\nDescription' in result)
    assert ('\\sphinxlineitem{Footnote in term \\sphinxfootnotemark[7]}%\n'
            '\\begin{footnotetext}[7]\\sphinxAtStartFootnote\n' in result)
    assert ('\\sphinxlineitem{\\sphinxhref{https://sphinx-doc.org/}{URL in term} '
            '(https://sphinx\\sphinxhyphen{}doc.org/)}\n'
            '\\sphinxAtStartPar\nDescription' in result)
    assert ('\\sphinxlineitem{Footnote in term \\sphinxfootnotemark[7]}%\n'
            '\\begin{footnotetext}[7]\\sphinxAtStartFootnote\n'
            'Footnote in term\n%\n\\end{footnotetext}\\ignorespaces '
            '\n\\sphinxAtStartPar\nDescription') in result
    assert ('\\sphinxlineitem{\\sphinxhref{https://sphinx-doc.org/}{Term in deflist} '
            '(https://sphinx\\sphinxhyphen{}doc.org/)}'
            '\n\\sphinxAtStartPar\nDescription') in result
    assert '\\sphinxurl{https://github.com/sphinx-doc/sphinx}\n' in result
    assert ('\\sphinxhref{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx\\sphinxhyphen{}dev@googlegroups.com}') in result
    assert '\\begin{savenotes}\\begin{fulllineitems}' not in result


@pytest.mark.sphinx(
    'latex', testroot='footnotes',
    confoverrides={'latex_show_urls': 'footnote'})
def test_latex_show_urls_is_footnote(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number %\n'
            '\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in bar\n%\n\\end{footnote} in bar.rst') in result
    assert ('Auto footnote number %\n\\begin{footnote}[2]\\sphinxAtStartFootnote\n'
            'footnote in baz\n%\n\\end{footnote} in baz.rst') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id38}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to-authoryear}]'
            '{\\sphinxcrossref{The section with a reference '
            'to \\sphinxcite{index:authoryear}}}}') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id39}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to}]'
            '{\\sphinxcrossref{The section with a reference to }}}') in result
    assert ('First footnote: %\n\\begin{footnote}[3]\\sphinxAtStartFootnote\n'
            'First\n%\n\\end{footnote}') in result
    assert ('Second footnote: %\n'
            '\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'Second\n%\n\\end{footnote}') in result
    assert ('\\sphinxhref{https://sphinx-doc.org/}{Sphinx}'
            '%\n\\begin{footnote}[4]\\sphinxAtStartFootnote\n'
            '\\sphinxnolinkurl{https://sphinx-doc.org/}\n%\n\\end{footnote}') in result
    assert ('Third footnote: %\n\\begin{footnote}[6]\\sphinxAtStartFootnote\n'
            'Third \\sphinxfootnotemark[7]\n%\n\\end{footnote}%\n'
            '\\begin{footnotetext}[7]\\sphinxAtStartFootnote\n'
            'Footnote inside footnote\n%\n'
            '\\end{footnotetext}\\ignorespaces') in result
    assert ('Fourth footnote: %\n\\begin{footnote}[8]\\sphinxAtStartFootnote\n'
            'Fourth\n%\n\\end{footnote}\n') in result
    assert ('\\sphinxhref{https://sphinx-doc.org/~test/}{URL including tilde}'
            '%\n\\begin{footnote}[5]\\sphinxAtStartFootnote\n'
            '\\sphinxnolinkurl{https://sphinx-doc.org/~test/}\n%\n\\end{footnote}') in result
    assert ('\\sphinxlineitem{\\sphinxhref{https://sphinx-doc.org/}'
            '{URL in term}\\sphinxfootnotemark[10]}%\n'
            '\\begin{footnotetext}[10]'
            '\\sphinxAtStartFootnote\n'
            '\\sphinxnolinkurl{https://sphinx-doc.org/}\n%\n'
            '\\end{footnotetext}\\ignorespaces \n\\sphinxAtStartPar\nDescription') in result
    assert ('\\sphinxlineitem{Footnote in term \\sphinxfootnotemark[12]}%\n'
            '\\begin{footnotetext}[12]'
            '\\sphinxAtStartFootnote\n'
            'Footnote in term\n%\n\\end{footnotetext}\\ignorespaces '
            '\n\\sphinxAtStartPar\nDescription') in result
    assert ('\\sphinxlineitem{\\sphinxhref{https://sphinx-doc.org/}{Term in deflist}'
            '\\sphinxfootnotemark[11]}%\n'
            '\\begin{footnotetext}[11]'
            '\\sphinxAtStartFootnote\n'
            '\\sphinxnolinkurl{https://sphinx-doc.org/}\n%\n'
            '\\end{footnotetext}\\ignorespaces \n\\sphinxAtStartPar\nDescription') in result
    assert ('\\sphinxurl{https://github.com/sphinx-doc/sphinx}\n' in result)
    assert ('\\sphinxhref{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx\\sphinxhyphen{}dev@googlegroups.com}\n') in result
    assert '\\begin{savenotes}\\begin{fulllineitems}' in result


@pytest.mark.sphinx(
    'latex', testroot='footnotes',
    confoverrides={'latex_show_urls': 'no'})
def test_latex_show_urls_is_no(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert ('Same footnote number %\n'
            '\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in bar\n%\n\\end{footnote} in bar.rst') in result
    assert ('Auto footnote number %\n\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'footnote in baz\n%\n\\end{footnote} in baz.rst') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id38}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to-authoryear}]'
            '{\\sphinxcrossref{The section with a reference '
            'to \\sphinxcite{index:authoryear}}}}') in result
    assert ('\\phantomsection\\label{\\detokenize{index:id39}}'
            '{\\hyperref[\\detokenize{index:the-section-with-a-reference-to}]'
            '{\\sphinxcrossref{The section with a reference to }}}' in result)
    assert ('First footnote: %\n\\begin{footnote}[2]\\sphinxAtStartFootnote\n'
            'First\n%\n\\end{footnote}') in result
    assert ('Second footnote: %\n'
            '\\begin{footnote}[1]\\sphinxAtStartFootnote\n'
            'Second\n%\n\\end{footnote}') in result
    assert '\\sphinxhref{https://sphinx-doc.org/}{Sphinx}' in result
    assert ('Third footnote: %\n\\begin{footnote}[3]\\sphinxAtStartFootnote\n'
            'Third \\sphinxfootnotemark[4]\n%\n\\end{footnote}%\n'
            '\\begin{footnotetext}[4]\\sphinxAtStartFootnote\n'
            'Footnote inside footnote\n%\n\\end{footnotetext}\\ignorespaces') in result
    assert ('Fourth footnote: %\n\\begin{footnote}[5]\\sphinxAtStartFootnote\n'
            'Fourth\n%\n\\end{footnote}\n') in result
    assert '\\sphinxhref{https://sphinx-doc.org/~test/}{URL including tilde}' in result
    assert ('\\sphinxlineitem{\\sphinxhref{https://sphinx-doc.org/}{URL in term}}\n'
            '\\sphinxAtStartPar\nDescription') in result
    assert ('\\sphinxlineitem{Footnote in term \\sphinxfootnotemark[7]}%\n'
            '\\begin{footnotetext}[7]\\sphinxAtStartFootnote\n'
            'Footnote in term\n%\n\\end{footnotetext}\\ignorespaces '
            '\n\\sphinxAtStartPar\nDescription') in result
    assert ('\\sphinxlineitem{\\sphinxhref{https://sphinx-doc.org/}{Term in deflist}}'
            '\n\\sphinxAtStartPar\nDescription') in result
    assert ('\\sphinxurl{https://github.com/sphinx-doc/sphinx}\n' in result)
    assert ('\\sphinxhref{mailto:sphinx-dev@googlegroups.com}'
            '{sphinx\\sphinxhyphen{}dev@googlegroups.com}\n') in result
    assert '\\begin{savenotes}\\begin{fulllineitems}' not in result


@pytest.mark.sphinx(
    'latex', testroot='footnotes',
    confoverrides={'latex_show_urls': 'footnote',
                   'rst_prolog': '.. |URL| replace:: `text <https://www.example.com/>`__'})
def test_latex_show_urls_footnote_and_substitutions(app, status, warning):
    # hyperlinks in substitutions should not effect to make footnotes (refs: #4784)
    test_latex_show_urls_is_footnote(app, status, warning)


@pytest.mark.sphinx('latex', testroot='image-in-section')
def test_image_in_section(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
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
    with pytest.raises(SphinxError):
        app.build(force_all=True)


@pytest.mark.sphinx('latex', testroot='toctree-maxdepth')
def test_toctree_maxdepth_manual(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}{1}' in result
    assert '\\setcounter{secnumdepth}' not in result
    assert '\\chapter{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_documents': [
        ('index', 'python.tex', 'Sphinx Tests Documentation',
         'Georg Brandl', 'howto'),
    ]})
def test_toctree_maxdepth_howto(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}{2}' in result
    assert '\\setcounter{secnumdepth}' not in result
    assert '\\section{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'root_doc': 'foo'})
def test_toctree_not_found(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}' not in result
    assert '\\setcounter{secnumdepth}' not in result
    assert '\\chapter{Foo A}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'root_doc': 'bar'})
def test_toctree_without_maxdepth(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}' not in result
    assert '\\setcounter{secnumdepth}' not in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'root_doc': 'qux'})
def test_toctree_with_deeper_maxdepth(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\setcounter{tocdepth}{3}' in result
    assert '\\setcounter{secnumdepth}{3}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': None})
def test_latex_toplevel_sectioning_is_None(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\chapter{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': 'part'})
def test_latex_toplevel_sectioning_is_part(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
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
                       ('index', 'python.tex', 'Sphinx Tests Documentation',
                        'Georg Brandl', 'howto'),
                   ]})
def test_latex_toplevel_sectioning_is_part_with_howto(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
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
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\chapter{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': 'chapter',
                   'latex_documents': [
                       ('index', 'python.tex', 'Sphinx Tests Documentation',
                        'Georg Brandl', 'howto'),
                   ]})
def test_latex_toplevel_sectioning_is_chapter_with_howto(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\section{Foo}' in result


@pytest.mark.sphinx(
    'latex', testroot='toctree-maxdepth',
    confoverrides={'latex_toplevel_sectioning': 'section'})
def test_latex_toplevel_sectioning_is_section(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    assert '\\section{Foo}' in result


@skip_if_stylefiles_notfound
@pytest.mark.sphinx('latex', testroot='maxlistdepth')
def test_maxlistdepth_at_ten(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    print(status.getvalue())
    print(warning.getvalue())
    compile_latex_document(app, 'python.tex')


@pytest.mark.sphinx('latex', testroot='latex-table',
                    confoverrides={'latex_table_style': []})
@pytest.mark.test_params(shared_result='latex-table')
def test_latex_table_tabulars(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    tables = {}
    for chap in re.split(r'\\(?:section|chapter){', result)[1:]:
        sectname, content = chap.split('}', 1)
        content = re.sub(r'\\sphinxstepscope', '', content)  # filter a separator
        tables[sectname] = content.strip()

    def get_expected(name):
        return (app.srcdir / 'expects' / (name + '.tex')).read_text(encoding='utf8').strip()

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


@pytest.mark.sphinx('latex', testroot='latex-table',
                    confoverrides={'latex_table_style': []})
@pytest.mark.test_params(shared_result='latex-table')
def test_latex_table_longtable(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    tables = {}
    for chap in re.split(r'\\(?:section|chapter){', result)[1:]:
        sectname, content = chap.split('}', 1)
        content = re.sub(r'\\sphinxstepscope', '', content)  # filter a separator
        tables[sectname] = content.strip()

    def get_expected(name):
        return (app.srcdir / 'expects' / (name + '.tex')).read_text(encoding='utf8').strip()

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


@pytest.mark.sphinx('latex', testroot='latex-table',
                    confoverrides={'latex_table_style': []})
@pytest.mark.test_params(shared_result='latex-table')
def test_latex_table_complex_tables(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    tables = {}
    for chap in re.split(r'\\(?:section|renewcommand){', result)[1:]:
        sectname, content = chap.split('}', 1)
        tables[sectname] = content.strip()

    def get_expected(name):
        return (app.srcdir / 'expects' / (name + '.tex')).read_text(encoding='utf8').strip()

    # grid table
    actual = tables['grid table']
    expected = get_expected('gridtable')
    assert actual == expected

    # grid table with tabularcolumns
    # MEMO: filename should end with tabularcolumns but tabularcolumn has been
    #       used in existing other cases
    actual = tables['grid table with tabularcolumns having no vline']
    expected = get_expected('gridtable_with_tabularcolumn')
    assert actual == expected

    # complex spanning cell
    actual = tables['complex spanning cell']
    expected = get_expected('complex_spanning_cell')
    assert actual == expected


@pytest.mark.sphinx('latex', testroot='latex-table')
def test_latex_table_with_booktabs_and_colorrows(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert r'\PassOptionsToPackage{booktabs}{sphinx}' in result
    assert r'\PassOptionsToPackage{colorrows}{sphinx}' in result
    # tabularcolumns
    assert r'\begin{longtable}{|c|c|}' in result
    # class: standard
    assert r'\begin{tabulary}{\linewidth}[t]{|T|T|T|T|T|}' in result
    assert r'\begin{longtable}{ll}' in result
    assert r'\begin{tabular}[t]{*{2}{\X{1}{2}}}' in result
    assert r'\begin{tabular}[t]{\X{30}{100}\X{70}{100}}' in result


@pytest.mark.sphinx('latex', testroot='latex-table',
                    confoverrides={'templates_path': ['_mytemplates/latex']})
def test_latex_table_custom_template_caseA(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert 'SALUT LES COPAINS' in result


@pytest.mark.sphinx('latex', testroot='latex-table',
                    confoverrides={'templates_path': ['_mytemplates']})
def test_latex_table_custom_template_caseB(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert 'SALUT LES COPAINS' not in result


@pytest.mark.sphinx('latex', testroot='latex-table')
@pytest.mark.test_params(shared_result='latex-table')
def test_latex_table_custom_template_caseC(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert 'SALUT LES COPAINS' not in result


@pytest.mark.sphinx('latex', testroot='directives-raw')
def test_latex_raw_directive(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')

    # standard case
    assert 'standalone raw directive (HTML)' not in result
    assert ('\\label{\\detokenize{index:id1}}\n'
            'standalone raw directive (LaTeX)' in result)

    # with substitution
    assert 'HTML: abc  ghi' in result
    assert 'LaTeX: abc def ghi' in result


@pytest.mark.sphinx('latex', testroot='images')
def test_latex_images(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'python.tex').read_text(encoding='utf8')

    # images are copied
    assert '\\sphinxincludegraphics{{python-logo}.png}' in result
    assert (app.outdir / 'python-logo.png').exists()

    # not found images
    assert '\\sphinxincludegraphics{{NOT_EXIST}.PNG}' not in result
    assert ('WARNING: Could not fetch remote image: '
            'https://www.google.com/NOT_EXIST.PNG [404]' in warning.getvalue())

    # an image having target
    assert ('\\sphinxhref{https://www.sphinx-doc.org/}'
            '{\\sphinxincludegraphics{{rimg}.png}}\n\n' in result)

    # a centerized image having target
    assert ('\\sphinxhref{https://www.python.org/}{{\\hspace*{\\fill}'
            '\\sphinxincludegraphics{{rimg}.png}\\hspace*{\\fill}}}\n\n' in result)


@pytest.mark.sphinx('latex', testroot='latex-index')
def test_latex_index(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert ('A \\index{famous@\\spxentry{famous}}famous '
            '\\index{equation@\\spxentry{equation}}equation:\n' in result)
    assert ('\n\\index{Einstein@\\spxentry{Einstein}}'
            '\\index{relativity@\\spxentry{relativity}}'
            '\\ignorespaces \n\\sphinxAtStartPar\nand') in result
    assert ('\n\\index{main \\sphinxleftcurlybrace{}@\\spxentry{'
            'main \\sphinxleftcurlybrace{}}}\\ignorespaces ' in result)


@pytest.mark.sphinx('latex', testroot='latex-equations')
def test_latex_equations(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    expected = (app.srcdir / 'expects' / 'latex-equations.tex').read_text(encoding='utf8').strip()

    assert expected in result


@pytest.mark.sphinx('latex', testroot='image-in-parsed-literal')
def test_latex_image_in_parsed_literal(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert ('{\\sphinxunactivateextrasandspace \\raisebox{-0.5\\height}'
            '{\\sphinxincludegraphics[height=2.00000cm]{{pic}.png}}'
            '}AFTER') in result


@pytest.mark.sphinx('latex', testroot='nested-enumerated-list')
def test_latex_nested_enumerated_list(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert ('\\sphinxsetlistlabels{\\arabic}{enumi}{enumii}{}{.}%\n'
            '\\setcounter{enumi}{4}\n' in result)
    assert ('\\sphinxsetlistlabels{\\alph}{enumii}{enumiii}{}{.}%\n'
            '\\setcounter{enumii}{3}\n' in result)
    assert ('\\sphinxsetlistlabels{\\arabic}{enumiii}{enumiv}{}{)}%\n'
            '\\setcounter{enumiii}{9}\n' in result)
    assert ('\\sphinxsetlistlabels{\\arabic}{enumiv}{enumv}{(}{)}%\n'
            '\\setcounter{enumiv}{23}\n' in result)
    assert ('\\sphinxsetlistlabels{\\roman}{enumii}{enumiii}{}{.}%\n'
            '\\setcounter{enumii}{2}\n' in result)


@pytest.mark.sphinx('latex', testroot='footnotes')
def test_latex_thebibliography(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    assert ('\\begin{sphinxthebibliography}{AuthorYe}\n'
            '\\bibitem[AuthorYear]{index:authoryear}\n\\sphinxAtStartPar\n'
            'Author, Title, Year\n'
            '\\end{sphinxthebibliography}\n' in result)
    assert '\\sphinxcite{index:authoryear}' in result


@pytest.mark.sphinx('latex', testroot='glossary')
def test_latex_glossary(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert (r'\sphinxlineitem{ähnlich\index{ähnlich@\spxentry{ähnlich}|spxpagem}'
            r'\phantomsection'
            r'\label{\detokenize{index:term-ahnlich}}}' in result)
    assert (r'\sphinxlineitem{boson\index{boson@\spxentry{boson}|spxpagem}\phantomsection'
            r'\label{\detokenize{index:term-boson}}}' in result)
    assert (r'\sphinxlineitem{\sphinxstyleemphasis{fermion}'
            r'\index{fermion@\spxentry{fermion}|spxpagem}'
            r'\phantomsection'
            r'\label{\detokenize{index:term-fermion}}}' in result)
    assert (r'\sphinxlineitem{tauon\index{tauon@\spxentry{tauon}|spxpagem}\phantomsection'
            r'\label{\detokenize{index:term-tauon}}}'
            r'\sphinxlineitem{myon\index{myon@\spxentry{myon}|spxpagem}\phantomsection'
            r'\label{\detokenize{index:term-myon}}}'
            r'\sphinxlineitem{electron\index{electron@\spxentry{electron}|spxpagem}\phantomsection'
            r'\label{\detokenize{index:term-electron}}}' in result)
    assert (r'\sphinxlineitem{über\index{über@\spxentry{über}|spxpagem}\phantomsection'
            r'\label{\detokenize{index:term-uber}}}' in result)


@pytest.mark.sphinx('latex', testroot='latex-labels')
def test_latex_labels(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'python.tex').read_text(encoding='utf8')

    # figures
    assert (r'\caption{labeled figure}'
            r'\label{\detokenize{index:id1}}'
            r'\label{\detokenize{index:figure2}}'
            r'\label{\detokenize{index:figure1}}'
            r'\end{figure}' in result)
    assert (r'\caption{labeled figure}'
            '\\label{\\detokenize{index:figure3}}\n'
            '\\begin{sphinxlegend}\n\\sphinxAtStartPar\n'
            'with a legend\n\\end{sphinxlegend}\n'
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

    # Embedded standalone hyperlink reference (refs: #5948)
    assert result.count(r'\label{\detokenize{index:section1}}') == 1


@pytest.mark.sphinx('latex', testroot='latex-figure-in-admonition')
def test_latex_figure_in_admonition(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert r'\begin{figure}[H]' in result


def test_default_latex_documents():
    from sphinx.util import texescape
    texescape.init()
    config = Config({'root_doc': 'index',
                     'project': 'STASI™ Documentation',
                     'author': "Wolfgang Schäuble & G'Beckstein."})
    config.add('latex_engine', None, True, None)
    config.add('latex_theme', 'manual', True, None)
    expected = [('index', 'stasi.tex', 'STASI™ Documentation',
                 r"Wolfgang Schäuble \& G\textquotesingle{}Beckstein.\@{}", 'manual')]
    assert default_latex_documents(config) == expected


@skip_if_requested
@skip_if_stylefiles_notfound
@pytest.mark.sphinx('latex', testroot='latex-includegraphics')
def test_includegraphics_oversized(app, status, warning):
    app.build(force_all=True)
    print(status.getvalue())
    print(warning.getvalue())
    compile_latex_document(app)


@pytest.mark.sphinx('latex', testroot='index_on_title')
def test_index_on_title(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert ('\\chapter{Test for index in top level title}\n'
            '\\label{\\detokenize{contents:test-for-index-in-top-level-title}}'
            '\\index{index@\\spxentry{index}}\n'
            in result)


@pytest.mark.sphinx('latex', testroot='latex-unicode',
                    confoverrides={'latex_engine': 'pdflatex'})
def test_texescape_for_non_unicode_supported_engine(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    assert 'script small e: e' in result
    assert 'double struck italic small i: i' in result
    assert r'superscript: \(\sp{\text{0}}\), \(\sp{\text{1}}\)' in result
    assert r'subscript: \(\sb{\text{0}}\), \(\sb{\text{1}}\)' in result


@pytest.mark.sphinx('latex', testroot='latex-unicode',
                    confoverrides={'latex_engine': 'xelatex'})
def test_texescape_for_unicode_supported_engine(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    print(result)
    assert 'script small e: e' in result
    assert 'double struck italic small i: i' in result
    assert 'superscript: ⁰, ¹' in result
    assert 'subscript: ₀, ₁' in result


@pytest.mark.sphinx('latex', testroot='basic',
                    confoverrides={'latex_elements': {'extrapackages': r'\usepackage{foo}'}})
def test_latex_elements_extrapackages(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'test.tex').read_text(encoding='utf8')
    assert r'\usepackage{foo}' in result


@pytest.mark.sphinx('latex', testroot='nested-tables')
def test_latex_nested_tables(app, status, warning):
    app.build(force_all=True)
    assert warning.getvalue() == ''


@pytest.mark.sphinx('latex', testroot='latex-container')
def test_latex_container(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')
    assert r'\begin{sphinxuseclass}{classname}' in result
    assert r'\end{sphinxuseclass}' in result


@pytest.mark.sphinx('latex', testroot='reST-code-role')
def test_latex_code_role(app):
    app.build()
    content = (app.outdir / 'python.tex').read_text(encoding='utf8')

    common_content = (
        r'\PYG{k}{def} '
        r'\PYG{n+nf}{foo}'
        r'\PYG{p}{(}'
        r'\PYG{l+m+mi}{1} '
        r'\PYG{o}{+} '
        r'\PYG{l+m+mi}{2} '
        r'\PYG{o}{+} '
        r'\PYG{k+kc}{None} '
        r'\PYG{o}{+} '
        r'\PYG{l+s+s2}{\PYGZdq{}}'
        r'\PYG{l+s+s2}{abc}'
        r'\PYG{l+s+s2}{\PYGZdq{}}'
        r'\PYG{p}{)}'
        r'\PYG{p}{:} '
        r'\PYG{k}{pass}')
    assert (r'Inline \sphinxcode{\sphinxupquote{%' + '\n' +
            common_content + '%\n}} code block') in content
    assert (r'\begin{sphinxVerbatim}[commandchars=\\\{\}]' +
            '\n' + common_content + '\n' + r'\end{sphinxVerbatim}') in content


@pytest.mark.sphinx('latex', testroot='images')
def test_copy_images(app, status, warning):
    app.build()

    test_dir = Path(app.outdir)
    images = {
        image.name for image in test_dir.rglob('*')
        if image.suffix in {'.gif', '.pdf', '.png', '.svg'}
    }
    images.discard('python-logo.png')
    assert images == {
        'img.pdf',
        'rimg.png',
        'testimäge.png',
    }


@pytest.mark.sphinx('latex', testroot='latex-labels-before-module')
def test_duplicated_labels_before_module(app, status, warning):
    app.build()
    content: str = (app.outdir / 'python.tex').read_text(encoding='utf8')

    def count_label(name):
        text = r'\phantomsection\label{\detokenize{%s}}' % name
        return content.count(text)

    pattern = r'\\phantomsection\\label\{\\detokenize\{index:label-(?:auto-)?\d+[a-z]*}}'
    # labels found in the TeX output
    output_labels = frozenset(match.group() for match in re.finditer(pattern, content))
    # labels that have been tested and occurring exactly once in the output
    tested_labels = set()

    # iterate over the (explicit) labels in the corresponding index.rst
    for rst_label_name in [
        'label_1a', 'label_1b', 'label_2', 'label_3',
        'label_auto_1a', 'label_auto_1b', 'label_auto_2', 'label_auto_3',
    ]:
        tex_label_name = 'index:' + rst_label_name.replace('_', '-')
        tex_label_code = r'\phantomsection\label{\detokenize{%s}}' % tex_label_name
        assert content.count(tex_label_code) == 1, f'duplicated label: {tex_label_name!r}'
        tested_labels.add(tex_label_code)

    # ensure that we did not forget any label to check
    # and if so, report them nicely in case of failure
    assert sorted(tested_labels) == sorted(output_labels)


@pytest.mark.sphinx('latex', testroot='domain-py-python_maximum_signature_line_length',
                    confoverrides={'python_maximum_signature_line_length': 23})
def test_one_parameter_per_line(app, status, warning):
    app.build(force_all=True)
    result = (app.outdir / 'python.tex').read_text(encoding='utf8')

    # TODO: should these asserts check presence or absence of a final \sphinxparamcomma?
    # signature of 23 characters is too short to trigger one-param-per-line mark-up
    assert ('\\pysiglinewithargsret{\\sphinxbfcode{\\sphinxupquote{hello}}}' in result)

    assert ('\\pysigwithonelineperarg{\\sphinxbfcode{\\sphinxupquote{foo}}}' in result)
