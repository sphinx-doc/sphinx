"""
    test_directive_patch
    ~~~~~~~~~~~~~~~~~~~

    Test the patched directives.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

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
