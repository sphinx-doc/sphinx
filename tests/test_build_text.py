# -*- coding: utf-8 -*-
"""
    test_build_text
    ~~~~~~~~~~~~~~~

    Test the build process with Text builder with the test root.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from textwrap import dedent

from docutils.utils import column_width

from util import *


def with_text_app(*args, **kw):
    default_kw = {
        'buildername': 'text',
        'srcdir': '(empty)',
        'confoverrides': {
            'project': 'text',
            'master_doc': 'contents',
        },
    }
    default_kw.update(kw)
    return with_app(*args, **default_kw)


@with_text_app()
def test_multibyte_title_line(app):
    title = u'\u65e5\u672c\u8a9e'
    underline = u'=' * column_width(title)
    content = u'\n'.join((title, underline, u''))

    (app.srcdir / 'contents.rst').write_text(content, encoding='utf-8')
    app.builder.build_all()
    result = (app.outdir / 'contents.txt').text(encoding='utf-8')

    expect_underline = underline.replace('=', '*')
    result_underline = result.splitlines()[2].strip()
    assert expect_underline == result_underline
