"""Public cleaning functions for :mod:`sphinx.testing.matcher`."""

from __future__ import annotations

__all__ = ()

import itertools
from functools import reduce
from typing import TYPE_CHECKING

from sphinx.testing.matcher import _engine, _util
from sphinx.testing.matcher.options import OptionsHolder
from sphinx.util.console import strip_escape_sequences

if TYPE_CHECKING:
    import re
    from collections.abc import Iterable

    from typing_extensions import Unpack

    from sphinx.testing.matcher.options import DeletePattern, Options, StripChars


def clean(text: str, /, **options: Unpack[Options]) -> Iterable[str]:
    """Clean a text, returning an iterable of lines.

    :param text: The text to clean.
    :param options: The cleaning options.
    :return: The list of cleaned lines.
    """
    config = OptionsHolder(**options)

    # clean the text as a string
    if not config.keep_ansi:
        text = strip_escape_sequences(text)
    text = strip_chars(text, config.strip)

    lines: Iterable[str] = text.splitlines(config.keep_break)
    lines = strip_lines(lines, config.stripline)

    keep_empty, compress, unique = config.keep_empty, config.compress, config.unique
    lines = filter_lines(lines, keep_empty=keep_empty, compress=compress, unique=unique)
    lines = prune_lines(lines, config.delete)

    if callable(ignore_predicate := config.ignore):
        lines = itertools.filterfalse(ignore_predicate, lines)

    return lines


def strip_chars(text: str, chars: StripChars = True, /) -> str:
    """Strip expected characters from *text*."""
    if isinstance(chars, bool):
        return text.strip() if chars else text
    return text.strip(chars)


def strip_lines(lines: Iterable[str], chars: StripChars = True, /) -> Iterable[str]:
    """Call :meth:`str.strip` to each line in *lines*."""
    if isinstance(chars, bool):
        return map(str.strip, lines) if chars else lines
    return (line.strip(chars) for line in lines)


def filter_lines(
    lines: Iterable[str],
    /,
    *,
    keep_empty: bool = True,
    compress: bool = False,
    unique: bool = False,
) -> Iterable[str]:
    """Filter the lines.

    :param lines: The lines to filter.
    :param keep_empty: If true, keep empty lines.
    :param unique: If true, remove duplicated lines.
    :param compress: If true, remove consecutive duplicated lines.
    :return: An iterable of filtered lines.

    Since removing empty lines first allows serial duplicates to be eliminated
    in the same iteration, duplicates elimination is performed *after* empty
    lines are removed. To change the behaviour, consider using::

        lines = filter_lines(lines, compress=True)
        lines = filter_lines(lines, empty=True)
    """
    if not keep_empty:
        lines = filter(None, lines)

    if unique:
        # 'compress' has no effect when 'unique' is set
        return _util.unique_everseen(lines)

    if compress:
        return _util.unique_justseen(lines)

    return lines


def prune_lines(
    lines: Iterable[str],
    patterns: DeletePattern,
    /,
    *,
    trace: list[list[tuple[str, list[str]]]] | None = None,
) -> Iterable[str]:
    r"""Remove substrings from a source satisfying some patterns.

    :param lines: The source to transform.
    :param patterns: One or more substring patterns to delete.
    :param trace: A buffer where intermediate results are stored.
    :return: An iterable of transformed lines.

    Usage::

        lines = prune_lines(['1111a', 'b1'], r'^\d+')
        assert list(lines) == ['a', 'b1']

    When specified, the *trace* contains the line's reduction chains, e.g., if
    the line is ``'ABC#123'`` amd ``patterns = (r'^[A-Z]', r'\d$')``, then the
    corresponding reduction chain is::

        [
            ('ABC#123', ['BC#123', 'BC#12']),
            ('BC#12', ['C#12', 'C#1']),
            ('C#1', ['#1', '#']),
        ]

    In the above example, the final value is given by ``'#'`` which can also
    be accessed by ``trace[i][-1][-1][-1]``.
    """
    patterns = _engine.to_line_patterns(patterns)
    compiled = _engine.compile(patterns, flavor='re')

    def prune_redux(line: str, pattern: re.Pattern[str]) -> str:
        return pattern.sub('', line)

    def prune_debug(line: str, accumulator: list[str]) -> str:
        values = itertools.accumulate(compiled, prune_redux, initial=line)
        accumulator.extend(itertools.islice(values, 1, None))  # skip initial value
        return accumulator[-1]  # a reduced value

    if trace is None:
        for line in lines:
            ret = reduce(prune_redux, compiled, line)
            while line != ret:
                line, ret = ret, reduce(prune_redux, compiled, ret)
            yield ret
    else:
        for line in lines:
            entry: list[tuple[str, list[str]]] = [(line, [])]
            ret = None
            ret = prune_debug(line, entry[-1][1])
            while line != ret:
                frame: tuple[str, list[str]] = (ret, [])
                line, ret = ret, prune_debug(ret, frame[1])
                if ret != line:
                    entry.append(frame)
            trace.append(entry)
            yield ret
