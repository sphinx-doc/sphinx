from __future__ import annotations

__all__ = ('Options', 'LineMatcher')

import contextlib
import itertools
from typing import TYPE_CHECKING, cast

from sphinx.testing._matcher import cleaner, engine, util
from sphinx.testing._matcher.buffer import Block, Line
from sphinx.testing._matcher.options import Configurable, Options

if TYPE_CHECKING:
    from collections.abc import Collection, Generator, Iterable, Iterator, Sequence
    from io import StringIO
    from re import Pattern
    from typing import Literal

    from typing_extensions import Self, Unpack

    from sphinx.testing._matcher.options import Flavor
    from sphinx.testing._matcher.util import LinePattern

    PatternType = Literal['line', 'block']


class LineMatcher(Configurable):
    """Helper object for matching output lines."""

    __slots__ = ('_content', '_stack')

    # make sure to have an independent object
    default_options = Configurable.default_options.copy()

    def __init__(self, content: str | StringIO, /, **options: Unpack[Options]) -> None:
        """Construct a :class:`LineMatcher` for the given string content.

        :param content: The source string.
        :param options: The matcher options.
        """
        self._content = content if isinstance(content, str) else content.getvalue()
        # stack of cached cleaned lines (with a possible indirection)
        self._stack: list[int | Block | None] = [None]
        super().__init__(**options)

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
        # only compute the default options if needeed ('keepends' is a boolean)
        keepends = options.get('keepends') or cls.default_options['keepends']
        glue = '' if keepends else '\n'
        return cls(glue.join(lines), **options)

    def __iter__(self) -> Iterator[Line]:
        """An iterator on the cached lines."""
        # we do not use Line.view to avoid checking the type of each line
        yield from (Line(s, i, _check=False) for i, s in enumerate(self.lines()))

    @contextlib.contextmanager
    def override(self, /, **options: Unpack[Options]) -> Generator[None, None, None]:
        self._stack.append(None)  # prepare the next cache entry
        with super().override(**options):
            yield
        self._stack.pop()  # pop the cached lines

    @property
    def content(self) -> str:
        """The raw content."""
        return self._content

    def lines(self) -> Block:
        """The content lines, cleaned up according to the current options.

        This method is efficient in the sense that the lines are computed
        once per set of options and cached for subsequent calls.
        """
        stack = self._stack
        assert stack, 'invalid stack state'
        cached = stack[-1]

        if cached is None:
            # compute for the first time the value
            options = self.default_options | cast(Options, self.options)
            # use the *same* type as a block's buffer to speed-up the Block's constructor
            lines = tuple(cleaner.clean_text(self.content, **options))
            # check if the value is the same as any of a previously cached value
            for addr, value in enumerate(itertools.islice(stack, 0, len(stack) - 1)):
                if isinstance(value, int):
                    cached = cast(Block, stack[value])
                    assert isinstance(cached.buffer, tuple)
                    if cached.buffer == lines:
                        # compare only the lines (C interface)
                        stack[-1] = value  # indirection
                        return cached

                if isinstance(value, Block):
                    assert isinstance(value.buffer, tuple)
                    if value.buffer == lines:
                        stack[-1] = addr  # indirection
                        return value

            # the value did not exist yet, so we store it at most once
            stack[-1] = cached = Block(lines, _check=False)
            return cached

        if isinstance(cached, int):
            value = self._stack[cached]
            assert isinstance(value, Block)
            return value

        assert isinstance(cached, Block)
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
        if not patterns:  # nothinig to match
            return

        compiled_patterns = set(self.__compile(patterns, flavor=flavor))
        matchers = {pattern.match for pattern in compiled_patterns}

        def predicate(line: Line) -> bool:
            text = line.buffer
            return any(matcher(text) for matcher in matchers)

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
        # in general, the patterns are smaller than the lines
        # so we expect the following to be more efficient than
        # cleaning up the whole text source
        patterns = engine.to_block_pattern(expect)
        if not patterns:  # no pattern to locate
            return

        lines: Sequence[str] = self.lines()
        if not lines:  # no line to match
            return

        if (width := len(patterns)) > len(lines):  # too many lines to match
            return

        compiled_patterns = self.__compile(patterns, flavor=flavor)
        block_iterator = enumerate(util.windowed(lines, width))
        for start, block in block_iterator:
            # check if the block matches the patterns line by line
            if all(pattern.match(line) for pattern, line in zip(compiled_patterns, block)):
                yield Block(block, start, _check=False)
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
        flavor: Flavor | None,
    ) -> None:
        blocks = self.iterfind_blocks(patterns, flavor=flavor)

        if count is None:
            if next(blocks, None):
                return

            keepends = self.get_option('keepends')
            ctx = util.highlight(self.lines(), keepends=keepends)
            pat = util.prettify_patterns(patterns, sort=pattern_type == 'line')
            logs = [f'{pattern_type} pattern', pat, 'not found in', ctx]
            raise AssertionError('\n\n'.join(logs))

        indices = {block.offset: len(block) for block in blocks}
        if (found := len(indices)) == count:
            return

        keepends = self.get_option('keepends')
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
        flavor: Flavor | None,
    ) -> None:
        if not patterns:  # no pattern to find
            return

        lines: Sequence[str] = self.lines()
        if not lines:  # no lines to match
            return

        # early abort if there are more lines to match than available
        if (window_size := len(patterns)) > len(lines):
            return

        compiled_patterns = self.__compile(patterns, flavor=flavor)

        for start, block in enumerate(util.windowed(lines, window_size)):
            if all(pattern.match(line) for pattern, line in zip(compiled_patterns, block)):
                pat = util.prettify_patterns(patterns, sort=pattern_type == 'line')
                block_object = Block(block, start, _check=False)
                ctx = util.get_debug_context(lines, block_object, context_size)
                logs = [f'{pattern_type} pattern', pat, 'found in', '\n'.join(ctx)]
                raise AssertionError('\n\n'.join(logs))

    def __compile(
        self, patterns: Iterable[LinePattern], *, flavor: Flavor | None
    ) -> Sequence[Pattern[str]]:
        flavor = self.get_option('flavor') if flavor is None else flavor
        return engine.compile(patterns, flavor=flavor)
