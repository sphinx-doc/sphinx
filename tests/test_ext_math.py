# -*- coding: utf-8 -*-
"""
    test_ext_math
    ~~~~~~~~~~~~~

    Test math extensions.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from util import with_app, SkipTest


@with_app(buildername='html', testroot='ext-math',
          confoverrides = {'extensions': ['sphinx.ext.jsmath'], 'jsmath_path': 'dummy.js'})
def test_jsmath(app, status, warning):
    app.builder.build_all()
    content = (app.outdir / 'math.html').text()

    assert '<div class="math">\na^2 + b^2 = c^2</div>' in content
    assert '<div class="math">\n\\begin{split}a + 1 &lt; b\\end{split}</div>' in content
    assert (u'<span class="eqno">(1)<a class="headerlink" href="#equation-foo" '
            u'title="Permalink to this equation">\xb6</a></span>'
            u'<div class="math" id="equation-foo">\ne^{i\\pi} = 1</div>' in content)
    assert (u'<span class="eqno">(2)<a class="headerlink" href="#equation-math:0" '
            u'title="Permalink to this equation">\xb6</a></span>'
            u'<div class="math" id="equation-math:0">\n'
            u'e^{ix} = \\cos x + i\\sin x</div>' in content)
    assert '<div class="math">\nn \\in \\mathbb N</div>' in content
    assert '<div class="math">\na + 1 &lt; b</div>' in content


@with_app('html', testroot='ext-math-simple',
          confoverrides = {'extensions': ['sphinx.ext.imgmath']})
def test_imgmath_png(app, status, warning):
    app.builder.build_all()
    if "LaTeX command 'latex' cannot be run" in warning.getvalue():
        raise SkipTest('LaTeX command "latex" is not available')
    if "dvipng command 'dvipng' cannot be run" in warning.getvalue():
        raise SkipTest('dvipng command "dvipng" is not available')

    content = (app.outdir / 'index.html').text()
    html = ('<div class="math">\s*<p>\s*<img src="_images/math/\w+.png"'
            '\s*alt="a\^2\+b\^2=c\^2"/>\s*</p>\s*</div>')
    assert re.search(html, content, re.S)


@with_app('html', testroot='ext-math-simple',
          confoverrides={'extensions': ['sphinx.ext.imgmath'],
                         'imgmath_image_format': 'svg'})
def test_imgmath_svg(app, status, warning):
    app.builder.build_all()
    if "LaTeX command 'latex' cannot be run" in warning.getvalue():
        raise SkipTest('LaTeX command "latex" is not available')
    if "dvisvgm command 'dvisvgm' cannot be run" in warning.getvalue():
        raise SkipTest('dvisvgm command "dvisvgm" is not available')

    content = (app.outdir / 'index.html').text()
    html = ('<div class="math">\s*<p>\s*<img src="_images/math/\w+.svg"'
            '\s*alt="a\^2\+b\^2=c\^2"/>\s*</p>\s*</div>')
    assert re.search(html, content, re.S)


@with_app('html', testroot='ext-math',
          confoverrides={'extensions': ['sphinx.ext.mathjax']})
def test_mathjax_align(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()
    html = (r'<div class="math">\s*'
            r'\\\[ \\begin\{align\}\\begin\{aligned\}S \&amp;= \\pi r\^2\\\\'
            r'V \&amp;= \\frac\{4\}\{3\} \\pi r\^3\\end\{aligned\}\\end\{align\} \\\]</div>')
    assert re.search(html, content, re.S)


@with_app('html', testroot='ext-math',
          confoverrides={'math_number_all': True,
                         'extensions': ['sphinx.ext.mathjax']})
def test_math_number_all_mathjax(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()
    html = (r'<div class="math" id="equation-index:0">\s*'
            r'<span class="eqno">\(1\)<a .*>\xb6</a></span>\\\[a\^2\+b\^2=c\^2\\\]</div>')
    assert re.search(html, content, re.S)


@with_app('latex', testroot='ext-math',
          confoverrides={'extensions': ['sphinx.ext.mathjax']})
def test_math_number_all_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'test.tex').text()
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
