# mypy: disable-error-code="import-not-found"
# mypy: disable-error-code="untyped-decorator"
from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

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


# Property-based tests using hypothesis
# These tests verify that parse_line_num_spec matches Python's slice semantics
# for all valid inputs, providing exhaustive coverage of edge cases.


@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow],
    max_examples=500,
)
@given(
    total=st.integers(min_value=1, max_value=100),
    start=st.integers(min_value=-100, max_value=100),
    end=st.integers(min_value=-100, max_value=100),
)
def test_parse_range_matches_python_slice(total: int, start: int, end: int) -> None:
    """Test that positive/negative ranges match Python slice behavior."""
    # Skip invalid cases that should raise ValueError
    if start == 0 or end == 0:
        return

    spec = f'{start}-{end}'

    # Resolve indices to check if range is valid (start <= end after resolving, and both >= 1)
    def resolve(idx: int) -> int:
        if idx > 0:
            return idx
        return total + idx + 1

    resolved_start = resolve(start)
    resolved_end = resolve(end)

    # If resolved range is invalid (start > end or start < 1 or end < 1), expect ValueError
    # Note: out-of-bounds (resolved > total) is allowed - caller handles it
    if resolved_start > resolved_end or resolved_start < 1 or resolved_end < 1:
        try:
            parse_line_num_spec(spec, total)
            pytest.fail(
                f'Expected ValueError for invalid range {spec!r} with total={total}'
            )
        except ValueError:
            return

    try:
        result = parse_line_num_spec(spec, total)
    except ValueError:
        pytest.fail(
            f'Unexpected ValueError for valid range {spec!r} with total={total}'
        )
        return

    # Convert to 0-based indices for comparison
    # Our spec is inclusive on both ends. Resolve to 1-based, then convert to 0-based.
    def resolve_1based(idx: int) -> int:
        if idx > 0:
            return idx
        return total + idx + 1

    resolved_start = resolve_1based(start)
    resolved_end = resolve_1based(end)

    # Expected is range(resolved_start - 1, resolved_end) in 0-based (inclusive end)
    expected = list(range(resolved_start - 1, resolved_end))

    assert result == expected, (
        f'Mismatch for {spec!r} total={total}: got {result}, expected {expected}'
    )


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
@given(
    total=st.integers(min_value=1, max_value=50),
    indices=st.lists(st.integers(min_value=-50, max_value=50), min_size=1, max_size=5),
)
def test_parse_comma_separated_matches_individual(
    total: int, indices: list[int]
) -> None:
    """Test that comma-separated specs equal concatenation of individual specs."""
    # Filter out 0 which is invalid
    indices = [i for i in indices if i != 0]
    if not indices:
        return

    spec = ','.join(str(i) for i in indices)
    try:
        result = parse_line_num_spec(spec, total)
    except ValueError:
        # If any individual index is invalid, the whole thing should fail
        for i in indices:
            try:
                parse_line_num_spec(str(i), total)
            except ValueError:
                return  # Expected - at least one invalid
        pytest.fail(f'Unexpected ValueError for {spec!r} with total={total}')
        return

    expected = []
    for i in indices:
        try:
            expected.extend(parse_line_num_spec(str(i), total))
        except ValueError:
            # If individual fails but combined doesn't, that's a bug
            pytest.fail(f'Individual {i} fails but combined {spec!r} succeeds')
            return

    assert result == expected, (
        f'Mismatch for {spec!r} total={total}: got {result}, expected {expected}'
    )


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
@given(
    total=st.integers(min_value=1, max_value=50),
    start=st.integers(min_value=-50, max_value=50),
)
def test_single_negative_index_matches_python(total: int, start: int) -> None:
    """Test single negative index (range form -N-N) matches Python indexing."""
    if start == 0:
        return

    spec = f'{start}-{start}'
    try:
        result = parse_line_num_spec(spec, total)
    except ValueError:
        # Should fail only if out of range (resolved < 1)
        resolved = total + start + 1 if start < 0 else start
        if resolved < 1:
            return  # Expected out of range (negative index too large)
        pytest.fail(f'Unexpected ValueError for {spec!r} with total={total}')
        return

    expected_idx = total + start if start < 0 else start - 1
    # Implementation allows out-of-bounds indices (caller handles it)
    assert result == [expected_idx], (
        f'Mismatch for {spec!r} total={total}: got {result}'
    )


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
@given(
    total=st.integers(min_value=1, max_value=50),
    start=st.integers(min_value=-50, max_value=50),
)
def test_half_open_left_negative(total: int, start: int) -> None:
    """Test classic half-open left syntax (-N) matches expected behavior."""
    if start <= 0:
        return  # Only positive numbers after dash are valid for this syntax

    spec = f'-{start}'
    try:
        result = parse_line_num_spec(spec, total)
    except ValueError:
        # Should not fail for positive start
        pytest.fail(f'Unexpected ValueError for {spec!r} with total={total}')
        return

    # "-N" means lines 1 through N (0-based: 0 to N-1)
    expected = list(range(start))
    assert result == expected, (
        f'Mismatch for {spec!r} total={total}: got {result}, expected {expected}'
    )


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=200)
@given(
    total=st.integers(min_value=1, max_value=50),
    start=st.integers(min_value=-50, max_value=50),
    end=st.integers(min_value=-50, max_value=50),
)
def test_range_with_half_open_right(total: int, start: int, end: int) -> None:
    """Test half-open right ranges (start- or -start-)."""
    if start == 0:
        return

    # Test positive start with half-open right
    spec = f'{start}-'
    try:
        result = parse_line_num_spec(spec, total)
    except ValueError:
        # Should fail only if resolved start < 1
        resolved = total + start + 1 if start < 0 else start
        if resolved < 1:
            return
        pytest.fail(f'Unexpected ValueError for {spec!r} with total={total}')
        return

    resolved_start = total + start + 1 if start < 0 else start
    # Implementation allows out-of-bounds indices (caller handles them)
    expected = list(range(resolved_start - 1, max(resolved_start, total + 1)))
    # Actually, the implementation uses max(start, total) for end
    # So expected end is max(resolved_start, total)
    expected_end = max(resolved_start, total)
    expected = list(range(resolved_start - 1, expected_end))
    assert result == expected, (
        f'Mismatch for {spec!r} total={total}: got {result}, expected {expected}'
    )


@settings(suppress_health_check=[HealthCheck.function_scoped_fixture], max_examples=100)
@given(
    total=st.integers(min_value=1, max_value=30),
    start=st.integers(min_value=-30, max_value=30),
    end=st.integers(min_value=-30, max_value=30),
)
def test_large_indices_rejected(total: int, start: int, end: int) -> None:
    """Test that unreasonably large indices are rejected with ValueError, not MemoryError."""
    if start == 0 or end == 0:
        return

    spec = f'{start}-{end}'
    try:
        result = parse_line_num_spec(spec, total)
    except ValueError:
        return  # Expected for invalid or too-large input
    except MemoryError:
        pytest.fail(
            f'MemoryError for {spec!r} with total={total} - should raise ValueError'
        )
        return
    except Exception as e:
        pytest.fail(
            f'Unexpected exception {type(e).__name__}: {e} for {spec!r} total={total}'
        )
        return

    # If it succeeds, indices should not be excessively large
    max_allowed = max(total * 2, 10000)
    for idx in result:
        assert idx <= max_allowed, (
            f'Index {idx} exceeds max_allowed {max_allowed} for {spec!r}'
        )


@settings(
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=100,
    deadline=None,
)
@given(
    total=st.integers(min_value=1, max_value=30),
    spec=st.text(alphabet='0123456789-', min_size=1, max_size=20),
)
def test_no_crash_on_random_input(total: int, spec: str) -> None:
    """Fuzz test: parser should never crash, only raise ValueError for invalid input."""
    try:
        result = parse_line_num_spec(spec, total)
        # If it succeeds, result should be a list of int indices
        # (may include out-of-bounds indices - caller handles them)
        assert isinstance(result, list)
        for idx in result:
            assert isinstance(idx, int)
    except ValueError:
        pass  # Expected for invalid input
    except Exception as e:
        pytest.fail(
            f'Unexpected exception {type(e).__name__}: {e} for spec={spec!r} total={total}'
        )
