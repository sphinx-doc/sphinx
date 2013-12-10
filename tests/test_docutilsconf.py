# -*- coding: utf-8 -*-
"""
    test_docutilsconf
    ~~~~~~~~~~~~~~~~~

    Test docutils.conf support for several writers.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
from StringIO import StringIO
from functools import wraps

from util import test_roots, TestApp


html_warnfile = StringIO()
root = test_roots / 'test-docutilsconf'


# need cleanenv to rebuild everytime.
# docutils.conf change did not effect to rebuild.
def with_conf_app(docutilsconf='', *args, **kwargs):
    default_kw = {
        'srcdir': root,
        'cleanenv': True,
    }
    default_kw.update(kwargs)
    def generator(func):
        @wraps(func)
        def deco(*args2, **kwargs2):
            app = TestApp(*args, **default_kw)
            (app.srcdir / 'docutils.conf').write_text(docutilsconf)
            try:
                cwd = os.getcwd()
                os.chdir(app.srcdir)
                func(app, *args2, **kwargs2)
            finally:
                os.chdir(cwd)
            # don't execute cleanup if test failed
            app.cleanup()
        return deco
    return generator


def regex_count(expr, result):
    return len(re.findall(expr, result))


@with_conf_app(buildername='html')
def test_html_with_default_docutilsconf(app):
    app.builder.build(['contents'])
    result = (app.outdir / 'contents.html').text(encoding='utf-8')

    assert regex_count(r'<th class="field-name">', result) == 1
    assert regex_count(r'<th class="field-name" colspan="2">', result) == 1
    assert regex_count(r'<td class="option-group">', result) == 1
    assert regex_count(r'<td class="option-group" colspan="2">', result) == 1


@with_conf_app(buildername='html', docutilsconf=(
    '\n[html4css1 writer]'
    '\noption-limit:1'
    '\nfield-name-limit:1'
    '\n')
)
def test_html_with_docutilsconf(app):
    app.builder.build(['contents'])
    result = (app.outdir / 'contents.html').text(encoding='utf-8')

    assert regex_count(r'<th class="field-name">', result) == 0
    assert regex_count(r'<th class="field-name" colspan="2">', result) == 2
    assert regex_count(r'<td class="option-group">', result) == 0
    assert regex_count(r'<td class="option-group" colspan="2">', result) == 2


@with_conf_app(buildername='html', warning=html_warnfile)
def test_html(app):
    app.builder.build(['contents'])
    assert html_warnfile.getvalue() == ''


@with_conf_app(buildername='latex', warning=html_warnfile)
def test_latex(app):
    app.builder.build(['contents'])
    assert html_warnfile.getvalue() == ''


@with_conf_app(buildername='man', warning=html_warnfile)
def test_man(app):
    app.builder.build(['contents'])
    assert html_warnfile.getvalue() == ''


@with_conf_app(buildername='texinfo', warning=html_warnfile)
def test_texinfo(app):
    app.builder.build(['contents'])
    assert html_warnfile.getvalue() == ''
