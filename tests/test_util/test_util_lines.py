from __future__ import annotations

import pytest

from sphinx.util._lines import parse_line_num_spec


def test_parse_line_num_spec() -> None:
    assert parse_line_num_spec('1,2,3', 10) == [0, 1, 2]
    assert parse_line_num_spec('4, 5, 6', 10) == [3, 4, 5]
    assert parse_line_num_spec('-4', 10) == [0, 1, 2, 3]
    assert parse_line_num_spec('7-9', 10) == [6, 7, 8]
    assert parse_line_num_spec('7-', 10) == [6, 7, 8, 9]
    assert parse_line_num_spec('1,7-', 10) == [0, 6, 7, 8, 9]
    assert parse_line_num_spec('7-7', 10) == [6]
    assert parse_line_num_spec('11-', 10) == [10]
    with pytest.raises(ValueError, match="invalid line number spec: '1-2-3'"):
        parse_line_num_spec('1-2-3', 10)
    with pytest.raises(ValueError, match="invalid line number spec: 'abc-def'"):
        parse_line_num_spec('abc-def', 10)
    with pytest.raises(ValueError, match="invalid line number spec: '-'"):
        parse_line_num_spec('-', 10)
    with pytest.raises(ValueError, match="invalid line number spec: '3-1'"):
        parse_line_num_spec('3-1', 10)


def test_parse_line_num_spec_negative_indices() -> None:
    # Positive start, negative end
    assert parse_line_num_spec('5--1', 10) == [4, 5, 6, 7, 8, 9]
    assert parse_line_num_spec('1--1', 10) == list(range(10))
    assert parse_line_num_spec('1--1', 1) == [0]

    # Negative start and end
    assert parse_line_num_spec('-3--1', 10) == [7, 8, 9]
    assert parse_line_num_spec('-1--1', 10) == [9]  # last line only
    assert parse_line_num_spec('-10--1', 10) == list(range(10))

    # Negative start, half-open right
    assert parse_line_num_spec('-3-', 10) == [7, 8, 9]
    assert parse_line_num_spec('-1-', 10) == [9]

    # Negative start, positive end
    assert parse_line_num_spec('-8-5', 10) == [2, 3, 4]

    # Mixed positive and negative
    assert parse_line_num_spec('1,3,-2--1', 10) == [0, 2, 8, 9]

    # Backward compat: bare "-N" still means lines 1-N
    assert parse_line_num_spec('-5', 10) == [0, 1, 2, 3, 4]

    # Negative index out of range
    with pytest.raises(ValueError, match='negative index out of range'):
        parse_line_num_spec('-15--1', 10)

    # Reversed range after resolving negatives (-3 in 10 = 8, end=5 → 8 > 5)
    with pytest.raises(ValueError, match='invalid line number spec'):
        parse_line_num_spec('-3-5', 10)


def test_parse_line_num_spec_negative_edge_cases() -> None:
    # Bare "-N" is ALWAYS legacy half-open left (lines 1-N)
    # This is critical for backward compatibility.
    assert parse_line_num_spec('-2', 10) == [0, 1]  # legacy: lines 1-2
    assert parse_line_num_spec('-5', 10) == [0, 1, 2, 3, 4]  # legacy: lines 1-5
    assert parse_line_num_spec('-10', 10) == list(range(10))  # legacy: lines 1-10

    # To select a single negative line, use a range: "-2--2"
    assert parse_line_num_spec('-2--2', 10) == [8]

    # Mixed: positive single, negative range
    assert parse_line_num_spec('1,-2--1', 10) == [0, 8, 9]

    # Small file: 1 line, -1--1 resolves to line 1
    assert parse_line_num_spec('-1--1', 1) == [0]

    # Small file: 2 lines, -2--1 resolves to lines 1-2
    assert parse_line_num_spec('-2--1', 2) == [0, 1]

    # Negative start that resolves to line 1
    assert parse_line_num_spec('-10--1', 10) == list(range(10))

    # Out of range: -11 as a single spec means legacy "1 to 11" but
    # 11 > 10, so the resolved range includes an out-of-bounds index.
    # The bare "-11" still parses as lines 1-11, returning [0..10]
    # (out-of-bounds indices are handled by lines_filter in code.py).
    assert parse_line_num_spec('-11', 10) == list(range(11))

    # Out of range in explicit negative range: -1--11
    with pytest.raises(ValueError, match='negative index out of range'):
        parse_line_num_spec('1--11', 10)

    # Out of range: -12--1 in a 10-line file
    with pytest.raises(ValueError, match='negative index out of range'):
        parse_line_num_spec('-12--1', 10)

    # Zero is never valid
    with pytest.raises(ValueError, match='line number 0 is not valid'):
        parse_line_num_spec('0', 10)

    # Range with both start and end resolving to same line
    assert parse_line_num_spec('-5--5', 10) == [5]

    # Whitespace tolerance (existing behavior)
    assert parse_line_num_spec('1, -1--1', 10) == [0, 9]

    # Multiple negative ranges
    assert parse_line_num_spec('-5--4,-2--1', 10) == [5, 6, 8, 9]

    # Negative end with positive start, comma-separated
    assert parse_line_num_spec('1-3,-2--1', 10) == [0, 1, 2, 8, 9]
