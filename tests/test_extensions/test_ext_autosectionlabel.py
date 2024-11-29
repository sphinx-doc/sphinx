"""Test sphinx.ext.autosectionlabel extension."""

import re
from pathlib import Path

import pytest


@pytest.mark.sphinx('html', testroot='ext-autosectionlabel')
def test_autosectionlabel_html(app, skipped_labels=False):
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    html = (
        '<li><p><a class="reference internal" href="#introduce-of-sphinx">'
        '<span class=".*?">Introduce of Sphinx</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#installation">'
        '<span class="std std-ref">Installation</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#for-windows-users">'
        '<span class="std std-ref">For Windows users</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#for-unix-users">'
        '<span class="std std-ref">For UNIX users</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#linux">'
        '<span class="std std-ref">Linux</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#freebsd">'
        '<span class="std std-ref">FreeBSD</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    # for smart_quotes (refs: #4027)
    html = (
        '<li><p><a class="reference internal" '
        'href="#this-one-s-got-an-apostrophe">'
        '<span class="std std-ref">This one’s got an apostrophe'
        '</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)


@pytest.mark.sphinx('texinfo', testroot='ext-autosectionlabel')
def test_autosectionlabel_texinfo(app):
    app.build(force_all=True)

    content = (app.outdir / 'projectnamenotset.texi').read_text(encoding='utf8')

    texinfo = (
        '@node Installation,References,Introduce of Sphinx,Top'
        '\n'
        '@anchor{index installation}@anchor{3}'
        '\n'
        '@chapter Installation'
    )
    assert texinfo in content

    texinfo = (
        '@node For Windows users,For UNIX users,,Installation'
        '\n'
        '@anchor{index for-windows-users}@anchor{4}'
        '\n'
        '@section For Windows users'
    )
    assert texinfo in content


# Reuse test definition from above, just change the test root directory
@pytest.mark.sphinx('html', testroot='ext-autosectionlabel-prefix-document')
def test_autosectionlabel_prefix_document_html(app):
    test_autosectionlabel_html(app)


@pytest.mark.sphinx(
    'html',
    testroot='ext-autosectionlabel',
    confoverrides={'autosectionlabel_maxdepth': 3},
)
def test_autosectionlabel_maxdepth(app):
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    # depth: 1
    html = (
        '<li><p><a class="reference internal" href="#test-ext-autosectionlabel">'
        '<span class=".*?">test-ext-autosectionlabel</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    # depth: 2
    html = (
        '<li><p><a class="reference internal" href="#installation">'
        '<span class="std std-ref">Installation</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    # depth: 3
    html = (
        '<li><p><a class="reference internal" href="#for-windows-users">'
        '<span class="std std-ref">For Windows users</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    # depth: 4
    html = '<li><p><span class="xref std std-ref">Linux</span></p></li>'
    assert re.search(html, content, re.DOTALL)

    assert "WARNING: undefined label: 'linux'" in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='ext-autosectionlabel-full-reference')
def test_autosectionlabel_full_reference(app):
    app.build(force_all=True)

    _autosectionlabel_full_reference_html_index(app.outdir / 'index.html')
    _autosectionlabel_full_reference_html_windows(app.outdir / 'windows.html')


def _autosectionlabel_full_reference_html_index(file: Path) -> None:
    content = file.read_text(encoding='utf8')

    html = (
        '<span id="index.Introduction-of-Sphinx"></span><h1>'
        'Introduction of Sphinx<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Introduction-of-Sphinx">'
        '<span class="std std-ref">Introduction of Sphinx</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation"></span><h1>'
        'Installation<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation">'
        '<span class="std std-ref">Installation</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-Windows-users"></span><h2>'
        'For Windows users<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-Windows-users">'
        '<span class="std std-ref">For Windows users</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-Windows-users.Windows"></span><h3>'
        'Windows<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-Windows-users.Windows">'
        '<span class="std std-ref">Windows</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-Windows-users.Windows.Command"></span><h4>'
        'Command<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-Windows-users.Windows.Command">'
        '<span class="std std-ref">Command</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-Windows-users.Windows.Command0"></span><h4>'
        'Command<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-Windows-users.Windows.Command0">'
        '<span class="std std-ref">Command</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-Windows-users.Windows.Command1"></span><h4>'
        'Command<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-Windows-users.Windows.Command1">'
        '<span class="std std-ref">Command</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-UNIX-users"></span><h2>'
        'For UNIX users<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-UNIX-users">'
        '<span class="std std-ref">For UNIX users</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-UNIX-users.Linux"></span><h3>'
        'Linux<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-UNIX-users.Linux">'
        '<span class="std std-ref">Linux</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-UNIX-users.Linux.Command1"></span><h4>'
        'Command1<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-UNIX-users.Linux.Command1">'
        '<span class="std std-ref">Command1</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-UNIX-users.FreeBSD"></span><h3>'
        'FreeBSD<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-UNIX-users.FreeBSD">'
        '<span class="std std-ref">FreeBSD</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="index.Installation.For-UNIX-users.FreeBSD.2nd-Command"></span><h4>'
        '2nd Command<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#index.Installation.For-UNIX-users.FreeBSD.2nd-Command">'
        '<span class="std std-ref">2nd Command</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    # for smart_quotes (refs: #4027)
    html = (
        '<span id="index.Installation.This-one-s-got-an-apostrophe"></span><h2>'
        'This one’s got an apostrophe<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal" '
        'href="#index.Installation.This-one-s-got-an-apostrophe">'
        '<span class="std std-ref">This one’s got an apostrophe'
        '</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)


def _autosectionlabel_full_reference_html_windows(file: Path) -> None:
    content = file.read_text(encoding='utf8')

    html = (
        '<span id="windows.For-Windows-users"></span><h1>'
        'For Windows users<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#windows.For-Windows-users">'
        '<span class="std std-ref">For Windows users</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="windows.For-Windows-users.Windows"></span><h2>'
        'Windows<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#windows.For-Windows-users.Windows">'
        '<span class="std std-ref">Windows</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="windows.For-Windows-users.Windows.Command"></span><h3>'
        'Command<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#windows.For-Windows-users.Windows.Command">'
        '<span class="std std-ref">Command</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="windows.For-Windows-users.Windows.Command0"></span><h3>'
        'Command<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#windows.For-Windows-users.Windows.Command0">'
        '<span class="std std-ref">Command</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<span id="windows.For-Windows-users.Windows.Command1"></span><h3>'
        'Command<a class="headerlink"'
        '.*'
        '<li><p><a class="reference internal"'
        ' href="#windows.For-Windows-users.Windows.Command1">'
        '<span class="std std-ref">Command</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)


@pytest.mark.sphinx('latex', testroot='ext-autosectionlabel-full-reference')
def test_autosectionlabel_full_reference_latex(app):
    app.build(force_all=True)

    content = (app.outdir / 'test.tex').read_text(encoding='utf8')
    content = content.replace('\\', '.').replace('[', '.').replace(']', '.')

    latex = (
        'chapter{Installation}'
        '.*'
        '.label{.detokenize{index.Installation}}'
        '.*'
        '{.hyperref..detokenize{index.Installation}.{.sphinxcrossref{.DUrole{std}{.DUrole{std-ref}{Installation}}}}}'
    )
    assert re.search(latex, content, re.DOTALL)

    latex = (
        'subsubsection{Command}'
        '.*'
        '.label{.detokenize{index.Installation.For-Windows-users.Windows.Command}}'
        '.*'
        '{.hyperref..detokenize{index.Installation.For-Windows-users.Windows.Command}.'
        '{.sphinxcrossref{.DUrole{std}{.DUrole{std-ref}{Command}}}}}'
    )
    assert re.search(latex, content, re.DOTALL)

    latex = (
        'subsubsection{Command}'
        '.*'
        '.label{.detokenize{index.Installation.For-Windows-users.Windows.Command0}}'
        '.*'
        '{.hyperref..detokenize{index.Installation.For-Windows-users.Windows.Command0}.'
        '{.sphinxcrossref{.DUrole{std}{.DUrole{std-ref}{Command}}}}}'
    )
    assert re.search(latex, content, re.DOTALL)

    latex = (
        'subsubsection{Command}'
        '.*'
        '.label{.detokenize{index.Installation.For-Windows-users.Windows.Command1}}'
        '.*'
        '{.hyperref..detokenize{index.Installation.For-Windows-users.Windows.Command1}.'
        '{.sphinxcrossref{.DUrole{std}{.DUrole{std-ref}{Command}}}}}'
    )
    assert re.search(latex, content, re.DOTALL)


@pytest.mark.sphinx('texinfo', testroot='ext-autosectionlabel-full-reference')
def test_autosectionlabel_full_reference_texinfo(app):
    app.build(force_all=True)

    content = (app.outdir / 'projectnamenotset.texi').read_text(encoding='utf8')

    texinfo = (
        '@node Installation,References,Directives,Top'
        '\n'
        '@anchor{index Installation}@anchor{5}@anchor{installation}@anchor{6}'
        '\n'
        '@unnumbered Installation'
    )
    assert texinfo in content

    texinfo = (
        '@node Command,Command<2>,,Windows'
        '\n'
        '@anchor{command}@anchor{b}@anchor{index Installation For-Windows-users Windows Command}@anchor{c}'
        '\n'
        '@subsection Command'
    )
    assert texinfo in content

    texinfo = (
        '@node Command<2>,Command<3>,Command,Windows'
        '\n'
        '@anchor{id1}@anchor{d}@anchor{index Installation For-Windows-users Windows Command0}@anchor{e}'
        '\n'
        '@subsection Command'
    )
    assert texinfo in content

    texinfo = (
        '@node Command<3>,,Command<2>,Windows'
        '\n'
        '@anchor{id2}@anchor{f}@anchor{index Installation For-Windows-users Windows Command1}@anchor{10}'
        '\n'
        '@subsection Command'
    )
    assert texinfo in content
