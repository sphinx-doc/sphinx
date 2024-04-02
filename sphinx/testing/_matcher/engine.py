from __future__ import annotations

__all__ = ()

import fnmatch
import re
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from typing import TypeVar

    from sphinx.testing._matcher.options import Flavor
    from sphinx.testing._matcher.util import LinePattern

    _LinePatternT = TypeVar('_LinePatternT', str, re.Pattern[str])


def _check_flavor(flavor: Flavor) -> None:
    allowed = ('none', 'fnmatch', 're')
    if flavor not in allowed:
        msg = f'unknown flavor: {flavor!r} (choose from {tuple(map(repr, allowed))})'
        raise ValueError(msg)


# fmt: off
@overload
def to_line_patterns(expect: str, *, optimized: bool = False) -> tuple[str]: ...  # NoQA: E704
@overload  # NoQA: E302
def to_line_patterns(  # NoQA: E704
    expect: re.Pattern[str], *, optimized: bool = False
) -> tuple[re.Pattern[str]]: ...
@overload  # NoQA: E302
def to_line_patterns(  # NoQA: E704
    expect: Iterable[LinePattern], *, optimized: bool = False
) -> tuple[LinePattern, ...]: ...
# fmt: on
def to_line_patterns(  # NoQA: E302
    expect: LinePattern | Iterable[LinePattern], *, optimized: bool = False
) -> Sequence[LinePattern]:
    """Get a read-only sequence of line-matching patterns.

    :param expect: One or more patterns a line should match.
    :param optimized: If true, patterns are sorted and duplicates are removed.
    :return: The possible line patterns.

    By convention,

        to_line_patterns("my pattern") == to_line_patterns(["my pattern"])
    """
    if isinstance(expect, (str, re.Pattern)):
        return (expect,)

    def key(x: str | re.Pattern[str]) -> str:
        return x if isinstance(x, str) else x.pattern

    if optimized:
        return tuple(sorted(set(expect), key=key))
    return tuple(expect)


# fmt: off
@overload
def to_block_pattern(expect: str) -> tuple[str, ...]: ...  # NoQA: E704
@overload
def to_block_pattern(expect: re.Pattern[str]) -> tuple[re.Pattern[str]]: ...  # NoQA: E704
@overload
def to_block_pattern(expect: Sequence[LinePattern]) -> Sequence[LinePattern]: ...  # NoQA: E704
# fmt: on
def to_block_pattern(expect: LinePattern | Iterable[LinePattern]) -> Sequence[LinePattern]:  # NoQA: E302
    """Get a read-only sequence for a s single block pattern.

    :param expect: A single string, a single pattern or one or more patterns.
    :return: The line patterns of the block.
    """
    if isinstance(expect, str):
        return tuple(expect.splitlines())
    if isinstance(expect, re.Pattern):
        return (expect,)
    return tuple(expect)


# fmt: off
@overload
def transform(fn: Callable[[str], str], x: str, /) -> str: ...  # NoQA: E704
@overload
def transform(fn: Callable[[str], str], x: re.Pattern[str], /) -> re.Pattern[str]: ...  # NoQA: E704
# fmt: on
def transform(fn: Callable[[str], str], x: LinePattern, /) -> LinePattern:  # NoQA: E302
    """Transform regular expressions, leaving compiled patterns untouched."""
    return fn(x) if isinstance(x, str) else x


def translate(patterns: Iterable[LinePattern], *, flavor: Flavor) -> Iterable[LinePattern]:
    r"""Translate regular expressions in *patterns* according to *flavor*.

    :param patterns: An iterable of patterns to translate if needed.
    :return: An iterable of :class:`re`-style patterns.

    Usage::

        patterns = list(translate(['a*', re.compile('b')], flavor='fnmatch'))
        patterns == ['(?:a.*)\\Z', re.compile('b')]
    """
    _check_flavor(flavor)

    if flavor == 'none':
        return (transform(re.escape, pattern) for pattern in patterns)
    if flavor == 'fnmatch':
        return (transform(fnmatch.translate, pattern) for pattern in patterns)

    return patterns


def compile(patterns: Iterable[LinePattern], *, flavor: Flavor) -> Sequence[re.Pattern[str]]:
    """Compile one or more patterns into :class:`~re.Pattern` objects."""
    patterns = translate(patterns, flavor=flavor)
    # mypy does not like map + re.compile() although it is correct but
    # this is likely due to https://github.com/python/mypy/issues/11880
    return [re.compile(pattern) for pattern in patterns]
