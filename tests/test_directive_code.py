# -*- coding: utf-8 -*-
"""
    test_directive_code
    ~~~~~~~~~~~~~~~~~~~

    Test the code-block directive.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from xml.etree import ElementTree

from util import with_app


@with_app('xml', testroot='directive-code')
def test_code_block(app, status, warning):
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


@with_app('xml', testroot='directive-code')
def test_code_block_dedent(app, status, warning):
    app.builder.build(['dedent_code'])
    et = ElementTree.parse(app.outdir / 'dedent_code.xml')
    blocks = et.findall('./section/section/literal_block')

    for i in range(5):  # 0-4
        actual = blocks[i].text
        indent = " " * (4 - i)
        expect = (
            indent + "def ruby?\n" +
            indent + "    false\n" +
            indent + "end"
        )
        assert (i, actual) == (i, expect)

    assert blocks[5].text == '\n\n'   # dedent: 1000


@with_app('html', testroot='directive-code')
def test_code_block_caption_html(app, status, warning):
    app.builder.build(['caption'])
    html = (app.outdir / 'caption.html').text(encoding='utf-8')
    caption = (u'<div class="code-block-caption">'
               u'<span class="caption-number">Listing 1 </span>'
               u'<span class="caption-text">caption <em>test</em> rb'
               u'</span><a class="headerlink" href="#id1" '
               u'title="Permalink to this code">\xb6</a></div>')
    assert caption in html


@with_app('latex', testroot='directive-code')
def test_code_block_caption_latex(app, status, warning):
    app.builder.build_all()
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8')
    caption = '\\sphinxSetupCaptionForVerbatim{caption \\sphinxstyleemphasis{test} rb}'
    label = '\\def\\sphinxLiteralBlockLabel{\\label{caption:id1}}'
    link  = '\hyperref[caption:name-test-rb]' \
            '{Listing \\ref{caption:name-test-rb}}'
    assert caption in latex
    assert label in latex
    assert link in latex


@with_app('latex', testroot='directive-code')
def test_code_block_namedlink_latex(app, status, warning):
    app.builder.build_all()
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8')
    label1 = '\def\sphinxLiteralBlockLabel{\label{caption:name-test-rb}}'
    link1  = '\\hyperref[caption:name\\string-test\\string-rb]'\
             '{\\sphinxcrossref{\\DUrole{std,std-ref}{Ruby}}'
    label2 = '\def\sphinxLiteralBlockLabel{\label{namedblocks:some-ruby-code}}'
    link2  = '\\hyperref[namedblocks:some\\string-ruby\\string-code]'\
             '{\\sphinxcrossref{\\DUrole{std,std-ref}{the ruby code}}}'
    assert label1 in latex
    assert link1 in latex
    assert label2 in latex
    assert link2 in latex


@with_app('xml', testroot='directive-code')
def test_literal_include(app, status, warning):
    app.builder.build(['index'])
    et = ElementTree.parse(app.outdir / 'index.xml')
    secs = et.findall('./section/section')
    literal_include = secs[1].findall('literal_block')
    literal_src = (app.srcdir / 'literal.inc').text(encoding='utf-8')
    assert len(literal_include) > 0
    actual = literal_include[0].text
    assert actual == literal_src


@with_app('xml', testroot='directive-code')
def test_literal_include_dedent(app, status, warning):
    literal_src = (app.srcdir / 'literal.inc').text(encoding='utf-8')
    literal_lines = [l[4:] for l in literal_src.split('\n')[9:11]]

    app.builder.build(['dedent'])
    et = ElementTree.parse(app.outdir / 'dedent.xml')
    blocks = et.findall('./section/section/literal_block')

    for i in range(5):  # 0-4
        actual = blocks[i].text
        indent = ' ' * (4 - i)
        expect = '\n'.join(indent + l for l in literal_lines) + '\n'
        assert (i, actual) == (i, expect)

    assert blocks[5].text == '\n\n'   # dedent: 1000


@with_app('xml', testroot='directive-code')
def test_literal_include_block_start_with_comment_or_brank(app, status, warning):
    app.builder.build(['python'])
    et = ElementTree.parse(app.outdir / 'python.xml')
    secs = et.findall('./section/section')
    literal_include = secs[0].findall('literal_block')
    assert len(literal_include) > 0
    actual = literal_include[0].text
    expect = (
        'def block_start_with_comment():\n'
        '    # Comment\n'
        '    return 1\n'
    )
    assert actual == expect

    actual = literal_include[1].text
    expect = (
        'def block_start_with_blank():\n'
        '\n'
        '    return 1\n'
    )
    assert actual == expect


@with_app('html', testroot='directive-code')
def test_literal_include_linenos(app, status, warning):
    app.builder.build(['linenos'])
    html = (app.outdir / 'linenos.html').text(encoding='utf-8')
    linenos = (
        '<td class="linenos"><div class="linenodiv"><pre>'
        ' 1\n'
        ' 2\n'
        ' 3\n'
        ' 4\n'
        ' 5\n'
        ' 6\n'
        ' 7\n'
        ' 8\n'
        ' 9\n'
        '10\n'
        '11\n'
        '12\n'
        '13\n'
        '14</pre></div></td>')
    assert linenos in html


@with_app('html', testroot='directive-code')
def test_literal_include_lineno_start(app, status, warning):
    app.builder.build(['lineno_start'])
    html = (app.outdir / 'lineno_start.html').text(encoding='utf-8')
    linenos = (
        '<td class="linenos"><div class="linenodiv"><pre>'
        '200\n'
        '201\n'
        '202\n'
        '203\n'
        '204\n'
        '205\n'
        '206\n'
        '207\n'
        '208\n'
        '209\n'
        '210\n'
        '211\n'
        '212\n'
        '213</pre></div></td>')
    assert linenos in html


@with_app('html', testroot='directive-code')
def test_literal_include_lineno_match(app, status, warning):
    app.builder.build(['lineno_match'])
    html = (app.outdir / 'lineno_match.html').text(encoding='utf-8')
    pyobject = (
        '<td class="linenos"><div class="linenodiv"><pre>'
        ' 9\n'
        '10\n'
        '11</pre></div></td>')

    assert pyobject in html

    lines = (
        '<td class="linenos"><div class="linenodiv"><pre>'
        '5\n'
        '6\n'
        '7\n'
        '8\n'
        '9</pre></div></td>')
    assert lines in html

    start_after = (
        '<td class="linenos"><div class="linenodiv"><pre>'
        ' 8\n'
        ' 9\n'
        '10\n'
        '11\n'
        '12\n'
        '13\n'
        '14</pre></div></td>')
    assert start_after in html

    start_at_end_at = (
        '<td class="linenos"><div class="linenodiv"><pre>'
        ' 9\n'
        '10\n'
        '11</pre></div></td>')
    assert start_at_end_at in html


@with_app('latex', testroot='directive-code')
def test_literalinclude_file_whole_of_emptyline(app, status, warning):
    app.builder.build_all()
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8').replace('\r\n', '\n')
    includes = (
        '\\begin{sphinxVerbatim}'
        '[commandchars=\\\\\\{\\},numbers=left,firstnumber=1,stepnumber=1]\n'
        '\n'
        '\n'
        '\n'
        '\\end{sphinxVerbatim}\n')
    assert includes in latex


@with_app('html', testroot='directive-code')
def test_literalinclude_caption_html(app, status, warning):
    app.builder.build('index')
    html = (app.outdir / 'caption.html').text(encoding='utf-8')
    caption = (u'<div class="code-block-caption">'
               u'<span class="caption-number">Listing 2 </span>'
               u'<span class="caption-text">caption <strong>test</strong> py'
               u'</span><a class="headerlink" href="#id2" '
               u'title="Permalink to this code">\xb6</a></div>')
    assert caption in html


@with_app('latex', testroot='directive-code')
def test_literalinclude_caption_latex(app, status, warning):
    app.builder.build('index')
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8')
    caption = '\\sphinxSetupCaptionForVerbatim{caption \\sphinxstylestrong{test} py}'
    label = '\\def\\sphinxLiteralBlockLabel{\\label{caption:id2}}'
    link  = '\hyperref[caption:name-test-py]' \
            '{Listing \\ref{caption:name-test-py}}'
    assert caption in latex
    assert label in latex
    assert link in latex


@with_app('latex', testroot='directive-code')
def test_literalinclude_namedlink_latex(app, status, warning):
    app.builder.build('index')
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8')
    label1 = '\def\sphinxLiteralBlockLabel{\label{caption:name-test-py}}'
    link1  = '\\hyperref[caption:name\\string-test\\string-py]'\
             '{\\sphinxcrossref{\\DUrole{std,std-ref}{Python}}'
    label2 = '\def\sphinxLiteralBlockLabel{\label{namedblocks:some-python-code}}'
    link2  = '\\hyperref[namedblocks:some\\string-python\\string-code]'\
             '{\\sphinxcrossref{\\DUrole{std,std-ref}{the python code}}}'
    assert label1 in latex
    assert link1 in latex
    assert label2 in latex
    assert link2 in latex


@with_app('xml', testroot='directive-code')
def test_literalinclude_classes(app, status, warning):
    app.builder.build(['classes'])
    et = ElementTree.parse(app.outdir / 'classes.xml')
    secs = et.findall('./section/section')

    code_block = secs[0].findall('literal_block')
    assert len(code_block) > 0
    assert 'foo bar' == code_block[0].get('classes')
    assert 'code_block' == code_block[0].get('names')

    literalinclude = secs[1].findall('literal_block')
    assert len(literalinclude) > 0
    assert 'bar baz' == literalinclude[0].get('classes')
    assert 'literal_include' == literalinclude[0].get('names')
