from __future__ import annotations

__all__ = ()

import fnmatch
import itertools
import re
from functools import reduce
from itertools import filterfalse
from typing import TYPE_CHECKING

from sphinx.testing._matcher import engine, util
from sphinx.util.console import strip_colors, strip_control_sequences

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import TypeVar

    from typing_extensions import Unpack

    from sphinx.testing._matcher.options import (
        DeletePattern,
        Flavor,
        LinePredicate,
        Options,
        StripChars,
    )

    _StrIterableT = TypeVar('_StrIterableT', bound=Iterable[str])


def clean_text(text: str, /, **options: Unpack[Options]) -> Iterable[str]:
    """Clean a text, returning an iterable of lines."""
    ctrl = options.get('ctrl', True)
    color = options.get('color', True)
    text = strip_ansi(text, ctrl=ctrl, color=color)

    strip = options.get('strip', False)
    text = strip_chars(text, strip)

    keepends = options.get('keepends', False)
    lines = text.splitlines(keepends)

    return clean_lines(lines, **options)


def clean_lines(lines: Iterable[str], /, **options: Unpack[Options]) -> Iterable[str]:
    """Clean an iterable of lines."""
    stripline = options.get('stripline', False)
    lines = strip_lines(lines, stripline)
    # Removing empty lines first ensures that serial duplicates can
    # be eliminated in one cycle. Inverting the order of operations
    # is not possible since empty lines may 'hide' duplicated lines.
    empty = options.get('empty', True)
    compress = options.get('compress', False)
    unique = options.get('unique', False)
    lines = filter_lines(lines, empty=empty, compress=compress, unique=unique)

    delete = options.get('delete', ())
    flavor = options.get('flavor', 'none')
    lines = prune(lines, delete, flavor=flavor)

    ignore = options.get('ignore', None)
    lines = ignore_lines(lines, ignore)

    return lines


def strip_ansi(text: str, /, ctrl: bool = False, color: bool = False) -> str:
    """Strip ANSI escape sequences.

    :param text: The text to clean.
    :param ctrl: If true, remove non-color ANSI escape sequences.
    :param color: If true, remove color ANSI escape sequences.
    :return: The cleaned text.
    """
    # non-color control sequences must be stripped before colors
    text = text if ctrl else strip_control_sequences(text)
    text = text if color else strip_colors(text)
    return text


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
    empty: bool = False,
    compress: bool = False,
    unique: bool = False,
) -> Iterable[str]:
    """Filter the lines.

    :param lines: The lines to filter.
    :param empty: If true, remove empty lines.
    :param unique: If true, remove duplicated lines.
    :param compress: If true, remove consecutive duplicated lines.
    :return: An iterable of filtered lines.

    Since removing empty lines first allows serial duplicates to be eliminated
    in the same iteration, duplicates elimination is performed *after* empty
    lines are removed. To change the behaviour, consider using::

        lines = filterlines(lines, compress=True)
        lines = filterlines(lines, empty=True)
    """
    if not empty:
        lines = filter(None, lines)

    if unique:
        # 'compress' has no effect when 'unique' is set
        return util.unique_everseen(lines)

    if compress:
        return util.unique_justseen(lines)

    return lines


def ignore_lines(lines: Iterable[str], predicate: LinePredicate | None, /) -> Iterable[str]:
    """Ignore lines satisfying the *predicate*.

    :param lines: The lines to filter.
    :param predicate: An optional predicate.
    :return: An iterable of filtered lines.
    """
    return filterfalse(predicate, lines) if callable(predicate) else lines


def prune(
    lines: Iterable[str],
    delete: DeletePattern,
    /,
    flavor: Flavor = 'none',
    *,
    trace: list[Sequence[tuple[str, Sequence[str]]]] | None = None,
) -> Iterable[str]:
    r"""Remove substrings from a source satisfying some patterns.

    :param lines: The source to transform.
    :param delete: One or more prefixes to remove or substitution patterns.
    :param flavor: Indicate the flavor of prefix regular expressions.
    :param trace: A buffer where intermediate results are stored.
    :return: An iterable of transformed lines.

    Usage::

        lines = prune(['1111a', 'b'], r'\d+', flavor='re')
        assert list(lines) == ['a', 'b']

        lines = prune(['a123b', 'c123d'], re.compile(r'\d+'))
        assert list(lines) == ['ab', 'cd']

    For debugging purposes, an empty list *trace* can be given
    When specified, *trace* is incrementally constructed as follows::

        for i, line in enumerate(lines):
            entry, res = [(line, frame := [])], line
            for j, pattern in enumerate(patterns):
                res = patterns.sub('', res)
                frame.append(res)

            while res != line:
                entry.append((res, frame := []))
                for j, pattern in enumerate(patterns):
                    res = patterns.sub('', res)
                    frame.append(res)

            trace.append(entry)
            yield res
    """
    delete_patterns = engine.to_line_patterns(delete)
    # Since fnmatch-style patterns do not support a meta-character for
    # matching at the start of the string, we first translate patterns
    # and then add an explicit '^' character in the regular expression.
    patterns = engine.translate(
        delete_patterns,
        flavor=flavor,
        default_translate=re.escape,
        fnmatch_translate=lambda prefix: fnmatch.translate(prefix).rstrip(r'\Z$'),
    )
    # and now we add the '^' meta-character to ensure that we only match
    # at the beginning of the string and not in the middle of the string
    patterns = (engine.transform('^'.__add__, pattern) for pattern in patterns)
    compiled = [re.compile(pattern) for pattern in patterns]

    def prune_redux(line: str, pattern: re.Pattern[str]) -> str:
        return pattern.sub('', line)

    def prune_debug(line: str, frame: list[str]) -> str:
        results = itertools.accumulate(compiled, prune_redux, initial=line)
        frame.extend(itertools.islice(results, 1, None))  # skip the first element
        assert frame
        return frame[-1]

    if trace is None:
        for line in lines:
            ret = reduce(prune_redux, compiled, line)
            while line != ret:
                line, ret = ret, reduce(prune_redux, compiled, ret)
            yield ret
    else:
        for line in lines:
            entry: list[tuple[str, list[str]]] = [(line, [])]
            ret = prune_debug(line, entry[-1][1])
            while line != ret:
                entry.append((ret, []))
                line, ret = ret, prune_debug(ret, entry[-1][1])
            trace.append(entry)
            yield ret
