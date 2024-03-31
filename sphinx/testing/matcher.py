from __future__ import annotations

__all__ = ('Options', 'LineMatcher')

import contextlib
from itertools import starmap
from types import MappingProxyType
from typing import TYPE_CHECKING

from sphinx.testing._matcher import cleaner, engine, util
from sphinx.testing._matcher.buffer import Block, Line
from sphinx.testing._matcher.options import DEFAULT_OPTIONS, Options, get_option

if TYPE_CHECKING:
    from collections.abc import Collection, Generator, Iterable, Iterator, Sequence
    from io import StringIO
    from re import Pattern
    from typing import Literal

    from typing_extensions import Self, Unpack

    from sphinx.testing._matcher.options import CompleteOptions, Flavor
    from sphinx.testing._matcher.util import LinePattern

    PatternType = Literal['line', 'block']


class LineMatcher:
    """Helper object for matching output lines."""

    __slots__ = ('_content', '_options', '_stack')

    def __init__(self, content: str | StringIO, /, **options: Unpack[Options]) -> None:
        """Construct a :class:`LineMatcher` for the given string content.

        :param content: The source string.
        :param options: The matcher options.
        """
        self._content = content if isinstance(content, str) else content.getvalue()
        # always complete the set of options for this object
        self._options: CompleteOptions = DEFAULT_OPTIONS | options
        # stack of cached cleaned lines (with a possible indirection)
        self._stack: list[int | tuple[str, ...] | None] = [None]

    @classmethod
    def from_lines(
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
            cached = tuple(cleaner.clean_text(self.content, **self.options))
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

    def find(
        self, expect: LinePattern | Collection[LinePattern], /, *, flavor: Flavor | None = None
    ) -> Sequence[Line]:
        """Same as :meth:`iterfind` but returns a sequence of lines."""
        return list(self.iterfind(expect, flavor=flavor))

    def iterfind(
        self, expect: LinePattern | Collection[LinePattern], /, *, flavor: Flavor | None = None
    ) -> Iterator[Line]:
        """Yield the lines that match one (or more) of the given patterns.

        When one or more patterns are given, the order of evaluation is the
        same as they are given (or arbitrary if they are given in a set).
        """
        patterns = engine.to_line_patterns(expect)
        matchers = [pattern.match for pattern in self.__compile(patterns, flavor=flavor)]

        def predicate(line: Line) -> bool:
            return any(matcher(line.buffer) for matcher in matchers)

        yield from filter(predicate, self)

    def find_blocks(
        self, expect: str | Sequence[LinePattern], /, *, flavor: Flavor | None = None
    ) -> Sequence[Block]:
        """Same as :meth:`iterfind_blocks` but returns a sequence of blocks."""
        return list(self.iterfind_blocks(expect, flavor=flavor))

    def iterfind_blocks(
        self, expect: str | Sequence[LinePattern], /, *, flavor: Flavor | None = None
    ) -> Iterator[Block]:
        """Yield non-overlapping blocks matching the given line patterns.

        :param expect: The line patterns that a block must satisfy.
        :param flavor: Optional temporary flavor for string patterns.
        :return: An iterator on the matching blocks.

        When *expect* is a single string, it is split into lines, each of
        which corresponding to the pattern a block's line must satisfy.

        .. note::

           This interface does not support single :class:`~re.Pattern`
           objects as they could be interpreted as a line or a block
           pattern.
        """
        patterns = engine.to_block_pattern(expect)

        lines = self.lines()
        # early abort if there are more expected lines than actual ones
        if (width := len(patterns)) > len(lines):
            return

        compiled_patterns = self.__compile(patterns, flavor=flavor)

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

    # assert methods

    def assert_match(
        self,
        expect: LinePattern | Collection[LinePattern],
        /,
        count: int | None = None,
        flavor: Flavor | None = None,
    ) -> None:
        """Assert that there exist one or more lines matching *pattern*.

        :param expect: One or more patterns the lines must satisfy.
        :param count: If specified, the exact number of matching lines.
        :param flavor: Optional temporary flavor for string patterns.
        """
        patterns = engine.to_line_patterns(expect)
        self._assert_found('line', patterns, count=count, flavor=flavor)

    def assert_no_match(
        self,
        expect: LinePattern | Collection[LinePattern],
        /,
        *,
        context: int = 3,
        flavor: Flavor | None = None,
    ) -> None:
        """Assert that there are no lines matching *pattern*.

        :param expect: One or more patterns the lines must not satisfy.
        :param context: Number of lines to print around a failing line.
        :param flavor: Optional temporary flavor for string patterns.
        """
        patterns = engine.to_line_patterns(expect)
        self._assert_not_found('line', patterns, context_size=context, flavor=flavor)

    def assert_lines(
        self,
        expect: str | Sequence[LinePattern],
        /,
        *,
        count: int | None = None,
        flavor: Flavor | None = None,
    ) -> None:
        """Assert that there exist one or more blocks matching the *patterns*.

        :param expect: The line patterns that a block must satisfy.
        :param count: The number of blocks that should be found.
        :param flavor: Optional temporary flavor for string patterns.

        When *expect* is a single string, it is split into lines, each
        of which corresponding to the pattern a block's line must satisfy.
        """
        patterns = engine.to_block_pattern(expect)
        self._assert_found('block', patterns, count=count, flavor=flavor)

    def assert_no_lines(
        self,
        expect: str | Sequence[LinePattern],
        /,
        *,
        context: int = 3,
        flavor: Flavor | None = None,
    ) -> None:
        """Assert that no block matches the *patterns*.

        :param expect: The line patterns that a block must satisfy.
        :param context: Number of lines to print around a failing block.
        :param flavor: Optional temporary flavor for string patterns.

        When *expect* is a single string, it is split into lines, each
        of which corresponding to the pattern a block's line must satisfy.

        Use :data:`sys.maxsize` to show all capture lines.
        """
        patterns = engine.to_block_pattern(expect)
        self._assert_not_found('block', patterns, context_size=context, flavor=flavor)

    def _assert_found(
        self,
        pattern_type: PatternType,
        patterns: Sequence[LinePattern],
        *,
        count: int | None,
        flavor: Flavor | None = None,
    ) -> None:
        blocks = self.iterfind_blocks(patterns, flavor=flavor)

        if count is None:
            if next(blocks, None):
                return

            keepends = get_option(self.options, 'keepends')
            ctx = util.highlight(self.lines(), keepends=keepends)
            pat = util.prettify_patterns(patterns, sort=pattern_type == 'line')
            logs = [f'{pattern_type} pattern', pat, 'not found in', ctx]
            raise AssertionError('\n\n'.join(logs))

        indices = {block.offset: len(block) for block in blocks}
        if (found := len(indices)) == count:
            return

        keepends = get_option(self.options, 'keepends')
        ctx = util.highlight(self.lines(), indices, keepends=keepends)
        pat = util.prettify_patterns(patterns, sort=pattern_type == 'line')
        noun = util.plural_form(pattern_type, count)
        logs = [f'found {found} != {count} {noun} matching', pat, 'in', ctx]
        raise AssertionError('\n\n'.join(logs))

    def _assert_not_found(
        self,
        pattern_type: PatternType,
        patterns: Sequence[LinePattern],
        *,
        context_size: int,
        flavor: Flavor | None = None,
    ) -> None:
        lines = self.lines()
        if (count := len(patterns)) > len(lines):
            return

        compiled_patterns = self.__compile(patterns, flavor=flavor)

        for start, block in enumerate(util.windowed(lines, count)):
            if all(pattern.match(line) for pattern, line in zip(compiled_patterns, block)):
                pat = util.prettify_patterns(patterns, sort=pattern_type == 'line')
                ctx = util.get_debug_context(lines, Block(block, start), context_size)
                logs = [f'{pattern_type} pattern', pat, 'found in', '\n'.join(ctx)]
                raise AssertionError('\n\n'.join(logs))

    def __compile(
        self, patterns: Iterable[LinePattern], *, flavor: Flavor | None
    ) -> Sequence[Pattern[str]]:
        flavor = get_option(self.options, 'flavor') if flavor is None else flavor
        return engine.compile(patterns, flavor=flavor)
