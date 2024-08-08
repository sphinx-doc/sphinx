import os

import docutils
import pytest
from docutils import frontend, nodes
from docutils.io import StringInput

from sphinx import addnodes, parsers
from sphinx.io import SphinxStandaloneReader
from sphinx.util.console import strip_colors

docutils_version = pytest.mark.skipif(
    docutils.__version_info__ < (0, 19), reason="at least docutils 0.19 required"
)


@pytest.fixture()
def document(app):
    settings = frontend.get_default_settings(parsers.RSTParser)
    settings.env = app.builder.env
    reader = SphinxStandaloneReader()
    reader.setup(app)
    reader.source = StringInput(source_path='dummy/document.rst')
    reader.settings = settings
    document = reader.new_document()
    return document


@pytest.fixture()
def parser(app):
    parser = parsers.RSTParser()
    parser.set_application(app)
    return parser


@docutils_version()
@pytest.mark.parametrize(('rst', 'expected'), [
    (
        # pep role
        ':pep:`8`',
        [addnodes.index, nodes.target, nodes.reference]
    ),
    (
        # rfc role
        ':rfc:`2324`',
        [addnodes.index, nodes.target, nodes.reference]
    ),
    (
        # correct interpretation of code with whitespace
        '``code   sample``',
        [nodes.literal]
    ),
    (
        # no ampersands in guilabel
        ':guilabel:`Foo`',
        [nodes.inline]
    ),
    (
        # kbd role
        ':kbd:`space`',
        [nodes.literal]
    ),
    (
        # description list: simple
        'term\n    description',
        [nodes.Text]
    ),
    (
        # description list: with classifiers
        'term : class1 : class2\n    description',
        [nodes.Text]
    ),
    (
        # glossary (description list): multiple terms
        '.. glossary::\n\n   term1\n   term2\n       description',
        [nodes.Text]
    ),
    (
        # basic inline markup
        '**Strong** text and *emphasis*',
        [nodes.strong, nodes.Text, nodes.emphasis]
    ),
    (
        # literal block
        'see this code block::\n\n   hello world!',
        [nodes.Text]
    ),
    (
        # missing literal block
        'see this code block::',
        [nodes.Text]
    ),
    (
        # section title
        'This is a title\n================\n',
        [nodes.Text]
    ),
    (
        # footnote reference
        'Reference a footnote [1]_',
        [nodes.Text, nodes.footnote_reference]
    ),
    (
        # substitution reference
        'here is a |substituted| text',
        [nodes.Text, nodes.substitution_reference, nodes.Text]
    ),
])
def test_inline_no_error(rst, expected, parser, document):
    parser.parse_inline(rst, document, 1)
    assert len(document.children) == 1
    paragraph = document.children[0]
    assert paragraph.__class__ == nodes.paragraph
    assert len(paragraph.children) == len(expected)
    for i, child in enumerate(paragraph.children):
        assert child.__class__ == expected[i]


@docutils_version()
@pytest.mark.parametrize(('rst', 'expected'), [
    (
        # invalid unfinished literal
        '``code sample',
        'WARNING: Inline literal start-string without end-string.'
    ),
])
def test_inline_errors(rst, expected, parser, document, warning):
    lineno = 5
    expected = f'dummy/document.rst:{lineno}: {expected}'
    parser.parse_inline(rst, document, lineno)
    assert len(document.children) > 1
    paragraph = document.children[0]
    messages = document.children[1:]
    assert paragraph.__class__ == nodes.paragraph
    for message in messages:
        assert message.__class__ == nodes.system_message
    warnings = getwarning(warning)
    assert expected in warnings


def getwarning(warnings):
    return strip_colors(warnings.getvalue().replace(os.sep, '/'))
