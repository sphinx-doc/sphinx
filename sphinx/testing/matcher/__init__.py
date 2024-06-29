"""Public module containing the matcher interface."""

from __future__ import annotations

__all__ = ('LineMatcher',)

import contextlib
import re
from collections.abc import Sequence, Set
from typing import TYPE_CHECKING, Union, cast, final

from sphinx.testing.matcher import _engine, _util, cleaner
from sphinx.testing.matcher._util import BlockPattern, LinePattern
from sphinx.testing.matcher.buffer import Block
from sphinx.testing.matcher.options import Options, OptionsHolder

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from io import StringIO
    from typing import Any, ClassVar, Literal

    from typing_extensions import Self, TypeAlias, Unpack

    from sphinx.testing.matcher._util import PatternLike, Patterns
    from sphinx.testing.matcher.buffer import Line, Region
    from sphinx.testing.matcher.options import CompleteOptions, Flavor

    _RegionType: TypeAlias = Literal['line', 'block']

LineSet: TypeAlias = Union[LinePattern, Set[LinePattern], Sequence[LinePattern]]
"""One or more valid lines to find.

Non-compiled patterns are compiled according to the matcher's flavor.
"""

BlockLike: TypeAlias = Union[str, BlockPattern]
"""A pattern for a block to find.

A non-compiled pattern is compiled according to :class:`LineMatcher`'s flavor,
or the flavor of methods such as :meth:`LineMatcher.assert_block_literal`.
"""


class LineMatcher(OptionsHolder):
    r"""Helper object for matching output lines.

    Matching output lines is achieved by matching against compiled regular
    expressions, i.e., :class:`~re.Pattern` objects, e.g.,:

    >>> matcher = LineMatcher.from_lines(('Line 1', 'Line 2.0', r'Line \d+'))
    >>> matcher.find(re.compile(r'Line \d+'))
    ('Line 1', 'Line 2.0')

    The interface also supports non-compiled :class:`str` expressions, which
    are interpreted according to the matcher :attr:`~.OptionsHolder.flavor`.

    The default flavor is :py3r:`literal`, meaning that such expressions are
    escaped via :func:`re.escape` before being compiled into *exact match*
    patterns, i.e., literal strings are assumed to span the entire line,
    and thus are prefixed with :py3r:`\A` and :py3r:`\Z` meta-characters:

    >>> matcher.find('Line 1')
    ('Line 1',)
    >>> matcher.find('Line 2')
    ()
    >>> matcher.find('Line 2.0')
    ('Line 2.0',)
    >>> matcher.find(r'Line \d+')
    ('Line \\d+',)

    A useful flavor is :py3r:`re` which compiles :class:`str` expressions into
    patterns *without* escaping them first or adding meta-characters.

    >>> matcher.find(r'Line \w+', flavor='re')
    ('Line 1', 'Line 2.0')

    For some users, it might also be useful to support :mod:`fnmatch`-style
    patterns described by the :py3r:`fnmatch` flavor and where strings are
    translated into :mod:`fnmatch` patterns via :func:`fnmatch.translate`
    but allowed to be
    """

    __slots__ = ('__content', '__stack')

    default_options: ClassVar[CompleteOptions] = OptionsHolder.default_options.copy()

    def __init__(self, content: str | StringIO, /, **options: Unpack[Options]) -> None:
        """Construct a :class:`LineMatcher` for the given string content.

        :param content: The source string or stream.
        :param options: The matcher options.
        """
        super().__init__(**options)
        self.__content = content if isinstance(content, str) else content.getvalue()
        # stack of cached cleaned lines (with a possible indirection)
        self.__stack: list[int | Block | None] = [None]

    @classmethod
    def from_lines(cls, lines: Iterable[str] = (), /, **options: Unpack[Options]) -> Self:
        r"""Construct a :class:`LineMatcher` object from a list of lines.

        This is typically useful when writing tests for :class:`LineMatcher`
        since writing the lines instead of a long string is usually cleaner.

        The lines are glued together depending on the :py3r:`keep_break`
        option, whose default value is given by :attr:`default_options`:

        >>> text = 'foo\nbar'
        >>> m1 = LineMatcher(text)
        >>> m2 = LineMatcher.from_lines(text.splitlines())
        >>> m2.lines() == m1.lines()
        True
        >>> m2.lines()
        ('foo', 'bar')
        >>>
        >>> m1 = LineMatcher(text, keep_break=True)
        >>> m2 = LineMatcher.from_lines(text.splitlines(True), keep_break=True)
        >>> m1.lines() == m2.lines()
        True
        >>> m1.lines()
        ('foo\n', 'bar')
        """
        keep_break = options.get('keep_break', cls.default_options['keep_break'])
        glue = '' if keep_break else '\n'
        return cls(glue.join(lines), **options)

    def __iter__(self) -> Iterator[Line]:
        """An iterator on the cached lines."""
        return self.lines().lines_iterator()

    @contextlib.contextmanager
    def override(self, /, **options: Unpack[Options]) -> Iterator[None]:
        """Temporarily extend the set of options with *options*."""
        self.__stack.append(None)  # prepare the next cache entry
        try:
            with super().override(**options):
                yield
        finally:
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

        if cached is not None:
            if isinstance(cached, int):
                return cast(Block, self.__stack[cached])
            return cached

        lines = self.__get_clean_lines()
        # check if the value is the same as any of a previously cached value
        # but do not use slices to avoid a copy of the stack
        for addr, value in zip(range(len(stack) - 1), stack):
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

    def iterfind(
        self, patterns: LineSet, /, *, flavor: Flavor | None = None
    ) -> Iterator[Line]:
        """Yield the lines that match one (or more) of the given patterns.

        :param patterns: The patterns deciding whether a line is selected.
        :param flavor: Optional temporary flavor for non-compiled patterns.

        By convention, the following are equivalent::

            matcher.iterfind('line to find', ...)
            matcher.iterfind(['line to find'], ...)

        For simple usages, consider using the following flavor-binding aliases:

        .. default-role:: py3r

        +-----------+---------------------------+
        | Flavor    | Alias                     |
        +===========+===========================+
        | `literal` | :meth:`iterfind_literal`  |
        +-----------+---------------------------+
        | `re`      | :meth:`iterfind_matching` |
        +-----------+---------------------------+

        .. default-role::

        .. seealso:: :attr:`Options.flavor <sphinx.testing.matcher.options.Options.flavor>`
        """
        # make sure that the patterns are correctly normalized
        patterns = _engine.to_line_patterns(patterns)
        if not patterns:  # nothinig to match
            return

        compiled_patterns = self.__compile(patterns, flavor=flavor)
        # remove duplicated patterns but retain order
        unique_compiled_patterns = _util.unique_everseen(compiled_patterns)
        # faster to iterate over a tuple rather than a set or a list
        matchers = tuple(pattern.match for pattern in unique_compiled_patterns)

        def predicate(line: Line) -> bool:
            text = line.buffer
            return any(matcher(text) for matcher in matchers)

        yield from filter(predicate, self)

    @final
    def iterfind_literal(self, lines: LineSet, /) -> Iterator[Line]:
        """Partialization of :meth:`iterfind` for the :py3r:`literal` flavor."""
        return self.iterfind(lines, flavor='literal')

    @final
    def iterfind_matching(self, lines: LineSet) -> Iterator[Line]:
        """Partialization of :meth:`iterfind` for the :py3r:`re` flavor."""
        return self.iterfind(lines, flavor='re')

    def find(self, patterns: LineSet, /, *, flavor: Flavor | None = None) -> tuple[Line, ...]:
        """Same as :meth:`iterfind` but returns a sequence of lines."""
        # use tuple to preserve immutability
        return tuple(self.iterfind(patterns, flavor=flavor))

    @final
    def find_literal(self, lines: LineSet, /) -> tuple[Line, ...]:
        """Partialization of :meth:`find` for the :py3r:`literal` flavor."""
        return self.find(lines, flavor='literal')

    @final
    def find_matching(self, lines: LineSet) -> tuple[Line, ...]:
        """Partialization of :meth:`find` for the :py3r:`re` flavor."""
        return self.find(lines, flavor='re')

    def iterfind_blocks(
        self, patterns: BlockLike, /, *, flavor: Flavor | None = None
    ) -> Iterator[Block]:
        r"""Yield non-overlapping blocks matching the given line patterns.

        :param patterns: The line patterns that a block must satisfy.
        :param flavor: Optional temporary flavor for non-compiled patterns.
        :return: An iterator on the matching blocks.

        By convention, the following are equivalent::

            matcher.iterfind_blocks('line1\nline2', ...)
            matcher.iterfind_blocks(['line1', 'line2'], ...)

        For simple usages, consider using the following flavor-binding aliases:

        .. default-role:: py3r

        +-----------+----------------------------------+
        | Flavor    | Alias                            |
        +===========+==================================+
        | `literal` | :meth:`iterfind_literal_blocks`  |
        +-----------+----------------------------------+
        | `re`      | :meth:`iterfind_matching_blocks` |
        +-----------+----------------------------------+

        .. default-role::

        .. seealso:: :attr:`Options.flavor <sphinx.testing.matcher.options.Options.flavor>`
        """
        # The number of patterns is usually smaller than the expected lines
        # and thus it is more efficient to normalize and count the number of
        # patterns rather than cleaning up the entire text source.
        patterns = _engine.to_block_pattern(patterns)
        if not patterns:  # no pattern to locate
            return

        lines: Sequence[str] = self.lines()
        if not lines:  # no line to match
            return

        if (blocksize := len(patterns)) > len(lines):  # too many lines to match
            return

        match_function = re.Pattern.match
        compiled_block = self.__compile(patterns, flavor=flavor)
        block_iterator = enumerate(_util.strict_windowed(lines, blocksize))
        for start, block in block_iterator:
            # check if the block matches the patterns line by line
            if all(map(match_function, compiled_block, block)):
                yield Block(block, start, _check=False)
                # Consume the iterator so that the next block consists
                # of lines just after the block that was just yielded.
                #
                # Note that since the iterator yielded *block*, its
                # state is already on the "next" line, so we need to
                # advance the iterator by *blocksize - 1* steps.
                _util.consume(block_iterator, blocksize - 1)

    @final
    def iterfind_literal_blocks(self, block: BlockLike, /) -> Iterator[Block]:
        """Partialization of :meth:`iterfind_blocks` for the :py3r:`literal` flavor."""
        return self.iterfind_blocks(block, flavor='literal')

    @final
    def iterfind_matching_blocks(self, block: BlockLike) -> Iterator[Block]:
        """Partialization of :meth:`iterfind_blocks` for the :py3r:`re` flavor."""
        return self.iterfind_blocks(block, flavor='re')

    def find_blocks(
        self, pattern: BlockLike, /, *, flavor: Flavor | None = None
    ) -> tuple[Block, ...]:
        """Same as :meth:`iterfind_blocks` but returns a sequence of blocks.

        For simple usages, consider using the following flavor-binding aliases:

        .. default-role:: py3r

        +-----------+------------------------------+
        | Flavor    | Alias                        |
        +===========+==============================+
        | `literal` | :meth:`find_literal_blocks`  |
        +-----------+------------------------------+
        | `re`      | :meth:`find_matching_blocks` |
        +-----------+------------------------------+

        .. default-role::

        .. seealso:: :attr:`Options.flavor <sphinx.testing.matcher.options.Options.flavor>`
        """
        # use tuple to preserve immutability
        return tuple(self.iterfind_blocks(pattern, flavor=flavor))

    @final
    def find_literal_blocks(self, block: BlockLike, /) -> tuple[Block, ...]:
        """Partialization of :meth:`find_blocks` for the :py3r:`literal` flavor."""
        return self.find_blocks(block, flavor='literal')

    @final
    def find_matching_blocks(self, block: BlockLike) -> tuple[Block, ...]:
        """Partialization of :meth:`find_blocks` for the :py3r:`re` flavor."""
        return self.find_blocks(block, flavor='re')

    # assert methods

    def assert_any_of(
        self, patterns: LineSet, /, *, count: int | None = None, flavor: Flavor | None = None
    ) -> None:
        """Assert the number of matching lines for the given patterns.

        :param patterns: The patterns deciding whether a line is counted.
        :param count: If specified, the exact number of matching lines.
        :param flavor: Optional temporary flavor for non-compiled patterns.

        By convention, the following are equivalent::

            matcher.assert_any_of('line to find', ...)
            matcher.assert_any_of(['line to find'], ...)

        For simple usages, consider using the following flavor-binding aliases:

        .. default-role:: py3r

        +-----------+----------------------------+
        | Flavor    | Alias                      |
        +===========+============================+
        | `literal` | :meth:`assert_any_literal` |
        +-----------+----------------------------+
        | `re`      | :meth:`assert_any_match`   |
        +-----------+----------------------------+

        .. default-role::

        .. seealso:: :attr:`Options.flavor <sphinx.testing.matcher.options.Options.flavor>`
        """
        # Normalize the patterns now so that we can have a nice debugging,
        # even if `to_line_patterns` is called in `iterfind` (it is a no-op
        # the second time).
        patterns = _engine.to_line_patterns(patterns)
        lines = self.iterfind(patterns, flavor=flavor)
        self.__assert_found('line', lines, patterns, count, flavor)

    @final
    def assert_any_literal(self, lines: LineSet, /, *, count: int | None = None) -> None:
        """Partialization of :meth:`assert_any_of` for the :py3r:`literal` flavor."""
        return self.assert_any_of(lines, count=count, flavor='literal')

    @final
    def assert_any_match(self, lines: LineSet, /, *, count: int | None = None) -> None:
        """Partialization of :meth:`assert_any_of` for the :py3r:`re` flavor."""
        return self.assert_any_of(lines, count=count, flavor='re')

    def assert_none_of(
        self, patterns: LineSet, /, *, context: int = 3, flavor: Flavor | None = None
    ) -> None:
        """Assert that there exist no matching line for the given patterns.

        :param patterns: The patterns deciding whether a line is counted.
        :param context: Number of lines to print around a failing line.
        :param flavor: Optional temporary flavor for non-compiled patterns.

        By convention, the following are equivalent::

            matcher.assert_none_of('some bad line', ...)
            matcher.assert_none_of(['some bad line'], ...)

        For simple usages, consider using the following flavor-binding aliases:

        .. default-role:: py3r

        +-----------+---------------------------+
        | Flavor    | Alias                     |
        +===========+===========================+
        | `literal` | :meth:`assert_no_literal` |
        +-----------+---------------------------+
        | `re`      | :meth:`assert_no_match`   |
        +-----------+---------------------------+

        .. default-role::

        .. seealso:: :attr:`Options.flavor <sphinx.testing.matcher.options.Options.flavor>`
        """
        # Normalize the patterns now so that we can have a nice debugging,
        # even if `to_line_patterns` is called in `iterfind` (it is a no-op
        # the second time).
        if patterns := _engine.to_line_patterns(patterns):
            lines = self.iterfind(patterns, flavor=flavor)
            self.__assert_not_found('line', lines, patterns, context, flavor)

    @final
    def assert_no_literal(self, lines: LineSet, /, *, context: int = 3) -> None:
        """Partialization of :meth:`assert_no_match` for the :py3r:`literal` flavor."""
        return self.assert_none_of(lines, context=context, flavor='literal')

    @final
    def assert_no_match(self, lines: LineSet, /, *, context: int = 3) -> None:
        """Partialization of :meth:`assert_no_match` for the :py3r:`re` flavor."""
        return self.assert_none_of(lines, context=context, flavor='re')

    def assert_block(
        self, pattern: BlockLike, /, *, count: int | None = None, flavor: Flavor | None = None
    ) -> None:
        r"""Assert that the number of matching blocks for the given patterns.

        :param pattern: The line patterns that a block must satisfy.
        :param count: The number of blocks that should be found.
        :param flavor: Optional temporary flavor for non-compiled patterns.

        By convention, the following are equivalent::

            matcher.assert_block('line1\nline2', ...)
            matcher.assert_block(['line1', 'line2'], ...)

        For simple usages, consider using the following flavor-binding aliases:

        .. default-role:: py3r

        +-----------+-------------------------------+
        | Flavor    | Alias                         |
        +===========+===============================+
        | `literal` | :meth:`assert_literal_block`  |
        +-----------+-------------------------------+
        | `re`      | :meth:`assert_matching_block` |
        +-----------+-------------------------------+

        .. default-role::

        .. seealso:: :attr:`Options.flavor <sphinx.testing.matcher.options.Options.flavor>`
        """
        # Normalize the patterns now so that we can have a nice debugging,
        # even if `to_block_pattern` is called in `iterfind` (it is a no-op
        # the second time).
        patterns = _engine.to_block_pattern(pattern)
        blocks = self.iterfind_blocks(patterns, flavor=flavor)
        self.__assert_found('block', blocks, patterns, count, flavor)

    @final
    def assert_literal_block(self, block: BlockLike, /, *, count: int | None = None) -> None:
        """Partialization of :meth:`assert_block` for the :py3r:`literal` flavor."""
        return self.assert_block(block, count=count, flavor='literal')

    @final
    def assert_matching_block(self, block: BlockLike, /, *, count: int | None = None) -> None:
        """Partialization of :meth:`assert_block` for the :py3r:`re` flavor."""
        return self.assert_block(block, count=count, flavor='re')

    def assert_no_block(
        self, pattern: str | BlockPattern, /, *, context: int = 3, flavor: Flavor | None = None
    ) -> None:
        r"""Assert that there exist no matching blocks for the given patterns.

        :param pattern: The line patterns that a block must satisfy.
        :param context: Number of lines to print around a failing block.
        :param flavor: Optional temporary flavor for non-compiled patterns.

        By convention, the following are equivalent::

            matcher.assert_no_block('line1\nline2', ...)
            matcher.assert_no_block(['line1', 'line2'], ...)

        For simple usages, consider using the following flavor-binding aliases:

        .. default-role:: py3r

        +-----------+----------------------------------+
        | Flavor    | Alias                            |
        +===========+==================================+
        | `literal` | :meth:`assert_no_literal_block`  |
        +-----------+----------------------------------+
        | `re`      | :meth:`assert_no_matching_block` |
        +-----------+----------------------------------+

        .. default-role::

        .. seealso:: :attr:`Options.flavor <sphinx.testing.matcher.options.Options.flavor>`
        """
        # Normalize the patterns now so that we can have a nice debugging,
        # even if `to_block_pattern` is called in `iterfind` (it is a no-op
        # the second time).
        if patterns := _engine.to_block_pattern(pattern):
            blocks = self.iterfind_blocks(patterns, flavor=flavor)
            self.__assert_not_found('block', blocks, patterns, context, flavor)

    @final
    def assert_no_literal_block(self, block: BlockLike, /, *, context: int = 3) -> None:
        """Partialization of :meth:`assert_no_block` for the :py3r:`literal` flavor."""
        return self.assert_no_block(block, context=context, flavor='literal')

    @final
    def assert_no_matching_block(self, block: BlockLike, /, *, context: int = 3) -> None:
        """Partialization of :meth:`assert_no_block` for the :py3r:`re` flavor."""
        return self.assert_no_block(block, context=context, flavor='re')

    # private

    def __assert_found(
        self,
        typ: _RegionType,  # the region's type
        regions: Iterator[Region[Any]],  # the regions that were found
        patterns: Iterable[PatternLike],  # the patterns that were used (debug only)
        count: int | None,  # the expected number of regions
        flavor: Flavor | None,  # the flavor that was used to compile the patterns
    ) -> None:
        if count is None:
            if next(regions, None) is not None:
                return

            ctx = _util.highlight(self.lines(), keepends=self.keep_break)
            pat = self.__pformat_patterns(typ, patterns)
            logs = [f'{typ} pattern', pat, 'not found in', ctx]
            raise AssertionError('\n\n'.join(logs))

        indices = {region.offset: region.length for region in regions}
        if (found := len(indices)) == count:
            return

        ctx = _util.highlight(self.lines(), indices, keepends=self.keep_break)
        pat = self.__pformat_patterns(typ, patterns)
        noun = _util.plural_form(typ, count)
        logs = [f'found {found} != {count} {noun} matching', pat, 'in', ctx]
        raise AssertionError('\n\n'.join(logs))

    def __assert_not_found(
        self,
        typ: _RegionType,
        regions: Iterator[Region[Any]],
        patterns: Sequence[PatternLike],
        context: int,
        flavor: Flavor | None,
    ) -> None:
        if (region := next(regions, None)) is None:
            return

        pat = self.__pformat_patterns(typ, patterns)
        ctx = _util.get_context_lines(self.lines(), region, context)
        logs = [f'{typ} pattern', pat, 'found in', '\n'.join(ctx)]
        raise AssertionError('\n\n'.join(logs))

    def __pformat_patterns(self, typ: _RegionType, patterns: Iterable[PatternLike]) -> str:
        """Prettify the *patterns* as a string to print."""
        lines = (p if isinstance(p, str) else p.pattern for p in patterns)
        source = sorted(lines) if typ == 'line' else lines
        return _util.indent_source(source, highlight=False)

    def __compile(self, patterns: Iterable[PatternLike], flavor: Flavor | None) -> Patterns:
        flavor = self.flavor if flavor is None else flavor
        return _engine.compile(patterns, flavor=flavor)

    def __get_clean_lines(self) -> tuple[str, ...]:
        options = cast(Options, self.complete_options)
        return tuple(cleaner.clean(self.content, **options))
