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

    from sphinx.testing.matcher._util import Patterns
    from sphinx.testing.matcher.options import Options, PrunePattern, StripChars

    Trace = list[list[tuple[str, list[str]]]]


def clean(text: str, /, **options: Unpack[Options]) -> Iterable[str]:
    """Clean a text, returning an iterable of lines.

    :param text: The text to clean.
    :return: An iterable of cleaned lines.

    See :class:`~.options.Options` for the meaning of each supported option.
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
    """Return a copy of *text* with leading and trailing characters removed.

    See :attr:`~.options.Options.strip` for the meaning of *chars*.
    """
    if isinstance(chars, bool):
        return text.strip() if chars else text
    return text.strip(chars)


def strip_lines(lines: Iterable[str], chars: StripChars = True, /) -> Iterable[str]:
    """Same as :func:`strip_chars` but applied to each line in *lines*.

    See :attr:`~.options.Options.stripline` for the meaning of *chars*.
    """
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
    :param keep_empty: If true, keep empty lines in the output.
    :param compress: If true, remove consecutive duplicated lines.
    :param unique: If true, remove duplicated lines.
    :return: An iterable of filtered lines.

    Since removing empty lines first allows serial duplicates to be eliminated
    in the same iteration, duplicates elimination is performed *after* empty
    lines are removed. Consider comparing::

        >>> lines = ['a', '', 'a', '', 'a']
        >>> list(filter_lines(lines, keep_empty=False, compress=True))
        ['a']

    together with::

        >>> lines = ['a', '', 'a', '', 'a']
        >>> filtered = filter_lines(lines, compress=True)
        >>> filtered = filter_lines(filtered, keep_empty=False)
        >>> list(filtered)
        ['a', 'a', 'a']
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
    lines: Iterable[str], patterns: PrunePattern, /, *, trace: Trace | None = None
) -> Iterable[str]:
    r"""Eliminate substrings in each line.

    :param lines: The source to transform.
    :param patterns: One or more substring patterns to delete.
    :param trace: A buffer where intermediate results are stored.
    :return: An iterable of transformed lines.

    Example::

        >>> lines = prune_lines(['1111a', 'b1'], r'^\d+')
        >>> list(lines)
        ['a', 'b1']

    When specified, the *trace* contains the line's reduction chains, e.g.::

        >>> trace = []
        >>> list(prune_lines(['ABC#123'], [r'^[A-Z]', r'\d$'], trace=trace))
        ['#']
        >>> trace  # doctest: +NORMALIZE_WHITESPACE
        [[('ABC#123', ['BC#123', 'BC#12']),
          ('BC#12', ['C#12', 'C#1']),
          ('C#1', ['#1', '#'])]]
    """
    patterns = _engine.to_line_patterns(patterns)
    compiled = _engine.compile(patterns, flavor='re')
    if trace is None:
        return _prune(lines, compiled)
    return _prune_debug(lines, compiled, trace)


def _prune_pattern(line: str, pattern: re.Pattern[str]) -> str:
    return pattern.sub('', line)


def _prune(lines: Iterable[str], compiled: Patterns) -> Iterable[str]:
    def apply(line: str) -> str:
        return reduce(_prune_pattern, compiled, line)

    def prune(line: str) -> str:
        text = apply(line)
        while text != line:
            line, text = text, apply(text)
        return text

    return map(prune, lines)


def _prune_debug(lines: Iterable[str], compiled: Patterns, trace: Trace) -> Iterable[str]:
    def apply(line: str) -> tuple[str, list[str]]:
        values = itertools.accumulate(compiled, _prune_pattern, initial=line)
        states = list(itertools.islice(values, 1, None))  # skip initial value
        return states[-1], states

    def prune(line: str) -> str:
        text, states = apply(line)
        # first reduction is always logged
        trace_item: list[tuple[str, list[str]]] = [(line, states)]

        while text != line:
            line, (text, states) = text, apply(text)
            trace_item.append((line, states))

        if len(trace_item) >= 2:
            # the while-loop was executed at least once and
            # the last appended item represents the identity
            trace_item.pop()

        trace.append(trace_item)
        return text

    return map(prune, lines)
