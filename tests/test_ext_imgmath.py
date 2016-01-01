# -*- coding: utf-8 -*-
"""
    test_ext_imgmath
    ~~~~~~~~~~~~~~~~

    Test sphinx.ext.imgmath extension.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from util import with_app, SkipTest


@with_app('html', testroot='ext-imgmath')
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

@with_app('html', testroot='ext-imgmath',
          confoverrides={'imgmath_image_format': 'svg'})
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
