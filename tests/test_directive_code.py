"""
    test_directive_code
    ~~~~~~~~~~~~~~~~~~~

    Test the code-block directive.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

import pytest
from docutils import nodes

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
    assert content == literal_inc_path.read_text()
    assert lines == 13
    assert reader.lineno_start == 1


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_lineno_start(literal_inc_path):
    options = {'lineno-start': 4}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == literal_inc_path.read_text()
    assert lines == 13
    assert reader.lineno_start == 4


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_pyobject1(literal_inc_path):
    options = {'lineno-match': True, 'pyobject': 'Foo'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Foo:\n"
                       "    pass\n")
    assert reader.lineno_start == 5


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
    options = {'lines': '1-3'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("# Literally included file using Python highlighting\n"
                       "\n"
                       "foo = \"Including Unicode characters: üöä\"\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_lines2(literal_inc_path):
    options = {'lines': '1,3,5'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("# Literally included file using Python highlighting\n"
                       "foo = \"Including Unicode characters: üöä\"\n"
                       "class Foo:\n")


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_lines_and_lineno_match1(literal_inc_path):
    options = {'lines': '3-5', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("foo = \"Including Unicode characters: üöä\"\n"
                       "\n"
                       "class Foo:\n")
    assert reader.lineno_start == 3


@pytest.mark.sphinx()  # init locale for errors
def test_LiteralIncludeReader_lines_and_lineno_match2(literal_inc_path, app, status, warning):
    options = {'lines': '0,3,5', 'lineno-match': True}
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
    assert reader.lineno_start == 5


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_start_after(literal_inc_path):
    options = {'lineno-match': True, 'start-after': 'Foo', 'end-before': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("    pass\n"
                       "\n")
    assert reader.lineno_start == 6


@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_LiteralIncludeReader_start_after_and_lines(literal_inc_path):
    options = {'lineno-match': True, 'lines': '6-',
               'start-after': 'Literally', 'end-before': 'comment'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("\n"
                       "class Bar:\n"
                       "    def baz():\n"
                       "        pass\n"
                       "\n")
    assert reader.lineno_start == 7


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


def test_LiteralIncludeReader_end_before(literal_inc_path):
    options = {'end-before': 'nclud'}  # *nclud* matches first and third lines.
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("# Literally included file using Python highlighting\n"
                       "\n")


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
    options = {'lines': '9-11', 'dedent': 2}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("  def baz():\n"
                       "      pass\n"
                       "\n")

    # dedent: 4
    options = {'lines': '9-11', 'dedent': 4}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("def baz():\n"
                       "    pass\n"
                       "\n")

    # dedent: 6
    options = {'lines': '9-11', 'dedent': 6}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("f baz():\n"
                       "  pass\n"
                       "\n")

    # dedent: None
    options = {'lines': '9-11', 'dedent': None}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("def baz():\n"
                       "    pass\n"
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
                       "@@ -6,8 +6,8 @@\n"
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
def test_force_option(app, status, warning):
    app.builder.build(['force'])
    assert 'force.rst' not in warning.getvalue()


@pytest.mark.sphinx('html', testroot='directive-code')
def test_code_block_caption_html(app, status, warning):
    app.builder.build(['caption'])
    html = (app.outdir / 'caption.html').read_text()
    caption = ('<div class="code-block-caption">'
               '<span class="caption-number">Listing 1 </span>'
               '<span class="caption-text">caption <em>test</em> rb'
               '</span><a class="headerlink" href="#id1" '
               'title="Permalink to this code">\xb6</a></div>')
    assert caption in html


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_code_block_caption_latex(app, status, warning):
    app.builder.build_all()
    latex = (app.outdir / 'python.tex').read_text()
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
    latex = (app.outdir / 'python.tex').read_text()
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
    latex = (app.outdir / 'python.tex').read_text().replace('\r\n', '\n')
    includes = '\\fvset{hllines={, 5, 6, 13, 14, 15, 24, 25, 26,}}%\n'
    assert includes in latex
    includes = '\\end{sphinxVerbatim}\n\\sphinxresetverbatimhllines\n'
    assert includes in latex


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literal_include(app, status, warning):
    app.builder.build(['index'])
    et = etree_parse(app.outdir / 'index.xml')
    secs = et.findall('./section/section')
    literal_include = secs[1].findall('literal_block')
    literal_src = (app.srcdir / 'literal.inc').read_text()
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
    html = (app.outdir / 'linenos.html').read_text()

    # :linenos:
    assert ('<span class="linenos"> 1</span><span class="c1">'
            '# Literally included file using Python highlighting</span>' in html)

    # :lineno-start:
    assert ('<span class="linenos">200</span><span class="c1">'
            '# Literally included file using Python highlighting</span>' in html)

    # :lines: 5-9
    assert ('<span class="linenos">5</span><span class="k">class</span> '
            '<span class="nc">Foo</span><span class="p">:</span>' in html)


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_literalinclude_file_whole_of_emptyline(app, status, warning):
    app.builder.build_all()
    latex = (app.outdir / 'python.tex').read_text().replace('\r\n', '\n')
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
    html = (app.outdir / 'caption.html').read_text()
    caption = ('<div class="code-block-caption">'
               '<span class="caption-number">Listing 2 </span>'
               '<span class="caption-text">caption <strong>test</strong> py'
               '</span><a class="headerlink" href="#id2" '
               'title="Permalink to this code">\xb6</a></div>')
    assert caption in html


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_literalinclude_caption_latex(app, status, warning):
    app.builder.build('index')
    latex = (app.outdir / 'python.tex').read_text()
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
    latex = (app.outdir / 'python.tex').read_text()
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


@pytest.mark.sphinx('dummy', testroot='directive-code')
def test_code_block_highlighted(app, status, warning):
    app.builder.build(['highlight'])
    doctree = app.env.get_doctree('highlight')
    codeblocks = list(doctree.traverse(nodes.literal_block))

    assert codeblocks[0]['language'] == 'default'
    assert codeblocks[1]['language'] == 'python2'
    assert codeblocks[2]['language'] == 'python3'
    assert codeblocks[3]['language'] == 'python2'


@pytest.mark.sphinx('html', testroot='directive-code')
def test_linenothreshold(app, status, warning):
    app.builder.build(['linenothreshold'])
    html = (app.outdir / 'linenothreshold.html').read_text()

    # code-block using linenothreshold
    assert ('<span class="linenos">1</span><span class="k">class</span> '
            '<span class="nc">Foo</span><span class="p">:</span>' in html)

    # code-block not using linenothreshold (no line numbers)
    assert '<span></span><span class="c1"># comment</span>' in html

    # literal include using linenothreshold
    assert ('<span class="linenos"> 1</span><span class="c1">'
            '# Literally included file using Python highlighting</span>' in html)

    # literal include not using linenothreshold (no line numbers)
    assert ('<span></span><span class="c1"># Very small literal include '
            '(linenothreshold check)</span>' in html)
