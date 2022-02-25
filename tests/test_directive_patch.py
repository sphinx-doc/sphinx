"""
    test_directive_patch
    ~~~~~~~~~~~~~~~~~~~

    Test the patched directives.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
from docutils import nodes

from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


def test_code_directive(app):
    # normal case
    text = ('.. code::\n'
            '\n'
            '   print("hello world")\n')

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block, 'print("hello world")'])
    assert_node(doctree[0], language="default", highlight_args={})

    # with language
    text = ('.. code:: python\n'
            '\n'
            '   print("hello world")\n')

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block, 'print("hello world")'])
    assert_node(doctree[0], language="python", highlight_args={})

    # :number-lines: option
    text = ('.. code:: python\n'
            '   :number-lines:\n'
            '\n'
            '   print("hello world")\n')

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block, 'print("hello world")'])
    assert_node(doctree[0], language="python", linenos=True, highlight_args={})

    # :number-lines: option
    text = ('.. code:: python\n'
            '   :number-lines: 5\n'
            '\n'
            '   print("hello world")\n')

    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.literal_block, 'print("hello world")'])
    assert_node(doctree[0], language="python", linenos=True, highlight_args={'linenostart': 5})


@pytest.mark.sphinx(testroot='directive-csv-table')
def test_csv_table_directive(app):
    # relative path from current document
    text = ('.. csv-table::\n'
            '   :file: example.csv\n')
    doctree = restructuredtext.parse(app, text, docname="subdir/index")
    assert_node(doctree,
                ([nodes.table, nodes.tgroup, (nodes.colspec,
                                              nodes.colspec,
                                              nodes.colspec,
                                              [nodes.tbody, nodes.row])],))
    assert_node(doctree[0][0][3][0],
                ([nodes.entry, nodes.paragraph, "FOO"],
                 [nodes.entry, nodes.paragraph, "BAR"],
                 [nodes.entry, nodes.paragraph, "BAZ"]))

    # absolute path from source directory
    text = ('.. csv-table::\n'
            '   :file: /example.csv\n')
    doctree = restructuredtext.parse(app, text, docname="subdir/index")
    assert_node(doctree,
                ([nodes.table, nodes.tgroup, (nodes.colspec,
                                              nodes.colspec,
                                              nodes.colspec,
                                              [nodes.tbody, nodes.row])],))
    assert_node(doctree[0][0][3][0],
                ([nodes.entry, nodes.paragraph, "foo"],
                 [nodes.entry, nodes.paragraph, "bar"],
                 [nodes.entry, nodes.paragraph, "baz"]))


def test_math_directive(app):
    # normal case
    text = '.. math:: E = mc^2'
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, nodes.math_block, 'E = mc^2\n\n'])

    # :name: option
    text = ('.. math:: E = mc^2\n'
            '   :name: eq1\n')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, (nodes.target,
                                           [nodes.math_block, "E = mc^2\n\n"])])
    assert_node(doctree[1], nodes.math_block, docname='index', label="eq1", number=1)

    # :label: option
    text = ('.. math:: E = mc^2\n'
            '   :label: eq2\n')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, (nodes.target,
                                           [nodes.math_block, 'E = mc^2\n\n'])])
    assert_node(doctree[1], nodes.math_block, docname='index', label="eq2", number=2)

    # :label: option without value
    text = ('.. math:: E = mc^2\n'
            '   :label:\n')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, [nodes.document, (nodes.target,
                                           [nodes.math_block, 'E = mc^2\n\n'])])
    assert_node(doctree[1], nodes.math_block, ids=['equation-index-0'],
                docname='index', label="index:0", number=3)
