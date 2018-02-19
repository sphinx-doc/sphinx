# -*- coding: utf-8 -*-
"""
    test_build_text
    ~~~~~~~~~~~~~~~

    Test the build process with Text builder with the test root.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
from docutils.utils import column_width

from sphinx.writers.text import MAXWIDTH


def with_text_app(*args, **kw):
    default_kw = {
        'buildername': 'text',
        'testroot': 'build-text',
    }
    default_kw.update(kw)
    return pytest.mark.sphinx(*args, **default_kw)


@with_text_app()
def test_maxwitdh_with_prefix(app, status, warning):
    app.builder.build_update()
    result = (app.outdir / 'maxwidth.txt').text(encoding='utf-8')

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
def test_lineblock(app, status, warning):
    # regression test for #1109: need empty line after line block
    app.builder.build_update()
    result = (app.outdir / 'lineblock.txt').text(encoding='utf-8')
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
def test_nonascii_title_line(app, status, warning):
    app.builder.build_update()
    result = (app.outdir / 'nonascii_title.txt').text(encoding='utf-8')
    expect_underline = '*********'
    result_underline = result.splitlines()[1].strip()
    assert expect_underline == result_underline


@with_text_app()
def test_nonascii_table(app, status, warning):
    app.builder.build_update()
    result = (app.outdir / 'nonascii_table.txt').text(encoding='utf-8')
    lines = [line.strip() for line in result.splitlines() if line.strip()]
    line_widths = [column_width(line) for line in lines]
    assert len(set(line_widths)) == 1  # same widths


@with_text_app()
def test_nonascii_maxwidth(app, status, warning):
    app.builder.build_update()
    result = (app.outdir / 'nonascii_maxwidth.txt').text(encoding='utf-8')
    lines = [line.strip() for line in result.splitlines() if line.strip()]
    line_widths = [column_width(line) for line in lines]
    assert max(line_widths) < MAXWIDTH


@with_text_app()
def test_table_with_empty_cell(app, status, warning):
    app.builder.build_update()
    result = (app.outdir / 'table.txt').text(encoding='utf-8')
    lines = [line.strip() for line in result.splitlines() if line.strip()]
    assert lines[0] == "+-------+-------+"
    assert lines[1] == "| XXX   | XXX   |"
    assert lines[2] == "+-------+-------+"
    assert lines[3] == "|       | XXX   |"
    assert lines[4] == "+-------+-------+"
    assert lines[5] == "| XXX   |       |"
    assert lines[6] == "+-------+-------+"


@with_text_app()
def test_list_items_in_admonition(app, status, warning):
    app.builder.build_update()
    result = (app.outdir / 'listitems.txt').text(encoding='utf-8')
    lines = [line.rstrip() for line in result.splitlines()]
    assert lines[0] == "See also:"
    assert lines[1] == ""
    assert lines[2] == "  * item 1"
    assert lines[3] == ""
    assert lines[4] == "  * item 2"


@with_text_app()
def test_secnums(app, status, warning):
    app.builder.build_all()
    contents = (app.outdir / 'contents.txt').text(encoding='utf8')
    lines = contents.splitlines()
    assert lines[0] == "* 1. Section A"
    assert lines[1] == ""
    assert lines[2] == "* 2. Section B"
    assert lines[3] == ""
    assert lines[4] == "  * 2.1. Sub Ba"
    assert lines[5] == ""
    assert lines[6] == "  * 2.2. Sub Bb"
    doc2 = (app.outdir / 'doc2.txt').text(encoding='utf8')
    expect = (
        "2. Section B\n"
        "************\n"
        "\n"
        "\n"
        "2.1. Sub Ba\n"
        "===========\n"
        "\n"
        "\n"
        "2.2. Sub Bb\n"
        "===========\n"
    )
    assert doc2 == expect

    app.config.text_secnumber_suffix = " "
    app.builder.build_all()
    contents = (app.outdir / 'contents.txt').text(encoding='utf8')
    lines = contents.splitlines()
    assert lines[0] == "* 1 Section A"
    assert lines[1] == ""
    assert lines[2] == "* 2 Section B"
    assert lines[3] == ""
    assert lines[4] == "  * 2.1 Sub Ba"
    assert lines[5] == ""
    assert lines[6] == "  * 2.2 Sub Bb"
    doc2 = (app.outdir / 'doc2.txt').text(encoding='utf8')
    expect = (
        "2 Section B\n"
        "***********\n"
        "\n"
        "\n"
        "2.1 Sub Ba\n"
        "==========\n"
        "\n"
        "\n"
        "2.2 Sub Bb\n"
        "==========\n"
    )
    assert doc2 == expect

    app.config.text_add_secnumbers = False
    app.builder.build_all()
    contents = (app.outdir / 'contents.txt').text(encoding='utf8')
    lines = contents.splitlines()
    assert lines[0] == "* Section A"
    assert lines[1] == ""
    assert lines[2] == "* Section B"
    assert lines[3] == ""
    assert lines[4] == "  * Sub Ba"
    assert lines[5] == ""
    assert lines[6] == "  * Sub Bb"
    doc2 = (app.outdir / 'doc2.txt').text(encoding='utf8')
    expect = (
        "Section B\n"
        "*********\n"
        "\n"
        "\n"
        "Sub Ba\n"
        "======\n"
        "\n"
        "\n"
        "Sub Bb\n"
        "======\n"
    )
    assert doc2 == expect
