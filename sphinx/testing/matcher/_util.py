"""Private utility functions for :mod:`sphinx.testing.matcher`.

All objects provided by this module are considered an implementation detail.
"""

from __future__ import annotations

__all__ = ()

import itertools
import re
import textwrap
from collections import deque
from collections.abc import Callable, Sequence
from operator import itemgetter
from typing import TYPE_CHECKING, Union, overload

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping
    from typing import Any, TypeVar

    from typing_extensions import Never, TypeAlias

    from sphinx.testing.matcher.buffer import Region

    _T = TypeVar('_T')

PatternLike: TypeAlias = Union[str, re.Pattern[str]]
"""A regular expression (compiled or not)."""
LinePattern: TypeAlias = Union[str, re.Pattern[str]]
"""A regular expression (compiled or not) for an entire line."""
LinePredicate: TypeAlias = Callable[[str], object]
"""A predicate called on an entire line."""
BlockPattern: TypeAlias = Sequence[LinePattern]
"""A sequence of regular expressions (compiled or not) for a block.

For instance, ``['a', re.compile('b*')]`` matches blocks
with the line ``'a'`` followed by a line matching ``'b*'``.
"""

Patterns: TypeAlias = tuple[re.Pattern[str], ...]
"""Sequence of compiled patterns to use."""


def consume(iterator: Iterator[object], /, n: int | None = None) -> None:
    """Advance the iterator *n*-steps ahead, or entirely if *n* is ``None``.

    Taken from `itertools recipes`__.

    __ https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    # use the C API to efficiently consume iterators
    if n is None:
        deque(iterator, maxlen=0)
    else:
        next(itertools.islice(iterator, n, n), None)


def unique_justseen(iterable: Iterable[_T], /) -> Iterator[_T]:
    """Yield elements in order, ignoring serial duplicates.

    Taken from `itertools recipes`__.

    __ https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    return map(next, map(itemgetter(1), itertools.groupby(iterable)))


def unique_everseen(iterable: Iterable[_T], /) -> Iterator[_T]:
    """Yield elements in order, ignoring duplicates.

    Taken from `itertools recipes`__.

    __ https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    seen: set[_T] = set()
    mark, pred = seen.add, seen.__contains__
    for element in itertools.filterfalse(pred, iterable):
        mark(element)
        yield element


def strict_windowed(iterable: Iterable[_T], n: int, /) -> Iterator[Sequence[_T]]:
    """Return a sliding window of width *n* over the given iterable.

    When *n* is *0*, the iterator does not yield anything.

    Adapted from `itertools recipes`__ for the case *n = 0*.

    __ https://docs.python.org/3/library/itertools.html#itertools-recipes
    """
    if n == 0:
        return

    iterator = iter(iterable)
    window = deque(itertools.islice(iterator, n), maxlen=n)
    if len(window) == n:
        yield window
    for group in iterator:
        window.append(group)
        yield window


def plural_form(noun: str, n: int, /) -> str:
    """Append ``'s'`` to *noun* if *n* is more than *1*."""
    return noun + 's' if n > 1 else noun


def omit_message(n: int, /) -> str:
    """The message to indicate that *n* lines where omitted."""
    noun = plural_form('line', n)
    return f'... (omitted {n} {noun}) ...'


def omit_line(n: int, /) -> list[str]:
    """Wrap :func:`omit_message` in a list, if any.

    If no lines are omitted, this returns the empty list. This is typically
    useful when used in combination to ``lines.extend(omit_line(n))``.
    """
    return [omit_message(n)] if n else []


def make_prefix(indent: int, /, *, highlight: bool = False) -> str:
    """Create the prefix used for indentation or highlighting."""
    prefix = ' ' * indent
    return f'>{prefix[1:]}' if highlight else prefix


@overload
def indent_source(  # NoQA: E704
    text: str, /, *, sep: Never = ..., indent: int = ..., highlight: bool = ...
) -> str: ...
@overload  # NoQA: E302
def indent_source(  # NoQA: E704
    lines: Iterable[str], /, *, sep: str = ..., indent: int = ..., highlight: bool = ...
) -> str: ...
def indent_source(  # NoQA: E302
    src: Iterable[str], /, *, sep: str = '\n', indent: int = 4, highlight: bool = False
) -> str:
    """Indent a string or an iterable of lines, returning a single string.

    :param indent: The number of indentation spaces.
    :param highlight: Indicate whether the prefix is a highlighter.
    :return: An indented line, possibly highlighted.
    """
    if isinstance(src, str):
        prefix = make_prefix(indent, highlight=highlight)
        return textwrap.indent(src, prefix)
    return sep.join(indent_lines(src, indent=indent, highlight=highlight))


def indent_lines(
    lines: Iterable[str], /, *, indent: int = 4, highlight: bool = False
) -> list[str]:
    """Return a list of lines prefixed by an indentation string.

    :param lines: The lines to indent.
    :param indent: The number of indentation spaces.
    :param highlight: Indicate whether the prefix is a highlighter.
    :return: A list of lines, possibly highlighted.
    """
    prefix = make_prefix(indent, highlight=highlight)
    return [prefix + line for line in lines]


def get_context_lines(
    source: Sequence[str], region: Region[Any], /, context: int, *, indent: int = 4
) -> list[str]:
    """Get some context lines around *block* and highlight the *region*.

    :param source: The source containing the *block*.
    :param region: A region to highlight (a line or a block).
    :param context: The number of lines to display around the block.
    :param indent: The number of indentation spaces.
    :return: A list of formatted lines.
    """
    assert region <= source, 'the region must be contained in the source'

    logs: list[str] = []
    writelines = logs.extend
    has_context = int(context > 0)
    before, after = region.context(context, limit := len(source))
    writelines(omit_line(has_context * before.start))
    writelines(indent_lines(source[before], indent=indent, highlight=False))
    # use region.span to ensure that single lines are wrapped in lists
    writelines(indent_lines(source[region.span], indent=indent, highlight=True))
    writelines(indent_lines(source[after], indent=indent, highlight=False))
    writelines(omit_line(has_context * (limit - after.stop)))

    return logs


def _highlight(
    source: Iterable[str], sections: Mapping[int, int], *, prefix: str, highlight_prefix: str
) -> Iterator[str]:
    iterator = enumerate(source)
    for index, line in iterator:
        if count := sections.get(index, None):
            yield highlight_prefix + line  # the first line of the block
            # yield the remaining lines of the block
            tail = map(itemgetter(1), itertools.islice(iterator, count - 1))
            yield from map(highlight_prefix.__add__, tail)
        else:
            yield prefix + line


def highlight(
    source: Iterable[str],
    sections: Mapping[int, int] | None = None,
    /,
    *,
    indent: int = 4,
    keepends: bool = False,
) -> str:
    """Highlight one or more blocks in *source*.

    :param source: The source to format.
    :param sections: The blocks to highlight given as their offset and size.
    :param indent: The number of indentation spaces.
    :param keepends: Indicate whether the *source* contains line breaks or not.
    :return: An indented text.
    """
    sep = '' if keepends else '\n'
    if sections:
        tab, accent = make_prefix(indent), make_prefix(indent, highlight=True)
        lines = _highlight(source, sections, prefix=tab, highlight_prefix=accent)
        return sep.join(lines)
    return indent_source(source, sep=sep, indent=indent, highlight=False)
