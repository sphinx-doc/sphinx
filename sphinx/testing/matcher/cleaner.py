"""Public cleaning functions for :mod:`sphinx.testing.matcher`."""

from __future__ import annotations

__all__ = ()

from functools import reduce
from itertools import accumulate, islice
from typing import TYPE_CHECKING

from sphinx.testing.matcher import _cleaner, _engine
from sphinx.testing.matcher.options import OptionsHolder
from sphinx.util.console import strip_escape_sequences

if TYPE_CHECKING:
    from collections.abc import Iterable
    from re import Pattern

    from typing_extensions import TypeAlias, Unpack

    from sphinx.testing.matcher._util import Patterns
    from sphinx.testing.matcher.options import Options, PrunePattern, StripChars

    TraceInfo: TypeAlias = list[list[tuple[str, list[str]]]]


def clean(text: str, /, **options: Unpack[Options]) -> Iterable[str]:
    """Clean a text, returning an iterable of lines.

    :param text: The text to clean.
    :return: An iterable of cleaned lines.

    See :class:`~.options.Options` for the meaning of each supported option.
    """
    args = OptionsHolder(**options)

    # clean the text as a string
    if not args.keep_ansi:
        text = strip_escape_sequences(text)
    text = strip_chars(text, args.strip)
    # obtain the lines
    lines: Iterable[str] = text.splitlines(args.keep_break)
    # process the lines according to the operation codes sequence$
    handlers = _cleaner.make_handlers(args)
    for opcode in _cleaner.get_active_opcodes(args):
        if (handler := handlers.get(opcode)) is None:
            raise ValueError('unknown operation code: %r' % opcode)
        lines = handler(lines)
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

    See :attr:`~.options.Options.strip_line` for the meaning of *chars*.
    """
    if isinstance(chars, bool):
        return map(str.strip, lines) if chars else lines
    return (line.strip(chars) for line in lines)


def prune_lines(
    lines: Iterable[str], patterns: PrunePattern, /, *, trace: TraceInfo | None = None
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


def _prune_pattern(line: str, pattern: Pattern[str]) -> str:
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


def _prune_debug(lines: Iterable[str], compiled: Patterns, trace: TraceInfo) -> Iterable[str]:
    def apply(line: str) -> tuple[str, list[str]]:
        values = accumulate(compiled, _prune_pattern, initial=line)
        states = list(islice(values, 1, None))  # skip initial value
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
