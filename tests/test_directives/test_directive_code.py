"""Test the code-block directive."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pygments
import pytest
from docutils import nodes

from sphinx.config import Config
from sphinx.directives.code import LiteralIncludeReader
from sphinx.testing.util import etree_parse

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp

DUMMY_CONFIG = Config({}, {})


@pytest.fixture(scope='module')
def testroot(rootdir: Path) -> Path:
    testroot_path = rootdir / 'test-directive-code'
    return testroot_path


@pytest.fixture(scope='module')
def literal_inc_path(testroot: Path) -> Path:
    return testroot / 'literal.inc'


def test_LiteralIncludeReader(literal_inc_path: Path) -> None:
    options = {'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == literal_inc_path.read_text(encoding='utf8')
    assert lines == 13
    assert reader.lineno_start == 1


def test_LiteralIncludeReader_lineno_start(literal_inc_path: Path) -> None:
    options = {'lineno-start': 4}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, lines = reader.read()
    assert content == literal_inc_path.read_text(encoding='utf8')
    assert lines == 13
    assert reader.lineno_start == 4


def test_LiteralIncludeReader_pyobject1(literal_inc_path: Path) -> None:
    options = {'lineno-match': True, 'pyobject': 'Foo'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'class Foo:\n    pass\n'
    assert reader.lineno_start == 5


def test_LiteralIncludeReader_pyobject2(literal_inc_path: Path) -> None:
    options = {'pyobject': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'class Bar:\n    def baz():\n        pass\n'
    assert reader.lineno_start == 1  # no lineno-match


def test_LiteralIncludeReader_pyobject3(literal_inc_path: Path) -> None:
    options = {'pyobject': 'Bar.baz'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '    def baz():\n        pass\n'


def test_LiteralIncludeReader_pyobject_and_lines(literal_inc_path: Path) -> None:
    options = {'pyobject': 'Bar', 'lines': '2-'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '    def baz():\n        pass\n'


def test_LiteralIncludeReader_lines1(literal_inc_path: Path) -> None:
    options = {'lines': '1-3'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == (
        '# Literally included file using Python highlighting\n'
        '\n'
        'foo = "Including Unicode characters: üöä"\n'
    )


def test_LiteralIncludeReader_lines2(literal_inc_path: Path) -> None:
    options = {'lines': '1,3,5'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == (
        '# Literally included file using Python highlighting\n'
        'foo = "Including Unicode characters: üöä"\n'
        'class Foo:\n'
    )


def test_LiteralIncludeReader_lines_negative(literal_inc_path: Path) -> None:
    # Negative end: lines 5 to last
    options = {'lines': '5--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == (
        'class Foo:\n    pass\n\nclass Bar:\n    def baz():\n        pass\n\n'
        '# comment after Bar class definition\ndef bar(): pass\n'
    )

    # Negative start and end: last 3 lines (-3--1)
    options = {'lines': '-3--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == (
        '\n# comment after Bar class definition\ndef bar(): pass\n'
    )

    # Negative start, half-open right: from -3 to end
    options = {'lines': '-3-'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == (
        '\n# comment after Bar class definition\ndef bar(): pass\n'
    )

    # Negative start, positive end: -8-5 → resolved start=6, end=5 → ValueError
    options = {'lines': '-8-5'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError, match='invalid line number spec'):
        reader.read()

    # -10-5: -10 in 13 = line 4, end=5 → lines 4-5 (blank + class Foo:)
    options = {'lines': '-10-5'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '\nclass Foo:\n'

    # Last line only: -1--1
    options = {'lines': '-1--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'def bar(): pass\n'

    # Single negative line via range: -2--2 selects second-to-last line
    options = {'lines': '-2--2'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '# comment after Bar class definition\n'

    # Full file via negative range: -13--1 (13 lines total)
    options = {'lines': '-13--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == literal_inc_path.read_text(encoding='utf8')

    # Out of range negative index: -14--1 in 13-line file
    options = {'lines': '-14--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError, match='negative index out of range'):
        reader.read()


def test_LiteralIncludeReader_lines_negative_lineno_match(literal_inc_path: Path) -> None:
    # lineno-match works with contiguous negative range
    options = {'lines': '-3--1', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    # -3--1 in 13 lines = lines 11-13 (0-based: 10,11,12)
    assert content == (
        '\n'
        '# comment after Bar class definition\n'
        'def bar(): pass\n'
    )
    assert reader.lineno_start == 11

    # lineno-match with positive start, negative end
    options = {'lines': '5--1', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert reader.lineno_start == 5

    # lineno-match with disjoint negative lines must fail
    # -5--4 resolves to lines 9-10, -1--1 resolves to line 13 → disjoint
    options = {'lines': '-5--4,-1--1', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError, match='Cannot use "lineno-match" with a disjoint set of "lines"'):
        reader.read()

    # lineno-match with negative start, half-open right
    options = {'lines': '-3-', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    # -3- in 13 lines = lines 11-13 (0-based: 10,11,12)
    assert content == (
        '\n'
        '# comment after Bar class definition\n'
        'def bar(): pass\n'
    )
    assert reader.lineno_start == 11

    # lineno-match with negative start, positive end
    options = {'lines': '-10-5', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    # -10-5 in 13 lines = lines 4-5
    assert content == '\nclass Foo:\n'
    assert reader.lineno_start == 4


def test_LiteralIncludeReader_lines_negative_comma_separated(literal_inc_path: Path) -> None:
    """Test comma-separated negative line specs."""
    # Multiple negative ranges
    options = {'lines': '-3--1,-6--4'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    # -3--1 = lines 11-13, -6--4 = lines 8-10
    assert '# comment after Bar class definition' in content
    assert 'def bar(): pass' in content
    assert 'def baz():' in content
    assert 'class Bar:' in content

    # Mix of positive and negative
    options = {'lines': '1-2,-2--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    # Line 1-2 and last 2 lines
    assert 'Literally included file' in content
    assert 'comment after Bar class definition' in content
    assert 'def bar(): pass' in content


def test_LiteralIncludeReader_lines_negative_with_pyobject(literal_inc_path: Path) -> None:
    """Test negative lines combined with pyobject filter."""
    # pyobject selects Bar class (lines 8-11), then lines filter applies to that subset
    options = {'pyobject': 'Bar', 'lines': '-2--1', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    # Bar class is 4 lines (8-11), -2--1 in 4 lines = lines 3-4 of selection
    # lines 10-11 of file: "    def baz():\n        pass\n"
    assert 'def baz():' in content
    assert 'pass' in content
    assert reader.lineno_start == 9


def test_LiteralIncludeReader_lines_negative_with_start_after(literal_inc_path: Path) -> None:
    """Test negative lines combined with start-after filter."""
    # start-after selects from after 'class Bar:' (line 8), then lines filter applies
    options = {'start-after': 'class Bar:', 'lines': '-2--1', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    # After 'class Bar:' we have 5 lines (9-13), -2--1 in 5 lines = lines 12-13 of file
    assert '# comment after Bar class definition' in content
    assert 'def bar(): pass' in content
    assert reader.lineno_start == 12


def test_LiteralIncludeReader_lines_negative_single_line(literal_inc_path: Path) -> None:
    """Test single negative line selection via range syntax."""
    # -1--1 selects last line only
    options = {'lines': '-1--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'def bar(): pass\n'

    # -2--2 selects second-to-last line only
    options = {'lines': '-2--2'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '# comment after Bar class definition\n'


def test_LiteralIncludeReader_lines_negative_half_open_right(literal_inc_path: Path) -> None:
    """Test half-open right ranges with negative start."""
    # -3- selects from line -3 to end
    options = {'lines': '-3-'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '\n# comment after Bar class definition\ndef bar(): pass\n'

    # -5- selects from line -5 to end
    options = {'lines': '-5-'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert 'def baz():' in content
    assert 'def bar(): pass' in content


def test_LiteralIncludeReader_lines_negative_empty_result(literal_inc_path: Path) -> None:
    """Test negative ranges that result in empty selection."""
    # -20--15 in 13-line file → out of range, should raise ValueError
    options = {'lines': '-20--15'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError, match='negative index out of range'):
        reader.read()

    # -15--10 in 13-line file → start < 1 after resolution
    options = {'lines': '-15--10'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(ValueError, match='negative index out of range'):
        reader.read()


def test_LiteralIncludeReader_lines_negative_with_prepend_append(literal_inc_path: Path) -> None:
    """Test negative lines combined with prepend and append."""
    options = {'lines': '-2--1', 'prepend': 'HEADER', 'append': 'FOOTER'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content.startswith('HEADER\n')
    assert content.endswith('FOOTER\n')
    assert '# comment after Bar class definition' in content
    assert 'def bar(): pass' in content


def test_LiteralIncludeReader_lines_negative_with_dedent(literal_inc_path: Path) -> None:
    """Test negative lines combined with dedent."""
    # The last few lines have different indentation
    options = {'lines': '9-11', 'dedent': 4}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'def baz():\n    pass\n\n'

    # Test with negative lines that include indented content
    options = {'lines': '-5--1', 'dedent': 4}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    # Lines 9-13 with dedent 4
    assert 'def baz():' in content
    assert 'pass' in content


def test_LiteralIncludeReader_lines_negative_with_diff(literal_inc_path: Path, testroot: Path) -> None:
    """Test negative lines combined with diff option."""
    # diff and lines are mutually exclusive, so test that the error is raised
    literal_diff_path = testroot / 'literal-diff.inc'
    options = {'diff': literal_diff_path, 'lines': '-3--1'}
    with pytest.raises(ValueError, match='Cannot use both "diff" and "lines" options'):
        LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)


def test_LiteralIncludeReader_lines_negative_tab_width(literal_inc_path: Path) -> None:
    """Test negative lines with tab-width option."""
    # Create a file with tabs
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('class TabTest:\n\tdef method(self):\n\t\tpass\n')
        tab_file = f.name
    try:
        options = {'tab-width': 4, 'lines': '-2--1'}
        reader = LiteralIncludeReader(tab_file, options, DUMMY_CONFIG)
        content, _lines = reader.read()
        # Last 2 lines with tabs expanded to 4 spaces
        assert '    def method(self):' in content or '        pass' in content
    finally:
        import os
        os.unlink(tab_file)


def test_LiteralIncludeReader_lines_negative_encoding(literal_inc_path: Path) -> None:
    """Test negative lines with encoding option."""
    options = {'encoding': 'utf-8', 'lines': '-1--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'def bar(): pass\n'


def test_LiteralIncludeReader_lines_negative_force(literal_inc_path: Path) -> None:
    """Test negative lines with force option."""
    options = {'force': True, 'lines': '-1--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'def bar(): pass\n'


def test_LiteralIncludeReader_lines_negative_language(literal_inc_path: Path) -> None:
    """Test negative lines with language option."""
    options = {'language': 'python', 'lines': '-1--1'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'def bar(): pass\n'


@pytest.mark.sphinx('html', testroot='root')  # init locale for errors
def test_LiteralIncludeReader_lines_and_lineno_match2(
    literal_inc_path: Path, app: SphinxTestApp
) -> None:
    options = {'lines': '1,3,5', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(
        ValueError,
        match='Cannot use "lineno-match" with a disjoint set of "lines"',
    ):
        reader.read()


@pytest.mark.sphinx('html', testroot='root')  # init locale for errors
def test_LiteralIncludeReader_lines_and_lineno_match3(
    literal_inc_path: Path, app: SphinxTestApp
) -> None:
    options = {'lines': '100-', 'lineno-match': True}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    with pytest.raises(
        ValueError,
        match="Line spec '100-': no lines pulled from include file",
    ):
        reader.read()


def test_LiteralIncludeReader_start_at(literal_inc_path: Path) -> None:
    options = {'lineno-match': True, 'start-at': 'Foo', 'end-at': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'class Foo:\n    pass\n\nclass Bar:\n'
    assert reader.lineno_start == 5


def test_LiteralIncludeReader_start_after(literal_inc_path: Path) -> None:
    options = {'lineno-match': True, 'start-after': 'Foo', 'end-before': 'Bar'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '    pass\n\n'
    assert reader.lineno_start == 6


def test_LiteralIncludeReader_start_after_and_lines(literal_inc_path: Path) -> None:
    options = {
        'lineno-match': True,
        'lines': '6-',
        'start-after': 'Literally',
        'end-before': 'comment',
    }
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '\nclass Bar:\n    def baz():\n        pass\n\n'
    assert reader.lineno_start == 7


def test_LiteralIncludeReader_start_at_and_lines(literal_inc_path: Path) -> None:
    options = {'lines': '2, 3, 5', 'start-at': 'foo', 'end-before': '#'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '\nclass Foo:\n\n'
    assert reader.lineno_start == 1


def test_LiteralIncludeReader_missing_start_and_end(literal_inc_path: Path) -> None:
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


def test_LiteralIncludeReader_end_before(literal_inc_path: Path) -> None:
    options = {'end-before': 'nclud'}  # *nclud* matches first and third lines.
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '# Literally included file using Python highlighting\n\n'


def test_LiteralIncludeReader_prepend(literal_inc_path: Path) -> None:
    options = {'lines': '1', 'prepend': 'Hello', 'append': 'Sphinx'}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == (
        'Hello\n# Literally included file using Python highlighting\nSphinx\n'
    )


def test_LiteralIncludeReader_dedent(literal_inc_path: Path) -> None:
    # dedent: 2
    options = {'lines': '9-11', 'dedent': 2}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == '  def baz():\n      pass\n\n'

    # dedent: 4
    options = {'lines': '9-11', 'dedent': 4}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'def baz():\n    pass\n\n'

    # dedent: 6
    options = {'lines': '9-11', 'dedent': 6}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'f baz():\n  pass\n\n'

    # dedent: None
    options = {'lines': '9-11', 'dedent': None}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'def baz():\n    pass\n\n'


def test_LiteralIncludeReader_dedent_and_append_and_prepend(
    literal_inc_path: Path,
) -> None:
    # dedent: 2
    options = {
        'lines': '9-11',
        'dedent': 2,
        'prepend': 'class Foo:',
        'append': '# comment',
    }
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'class Foo:\n  def baz():\n      pass\n\n# comment\n'


def test_LiteralIncludeReader_tabwidth(testroot: Path) -> None:
    # tab-width: 4
    options = {'tab-width': 4, 'pyobject': 'Qux'}
    reader = LiteralIncludeReader(testroot / 'target.py', options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'class Qux:\n    def quux(self):\n        pass\n'

    # tab-width: 8
    options = {'tab-width': 8, 'pyobject': 'Qux'}
    reader = LiteralIncludeReader(testroot / 'target.py', options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'class Qux:\n        def quux(self):\n                pass\n'


def test_LiteralIncludeReader_tabwidth_dedent(testroot: Path) -> None:
    options = {'tab-width': 4, 'dedent': 4, 'pyobject': 'Qux.quux'}
    reader = LiteralIncludeReader(testroot / 'target.py', options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == 'def quux(self):\n    pass\n'


def test_LiteralIncludeReader_diff(testroot: Path, literal_inc_path: Path) -> None:
    literal_diff_path = testroot / 'literal-diff.inc'
    options = {'diff': literal_diff_path}
    reader = LiteralIncludeReader(literal_inc_path, options, DUMMY_CONFIG)
    content, _lines = reader.read()
    assert content == (
        f'--- {literal_diff_path}\n'
        f'+++ {literal_inc_path}\n'
        '@@ -6,8 +6,8 @@\n'
        '     pass\n'
        ' \n'
        ' class Bar:\n'
        '-    def baz(self):\n'
        '+    def baz():\n'
        '         pass\n'
        ' \n'
        '-# comment after Bar class\n'
        '+# comment after Bar class definition\n'
        ' def bar(): pass\n'
    )


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_code_block(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'index.rst'])
    et = etree_parse(app.outdir / 'index.xml')
    secs = et.findall('./section/section')
    code_block = secs[0].findall('literal_block')
    assert len(code_block) > 0
    actual = code_block[0].text
    expect = '    def ruby?\n        false\n    end'
    assert actual == expect


@pytest.mark.sphinx('html', testroot='directive-code')
def test_force_option(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'force.rst'])
    assert 'force.rst' not in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='directive-code')
def test_code_block_caption_html(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'caption.rst'])
    html = (app.outdir / 'caption.html').read_text(encoding='utf8')
    caption = (
        '<div class="code-block-caption">'
        '<span class="caption-number">Listing 1 </span>'
        '<span class="caption-text">caption <em>test</em> rb'
        '</span><a class="headerlink" href="#id1" '
        'title="Link to this code">\xb6</a></div>'
    )
    assert caption in html


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_code_block_caption_latex(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    latex = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')
    caption = '\\sphinxSetupCaptionForVerbatim{caption \\sphinxstyleemphasis{test} rb}'
    label = '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:id1}}}'
    link = (
        '\\hyperref[\\detokenize{caption:name-test-rb}]'
        '{Listing \\ref{\\detokenize{caption:name-test-rb}}}'
    )
    assert caption in latex
    assert label in latex
    assert link in latex


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_code_block_namedlink_latex(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    latex = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')
    label1 = (
        '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:name-test-rb}}}'
    )
    link1 = (
        '\\hyperref[\\detokenize{caption:name-test-rb}]'
        '{\\sphinxcrossref{\\DUrole{std}{\\DUrole{std-ref}{Ruby}}}}'
    )
    label2 = (
        '\\def\\sphinxLiteralBlockLabel'
        '{\\label{\\detokenize{namedblocks:some-ruby-code}}}'
    )
    link2 = (
        '\\hyperref[\\detokenize{namedblocks:some-ruby-code}]'
        '{\\sphinxcrossref{\\DUrole{std}{\\DUrole{std-ref}{the ruby code}}}}'
    )
    assert label1 in latex
    assert link1 in latex
    assert label2 in latex
    assert link2 in latex


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_code_block_emphasize_latex(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'emphasize.rst'])
    latex = (
        (app.outdir / 'projectnamenotset.tex')
        .read_text(encoding='utf8')
        .replace('\r\n', '\n')
    )
    includes = '\\fvset{hllines={, 6, 7, 16, 17, 18, 19, 29, 30, 31,}}%\n'
    assert includes in latex
    includes = '\\end{sphinxVerbatim}\n\\sphinxresetverbatimhllines\n'
    assert includes in latex


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literal_include(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'index.rst'])
    et = etree_parse(app.outdir / 'index.xml')
    secs = et.findall('./section/section')
    literal_include = secs[1].findall('literal_block')
    literal_src = (app.srcdir / 'literal.inc').read_text(encoding='utf8')
    assert len(literal_include) > 0
    actual = literal_include[0].text
    assert actual == literal_src


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literal_include_block_start_with_comment_or_brank(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'python.rst'])
    et = etree_parse(app.outdir / 'python.xml')
    secs = et.findall('./section/section')
    literal_include = secs[0].findall('literal_block')
    assert len(literal_include) > 0
    actual = literal_include[0].text
    expect = 'def block_start_with_comment():\n    # Comment\n    return 1\n'
    assert actual == expect

    actual = literal_include[1].text
    expect = 'def block_start_with_blank():\n\n    return 1\n'
    assert actual == expect


@pytest.mark.sphinx('html', testroot='directive-code')
def test_literal_include_linenos(app: SphinxTestApp) -> None:
    if tuple(map(int, pygments.__version__.split('.')[:2])) >= (2, 19):
        sp = '<span class="w"> </span>'
    else:
        sp = ' '

    app.build(filenames=[app.srcdir / 'linenos.rst'])
    html = (app.outdir / 'linenos.html').read_text(encoding='utf8')

    # :linenos:
    assert (
        '<span class="linenos"> 1</span><span class="c1">'
        '# Literally included file using Python highlighting</span>'
    ) in html

    # :lineno-start:
    assert (
        '<span class="linenos">200</span><span class="c1">'
        '# Literally included file using Python highlighting</span>'
    ) in html

    # :lines: 5-9
    assert (
        f'<span class="linenos">5</span><span class="k">class</span>{sp}'
        '<span class="nc">Foo</span><span class="p">:</span>'
    ) in html


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_literalinclude_file_whole_of_emptyline(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    latex = (
        (app.outdir / 'projectnamenotset.tex')
        .read_text(encoding='utf8')
        .replace('\r\n', '\n')
    )
    includes = (
        '\\begin{sphinxVerbatim}'
        '[commandchars=\\\\\\{\\},numbers=left,firstnumber=1,stepnumber=1]\n'
        '\n'
        '\n'
        '\n'
        '\\end{sphinxVerbatim}\n'
    )
    assert includes in latex


@pytest.mark.sphinx('html', testroot='directive-code')
def test_literalinclude_caption_html(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    html = (app.outdir / 'caption.html').read_text(encoding='utf8')
    caption = (
        '<div class="code-block-caption">'
        '<span class="caption-number">Listing 2 </span>'
        '<span class="caption-text">caption <strong>test</strong> py'
        '</span><a class="headerlink" href="#id2" '
        'title="Link to this code">\xb6</a></div>'
    )
    assert caption in html


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_literalinclude_caption_latex(app: SphinxTestApp) -> None:
    app.build(filenames=(Path('index'),))
    latex = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')
    caption = '\\sphinxSetupCaptionForVerbatim{caption \\sphinxstylestrong{test} py}'
    label = '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:id2}}}'
    link = (
        '\\hyperref[\\detokenize{caption:name-test-py}]'
        '{Listing \\ref{\\detokenize{caption:name-test-py}}}'
    )
    assert caption in latex
    assert label in latex
    assert link in latex


@pytest.mark.sphinx('latex', testroot='directive-code')
def test_literalinclude_namedlink_latex(app: SphinxTestApp) -> None:
    app.build(filenames=(Path('index'),))
    latex = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')
    label1 = (
        '\\def\\sphinxLiteralBlockLabel{\\label{\\detokenize{caption:name-test-py}}}'
    )
    link1 = (
        '\\hyperref[\\detokenize{caption:name-test-py}]'
        '{\\sphinxcrossref{\\DUrole{std}{\\DUrole{std-ref}{Python}}}}'
    )
    label2 = (
        '\\def\\sphinxLiteralBlockLabel'
        '{\\label{\\detokenize{namedblocks:some-python-code}}}'
    )
    link2 = (
        '\\hyperref[\\detokenize{namedblocks:some-python-code}]'
        '{\\sphinxcrossref{\\DUrole{std}{\\DUrole{std-ref}{the python code}}}}'
    )
    assert label1 in latex
    assert link1 in latex
    assert label2 in latex
    assert link2 in latex


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literalinclude_classes(app: SphinxTestApp) -> None:
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
def test_literalinclude_pydecorators(app: SphinxTestApp) -> None:
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
    expect = '@function_decorator\n@other_decorator()\ndef the_function():\n    pass\n'
    assert actual == expect


@pytest.mark.sphinx('dummy', testroot='directive-code')
def test_code_block_highlighted(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'highlight.rst'])
    doctree = app.env.get_doctree('highlight')
    codeblocks = list(doctree.findall(nodes.literal_block))

    assert codeblocks[0]['language'] == 'default'
    assert codeblocks[1]['language'] == 'python2'
    assert codeblocks[2]['language'] == 'python3'
    assert codeblocks[3]['language'] == 'python2'


@pytest.mark.sphinx('html', testroot='directive-code')
def test_linenothreshold(app: SphinxTestApp) -> None:
    if tuple(map(int, pygments.__version__.split('.')[:2])) >= (2, 19):
        sp = '<span class="w"> </span>'
    else:
        sp = ' '

    app.build(filenames=[app.srcdir / 'linenothreshold.rst'])
    html = (app.outdir / 'linenothreshold.html').read_text(encoding='utf8')

    # code-block using linenothreshold
    assert (
        f'<span class="linenos">1</span><span class="k">class</span>{sp}'
        '<span class="nc">Foo</span><span class="p">:</span>'
    ) in html

    # code-block not using linenothreshold (no line numbers)
    assert '<span></span><span class="c1"># comment</span>' in html

    # literal include using linenothreshold
    assert (
        '<span class="linenos"> 1</span><span class="c1">'
        '# Literally included file using Python highlighting</span>'
    ) in html

    # literal include not using linenothreshold (no line numbers)
    assert (
        '<span></span><span class="c1"># Very small literal include '
        '(linenothreshold check)</span>'
    ) in html


@pytest.mark.sphinx('dummy', testroot='directive-code')
def test_code_block_dedent(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'dedent.rst'])
    doctree = app.env.get_doctree('dedent')
    codeblocks = list(doctree.findall(nodes.literal_block))
    # Note: comparison string should not have newlines at the beginning or end
    text_0_indent = """First line
Second line
    Third line
Fourth line"""
    text_2_indent = """  First line
  Second line
      Third line
  Fourth line"""
    text_4_indent = """    First line
    Second line
        Third line
    Fourth line"""

    assert codeblocks[0].astext() == text_0_indent
    assert codeblocks[1].astext() == text_0_indent
    assert codeblocks[2].astext() == text_4_indent
    assert codeblocks[3].astext() == text_2_indent
    assert codeblocks[4].astext() == text_4_indent
    assert codeblocks[5].astext() == text_0_indent


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literal_include_negative_lines_build(app: SphinxTestApp) -> None:
    """Integration test: build a document with literalinclude + negative :lines: specs."""
    app.build(filenames=[app.srcdir / 'negative-lines.rst'])
    et = etree_parse(app.outdir / 'negative-lines.xml')
    blocks = et.findall('.//literal_block')
    assert len(blocks) == 4, f'Expected 4 literal blocks, got {len(blocks)}'

    # Block 0: :lines: -3--1 → last 3 lines (11-13)
    # literal.inc has 13 lines. Lines 11-13 are:
    #   \n# comment after Bar class definition\ndef bar(): pass\n
    assert blocks[0].text == (
        '\n'
        '# comment after Bar class definition\n'
        'def bar(): pass\n'
    )

    # Block 1: :lines: 5--1 → lines 5 to end
    # Lines 5-13: class Foo: ... def bar(): pass\n
    assert 'class Foo:' in blocks[1].text
    assert 'def bar(): pass' in blocks[1].text

    # Block 2: :lines: -1--1 → last line only
    assert blocks[2].text == 'def bar(): pass\n'

    # Block 3: :lines: -3- → same as -3--1 (half-open right with negative start)
    assert blocks[3].text == blocks[0].text


@pytest.mark.sphinx('html', testroot='directive-code')
def test_literalinclude_emphasize_lines_negative(app: SphinxTestApp) -> None:
    """Test emphasize-lines with negative indices in literalinclude."""
    # Create a test rst file with negative emphasize-lines
    rst_content = '''
Test Negative Emphasize Lines
=============================

.. literalinclude:: literal.inc
   :language: python
   :emphasize-lines: -3--1
   :linenos:
'''
    test_file = app.srcdir / 'test_emphasize_negative.rst'
    test_file.write_text(rst_content.strip(), encoding='utf8')
    app.build(filenames=[test_file])
    html = (app.outdir / 'test_emphasize_negative.html').read_text(encoding='utf8')

    # Last 3 lines should be highlighted (lines 11-13 in 13-line file)
    # Check for hl_lines in the output
    assert 'hllines=' in html or 'highlight' in html.lower()


@pytest.mark.sphinx('html', testroot='directive-code')
def test_code_block_emphasize_lines_negative(app: SphinxTestApp) -> None:
    """Test emphasize-lines with negative indices in code-block."""
    rst_content = '''
Test Code Block Negative Emphasize Lines
========================================

.. code-block:: python
   :emphasize-lines: -2--1

   def foo():
       print("line 1")
       print("line 2")
       print("line 3")
'''
    test_file = app.srcdir / 'test_code_emphasize_negative.rst'
    test_file.write_text(rst_content.strip(), encoding='utf8')
    app.build(filenames=[test_file])
    html = (app.outdir / 'test_code_emphasize_negative.html').read_text(encoding='utf8')

    # Last 2 lines should be highlighted
    assert 'hllines=' in html or 'highlight' in html.lower()


@pytest.mark.sphinx('xml', testroot='directive-code')
def test_literalinclude_negative_lines_edge_cases(app: SphinxTestApp) -> None:
    """Test edge cases for negative line numbers in literalinclude."""
    # Test single negative line via range
    rst_content = '''
Test Edge Cases
===============

.. literalinclude:: literal.inc
   :language: python
   :lines: -2--2
'''
    test_file = app.srcdir / 'test_edge_cases.rst'
    test_file.write_text(rst_content.strip(), encoding='utf8')
    app.build(filenames=[test_file])
    et = etree_parse(app.outdir / 'test_edge_cases.xml')
    blocks = et.findall('.//literal_block')
    assert len(blocks) == 1
    # -2--2 in 13 lines = line 12 (0-based: 11) = "# comment after Bar class definition"
    assert 'comment after Bar class definition' in blocks[0].text

    # Test full file via negative range
    rst_content2 = '''
Test Full File
==============

.. literalinclude:: literal.inc
   :language: python
   :lines: -13--1
'''
    test_file2 = app.srcdir / 'test_full_negative.rst'
    test_file2.write_text(rst_content2.strip(), encoding='utf8')
    app.build(filenames=[test_file2])
    et = etree_parse(app.outdir / 'test_full_negative.xml')
    blocks = et.findall('.//literal_block')
    assert len(blocks) == 1
    # Should include all 13 lines
    full_content = (app.srcdir / 'literal.inc').read_text(encoding='utf8')
    assert blocks[0].text == full_content

    # Test out of range negative index
    rst_content3 = '''
Test Out of Range
=================

.. literalinclude:: literal.inc
   :language: python
   :lines: -14--1
'''
    test_file3 = app.srcdir / 'test_outofrange.rst'
    test_file3.write_text(rst_content3.strip(), encoding='utf8')
    # Should warn but not crash
    app.build(filenames=[test_file3])
    assert 'negative index out of range' in app.warning.getvalue().lower()
