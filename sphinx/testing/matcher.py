from __future__ import annotations

__all__ = ('Options', 'LineMatcher')

import contextlib
import fnmatch
import re
from itertools import starmap
from types import MappingProxyType
from typing import TYPE_CHECKING, final

import pytest

from sphinx.testing._matcher import util
from sphinx.testing._matcher.buffer import Block, Line
from sphinx.testing._matcher.options import DEFAULT_OPTIONS, Options, get_option
from sphinx.util.console import strip_colors, strip_control_sequences

if TYPE_CHECKING:
    from collections.abc import Collection, Generator, Iterable, Iterator, Sequence
    from typing import Literal

    from typing_extensions import Self, Unpack

    from sphinx.testing._matcher.options import CompleteOptions
    from sphinx.testing._matcher.util import LinePattern

    PatternType = Literal['line', 'block']


def clean(text: str, /, **options: Unpack[Options]) -> tuple[str, ...]:
    """Split *text* into lines.

    :param text: The text to get the cleaned lines of.
    :param options: The processing options.
    :return: A list of cleaned lines.
    """
    if not get_option(options, 'ctrl'):
        # Non-color ANSI esc. seq. must be stripped before colors;
        # see :func:`sphinx.util.console.strip_escape_sequences`.
        text = strip_control_sequences(text)

    if not get_option(options, 'color'):
        text = strip_colors(text)

    chars = get_option(options, 'strip')
    if isinstance(chars, bool) and chars:
        text = text.strip()
    elif isinstance(chars, str) or chars is None:
        text = text.strip(chars)
    elif chars is not False:
        msg = 'expecting a boolean, a string or None for %r, got: %r' % ('strip', chars)
        raise TypeError(msg)

    keepends = get_option(options, 'keepends')
    lines: Iterable[str] = text.splitlines(keepends=keepends)

    chars = get_option(options, 'stripline')
    if isinstance(chars, bool) and chars:
        lines = map(str.strip, lines)
    elif isinstance(chars, str) or chars is None:
        lines = (line.strip(chars) for line in lines)
    elif chars is not False:
        msg = 'expecting a boolean, a string or None for %r, got: %r' % ('stripline', chars)
        raise TypeError(msg)

    # Removing empty lines first ensures that serial duplicates can
    # be eliminated in one cycle. Inverting the order of operations
    # is not possible since empty lines may 'hide' duplicated lines.
    if not get_option(options, 'empty'):
        lines = filter(None, lines)

    if get_option(options, 'unique'):
        # 'compress' has no effect when 'unique' is set
        lines = util.unique_everseen(lines)
    elif get_option(options, 'compress'):
        lines = util.unique_justseen(lines)

    return tuple(lines)


def _to_lines_pattern(expect: LinePattern | Collection[LinePattern]) -> Sequence[LinePattern]:
    return [expect] if isinstance(expect, (str, re.Pattern)) else list(expect)


def _to_block_pattern(expect: LinePattern | Sequence[LinePattern]) -> Sequence[LinePattern]:
    """Make *pattern* compatible for block-matching."""
    if isinstance(expect, str):
        return expect.splitlines()
    if isinstance(expect, re.Pattern):
        return [expect]
    return expect


@final
class LineMatcher:
    """Helper object for matching output lines."""

    __slots__ = ('_content', '_options', '_stack')

    def __init__(self, content: str, /, **options: Unpack[Options]) -> None:
        """Construct a :class:`LineMatcher` for the given string content.

        :param content: The source string.
        :param options: The matcher options.
        """
        self._content = content
        # always complete the set of options for this object
        self._options: CompleteOptions = DEFAULT_OPTIONS | options
        # stack of cached cleaned lines (with a possible indirection)
        self._stack: list[int | tuple[str, ...] | None] = [None]

    @classmethod
    def parse(
        cls, lines: Iterable[str], sep: str = '\n', /, **options: Unpack[Options]
    ) -> Self:
        """Construct a :class:`LineMatcher` object from a list of lines.

        This is typically useful when writing tests for :class:`LineMatcher`
        since writing the lines instead of a long string is usually cleaner.
        """
        return cls(sep.join(lines), **options)

    def __iter__(self) -> Iterator[Line]:
        """The cached lines as :class:`~sphinx.testing._matcher.Line` instances."""
        return starmap(Line.view, enumerate(self.lines()))

    @property
    def content(self) -> str:
        """The raw content."""
        return self._content

    @property
    def options(self) -> CompleteOptions:
        """Return a *read-only* view on the (complete) set of options.

        The runtime type of this field is a :class:`!MappingProxyType` and
        protects against *runtime* destructive operations (which would not
        have been the case solely with a type annotation).
        """
        return MappingProxyType(self._options)  # type: ignore[return-value]

    @contextlib.contextmanager
    def use(self, /, **options: Unpack[Options]) -> Generator[None, None, None]:
        """Temporarily set the set of options for this object to *options*.

        If an option is not specified in *options*, its default value is used.
        """
        local_options = DEFAULT_OPTIONS | options
        with self.override(**local_options):
            yield

    @contextlib.contextmanager
    def override(self, /, **options: Unpack[Options]) -> Generator[None, None, None]:
        """Temporarily extend the set of options for this object using *options*."""
        saved_options = self._options.copy()
        self._options |= options
        self._stack.append(None)  # prepare the next cache entry
        try:
            yield
        finally:
            self._stack.pop()  # pop the cached lines for this scope
            self._options = saved_options

    def lines(self) -> tuple[str, ...]:
        """The content lines, cleaned up according to the current options.

        This method is efficient in the sense that the lines are computed
        once per set of options and cached for subsequent calls.
        """
        stack = self._stack
        assert stack, 'invalid stack state'
        cached = stack[-1]

        if cached is None:
            # compute for the first time the value
            cached = clean(self.content, **self.options)
            # check if the value is the same as any of a previously cached value
            for addr, value in enumerate(stack):
                if value == cached:
                    stack[-1] = addr  # indirection
                    return cached
            # the value did not exist yet, so we store it at most once
            stack[-1] = cached
            return cached

        if isinstance(cached, int):
            value = self._stack[cached]
            assert isinstance(value, tuple)
            return value

        assert isinstance(cached, tuple)
        return cached

    def match(self, expect: LinePattern | Collection[LinePattern], /) -> Sequence[Line]:
        """Same as :meth:`itermatch` but returns a sequence of lines."""
        return list(self.itermatch(expect))

    def itermatch(self, expect: LinePattern | Collection[LinePattern], /) -> Iterator[Line]:
        """Yield the lines that match one (or more) of the given patterns.

        When one or more patterns are given, the order of evaluation is the
        same as they are given (or arbitrary if they are given in a set).
        """
        patterns = _to_lines_pattern(expect)
        matchers = [pattern.match for pattern in self.__compile(patterns)]

        def predicate(line: Line) -> bool:
            return any(matcher(str(line)) for matcher in matchers)

        yield from filter(predicate, self)

    def find(self, expect: str | Sequence[LinePattern], /) -> Sequence[Block]:
        """Same as :meth:`iterfind` but returns a sequence of blocks."""
        return list(self.iterfind(expect))

    def iterfind(self, expect: str | Sequence[LinePattern], /) -> Iterator[Block]:
        """Yield non-overlapping blocks matching the given line patterns.

        :param expect: The line patterns that a block must satisfy.
        :return: An iterator on the matching blocks.

        When *expect* is a single string, it is split into lines, each of
        which corresponding to the pattern a block's line must satisfy.

        .. note::

           This interface does not support single :class:`~re.Pattern`
           objects as they could be interpreted as a line or a block
           pattern.
        """
        patterns = _to_block_pattern(expect)

        lines = self.lines()
        # early abort if there are more expected lines than actual ones
        if (width := len(patterns)) > len(lines):
            return

        compiled_patterns = self.__compile(patterns)

        block_iterator = enumerate(util.windowed(lines, width))
        for start, block in block_iterator:
            # check if the block matches the pattern line by line
            if all(pattern.match(line) for pattern, line in zip(compiled_patterns, block)):
                yield Block(block, start)
                # Consume the iterator so that the next block consists
                # of lines just after the block that was just yielded.
                #
                # Note that since the iterator yielded *block*, its
                # state is already on the "next" line, so we need to
                # advance by the block size - 1 only.
                util.consume(block_iterator, width - 1)

    def assert_match(
        self, expect: LinePattern | Collection[LinePattern], /, *, count: int | None = None
    ) -> None:
        """Assert that there exist one or more lines matching *pattern*.

        :param expect: One or more patterns the lines must satisfy.
        :param count: If specified, the exact number of matching lines.
        """
        patterns = _to_lines_pattern(expect)
        self._assert_found('line', patterns, count=count)

    def assert_not_match(
        self, expect: LinePattern | Collection[LinePattern], /, *, context: int = 3
    ) -> None:
        """Assert that there are no lines matching *pattern*.

        :param expect: One or more patterns the lines must not satisfy.
        :param context: Number of lines to print around a failing line.
        """
        patterns = _to_lines_pattern(expect)
        self._assert_not_found('line', patterns, context_size=context)

    def assert_block(
        self, expect: str | Sequence[LinePattern], /, *, count: int | None = None
    ) -> None:
        """Assert that there exist one or more blocks matching the *patterns*.

        :param expect: The line patterns that a block must satisfy.
        :param count: The number of blocks that should be found.

        When *expect* is a single string, it is split into lines, each
        of which corresponding to the pattern a block's line must satisfy.
        """
        patterns = _to_block_pattern(expect)
        self._assert_found('block', patterns, count=count)

    def assert_not_block(
        self, expect: str | Sequence[LinePattern], /, *, context: int = 1
    ) -> None:
        """Assert that no block matches the *patterns*.

        :param expect: The line patterns that a block must satisfy.
        :param context: Number of lines to print around a failing block.

        When *expect* is a single string, it is split into lines, each
        of which corresponding to the pattern a block's line must satisfy.

        Use :data:`sys.maxsize` to show all capture lines.
        """
        patterns = _to_block_pattern(expect)
        self._assert_not_found('block', patterns, context_size=context)

    def _assert_found(
        self, what: PatternType, /, patterns: Sequence[LinePattern], *, count: int | None
    ) -> None:
        blocks = self.iterfind(patterns)

        if count is None:
            if next(blocks, None):
                return

            keepends = get_option(self.options, 'keepends')
            ctx = util.highlight(self.lines(), keepends=keepends)
            pat = util.prettify_patterns(patterns)
            logs = [f'{what} pattern', pat, 'not found in', ctx]
            pytest.fail('\n\n'.join(logs))

        indices = {block.offset: len(block) for block in blocks}
        if (found := len(indices)) == count:
            return

        keepends = get_option(self.options, 'keepends')
        ctx = util.highlight(self.lines(), indices, keepends=keepends)
        pat = util.prettify_patterns(patterns)
        noun = util.plural_form(what, count)
        logs = [f'found {found} != {count} {noun} matching', pat, 'in', ctx]
        pytest.fail('\n\n'.join(logs))

    def _assert_not_found(
        self, what: PatternType, /, patterns: Sequence[LinePattern], *, context_size: int
    ) -> None:
        lines = self.lines()
        if (count := len(patterns)) > len(lines):
            return

        compiled_patterns = self.__compile(patterns)

        for start, block in enumerate(util.windowed(lines, count)):
            if all(pattern.match(line) for pattern, line in zip(compiled_patterns, block)):
                pattern = util.prettify_patterns(patterns)
                context = util.get_debug_context(
                    lines, Block(block, start), context=context_size
                )
                logs = [f'{what} pattern', pattern, 'found in', '\n'.join(context)]
                pytest.fail('\n\n'.join(logs))

    def __compile(self, patterns: Iterable[LinePattern], /) -> Sequence[re.Pattern[str]]:
        flavor = get_option(self.options, 'flavor')
        if flavor == 'fnmatch':
            patterns = [fnmatch.translate(p) if isinstance(p, str) else p for p in patterns]
        elif flavor == 'exact':
            patterns = [re.escape(p) if isinstance(p, str) else p for p in patterns]

        # mypy does not like map + re.compile() although it is correct but
        # this is likely due to https://github.com/python/mypy/issues/11880
        return [re.compile(pattern) for pattern in patterns]
