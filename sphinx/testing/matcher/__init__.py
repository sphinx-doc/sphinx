"""Public module containing the matcher interface."""

from __future__ import annotations

__all__ = ('LineMatcher',)

import contextlib
import itertools
import re
from typing import TYPE_CHECKING, cast, overload

from sphinx.testing.matcher import cleaner, _engine, _util
from sphinx.testing.matcher.buffer import Block
from sphinx.testing.matcher.options import Options, OptionsHolder

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable, Iterator, Sequence, Set
    from io import StringIO
    from re import Pattern
    from typing import ClassVar, Literal

    from typing_extensions import Self, Unpack

    from sphinx.testing.matcher._util import BlockPattern, LinePattern
    from sphinx.testing.matcher.buffer import Line
    from sphinx.testing.matcher.options import CompleteOptions, Flavor

    PatternType = Literal['line', 'block']


class LineMatcher(OptionsHolder):
    """Helper object for matching output lines."""

    __slots__ = ('__content', '__stack')

    default_options: ClassVar[CompleteOptions] = OptionsHolder.default_options.copy()

    def __init__(self, content: str | StringIO, /, **options: Unpack[Options]) -> None:
        """Construct a :class:`LineMatcher` for the given string content.

        :param content: The source string.
        :param options: The matcher options.
        """
        super().__init__(**options)
        self.__content = content if isinstance(content, str) else content.getvalue()
        # stack of cached cleaned lines (with a possible indirection)
        self.__stack: list[int | Block | None] = [None]

    @classmethod
    def from_lines(cls, lines: Iterable[str] = (), /, **options: Unpack[Options]) -> Self:
        """Construct a :class:`LineMatcher` object from a list of lines.

        This is typically useful when writing tests for :class:`LineMatcher`
        since writing the lines instead of a long string is usually cleaner.

        The lines are glued together according to whether line breaks,
        which can be specified by the keyword argument *keepends*.

        By default, the lines are assumed *not* to have line breaks (since
        this is usually what is the most common).
        """
        keep_break = options.get('keep_break', cls.default_options['keep_break'])
        glue = '' if keep_break else '\n'
        return cls(glue.join(lines), **options)

    def __iter__(self) -> Iterator[Line]:
        """An iterator on the cached lines."""
        return self.lines().lines_iterator()

    @contextlib.contextmanager
    def override(self, /, **options: Unpack[Options]) -> Generator[None, None, None]:
        """Temporarily extend the set of options with *options*."""
        self.__stack.append(None)  # prepare the next cache entry
        with super().override(**options):
            yield
        self.__stack.pop()  # pop the cached lines

    @property
    def content(self) -> str:
        """The raw content."""
        return self.__content

    def lines(self) -> Block:
        """The content lines, cleaned up according to the current options.

        This method is efficient in the sense that the lines are computed
        once per set of options and cached for subsequent calls.
        """
        stack = self.__stack
        assert stack, 'invalid stack state'
        cached = stack[-1]

        if cached is None:
            options = self.default_options | cast(Options, self.options)
            # compute for the first time the block's lines
            lines = tuple(cleaner.clean(self.content, **options))
            # check if the value is the same as any of a previously cached value
            for addr, value in enumerate(itertools.islice(stack, 0, len(stack) - 1)):
                if isinstance(value, int):
                    cached = cast(Block, stack[value])
                    if cached.buffer == lines:
                        # compare only the lines as strings
                        stack[-1] = value  # indirection near to beginning
                        return cached

                if isinstance(value, Block):
                    if value.buffer == lines:
                        stack[-1] = addr  # indirection
                        return value

            # the value did not exist yet, so we store it at most once
            stack[-1] = cached = Block(lines, _check=False)
            return cached

        if isinstance(cached, int):
            value = self.__stack[cached]
            assert isinstance(value, Block)
            return value

        return cached

    def find(
        self,
        patterns: LinePattern | Set[LinePattern] | Sequence[LinePattern],
        /,
        *,
        flavor: Flavor | None = None,
    ) -> Sequence[Line]:
        """Same as :meth:`iterfind` but returns a sequence of lines."""
        return list(self.iterfind(patterns, flavor=flavor))

    def iterfind(
        self,
        patterns: LinePattern | Set[LinePattern] | Sequence[LinePattern],
        /,
        *,
        flavor: Flavor | None = None,
    ) -> Iterator[Line]:
        """Yield the lines that match one (or more) of the given patterns.

        :param patterns: The patterns deciding whether a line is selected.
        :param flavor: Optional temporary flavor for non-compiled patterns.
        """
        patterns = _engine.to_line_patterns(patterns)
        if not patterns:  # nothinig to match
            return

        compiled_patterns = set(self.__compile(patterns, flavor=flavor))
        # faster to iterate over a tuple rather than a set or a list
        matchers = tuple(pattern.match for pattern in compiled_patterns)

        def predicate(line: Line) -> bool:
            text = line.buffer
            return any(matcher(text) for matcher in matchers)

        yield from filter(predicate, self)

    def find_blocks(
        self, pattern: str | BlockPattern, /, *, flavor: Flavor | None = None
    ) -> Sequence[Block]:
        """Same as :meth:`iterfind_blocks` but returns a sequence of blocks."""
        return list(self.iterfind_blocks(pattern, flavor=flavor))

    def iterfind_blocks(
        self, patterns: str | BlockPattern, /, *, flavor: Flavor | None = None
    ) -> Iterator[Block]:
        """Yield non-overlapping blocks matching the given line patterns.

        :param patterns: The line patterns that a block must satisfy.
        :param flavor: Optional temporary flavor for non-compiled patterns.
        :return: An iterator on the matching blocks.

        When *patterns* is a single string, it is split into lines, each
        of which corresponding to the pattern a block's line must satisfy.

        .. note::

           Standalone :class:`~re.Pattern` objects are not supported
           as they could be interpreted as a line or a block pattern.
        """
        # in general, the patterns are smaller than the lines
        # so we expect the following to be more efficient than
        # cleaning up the whole text source
        patterns = _engine.to_block_pattern(patterns)
        if not patterns:  # no pattern to locate
            return

        lines: Sequence[str] = self.lines()
        if not lines:  # no line to match
            return

        if (width := len(patterns)) > len(lines):  # too many lines to match
            return

        match_function = re.Pattern.match
        compiled_patterns = self.__compile(patterns, flavor=flavor)
        block_iterator = enumerate(_util.strict_windowed(lines, width))
        for start, block in block_iterator:
            # check if the block matches the patterns line by line
            if all(map(match_function, compiled_patterns, block)):
                yield Block(block, start, _check=False)
                # Consume the iterator so that the next block consists
                # of lines just after the block that was just yielded.
                #
                # Note that since the iterator yielded *block*, its
                # state is already on the "next" line, so we need to
                # advance by the block size - 1 only.
                _util.consume(block_iterator, width - 1)

    # assert methods

    def assert_match(
        self,
        patterns: LinePattern | Set[LinePattern] | Sequence[LinePattern],
        /,
        count: int | None = None,
        flavor: Flavor | None = None,
    ) -> None:
        """Assert that the number of matching lines for the given patterns.

        A matching line is a line that satisfies one or more patterns
        given in *patterns*.

        :param patterns: The patterns deciding whether a line is counted.
        :param count: If specified, the exact number of matching lines.
        :param flavor: Optional temporary flavor for non-compiled patterns.
        """
        patterns = _engine.to_line_patterns(patterns)
        self._assert_found('line', patterns, count=count, flavor=flavor)

    def assert_no_match(
        self,
        patterns: LinePattern | Set[LinePattern] | Sequence[LinePattern],
        /,
        *,
        context: int = 3,
        flavor: Flavor | None = None,
    ) -> None:
        """Assert that there exist no matching line for the given patterns.

        A matching line is a line that satisfies one or more patterns
        given in *patterns*.

        :param patterns: The patterns deciding whether a line is counted.
        :param context: Number of lines to print around a failing line.
        :param flavor: Optional temporary flavor for non-compiled patterns.
        """
        patterns = _engine.to_line_patterns(patterns)
        self._assert_not_found('line', patterns, context_size=context, flavor=flavor)

    def assert_block(
        self,
        lines: str | BlockPattern,
        /,
        *,
        count: int | None = None,
        flavor: Flavor | None = None,
    ) -> None:
        """Assert that the number of matching blocks for the given patterns.

        :param lines: The line patterns that a block must satisfy.
        :param count: The number of blocks that should be found.
        :param flavor: Optional temporary flavor for non-compiled patterns.

        When *lines* is a single string, it is split into lines, each of
        which corresponding to the pattern a block's line must satisfy.
        """
        patterns = _engine.to_block_pattern(lines)
        self._assert_found('block', patterns, count=count, flavor=flavor)

    def assert_no_block(
        self,
        lines: str | BlockPattern,
        /,
        *,
        context: int = 3,
        flavor: Flavor | None = None,
    ) -> None:
        """Assert that there exist no matching blocks for the given patterns.

        :param lines: The line patterns that a block must satisfy.
        :param context: Number of lines to print around a failing block.
        :param flavor: Optional temporary flavor for non-compiled patterns.

        When *patterns* is a single string, it is split into lines, each
        of which corresponding to the pattern a block's line must satisfy.

        Use :data:`sys.maxsize` to show all capture lines.
        """
        patterns = _engine.to_block_pattern(lines)
        self._assert_not_found('block', patterns, context_size=context, flavor=flavor)

    def _assert_found(
        self,
        pattern_type: PatternType,
        patterns: Sequence[LinePattern],
        *,
        count: int | None,
        flavor: Flavor | None,
    ) -> None:
        regions = self.__find(pattern_type, patterns, flavor=flavor)

        if count is None:
            if next(regions, None) is not None:
                return

            ctx = _util.highlight(self.lines(), keepends=self.keep_break)
            pat = _util.prettify_patterns(patterns, sort=pattern_type == 'line')
            logs = [f'{pattern_type} pattern', pat, 'not found in', ctx]
            raise AssertionError('\n\n'.join(logs))

        indices = {region.offset: region.length for region in regions}
        if (found := len(indices)) == count:
            return

        ctx = _util.highlight(self.lines(), indices, keepends=self.keep_break)
        pat = _util.prettify_patterns(patterns, sort=pattern_type == 'line')
        noun = _util.plural_form(pattern_type, count)
        logs = [f'found {found} != {count} {noun} matching', pat, 'in', ctx]
        raise AssertionError('\n\n'.join(logs))

    def _assert_not_found(
        self,
        pattern_type: PatternType,
        patterns: Sequence[LinePattern],
        *,
        context_size: int,
        flavor: Flavor | None,
    ) -> None:
        if not patterns:  # no pattern to find
            return

        values = self.__find(pattern_type, patterns, flavor=flavor)
        found: Line | Block | None = next(values, None)
        if found is None:
            return

        pat = _util.prettify_patterns(patterns, sort=pattern_type == 'line')
        ctx = _util.get_context_lines(self.lines(), found, context_size)
        logs = [f'{pattern_type} pattern', pat, 'found in', '\n'.join(ctx)]
        raise AssertionError('\n\n'.join(logs))

    def __compile(
        self, patterns: Iterable[LinePattern], *, flavor: Flavor | None
    ) -> Sequence[Pattern[str]]:
        flavor = self.flavor if flavor is None else flavor
        return _engine.compile(patterns, flavor=flavor)

    @overload
    def __find(  # NoQA: E704
        self,
        pattern_type: Literal['line'],
        patterns: Sequence[LinePattern],
        /,
        flavor: Flavor | None,
    ) -> Iterator[Line]: ...
    @overload  # NoQA: E301
    def __find(  # NoQA: E704
        self,
        pattern_type: Literal['block'],
        patterns: Sequence[LinePattern],
        /,
        flavor: Flavor | None,
    ) -> Iterator[Block]: ...
    def __find(  # NoQA: E301
        self,
        pattern_type: PatternType,
        patterns: Sequence[LinePattern],
        /,
        flavor: Flavor | None,
    ) -> Iterator[Line] | Iterator[Block]:
        if pattern_type == 'line':
            return self.iterfind(patterns, flavor=flavor)
        return self.iterfind_blocks(patterns, flavor=flavor)
