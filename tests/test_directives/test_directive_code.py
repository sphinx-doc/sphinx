"""Test the code-block directive."""

import os.path

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


def test_LiteralIncludeReader(literal_inc_path):
    options = {'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == literal_inc_path.read_text(encoding='utf8')
    assert lines == 13
    assert reader.lineno_start == 1


def test_LiteralIncludeReader_lineno_start(literal_inc_path):
    options = {'lineno-start': 4}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == literal_inc_path.read_text(encoding='utf8')
    assert lines == 13
    assert reader.lineno_start == 4


def test_LiteralIncludeReader_pyobject1(literal_inc_path):
    options = {'lineno-match': True, 'pyobject': 'Foo'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Foo:\n"
                       "    pass\n")
    assert reader.lineno_start == 5


def test_LiteralIncludeReader_pyobject2(literal_inc_path):
    options = {'pyobject': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Bar:\n"
                       "    def baz():\n"
                       "        pass\n")
    assert reader.lineno_start == 1  # no lineno-match


def test_LiteralIncludeReader_pyobject3(literal_inc_path):
    options = {'pyobject': 'Bar.baz'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("    def baz():\n"
                       "        pass\n")


def test_LiteralIncludeReader_pyobject_and_lines(literal_inc_path):
    options = {'pyobject': 'Bar', 'lines': '2-'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("    def baz():\n"
                       "        pass\n")


def test_LiteralIncludeReader_lines1(literal_inc_path):
    options = {'lines': '1-3'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("# Literally included file using Python highlighting\n"
                       "\n"
                       "foo = \"Including Unicode characters: üöä\"\n")


def test_LiteralIncludeReader_lines2(literal_inc_path):
    options = {'lines': '1,3,5'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("# Literally included file using Python highlighting\n"
                       "foo = \"Including Unicode characters: üöä\"\n"
                       "class Foo:\n")


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
    with pytest.raises(ValueError, match='Cannot use "lineno-match" with a disjoint set of "lines"'):
        reader.read()


@pytest.mark.sphinx()  # init locale for errors
def test_LiteralIncludeReader_lines_and_lineno_match3(literal_inc_path, app, status, warning):
    options = {'lines': '100-', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError, match="Line spec '100-': no lines pulled from include file"):
        reader.read()


def test_LiteralIncludeReader_start_at(literal_inc_path):
    options = {'lineno-match': True, 'start-at': 'Foo', 'end-at': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Foo:\n"
                       "    pass\n"
                       "\n"
                       "class Bar:\n")
    assert reader.lineno_start == 5


def test_LiteralIncludeReader_start_after(literal_inc_path):
    options = {'lineno-match': True, 'start-after': 'Foo', 'end-before': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("    pass\n"
                       "\n")
    assert reader.lineno_start == 6


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
    with pytest.raises(ValueError, match='start-at pattern not found: NOTHING'):
        reader.read()

    options = {'end-at': 'NOTHING'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError, match='end-at pattern not found: NOTHING'):
        reader.read()

    options = {'start-after': 'NOTHING'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError, match='start-after pattern not found: NOTHING'):
        reader.read()

    options = {'end-before': 'NOTHING'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError, match='end-before pattern not found: NOTHING'):
        reader.read()


def test_LiteralIncludeReader_end_before(literal_inc_path):
    options = {'end-before': 'nclud'}  # *nclud* matches first and third lines.
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("# Literally included file using Python highlighting\n"
                       "\n")


def test_LiteralIncludeReader_prepend(literal_inc_path):
    options = {'lines': '1', 'prepend': 'Hello', 'append': 'Sphinx'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("Hello\n"
                       "# Literally included file using Python highlighting\n"
                       "Sphinx\n")


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


def test_LiteralIncludeReader_dedent_and_append_and_prepend(literal_inc_path):
    # dedent: 2
    options = {'lines': '9-11', 'dedent': 2, 'prepend': 'class Foo:', 'append': '# comment'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("class Foo:\n"
                       "  def baz():\n"
                       "      pass\n"
                       "\n"
                       "# comment\n")


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


def test_LiteralIncludeReader_tabwidth_dedent(testroot):
    options = {'tab-width': 4, 'dedent': 4, 'pyobject': 'Qux.quux'}
    reader = LiteralIncludeReader(testroot / 'target.py', options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("def quux(self):\n"
                       "    pass\n")


def test_LiteralIncludeReader_diff(testroot, literal_inc_path):
    options = {'diff': testroot / 'literal-diff.inc'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == ("--- " + os.path.join(testroot, 'literal-diff.inc') + "\n"
                       "+++ " + os.path.join(testroot, 'literal.inc') + "\n"
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
    app.build(filenames=[app.srcdir / 'index.rst'])
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
    app.build(filenames=[app.srcdir / 'force.rst'])
    assert 'force.rst' not in warning.getvalue()


@pytest.mark.sphinx('html', testroot='directive-code')
def test_code_block_caption_html(app, status, warning):
    app.build(filenames=[app.srcdir / 'caption.rst'])
    html = (app.outdir / 'caption.html').read_text(encoding='utf8')
    caption = ('<div class="code-block-caption">'
               '<span class="caption-number">Listing 1 </span>'
               '<span class="caption-text">caption <em>test</em> rb'
               '</span><a class="headerlink" href="#id1" '
               'title="Link to this code">\xb6</a></div>')
    assert caption in html


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_code_block_caption_latex(app, status, warning):
    app.build(force_all=True)
    latex = (app.outdir / 'python.tex').read_text(encoding='utf8')
    caption = '\\sphinxSetupCaptionForVerbatim{caption \\sphinxstyleemphasis{test} rb}'
    label = '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:id1}}}'
    link = '\\hyperref[\\detokenize{caption:name-test-rb}]' \
           '{Listing \\ref{\\detokenize{caption:name-test-rb}}}'
    assert caption in latex
    assert label in latex
    assert link in latex


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_code_block_namedlink_latex(app, status, warning):
    app.build(force_all=True)
    latex = (app.outdir / 'python.tex').read_text(encoding='utf8')
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
    app.build(filenames=[app.srcdir / 'emphasize.rst'])
    latex = (app.outdir / 'python.tex').read_text(encoding='utf8').replace('\r\n', '\n')
    includes = '\\fvset{hllines={, 5, 6, 13, 14, 15, 24, 25, 26,}}%\n'
    assert includes in latex
    includes = '\\end{sphinxVerbatim}\n\\sphinxresetverbatimhllines\n'
    assert includes in latex


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literal_include(app, status, warning):
    app.build(filenames=[app.srcdir / 'index.rst'])
    et = etree_parse(app.outdir / 'index.xml')
    secs = et.findall('./section/section')
    literal_include = secs[1].findall('literal_block')
    literal_src = (app.srcdir / 'literal.inc').read_text(encoding='utf8')
    assert len(literal_include) > 0
    actual = literal_include[0].text
    assert actual == literal_src


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literal_include_block_start_with_comment_or_brank(app, status, warning):
    app.build(filenames=[app.srcdir / 'python.rst'])
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
    app.build(filenames=[app.srcdir / 'linenos.rst'])
    html = (app.outdir / 'linenos.html').read_text(encoding='utf8')

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
    app.build(force_all=True)
    latex = (app.outdir / 'python.tex').read_text(encoding='utf8').replace('\r\n', '\n')
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
    app.build(force_all=True)
    html = (app.outdir / 'caption.html').read_text(encoding='utf8')
    caption = ('<div class="code-block-caption">'
               '<span class="caption-number">Listing 2 </span>'
               '<span class="caption-text">caption <strong>test</strong> py'
               '</span><a class="headerlink" href="#id2" '
               'title="Link to this code">\xb6</a></div>')
    assert caption in html


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_literalinclude_caption_latex(app, status, warning):
    app.build(filenames='index')
    latex = (app.outdir / 'python.tex').read_text(encoding='utf8')
    caption = '\\sphinxSetupCaptionForVerbatim{caption \\sphinxstylestrong{test} py}'
    label = '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:id2}}}'
    link = '\\hyperref[\\detokenize{caption:name-test-py}]' \
           '{Listing \\ref{\\detokenize{caption:name-test-py}}}'
    assert caption in latex
    assert label in latex
    assert link in latex


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_literalinclude_namedlink_latex(app, status, warning):
    app.build(filenames='index')
    latex = (app.outdir / 'python.tex').read_text(encoding='utf8')
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
    app.build(filenames=[app.srcdir / 'classes.rst'])
    et = etree_parse(app.outdir / 'classes.xml')
    secs = et.findall('./section/section')

    code_block = secs[0].findall('literal_block')
    assert len(code_block) > 0
    assert code_block[0].get('classes') == 'foo bar'
    assert code_block[0].get('names') == 'code_block'

    literalinclude = secs[1].findall('literal_block')
    assert len(literalinclude) > 0
    assert literalinclude[0].get('classes') == 'bar baz'
    assert literalinclude[0].get('names') == 'literal_include'


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literalinclude_pydecorators(app, status, warning):
    app.build(filenames=[app.srcdir / 'py-decorators.rst'])
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
    app.build(filenames=[app.srcdir / 'highlight.rst'])
    doctree = app.env.get_doctree('highlight')
    codeblocks = list(doctree.findall(nodes.literal_block))

    assert codeblocks[0]['language'] == 'default'
    assert codeblocks[1]['language'] == 'python2'
    assert codeblocks[2]['language'] == 'python3'
    assert codeblocks[3]['language'] == 'python2'


@pytest.mark.sphinx('html', testroot='directive-code')
def test_linenothreshold(app, status, warning):
    app.build(filenames=[app.srcdir / 'linenothreshold.rst'])
    html = (app.outdir / 'linenothreshold.html').read_text(encoding='utf8')

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


@pytest.mark.sphinx('dummy', testroot='directive-code')
def test_code_block_dedent(app, status, warning):
    app.build(filenames=[app.srcdir / 'dedent.rst'])
    doctree = app.env.get_doctree('dedent')
    codeblocks = list(doctree.findall(nodes.literal_block))
    # Note: comparison string should not have newlines at the beginning or end
    text_0_indent = '''First line
Second line
    Third line
Fourth line'''
    text_2_indent = '''  First line
  Second line
      Third line
  Fourth line'''
    text_4_indent = '''    First line
    Second line
        Third line
    Fourth line'''

    assert codeblocks[0].astext() == text_0_indent
    assert codeblocks[1].astext() == text_0_indent
    assert codeblocks[2].astext() == text_4_indent
    assert codeblocks[3].astext() == text_2_indent
    assert codeblocks[4].astext() == text_4_indent
    assert codeblocks[5].astext() == text_0_indent
