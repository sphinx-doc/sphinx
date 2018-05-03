# -*- coding: utf-8 -*-
"""
    test_roles
    ~~~~~~~~~~

    Test sphinx.roles

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from mock import Mock

from sphinx.roles import emph_literal_role
from sphinx.testing.util import assert_node


def test_samp():
    # normal case
    text = 'print 1+{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret, ([nodes.literal, ("print 1+",
                                       [nodes.emphasis, "variable"])],))
    assert msg == []

    # two emphasis items
    text = 'print {1}+{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret, ([nodes.literal, ("print ",
                                       [nodes.emphasis, "1"],
                                       "+",
                                       [nodes.emphasis, "variable"])],))
    assert msg == []

    # empty curly brace
    text = 'print 1+{}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret, ([nodes.literal, "print 1+{}"],))
    assert msg == []

    # half-opened variable
    text = 'print 1+{variable'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret, ([nodes.literal, "print 1+{variable"],))
    assert msg == []

    # nested
    text = 'print 1+{{variable}}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret, ([nodes.literal, ("print 1+",
                                       [nodes.emphasis, "{variable"],
                                       "}")],))
    assert msg == []

    # emphasized item only
    text = '{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret, ([nodes.literal, nodes.emphasis, "variable"],))
    assert msg == []

    # escaping
    text = r'print 1+\{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret, ([nodes.literal, "print 1+{variable}"],))
    assert msg == []

    # escaping (2)
    text = r'print 1+\{{variable}\}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret, ([nodes.literal, ("print 1+{",
                                       [nodes.emphasis, "variable"],
                                       "}")],))
    assert msg == []

    # escape a backslash
    text = r'print 1+\\{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret, ([nodes.literal, ("print 1+\\",
                                       [nodes.emphasis, "variable"])],))
    assert msg == []
