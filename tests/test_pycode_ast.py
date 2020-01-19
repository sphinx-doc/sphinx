"""
    test_pycode_ast
    ~~~~~~~~~~~~~~~

    Test pycode.ast

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from sphinx.pycode import ast


@pytest.mark.parametrize('source,expected', [
    ("os.path", "os.path"),                     # Attribute
    ("b'bytes'", "b'bytes'"),                   # Bytes
    ("object()", "object()"),                   # Call
    ("1234", "1234"),                           # Constant
    ("{'key1': 'value1', 'key2': 'value2'}",
     "{'key1': 'value1', 'key2': 'value2'}"),   # Dict
    ("...", "..."),                             # Ellipsis
    ("Tuple[int, int]", "Tuple[int, int]"),     # Index, Subscript
    ("lambda x, y: x + y",
     "<function <lambda>>"),                    # Lambda
    ("[1, 2, 3]", "[1, 2, 3]"),                 # List
    ("sys", "sys"),                             # Name, NameConstant
    ("1234", "1234"),                           # Num
    ("{1, 2, 3}", "{1, 2, 3}"),                 # Set
    ("'str'", "'str'"),                         # Str
    ("(1, 2, 3)", "1, 2, 3"),                   # Tuple
])
def test_unparse(source, expected):
    module = ast.parse(source)
    assert ast.unparse(module.body[0].value) == expected


def test_unparse_None():
    assert ast.unparse(None) is None
