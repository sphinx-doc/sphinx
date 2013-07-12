# -*- coding: utf-8 -*-
"""
    test_build_text
    ~~~~~~~~~~~~~~~

    Test the build process with Text builder with the test root.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils.utils import column_width
from sphinx.writers.text import MAXWIDTH

from util import with_app


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
def test_maxwitdh_with_prefix(app):
    long_string = u' '.join([u"ham"] * 30)
    contents = (
            u".. seealso:: %(long_string)s\n\n"
            u"* %(long_string)s\n"
            u"* %(long_string)s\n"
            u"\nspam egg\n"
            ) % locals()

    (app.srcdir / 'contents.rst').write_text(contents, encoding='utf-8')
    app.builder.build_all()
    result = (app.outdir / 'contents.txt').text(encoding='utf-8')

    lines = result.splitlines()
    line_widths = [column_width(line) for line in lines]
    assert max(line_widths) < MAXWIDTH
    assert lines[0].startswith('See also: ham')
    assert lines[1].startswith('  ham')
    assert lines[2] == ''
    assert lines[3].startswith('* ham')
    assert lines[4].startswith('  ham')
    assert lines[5] == ''
    assert lines[6].startswith('* ham')
    assert lines[7].startswith('  ham')
    assert lines[8] == ''
    assert lines[9].startswith('spam egg')


@with_text_app()
def test_lineblock(app):
    # regression test for #1109: need empty line after line block
    contents = (
            u"* one\n"
            u"\n"
            u"  | line-block 1\n"
            u"  | line-block 2\n"
            u"\n"
            u"followed paragraph.\n"
            )

    (app.srcdir / 'contents.rst').write_text(contents, encoding='utf-8')
    app.builder.build_all()
    result = (app.outdir / 'contents.txt').text(encoding='utf-8')

    expect = (
            u"* one\n"
            u"\n"
            u"     line-block 1\n"
            u"     line-block 2\n"
            u"\n"
            u"followed paragraph.\n"
            )

    assert result == expect


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


@with_text_app()
def test_multibyte_table(app):
    text = u'\u65e5\u672c\u8a9e'
    contents = (u"\n.. list-table::"
                 "\n"
                 "\n   - - spam"
                 "\n     - egg"
                 "\n"
                 "\n   - - %(text)s"
                 "\n     - %(text)s"
                 "\n" % locals())

    (app.srcdir / 'contents.rst').write_text(contents, encoding='utf-8')
    app.builder.build_all()
    result = (app.outdir / 'contents.txt').text(encoding='utf-8')

    lines = [line.strip() for line in result.splitlines() if line.strip()]
    line_widths = [column_width(line) for line in lines]
    assert len(set(line_widths)) == 1  # same widths


@with_text_app()
def test_multibyte_maxwidth(app):
    sb_text = u'abc'  #length=3
    mb_text = u'\u65e5\u672c\u8a9e'  #length=3

    sb_line = ' '.join([sb_text] * int(MAXWIDTH / 3))
    mb_line = ' '.join([mb_text] * int(MAXWIDTH / 3))
    mix_line = ' '.join([sb_text, mb_text] * int(MAXWIDTH / 6))

    contents = u'\n\n'.join((sb_line, mb_line, mix_line))

    (app.srcdir / 'contents.rst').write_text(contents, encoding='utf-8')
    app.builder.build_all()
    result = (app.outdir / 'contents.txt').text(encoding='utf-8')

    lines = [line.strip() for line in result.splitlines() if line.strip()]
    line_widths = [column_width(line) for line in lines]
    assert max(line_widths) < MAXWIDTH
