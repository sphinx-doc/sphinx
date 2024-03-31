from __future__ import annotations

__all__ = ()

from functools import reduce
from itertools import filterfalse
from typing import TYPE_CHECKING

from sphinx.testing._matcher import engine, util
from sphinx.testing._matcher.options import get_option
from sphinx.util.console import strip_colors, strip_control_sequences

if TYPE_CHECKING:
    import re
    from collections.abc import Iterable

    from typing_extensions import Unpack

    from sphinx.testing._matcher.options import (
        DeletePattern,
        Flavor,
        LinePredicate,
        Options,
        StripChars,
    )


def clean_text(text: str, /, **options: Unpack[Options]) -> Iterable[str]:
    """Clean a text."""
    ctrl = get_option(options, 'ctrl')
    color = get_option(options, 'color')
    text = strip_ansi(text, ctrl=ctrl, color=color)

    text = strip_chars(text, get_option(options, 'strip'))
    lines = splitlines(text, get_option(options, 'keepends'))
    return clean_lines(lines, **options)


def clean_lines(lines: Iterable[str], /, **options: Unpack[Options]) -> Iterable[str]:
    """Clean a list of lines."""
    lines = strip_lines(lines, get_option(options, 'stripline'))
    # Removing empty lines first ensures that serial duplicates can
    # be eliminated in one cycle. Inverting the order of operations
    # is not possible since empty lines may 'hide' duplicated lines.
    empty = get_option(options, 'empty')
    compress = get_option(options, 'compress')
    unique = get_option(options, 'unique')
    lines = filterlines(lines, empty=empty, compress=compress, unique=unique)

    delete = get_option(options, 'delete')
    flavor = get_option(options, 'flavor')
    lines = prune(lines, delete, flavor=flavor)

    return ignorelines(lines, get_option(options, 'ignore'))


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

    if isinstance(chars, str) or chars is None:
        return text.strip(chars)

    msg = 'expecting a boolean, a string or None for %r, got: %r' % ('strip', chars)
    raise ValueError(msg)


def strip_lines(lines: Iterable[str], chars: StripChars = True, /) -> Iterable[str]:
    """Call :meth:`str.strip` to each line in *lines*."""
    if isinstance(chars, bool):
        return map(str.strip, lines) if chars else lines

    if isinstance(chars, str) or chars is None:
        return (line.strip(chars) for line in lines)

    msg = 'expecting a boolean, a string or None for %r, got: %r' % ('stripline', chars)
    raise ValueError(msg)


def splitlines(text: str, /, keepends: bool = False) -> Iterable[str]:
    """Split *text* into lines."""
    return text.splitlines(keepends=keepends)


def filterlines(
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

    By convention, duplicates elimination is performed *after* empty lines
    are removed. To reverse the behaviour, consider using::

        lines = filterlines(lines, compress=True)
        lines = filterlines(lines, empty=True)
    """
    # Removing empty lines first ensures that serial duplicates can
    # be eliminated in one cycle. Inverting the order of operations
    # is not possible since empty lines may 'hide' duplicated lines.
    if not empty:
        lines = filter(None, lines)

    if unique:
        # 'compress' has no effect when 'unique' is set
        return util.unique_everseen(lines)

    if compress:
        return util.unique_justseen(lines)

    return lines


def ignorelines(lines: Iterable[str], predicate: LinePredicate | None, /) -> Iterable[str]:
    """Ignore lines satisfying the *predicate*.

    :param lines: The lines to filter.
    :param predicate: An optional predicate.
    :return: An iterable of filtered lines.
    """
    return filterfalse(predicate, lines) if callable(predicate) else lines


def prune(
    lines: Iterable[str], delete: DeletePattern, /, flavor: Flavor = 'none'
) -> Iterable[str]:
    r"""Remove substrings from *lines* satisfying some patterns.

    :param lines: The lines to transform.
    :param delete: One or more prefixes to remove or substitution patterns.
    :param flavor: Indicate the flavor of prefix regular expressions.
    :return: An iterable of transformed lines.

    Usage::

        lines = prune(['1111a', 'b'], r'\d+', flavor='re')
        assert list(lines) == ['a', 'b']

        lines = prune(['a123b', 'c123d'], re.compile(r'\d+'))
        assert list(lines) == ['ab', 'cd']
    """
    delete_patterns = engine.to_line_patterns(delete)
    patterns = engine.translate(delete_patterns, flavor=flavor)
    # ensure that we are using the beginning of the string (this must
    # be done *after* the regular expression translation, since fnmatch
    # patterns do not support 'start of the string' syntax)
    patterns = (engine.transform(lambda p: rf'^{p}', p) for p in patterns)
    compiled = engine.compile(patterns, flavor='re')

    def sub(line: str, pattern: re.Pattern[str]) -> str:
        return pattern.sub('', line)

    for line in lines:
        ret = reduce(sub, compiled, line)
        while line != ret:
            line, ret = ret, reduce(sub, compiled, ret)
        yield ret
