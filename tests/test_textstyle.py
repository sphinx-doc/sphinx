# -*- coding: utf-8 -*-
"""
    test_textstyle
    ~~~~~~~~~~~~~~~~~~~~

    Test ruby and del role

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('html', testroot='textstyle')
def test_textstyle_html(app, status, warning):
    app.builder.build_all()
    text = (app.outdir / 'test.html').text()
    text = text.replace('\n', '')
    ruby_sample = ''.join((
        '<ruby><rb>Leo</rb><rp>(</rp><rt>I read</rt><rp>)</rp></ruby>',
        ' ',
        '<ruby><rb>un</rb><rp>(</rp><rt>a</rt><rp>)</rp></ruby>',
        ' ',
        '<ruby><rb>libro</rb><rp>(</rp><rt>book</rt><rp>)</rp></ruby>',
    ))
    del_sample = 'Sold Out: <del>Root Beer 24ct $19.99</del>'
    assert ruby_sample in text
    assert del_sample in text


@pytest.mark.sphinx('man', testroot='textstyle')
def test_textstyle_man(app, status, warning):
    app.builder.build_all()
    text = (app.outdir / 'test.1').text()
    assert 'Leo(I read) un(a) libro(book)' in text
    assert 'Sold Out: [DELETE:Root Beer 24ct $19.99]' in text


@pytest.mark.sphinx('text', testroot='textstyle')
def test_textstyle_text(app, status, warning):
    app.builder.build_all()
    text = (app.outdir / 'test.txt').text()
    assert 'Leo(I read) un(a) libro(book)' in text
    assert 'Sold Out: [DELETE:Root Beer 24ct $19.99]' in text


@pytest.mark.sphinx('texinfo', testroot='textstyle')
def test_textstyle_texinfo(app, status, warning):
    app.builder.build_all()
    text = (app.outdir / 'test.texi').text()
    assert 'Leo(I read) un(a) libro(book)' in text
    assert 'Sold Out: [DELETE:Root Beer 24ct $19.99]' in text


@pytest.mark.sphinx('latex', testroot='textstyle')
def test_textstyle_latex(app, status, warning):
    app.builder.build_all()
    text = (app.outdir / 'test.tex').text()
    ruby = r'\jruby[g]{Leo}{I read} \jruby[g]{un}{a} \jruby[g]{libro}{book}'
    delete = r'Sold Out: \sout{Root Beer 24ct \$19.99}'
    assert ruby in text
    assert delete in text
