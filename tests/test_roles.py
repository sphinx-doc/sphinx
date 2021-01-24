"""
    test_roles
    ~~~~~~~~~~

    Test sphinx.roles

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest.mock import Mock

from docutils import nodes

from sphinx.roles import EmphasizedLiteral
from sphinx.testing.util import assert_node


def test_samp():
    emph_literal_role = EmphasizedLiteral()

    # normal case
    text = 'print 1+{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, ("print 1+",
                                         [nodes.emphasis, "variable"])])
    assert msg == []

    # two emphasis items
    text = 'print {1}+{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, ("print ",
                                         [nodes.emphasis, "1"],
                                         "+",
                                         [nodes.emphasis, "variable"])])
    assert msg == []

    # empty curly brace
    text = 'print 1+{}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, "print 1+{}"])
    assert msg == []

    # half-opened variable
    text = 'print 1+{variable'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, "print 1+{variable"])
    assert msg == []

    # nested
    text = 'print 1+{{variable}}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, ("print 1+",
                                         [nodes.emphasis, "{variable"],
                                         "}")])
    assert msg == []

    # emphasized item only
    text = '{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, nodes.emphasis, "variable"])
    assert msg == []

    # escaping
    text = r'print 1+\{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, "print 1+{variable}"])
    assert msg == []

    # escaping (2)
    text = r'print 1+\{{variable}\}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, ("print 1+{",
                                         [nodes.emphasis, "variable"],
                                         "}")])
    assert msg == []

    # escape a backslash
    text = r'print 1+\\{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, ("print 1+\\",
                                         [nodes.emphasis, "variable"])])
    assert msg == []
