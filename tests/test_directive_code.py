# -*- coding: utf-8 -*-
"""
    test_directive_code
    ~~~~~~~~~~~~~~~~~~~

    Test the code-block directive.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

import pytest

from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
from sphinx.testing.util import etree_parse

DUMMY_CONFIG = Config({}, {})


@pytest.fixture(scope='module')
def testroot(rootdir):
    testroot_path = rootdir / 'test-directive-code'
    return testroot_path


@pytest.fixture(scope='module')
def literal_inc_path(testroot):
    return testroot / 'literal.inc'


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader(literal_inc_path):
    options = {'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == literal_inc_path.text()
    assert lines == 14
    assert reader.lineno_start == 1


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_lineno_start(literal_inc_path):
    options = {'lineno-start': 5}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == literal_inc_path.text()
    assert lines == 14
    assert reader.lineno_start == 5


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_pyobject1(literal_inc_path):
    options = {'lineno-match': True, 'pyobject': 'Foo'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Foo:\n"
                       "    pass\n")
    assert reader.lineno_start == 6


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_pyobject2(literal_inc_path):
    options = {'pyobject': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Bar:\n"
                       "    def baz():\n"
                       "        pass\n")
    assert reader.lineno_start == 1  # no lineno-match


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_pyobject3(literal_inc_path):
    options = {'pyobject': 'Bar.baz'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("    def baz():\n"
                       "        pass\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_pyobject_and_lines(literal_inc_path):
    options = {'pyobject': 'Bar', 'lines': '2-'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("    def baz():\n"
                       "        pass\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_lines1(literal_inc_path):
    options = {'lines': '1-4'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == (u"# Literally included file using Python highlighting\n"
                       u"# -*- coding: utf-8 -*-\n"
                       u"\n"
                       u"foo = \"Including Unicode characters: üöä\"\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_lines2(literal_inc_path):
    options = {'lines': '1,4,6'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == (u"# Literally included file using Python highlighting\n"
                       u"foo = \"Including Unicode characters: üöä\"\n"
                       u"class Foo:\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_lines_and_lineno_match1(literal_inc_path):
    options = {'lines': '4-6', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == (u"foo = \"Including Unicode characters: üöä\"\n"
                       u"\n"
                       u"class Foo:\n")
    assert reader.lineno_start == 4


@pytest.mark.sphinx()  # init locale for errors
def test_LiteralIncludeReader_lines_and_lineno_match2(literal_inc_path, app, status, warning):
    options = {'lines': '1,4,6', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError):
        content, lines = reader.read()


@pytest.mark.sphinx()  # init locale for errors
def test_LiteralIncludeReader_lines_and_lineno_match3(literal_inc_path, app, status, warning):
    options = {'lines': '100-', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError):
        content, lines = reader.read()


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_start_at(literal_inc_path):
    options = {'lineno-match': True, 'start-at': 'Foo', 'end-at': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Foo:\n"
                       "    pass\n"
                       "\n"
                       "class Bar:\n")
    assert reader.lineno_start == 6


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_start_after(literal_inc_path):
    options = {'lineno-match': True, 'start-after': 'Foo', 'end-before': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("    pass\n"
                       "\n")
    assert reader.lineno_start == 7


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_start_after_and_lines(literal_inc_path):
    options = {'lineno-match': True, 'lines': '6-',
               'start-after': 'coding', 'end-before': 'comment'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("\n"
                       "class Bar:\n"
                       "    def baz():\n"
                       "        pass\n"
                       "\n")
    assert reader.lineno_start == 8


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_start_at_and_lines(literal_inc_path):
    options = {'lines': '2, 3, 5', 'start-at': 'foo', 'end-before': '#'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("\n"
                       "class Foo:\n"
                       "\n")
    assert reader.lineno_start == 1


def test_LiteralIncludeReader_missing_start_and_end(literal_inc_path):
    options = {'start-at': 'NOTHING'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError):
        content, lines = reader.read()

    options = {'end-at': 'NOTHING'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError):
        content, lines = reader.read()

    options = {'start-after': 'NOTHING'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError):
        content, lines = reader.read()

    options = {'end-before': 'NOTHING'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError):
        content, lines = reader.read()


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_prepend(literal_inc_path):
    options = {'lines': '1', 'prepend': 'Hello', 'append': 'Sphinx'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("Hello\n"
                       "# Literally included file using Python highlighting\n"
                       "Sphinx\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_dedent(literal_inc_path):
    # dedent: 2
    options = {'lines': '10-12', 'dedent': 2}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("  def baz():\n"
                       "      pass\n"
                       "\n")

    # dedent: 4
    options = {'lines': '10-12', 'dedent': 4}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("def baz():\n"
                       "    pass\n"
                       "\n")

    # dedent: 6
    options = {'lines': '10-12', 'dedent': 6}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("f baz():\n"
                       "  pass\n"
                       "\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_tabwidth(testroot):
    # tab-width: 4
    options = {'tab-width': 4, 'pyobject': 'Qux'}
    reader = LiteralIncludeReader(testroot / 'target.py', options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Qux:\n"
                       "    def quux(self):\n"
                       "        pass\n")

    # tab-width: 8
    options = {'tab-width': 8, 'pyobject': 'Qux'}
    reader = LiteralIncludeReader(testroot / 'target.py', options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Qux:\n"
                       "        def quux(self):\n"
                       "                pass\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_tabwidth_dedent(testroot):
    options = {'tab-width': 4, 'dedent': 4, 'pyobject': 'Qux.quux'}
    reader = LiteralIncludeReader(testroot / 'target.py', options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("def quux(self):\n"
                       "    pass\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_diff(testroot, literal_inc_path):
    options = {'diff': testroot / 'literal-diff.inc'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("--- " + testroot + "/literal-diff.inc\n"
                       "+++ " + testroot + "/literal.inc\n"
                       "@@ -7,8 +7,8 @@\n"
                       "     pass\n"
                       " \n"
                       " class Bar:\n"
                       "-    def baz(self):\n"
                       "+    def baz():\n"
                       "         pass\n"
                       " \n"
                       "-# comment after Bar class\n"
                       "+# comment after Bar class definition\n"
                       " def bar(): pass\n")


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_code_block(app, status, warning):
    app.builder.build('index')
    et = etree_parse(app.outdir / 'index.xml')
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


@pytest.mark.sphinx('html', testroot='directive-code')
def test_code_block_caption_html(app, status, warning):
    app.builder.build(['caption'])
    html = (app.outdir / 'caption.html').text(encoding='utf-8')
    caption = (u'<div class="code-block-caption">'
               u'<span class="caption-number">Listing 1 </span>'
               u'<span class="caption-text">caption <em>test</em> rb'
               u'</span><a class="headerlink" href="#id1" '
               u'title="Permalink to this code">\xb6</a></div>')
    assert caption in html


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_code_block_caption_latex(app, status, warning):
    app.builder.build_all()
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8')
    caption = '\\sphinxSetupCaptionForVerbatim{caption \\sphinxstyleemphasis{test} rb}'
    label = '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:id1}}}'
    link = '\\hyperref[\\detokenize{caption:name-test-rb}]' \
           '{Listing \\ref{\\detokenize{caption:name-test-rb}}}'
    assert caption in latex
    assert label in latex
    assert link in latex


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_code_block_namedlink_latex(app, status, warning):
    app.builder.build_all()
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8')
    label1 = '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:name-test-rb}}}'
    link1 = '\\hyperref[\\detokenize{caption:name-test-rb}]'\
            '{\\sphinxcrossref{\\DUrole{std,std-ref}{Ruby}}'
    label2 = ('\\def\\sphinxLiteralBlockLabel'
              '{\\label{\\detokenize{namedblocks:some-ruby-code}}}')
    link2 = '\\hyperref[\\detokenize{namedblocks:some-ruby-code}]'\
            '{\\sphinxcrossref{\\DUrole{std,std-ref}{the ruby code}}}'
    assert label1 in latex
    assert link1 in latex
    assert label2 in latex
    assert link2 in latex


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_code_block_emphasize_latex(app, status, warning):
    app.builder.build(['emphasize'])
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8').replace('\r\n', '\n')
    includes = '\\fvset{hllines={, 5, 6, 13, 14, 15, 24, 25, 26, 27,}}%\n'
    assert includes in latex


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literal_include(app, status, warning):
    app.builder.build(['index'])
    et = etree_parse(app.outdir / 'index.xml')
    secs = et.findall('./section/section')
    literal_include = secs[1].findall('literal_block')
    literal_src = (app.srcdir / 'literal.inc').text(encoding='utf-8')
    assert len(literal_include) > 0
    actual = literal_include[0].text
    assert actual == literal_src


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literal_include_block_start_with_comment_or_brank(app, status, warning):
    app.builder.build(['python'])
    et = etree_parse(app.outdir / 'python.xml')
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


@pytest.mark.sphinx('html', testroot='directive-code')
def test_literal_include_linenos(app, status, warning):
    app.builder.build(['linenos'])
    html = (app.outdir / 'linenos.html').text(encoding='utf-8')

    # :linenos:
    assert ('<td class="linenos"><div class="linenodiv"><pre>'
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
            '14</pre></div></td>' in html)

    # :lineno-start:
    assert ('<td class="linenos"><div class="linenodiv"><pre>'
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
            '213</pre></div></td>' in html)

    # :lineno-match:
    assert ('<td class="linenos"><div class="linenodiv"><pre>'
            '5\n'
            '6\n'
            '7\n'
            '8\n'
            '9</pre></div></td>' in html)


@pytest.mark.sphinx('latex', testroot='directive-code')
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


@pytest.mark.sphinx('html', testroot='directive-code')
def test_literalinclude_caption_html(app, status, warning):
    app.builder.build('index')
    html = (app.outdir / 'caption.html').text(encoding='utf-8')
    caption = (u'<div class="code-block-caption">'
               u'<span class="caption-number">Listing 2 </span>'
               u'<span class="caption-text">caption <strong>test</strong> py'
               u'</span><a class="headerlink" href="#id2" '
               u'title="Permalink to this code">\xb6</a></div>')
    assert caption in html


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_literalinclude_caption_latex(app, status, warning):
    app.builder.build('index')
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8')
    caption = '\\sphinxSetupCaptionForVerbatim{caption \\sphinxstylestrong{test} py}'
    label = '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:id2}}}'
    link = '\\hyperref[\\detokenize{caption:name-test-py}]' \
           '{Listing \\ref{\\detokenize{caption:name-test-py}}}'
    assert caption in latex
    assert label in latex
    assert link in latex


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_literalinclude_namedlink_latex(app, status, warning):
    app.builder.build('index')
    latex = (app.outdir / 'Python.tex').text(encoding='utf-8')
    label1 = '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:name-test-py}}}'
    link1 = '\\hyperref[\\detokenize{caption:name-test-py}]'\
            '{\\sphinxcrossref{\\DUrole{std,std-ref}{Python}}'
    label2 = ('\\def\\sphinxLiteralBlockLabel'
              '{\\label{\\detokenize{namedblocks:some-python-code}}}')
    link2 = '\\hyperref[\\detokenize{namedblocks:some-python-code}]'\
            '{\\sphinxcrossref{\\DUrole{std,std-ref}{the python code}}}'
    assert label1 in latex
    assert link1 in latex
    assert label2 in latex
    assert link2 in latex


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literalinclude_classes(app, status, warning):
    app.builder.build(['classes'])
    et = etree_parse(app.outdir / 'classes.xml')
    secs = et.findall('./section/section')

    code_block = secs[0].findall('literal_block')
    assert len(code_block) > 0
    assert 'foo bar' == code_block[0].get('classes')
    assert 'code_block' == code_block[0].get('names')

    literalinclude = secs[1].findall('literal_block')
    assert len(literalinclude) > 0
    assert 'bar baz' == literalinclude[0].get('classes')
    assert 'literal_include' == literalinclude[0].get('names')


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literalinclude_pydecorators(app, status, warning):
    app.builder.build(['py-decorators'])
    et = etree_parse(app.outdir / 'py-decorators.xml')
    secs = et.findall('./section/section')

    literal_include = secs[0].findall('literal_block')
    assert len(literal_include) == 3

    actual = literal_include[0].text
    expect = (
        '@class_decorator\n'
        '@other_decorator()\n'
        'class TheClass(object):\n'
        '\n'
        '    @method_decorator\n'
        '    @other_decorator()\n'
        '    def the_method():\n'
        '        pass\n'
    )
    assert actual == expect

    actual = literal_include[1].text
    expect = (
        '    @method_decorator\n'
        '    @other_decorator()\n'
        '    def the_method():\n'
        '        pass\n'
    )
    assert actual == expect

    actual = literal_include[2].text
    expect = (
        '@function_decorator\n'
        '@other_decorator()\n'
        'def the_function():\n'
        '    pass\n'
    )
    assert actual == expect
