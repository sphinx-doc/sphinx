from __future__ import annotations

__all__ = ()

import fnmatch
import re
from collections.abc import Sequence, Set
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from typing import TypeVar

    from sphinx.testing._matcher.options import Flavor
    from sphinx.testing._matcher.util import LinePattern

    _LinePatternT = TypeVar('_LinePatternT', str, re.Pattern[str])


def _check_flavor(flavor: Flavor) -> None:
    allowed: Sequence[Flavor] = ('none', 'fnmatch', 're')
    if flavor not in allowed:
        msg = f'unknown flavor: {flavor!r} (choose from: {allowed})'
        raise ValueError(msg)


def _sort_pattern(s: str | re.Pattern[str]) -> tuple[str, int, int]:
    if isinstance(s, str):
        return (s, -1, -1)
    return (s.pattern, s.flags, s.groups)


@overload
def to_line_patterns(expect: str) -> tuple[str]: ...  # NoQA: E704
@overload
def to_line_patterns(expect: re.Pattern[str]) -> tuple[re.Pattern[str]]: ...  # NoQA: E704
@overload
def to_line_patterns(expect: Iterable[LinePattern], /) -> tuple[LinePattern, ...]: ...  # NoQA: E704
def to_line_patterns(expect: LinePattern | Iterable[LinePattern]) -> Sequence[LinePattern]:  # NoqA: E302
    """Get a read-only sequence of line-matching patterns.

    :param expect: One or more patterns a line should match.
    :return: The possible line patterns.

    By convention,::

        to_line_patterns("my pattern") == to_line_patterns(["my pattern"])

    .. note::

       The order in which the patterns are given is retained, except for
       iterables that do not have an ordering (e.g., :class:`set`). For
       such collections, patterns are ordered accroding to their string
       representation, :class:`flags <re.RegexFlag>` and capture groups.
    """
    if isinstance(expect, (str, re.Pattern)):
        return (expect,)

    if isinstance(expect, Set):
        return tuple(sorted(expect, key=_sort_pattern))

    return tuple(expect)


@overload
def to_block_pattern(expect: str) -> tuple[str, ...]: ...  # NoQA: E704
@overload
def to_block_pattern(expect: re.Pattern[str]) -> tuple[re.Pattern[str]]: ...  # NoQA: E704
@overload
def to_block_pattern(expect: Sequence[LinePattern]) -> Sequence[LinePattern]: ...  # NoQA: E704
def to_block_pattern(expect: LinePattern | Sequence[LinePattern]) -> Sequence[LinePattern]:  # NoQA: E302
    r"""Get a read-only sequence for a s single block pattern.

    :param expect: A string, :class:`~re.Pattern` or a sequence thereof.
    :return: The line patterns of the block.
    :raise TypeError: The type of *expect* is not supported.

    When *expect* is a single string, it is split into lines to produce
    the corresponding block pattern, e.g.::

        to_block_pattern('line1\nline2') == ('line1', 'line2')
    """
    if isinstance(expect, str):
        return tuple(expect.splitlines())
    if isinstance(expect, re.Pattern):
        return (expect,)
    if not isinstance(expect, Sequence):
        msg = f'expecting a sequence of patterns, got: {expect!r}'
        raise TypeError(msg)
    return tuple(expect)


@overload
def transform(fn: Callable[[str], str], x: str, /) -> str: ...  # NoQA: E704
@overload
def transform(fn: Callable[[str], str], x: re.Pattern[str], /) -> re.Pattern[str]: ...  # NoQA: E704
def transform(fn: Callable[[str], str], x: LinePattern, /) -> LinePattern:  # NoQA: E302
    """Transform regular expressions, leaving compiled patterns untouched."""
    return fn(x) if isinstance(x, str) else x


def string_expression(line: str, /) -> str:
    """A regular expression matching exactly *line*."""
    return rf'^(?s:{re.escape(line)})\Z'


def translate(
    patterns: Iterable[LinePattern],
    *,
    flavor: Flavor,
    default_translate: Callable[[str], str] = string_expression,
    fnmatch_translate: Callable[[str], str] = fnmatch.translate,
) -> Iterable[LinePattern]:
    r"""Translate regular expressions in *patterns* according to *flavor*.

    :param patterns: An iterable of patterns to translate if needed.
    :param flavor: The regex pattern to use.
    :param default_translate: Translation function for ``'none'`` flavor.
    :param fnmatch_translate: Translation function for ``'fnmatch'`` flavor.
    :return: An iterable of :class:`re`-style patterns.
    """
    _check_flavor(flavor)

    if flavor == 'none':
        return (transform(default_translate, pattern) for pattern in patterns)
    if flavor == 'fnmatch':
        return (transform(fnmatch_translate, pattern) for pattern in patterns)

    return patterns


def compile(
    patterns: Iterable[LinePattern],
    *,
    flavor: Flavor,
    default_translate: Callable[[str], str] = string_expression,
    fnmatch_translate: Callable[[str], str] = fnmatch.translate,
) -> Sequence[re.Pattern[str]]:
    """Compile one or more patterns into :class:`~re.Pattern` objects."""
    patterns = translate(
        patterns,
        flavor=flavor,
        default_translate=default_translate,
        fnmatch_translate=fnmatch_translate,
    )
    # mypy does not like map + re.compile() although it is correct but
    # this is likely due to https://github.com/python/mypy/issues/11880
    return tuple(re.compile(pattern) for pattern in patterns)
