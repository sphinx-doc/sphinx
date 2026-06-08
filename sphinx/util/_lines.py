from __future__ import annotations


def _resolve(num: int, total: int, spec: str) -> int:
    """Resolve a potentially negative line number to a 1-based positive index.

    ``-1`` → ``total``, ``-2`` → ``total - 1``, etc.
    """
    if num >= 0:
        return num
    resolved = total + num + 1
    if resolved < 1:
        msg = f'negative index out of range in line number spec: {spec!r}'
        raise ValueError(msg)
    return resolved


def _parse_part(part: str, total: int) -> list[int]:
    """Parse a single comma-separated part of a line number spec and
    return 0-based line indices.
    """
    part = part.strip()
    if not part:
        msg = f'invalid line number spec: {part!r}'
        raise ValueError(msg)

    # Special case: the original Sphinx syntax "-N" (single dash + number)
    # means "lines 1 through N" (half-open left).  We preserve this for
    # backward compatibility.  The string must be "-" followed by a positive
    # integer (e.g. "-5").  Bare "-" or "--1" don't match this pattern.
    if part.startswith('-') and part.count('-') == 1 and part[1:].isdigit():
        # Classic half-open left: "-5" → lines 1 to 5
        end = int(part[1:])
        if end <= 0:
            msg = f'invalid line number spec: {part!r}'
            raise ValueError(msg)
        # Guard against unreasonably large indices that would cause MemoryError
        max_allowed = max(total * 2, 10000)
        if end > max_allowed:
            msg = f'line number spec index too large: {part!r}'
            raise ValueError(msg)
        # Allow out-of-bounds indices; caller (lines_filter) handles them
        return list(range(end))

    # Find the range separator dash.  A dash is a separator if:
    # - It is not at position 0 (that's a negative-sign for start).
    # - It is not preceded by another dash (that's a negative-sign for end).
    #
    # Walk character by character to find the first dash that is a range
    # separator, handling negative numbers properly.
    sep_idx = None
    i = 0
    while i < len(part):
        c = part[i]
        if c == '-':
            if i == 0:
                # Minus sign for a negative start number; skip it and its digits
                i += 1
                while i < len(part) and part[i].isdigit():
                    i += 1
                continue
            if i > 0 and part[i - 1] == '-':
                # This dash follows another dash: it's the minus sign of
                # a negative end number.  We must have already set sep_idx
                # to the dash *before* this one.
                i += 1
                while i < len(part) and part[i].isdigit():
                    i += 1
                continue
            if sep_idx is not None:
                # We already found a separator dash; a second one is invalid.
                msg = f'invalid line number spec: {part!r}'
                raise ValueError(msg)
            # This is the range separator dash.
            sep_idx = i
            i += 1
            # Skip over negative-end minus sign if present
            if i < len(part) and part[i] == '-':
                i += 1
            while i < len(part) and part[i].isdigit():
                i += 1
            continue
        if c.isdigit():
            i += 1
            continue
        msg = f'invalid line number spec: {part!r}'
        raise ValueError(msg)

    if sep_idx is None:
        # Single number (no range): e.g. "3"
        try:
            start = int(part)
        except ValueError as err:
            msg = f'invalid line number spec: {part!r}'
            raise ValueError(msg) from err
        if start == 0:
            msg = 'line number 0 is not valid (line numbering starts at 1)'
            raise ValueError(msg)
        if start < 0:
            start = _resolve(start, total, part)
        # Guard against unreasonably large indices
        max_allowed = max(total * 2, 10000)
        if start - 1 > max_allowed:
            msg = f'line number spec index too large: {part!r}'
            raise ValueError(msg)
        return [start - 1]

    # Range form
    start_str = part[:sep_idx]
    rest = part[sep_idx + 1:]  # after the separator dash

    try:
        start = int(start_str)
    except ValueError as err:
        msg = f'invalid line number spec: {part!r}'
        raise ValueError(msg) from err
    start = _resolve(start, total, part)

    if not rest:
        # Half-open right: "3-" or "-3-"
        end = max(start, total)
    else:
        try:
            end = int(rest)
        except ValueError as err:
            msg = f'invalid line number spec: {part!r}'
            raise ValueError(msg) from err
        end = _resolve(end, total, part)

    if start == 0 or end == 0:
        msg = 'line number 0 is not valid (line numbering starts at 1)'
        raise ValueError(msg)
    if start > end:
        msg = f'invalid line number spec: {part!r}'
        raise ValueError(msg)
    # Guard against unreasonably large indices that would cause MemoryError
    # when creating the range. The caller (lines_filter) handles out-of-bounds
    # indices, but we should not attempt to allocate massive lists.
    max_allowed = max(total * 2, 10000)
    if start - 1 > max_allowed or end > max_allowed:
        msg = f'line number spec indices too large: {part!r}'
        raise ValueError(msg)
    return list(range(start - 1, end))


def parse_line_num_spec(spec: str, total: int) -> list[int]:
    """Parse a line number spec (such as ``"1,2,4-6"``) and return a list of
    wanted line numbers as 0-based indices.

    Negative indices are supported in ranges: ``-1`` refers to the last line,
    ``-2`` to the second-to-last, and so on — mirroring Python's sequence
    indexing.  Examples (given ``total=10``):

    * ``"5--1"``   → lines 5 through 10  (positive start, negative end)
    * ``"-3--1"``  → lines 8 through 10  (negative start and end)
    * ``"-3-"``    → lines 8 through 10  (negative start, half-open right)
    * ``"-8-5"``   → lines 3 through 5   (negative start, positive end)

    A bare negative value like ``"-5"`` retains its existing Sphinx meaning
    (lines 1 through 5) for backward compatibility.  Use ``"-5--1"`` to
    select the last five lines.

    Line ``0`` is never valid; numbering starts at ``1``.
    """
    items: list[int] = []
    parts = spec.split(',')
    for part in parts:
        items.extend(_parse_part(part, total))
    return items
