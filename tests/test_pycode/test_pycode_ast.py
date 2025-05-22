"""Test pycode.ast"""

from __future__ import annotations

import ast

import pytest

from sphinx.pycode.ast import unparse as ast_unparse


@pytest.mark.parametrize(
    ('source', 'expected'),
    [
        ('a + b', 'a + b'),                        # Add
        ('a and b', 'a and b'),                    # And
        ('os.path', 'os.path'),                    # Attribute
        ('1 * 2', '1 * 2'),                        # BinOp
        ('a & b', 'a & b'),                        # BitAnd
        ('a | b', 'a | b'),                        # BitOr
        ('a ^ b', 'a ^ b'),                        # BitXor
        ('a and b and c', 'a and b and c'),        # BoolOp
        ("b'bytes'", "b'bytes'"),                  # Bytes
        ('object()', 'object()'),                  # Call
        ('1234', '1234'),                          # Constant, Num
        ("{'key1': 'value1', 'key2': 'value2'}",
         "{'key1': 'value1', 'key2': 'value2'}"),  # Dict
        ('a / b', 'a / b'),                        # Div
        ('...', '...'),                            # Ellipsis
        ('a // b', 'a // b'),                      # FloorDiv
        ('Tuple[int, int]', 'Tuple[int, int]'),    # Index, Subscript
        ('~1', '~1'),                              # Invert
        ('lambda x, y: x + y',
         'lambda x, y: ...'),                      # Lambda
        ('[1, 2, 3]', '[1, 2, 3]'),                # List
        ('a << b', 'a << b'),                      # LShift
        ('a @ b', 'a @ b'),                        # MatMult
        ('a % b', 'a % b'),                        # Mod
        ('a * b', 'a * b'),                        # Mult
        ('sys', 'sys'),                            # Name, NameConstant
        ('not a', 'not a'),                        # Not
        ('a or b', 'a or b'),                      # Or
        ('a**b', 'a**b'),                          # Pow
        ('a >> b', 'a >> b'),                      # RShift
        ('{1, 2, 3}', '{1, 2, 3}'),                # Set
        ('a - b', 'a - b'),                        # Sub
        ("'str'", "'str'"),                        # Str
        ('+a', '+a'),                              # UAdd
        ('-1', '-1'),                              # UnaryOp
        ('-a', '-a'),                              # USub
        ('(1, 2, 3)', '(1, 2, 3)'),                # Tuple
        ('()', '()'),                              # Tuple (empty)
        ('(1,)', '(1,)'),                          # Tuple (single item)
        ('lambda x=0, /, y=1, *args, z, **kwargs: x + y + z',
         'lambda x=0, /, y=1, *args, z, **kwargs: ...'),  # posonlyargs
        ('0x1234', '0x1234'),                      # Constant
        ('1_000_000', '1_000_000'),                # Constant
        ('Tuple[:,:]', 'Tuple[:, :]'),             # Index, Subscript, 2x Slice
        ('Tuple[1:2]', 'Tuple[1:2]'),              # Index, Subscript, Slice(no-step)
        ('Tuple[1:2:3]', 'Tuple[1:2:3]'),          # Index, Subscript, Slice
        ('x[:, np.newaxis, :, :]',
         'x[:, np.newaxis, :, :]'),                # Index, Subscript, numpy extended syntax
        ('y[:, 1:3][np.array([0, 2, 4]), :]',
         'y[:, 1:3][np.array([0, 2, 4]), :]'),     # Index, 2x Subscript, numpy extended syntax
        ('*tuple[str, int]', '*tuple[str, int]'),  # Starred
    ],
)  # fmt: skip
def test_unparse(source: str, expected: str) -> None:
    expr = ast.parse(source).body[0]
    assert isinstance(expr, ast.Expr)
    assert ast_unparse(expr.value, source) == expected


def test_unparse_None() -> None:
    assert ast_unparse(None) is None
