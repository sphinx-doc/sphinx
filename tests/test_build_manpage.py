"""Test the build process with manpage builder with the test root."""

import docutils
import pytest

from sphinx.builders.manpage import default_man_pages
from sphinx.config import Config


@pytest.mark.sphinx('man')
def test_all(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / 'sphinxtests.1').exists()

    content = (app.outdir / 'sphinxtests.1').read_text(encoding='utf8')
    assert r'\fBprint \fP\fIi\fP\fB\en\fP' in content
    assert r'\fBmanpage\en\fP' in content

    # heading (title + description)
    assert r'sphinxtests \- Sphinx <Tests> 0.6alpha1' in content

    # term of definition list including nodes.strong
    assert '\n.B term1\n' in content
    assert '\nterm2 (\\fBstronged partially\\fP)\n' in content

    # test samp with braces
    assert '\n\\fIvariable_only\\fP\n' in content
    assert '\n\\fIvariable\\fP\\fB and text\\fP\n' in content
    assert '\n\\fBShow \\fP\\fIvariable\\fP\\fB in the middle\\fP\n' in content

    assert 'Footnotes' not in content


@pytest.mark.sphinx('man', testroot='basic',
                    confoverrides={'man_pages': [('index', 'title', None, [], 1)]})
def test_man_pages_empty_description(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'title.1').read_text(encoding='utf8')
    assert r'title \-' not in content


@pytest.mark.sphinx('man', testroot='basic',
                    confoverrides={'man_make_section_directory': True})
def test_man_make_section_directory(app, status, warning):
    app.build()
    assert (app.outdir / 'man1' / 'python.1').exists()


@pytest.mark.sphinx('man', testroot='directive-code')
def test_captioned_code_block(app, status, warning):
    app.builder.build_all()
    content = (app.outdir / 'python.1').read_text(encoding='utf8')

    if docutils.__version_info__[:2] < (0, 21):
        expected = """\
.sp
caption \\fItest\\fP rb
.INDENT 0.0
.INDENT 3.5
.sp
.nf
.ft C
def ruby?
    false
end
.ft P
.fi
.UNINDENT
.UNINDENT
"""
    else:
        expected = """\
.sp
caption \\fItest\\fP rb
.INDENT 0.0
.INDENT 3.5
.sp
.EX
def ruby?
    false
end
.EE
.UNINDENT
.UNINDENT
"""

    assert expected in content


def test_default_man_pages():
    config = Config({'project': 'STASI™ Documentation',
                     'author': "Wolfgang Schäuble & G'Beckstein",
                     'release': '1.0'})
    expected = [('index', 'stasi', 'STASI™ Documentation 1.0',
                 ["Wolfgang Schäuble & G'Beckstein"], 1)]
    assert default_man_pages(config) == expected


@pytest.mark.sphinx('man', testroot='markup-rubric')
def test_rubric(app, status, warning):
    app.build()
    content = (app.outdir / 'python.1').read_text(encoding='utf8')
    assert 'This is a rubric\n' in content
