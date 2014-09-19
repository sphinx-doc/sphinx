# -*- coding: utf-8 -*-
"""
    test_directive_code
    ~~~~~~~~~~~~~~~~~~~

    Test the code-block directive.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
from xml.etree import ElementTree

from util import with_app, test_roots


def teardown_module():
    (test_roots / 'test-directive-code' / '_build').rmtree(True)


@with_app(buildername='xml',
          srcdir=(test_roots / 'test-directive-code'),
          _copy_to_temp=True)
def test_code_block(app):
    app.builder.build('index')
    et = ElementTree.parse(app.outdir / 'index.xml')
    secs = et.findall('./section/section')
    code_block = secs[0].findall('literal_block')
    assert len(code_block) > 0
    actual = code_block[0].text
    expect = (
        "    def ruby?\n" +
        "        false\n" +
        "    end"
    )
    assert actual == expect


@with_app(buildername='xml',
          srcdir=(test_roots / 'test-directive-code'),
          _copy_to_temp=True)
def test_code_block_dedent(app):
    outdir = app.outdir

    def get_dedent_actual(dedent):
        dedent_text = (app.srcdir / 'dedent.rst').text(encoding='utf-8')
        dedent_text = re.sub(
            r':dedent: \d', ':dedent: %d' % dedent, dedent_text)
        (app.srcdir / 'dedent.rst').write_text(dedent_text, encoding='utf-8')

        # use another output dir to force rebuild
        app.outdir = outdir / str(dedent)
        app._init_env(freshenv=True)
        app._init_builder(app.builder.name)
        app.builder.build(['dedent'], method='specific')

        et = ElementTree.parse(app.outdir / 'dedent.xml')
        secs = et.findall('./section/section')
        code_block = secs[0].findall('literal_block')

        assert len(code_block) > 0
        actual = code_block[0].text
        return actual

    for i in range(5):  # 0-4
        actual = get_dedent_actual(i)
        indent = " " * (4 - i)
        expect = (
            indent + "def ruby?\n" +
            indent + "    false\n" +
            indent + "end"
        )
        assert (i, actual) == (i, expect)

    actual = get_dedent_actual(1000)
    assert actual == '\n\n'


@with_app(buildername='html',
          srcdir=(test_roots / 'test-directive-code'),
          _copy_to_temp=True)
def test_code_block_caption_html(app):
    app.builder.build('index')
    html = (app.outdir / 'caption.html').text()
    caption = '<div class="code-block-caption">caption <em>test</em> rb</div>'
    print caption, html
    assert caption in html


@with_app(buildername='latex',
          srcdir=(test_roots / 'test-directive-code'),
          _copy_to_temp=True)
def test_code_block_caption_latex(app):
    app.builder.build('index')
    latex = (app.outdir / 'Python.tex').text()
    caption = '\\caption{caption \\emph{test} rb}'
    assert caption in latex


@with_app(buildername='xml',
          srcdir=(test_roots / 'test-directive-code'),
          _copy_to_temp=True)
def test_literal_include(app):
    app.builder.build('index')
    et = ElementTree.parse(app.outdir / 'index.xml')
    secs = et.findall('./section/section')
    literal_include = secs[1].findall('literal_block')
    literal_src = (app.srcdir / 'literal.inc').text(encoding='utf-8')
    assert len(literal_include) > 0
    actual = literal_include[0].text
    assert actual == literal_src


@with_app(buildername='xml',
          srcdir=(test_roots / 'test-directive-code'),
          _copy_to_temp=True)
def test_literal_include_dedent(app):
    outdir = app.outdir
    literal_src = (app.srcdir / 'literal.inc').text(encoding='utf-8')
    literal_lines = [l[4:] for l in literal_src.split('\n')[9:11]]

    def get_dedent_actual(dedent):
        dedent_text = (app.srcdir / 'dedent.rst').text(encoding='utf-8')
        dedent_text = re.sub(
            r':dedent: \d', ':dedent: %d' % dedent, dedent_text)
        (app.srcdir / 'dedent.rst').write_text(dedent_text, encoding='utf-8')

        # use another output dir to force rebuild
        app.outdir = outdir / str(dedent)
        app._init_env(freshenv=True)
        app._init_builder(app.builder.name)
        app.builder.build(['dedent'])

        et = ElementTree.parse(app.outdir / 'dedent.xml')
        secs = et.findall('./section/section')
        literal_include = secs[1].findall('literal_block')

        assert len(literal_include) > 0
        actual = literal_include[0].text
        return actual


    for i in range(5):  # 0-4
        actual = get_dedent_actual(i)
        indent = " " * (4 - i)
        expect = '\n'.join(indent + l for l in literal_lines) + '\n'
        assert (i, actual) == (i, expect)


    actual = get_dedent_actual(1000)
    assert actual == '\n\n'


@with_app(buildername='html',
          srcdir=(test_roots / 'test-directive-code'),
          _copy_to_temp=True)
def test_literalinclude_caption_html(app):
    app.builder.build('index')
    html = (app.outdir / 'caption.html').text()
    caption = '<div class="code-block-caption">caption <strong>test</strong> py</div>'
    assert caption in html


@with_app(buildername='latex',
          srcdir=(test_roots / 'test-directive-code'),
          _copy_to_temp=True)
def test_literalinclude_caption_latex(app):
    app.builder.build('index')
    latex = (app.outdir / 'Python.tex').text()
    caption = '\\caption{caption \\textbf{test} py}'
    assert caption in latex
