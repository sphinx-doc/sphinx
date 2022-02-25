"""
    test_ext_math
    ~~~~~~~~~~~~~

    Test math extensions.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import subprocess
import warnings

import pytest
from docutils import nodes

from sphinx.ext.mathjax import MATHJAX_URL
from sphinx.testing.util import assert_node


def has_binary(binary):
    try:
        subprocess.check_output([binary])
    except FileNotFoundError:
        return False
    except OSError:
        pass
    return True


@pytest.mark.skipif(not has_binary('dvipng'),
                    reason='Requires dvipng" binary')
@pytest.mark.sphinx('html', testroot='ext-math-simple',
                    confoverrides = {'extensions': ['sphinx.ext.imgmath']})
def test_imgmath_png(app, status, warning):
    app.builder.build_all()
    if "LaTeX command 'latex' cannot be run" in warning.getvalue():
        raise pytest.skip.Exception('LaTeX command "latex" is not available')
    if "dvipng command 'dvipng' cannot be run" in warning.getvalue():
        raise pytest.skip.Exception('dvipng command "dvipng" is not available')

    content = (app.outdir / 'index.html').read_text()
    html = (r'<div class="math">\s*<p>\s*<img src="_images/math/\w+.png"'
            r'\s*alt="a\^2\+b\^2=c\^2"/>\s*</p>\s*</div>')
    assert re.search(html, content, re.S)


@pytest.mark.skipif(not has_binary('dvisvgm'),
                    reason='Requires dvisvgm" binary')
@pytest.mark.sphinx('html', testroot='ext-math-simple',
                    confoverrides={'extensions': ['sphinx.ext.imgmath'],
                                   'imgmath_image_format': 'svg'})
def test_imgmath_svg(app, status, warning):
    app.builder.build_all()
    if "LaTeX command 'latex' cannot be run" in warning.getvalue():
        raise pytest.skip.Exception('LaTeX command "latex" is not available')
    if "dvisvgm command 'dvisvgm' cannot be run" in warning.getvalue():
        raise pytest.skip.Exception('dvisvgm command "dvisvgm" is not available')

    content = (app.outdir / 'index.html').read_text()
    html = (r'<div class="math">\s*<p>\s*<img src="_images/math/\w+.svg"'
            r'\s*alt="a\^2\+b\^2=c\^2"/>\s*</p>\s*</div>')
    assert re.search(html, content, re.S)


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax'],
                                   'mathjax_options': {'integrity': 'sha384-0123456789'}})
def test_mathjax_options(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    assert ('<script async="async" integrity="sha384-0123456789" '
            'src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">'
            '</script>' in content)


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax']})
def test_mathjax_align(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    html = (r'<div class="math notranslate nohighlight">\s*'
            r'\\\[ \\begin\{align\}\\begin\{aligned\}S \&amp;= \\pi r\^2\\\\'
            r'V \&amp;= \\frac\{4\}\{3\} \\pi r\^3\\end\{aligned\}\\end\{align\} \\\]</div>')
    assert re.search(html, content, re.S)


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'math_number_all': True,
                                   'extensions': ['sphinx.ext.mathjax']})
def test_math_number_all_mathjax(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    html = (r'<div class="math notranslate nohighlight" id="equation-index-0">\s*'
            r'<span class="eqno">\(1\)<a .*>\xb6</a></span>\\\[a\^2\+b\^2=c\^2\\\]</div>')
    assert re.search(html, content, re.S)


@pytest.mark.sphinx('latex', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax']})
def test_math_number_all_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'python.tex').read_text()
    macro = (r'\\begin{equation\*}\s*'
             r'\\begin{split}a\^2\+b\^2=c\^2\\end{split}\s*'
             r'\\end{equation\*}')
    assert re.search(macro, content, re.S)

    macro = r'Inline \\\(E=mc\^2\\\)'
    assert re.search(macro, content, re.S)

    macro = (r'\\begin{equation\*}\s*'
             r'\\begin{split}e\^{i\\pi}\+1=0\\end{split}\s+'
             r'\\end{equation\*}')
    assert re.search(macro, content, re.S)

    macro = (r'\\begin{align\*}\\!\\begin{aligned}\s*'
             r'S &= \\pi r\^2\\\\\s*'
             r'V &= \\frac\{4}\{3} \\pi r\^3\\\\\s*'
             r'\\end{aligned}\\end{align\*}')
    assert re.search(macro, content, re.S)

    macro = r'Referencing equation \\eqref{equation:math:foo}.'
    assert re.search(macro, content, re.S)


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax'],
                                   'math_eqref_format': 'Eq.{number}'})
def test_math_eqref_format_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'math.html').read_text()
    html = ('<p>Referencing equation <a class="reference internal" '
            'href="#equation-foo">Eq.1</a> and <a class="reference internal" '
            'href="#equation-foo">Eq.1</a>.</p>')
    assert html in content


@pytest.mark.sphinx('latex', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax'],
                                   'math_eqref_format': 'Eq.{number}'})
def test_math_eqref_format_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'python.tex').read_text()
    macro = (r'Referencing equation Eq.\\ref{equation:math:foo} and '
             r'Eq.\\ref{equation:math:foo}.')
    assert re.search(macro, content, re.S)


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax'],
                                   'numfig': True,
                                   'math_numfig': True})
def test_mathjax_numfig_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'math.html').read_text()
    html = ('<div class="math notranslate nohighlight" id="equation-math-0">\n'
            '<span class="eqno">(1.2)')
    assert html in content
    html = ('<p>Referencing equation <a class="reference internal" '
            'href="#equation-foo">(1.1)</a> and '
            '<a class="reference internal" href="#equation-foo">(1.1)</a>.</p>')
    assert html in content


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.imgmath'],
                                   'numfig': True,
                                   'numfig_secnum_depth': 0,
                                   'math_numfig': True})
def test_imgmath_numfig_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'page.html').read_text()
    html = '<span class="eqno">(3)<a class="headerlink" href="#equation-bar"'
    assert html in content
    html = ('<p>Referencing equations <a class="reference internal" '
            'href="math.html#equation-foo">(1)</a> and '
            '<a class="reference internal" href="#equation-bar">(3)</a>.</p>')
    assert html in content


@pytest.mark.sphinx('dummy', testroot='ext-math-compat')
def test_math_compat(app, status, warning):
    with warnings.catch_warnings(record=True):
        app.builder.build_all()
        doctree = app.env.get_and_resolve_doctree('index', app.builder)

        assert_node(doctree,
                    [nodes.document, nodes.section, (nodes.title,
                                                     [nodes.section, (nodes.title,
                                                                      nodes.paragraph)],
                                                     nodes.section)])
        assert_node(doctree[0][1][1],
                    ('Inline: ',
                     [nodes.math, "E=mc^2"],
                     '\nInline my math: ',
                     [nodes.math, "E = mc^2"]))
        assert_node(doctree[0][2],
                    ([nodes.title, "block"],
                     [nodes.math_block, "a^2+b^2=c^2\n\n"],
                     [nodes.paragraph, "Second math"],
                     [nodes.math_block, "e^{i\\pi}+1=0\n\n"],
                     [nodes.paragraph, "Multi math equations"],
                     [nodes.math_block, "E = mc^2"]))


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax'],
                                   'mathjax3_config': {'extensions': ['tex2jax.js']}})
def test_mathjax3_config(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    assert MATHJAX_URL in content
    assert ('<script defer="defer" src="%s">' % MATHJAX_URL in content)
    assert ('<script>window.MathJax = {"extensions": ["tex2jax.js"]}</script>' in content)


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax'],
                                   'mathjax2_config': {'extensions': ['tex2jax.js']}})
def test_mathjax2_config(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    assert ('<script async="async" src="%s">' % MATHJAX_URL in content)
    assert ('<script type="text/x-mathjax-config">'
            'MathJax.Hub.Config({"extensions": ["tex2jax.js"]})'
            '</script>' in content)


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax'],
                                   'mathjax_options': {'async': 'async'},
                                   'mathjax3_config': {'extensions': ['tex2jax.js']}})
def test_mathjax_options_async_for_mathjax3(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    assert MATHJAX_URL in content
    assert ('<script async="async" src="%s">' % MATHJAX_URL in content)


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax'],
                                   'mathjax_options': {'defer': 'defer'},
                                   'mathjax2_config': {'extensions': ['tex2jax.js']}})
def test_mathjax_options_defer_for_mathjax2(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    assert ('<script defer="defer" src="%s">' % MATHJAX_URL in content)


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax']})
def test_mathjax_is_installed_only_if_document_having_math(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    assert MATHJAX_URL in content

    content = (app.outdir / 'nomath.html').read_text()
    assert MATHJAX_URL not in content


@pytest.mark.sphinx('html', testroot='basic',
                    confoverrides={'extensions': ['sphinx.ext.mathjax']})
def test_mathjax_is_not_installed_if_no_equations(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    assert 'MathJax.js' not in content


@pytest.mark.sphinx('html', testroot='ext-math',
                    confoverrides={'extensions': ['sphinx.ext.mathjax']})
def test_mathjax_is_installed_if_no_equations_when_forced(app, status, warning):
    app.set_html_assets_policy('always')
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    assert MATHJAX_URL in content

    content = (app.outdir / 'nomath.html').read_text()
    assert MATHJAX_URL in content
