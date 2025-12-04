"""Test sphinx.roles"""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from docutils import nodes

from sphinx.roles import EmphasizedLiteral, _format_rfc_target
from sphinx.testing.util import assert_node


def test_samp() -> None:
    emph_literal_role = EmphasizedLiteral()

    # normal case
    text = 'print 1+{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(
        ret[0],
        [
            nodes.literal,
            (
                'print 1+',
                [nodes.emphasis, 'variable'],
            ),
        ],
    )
    assert msg == []

    # two emphasis items
    text = 'print {1}+{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(
        ret[0],
        [
            nodes.literal,
            (
                'print ',
                [nodes.emphasis, '1'],
                '+',
                [nodes.emphasis, 'variable'],
            ),
        ],
    )
    assert msg == []

    # empty curly brace
    text = 'print 1+{}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, 'print 1+{}'])
    assert msg == []

    # half-opened variable
    text = 'print 1+{variable'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, 'print 1+{variable'])
    assert msg == []

    # nested
    text = 'print 1+{{variable}}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(
        ret[0],
        [
            nodes.literal,
            (
                'print 1+',
                [nodes.emphasis, '{variable'],
                '}',
            ),
        ],
    )
    assert msg == []

    # emphasized item only
    text = '{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, nodes.emphasis, 'variable'])
    assert msg == []

    # escaping
    text = r'print 1+\{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(ret[0], [nodes.literal, 'print 1+{variable}'])
    assert msg == []

    # escaping (2)
    text = r'print 1+\{{variable}\}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(
        ret[0],
        [
            nodes.literal,
            (
                'print 1+{',
                [nodes.emphasis, 'variable'],
                '}',
            ),
        ],
    )
    assert msg == []

    # escape a backslash
    text = r'print 1+\\{variable}'
    ret, msg = emph_literal_role('samp', text, text, 0, Mock())
    assert_node(
        ret[0],
        [
            nodes.literal,
            (
                'print 1+\\',
                [nodes.emphasis, 'variable'],
            ),
        ],
    )
    assert msg == []


@pytest.mark.parametrize(
    ('target', 'expected_output'),
    [
        ('123', 'RFC 123'),
        ('123#', 'RFC 123#'),
        ('123#id1', 'RFC 123#id1'),
        ('123#section', 'RFC 123 Section'),
        ('123#section-1', 'RFC 123 Section 1'),
        ('123#section-2.5.3', 'RFC 123 Section 2.5.3'),
        ('123#page-13', 'RFC 123 Page 13'),
        ('123#appendix-B', 'RFC 123 Appendix B'),
        # Section names are also present in some RFC anchors. Until we come up with a reliable way
        # to reconstruct the section names from the corresponding anchors with the correct
        # capitalization it's probably better to leave them alone.
        ('9076#name-risks-in-the-dns-data', 'RFC 9076#name-risks-in-the-dns-data'),
    ],
)
def test_format_rfc_target(target: str, expected_output: str) -> None:
    assert _format_rfc_target(target) == expected_output
