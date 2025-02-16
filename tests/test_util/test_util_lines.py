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
