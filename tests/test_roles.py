"""Test sphinx.roles"""

from unittest.mock import Mock

from docutils import nodes
import pytest

from sphinx.roles import _format_rfc_target, EmphasizedLiteral
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


@pytest.mark.parametrize('target,expected_output', [
    ['123', 'RFC 123'],
    ['123#section-1', 'RFC 123 Section 1'],
    ['123#section-2.5.3', 'RFC 123 Section 2.5.3'],
    ['123#page-13', 'RFC 123 Page 13'],
    ['123#appendix-B', 'RFC 123 Appendix B'],
])
def test_format_rfc_target(target: str, expected_output: str) -> None:
    assert _format_rfc_target(target) == expected_output
