"""Interface for comparing strings or list of strings."""

from __future__ import annotations

__all__ = ('Region', 'Line', 'Block')

import abc
import contextlib
import itertools
import re
from collections.abc import Sequence
from typing import TYPE_CHECKING, Generic, TypeVar, overload

from sphinx.testing.matcher._util import consume as _consume

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from typing import Any, Union

    from typing_extensions import Self, TypeAlias

    from sphinx.testing.matcher._util import LinePattern, LinePredicate, PatternLike

    SubStringLike: TypeAlias = PatternLike
    """A line's substring or a compiled substring pattern."""

    BlockLineLike: TypeAlias = Union[object, LinePattern, LinePredicate]
    """A block's line, a compiled pattern or a predicate."""

# We would like to have a covariant buffer type but Python does not
# support higher-kinded type, so we can only use an invariant type.
T = TypeVar('T', bound=Sequence[str])


class Region(Generic[T], Sequence[str], abc.ABC):
    """A string or a sequence of strings implementing rich comparison.

    Given an implicit *source* as a list of strings, a :class:`Region` is
    of that of that implicit *source* starting at some :attr:`offset`.
    """

    # add __weakref__ to allow the object being weak-referencable
    __slots__ = ('__buffer', '__offset', '__weakref__')

    def __init__(self, buffer: T, /, offset: int = 0, *, _check: bool = True) -> None:
        """Construct a :class:`Region` object.

        :param buffer: The region's content (a string or a list of strings).
        :param offset: The region's offset with respect to the original source.
        :param _check: An internal parameter used for validating inputs.

        The *_check* parameter is only meant for internal usage and strives
        to speed-up the construction of :class:`Region` objects for which
        their constructor arguments are known to be valid at call time.
        """
        if _check:
            if not isinstance(offset, int):
                msg = f'offset must be an integer, got: {offset!r}'
                raise TypeError(msg)

            if offset < 0:
                msg = f'offset must be >= 0, got: {offset!r}'
                raise ValueError(msg)

        self.__buffer = buffer
        self.__offset = offset

    @property
    def buffer(self) -> T:
        """The internal (immutable) buffer."""
        return self.__buffer

    @property
    def offset(self) -> int:
        """The index of this region in the original source."""
        return self.__offset

    @property
    def length(self) -> int:
        """The number of "atomic" items in this region."""
        return len(self)

    @property
    @abc.abstractmethod
    def span(self) -> slice:
        """A slice representing this region in its source."""

    def context(self, delta: int, limit: int) -> tuple[slice, slice]:
        """A slice object indicating a context around this region.

        :param delta: The number of context lines to show.
        :param limit: The number of lines in the source the region belongs to.
        :return: The slices for the 'before' and 'after' lines.

        Example::

            source = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
            block = Block(['4', '5', '6'], 3)
            before, after = block.context(2, 10)
            assert source[before] == ['2', '3']
            assert source[after] == ['7', '8']
        """
        assert delta >= 0, 'context size must be >= 0'
        assert limit >= 0, 'source length must be >= 0'

        span = self.span
        before_start, before_stop = max(0, span.start - delta), min(span.start, limit)
        before_slice = slice(before_start, before_stop)

        after_start, after_stop = min(span.stop, limit), min(span.stop + delta, limit)
        after_slice = slice(after_start, after_stop)

        return before_slice, after_slice

    @abc.abstractmethod
    # The 'value' is 'Any' so that subclasses do not violate Liskov's substitution principle
    def count(self, value: Any, /) -> int:
        """Count the number of occurences of matching item."""

    # The 'value' is 'Any' so that subclasses do not violate Liskov's substitution principle
    def index(self, value: Any, start: int = 0, stop: int | None = None, /) -> int:
        """Return the lowest index of a matching item.

        :raise ValueError: The value does not exist.
        """
        index = self.find(value, start, stop)
        if index == -1:
            raise ValueError(value)
        return index

    @abc.abstractmethod
    # The 'value' is 'Any' so that subclasses do not violate Liskov's substitution principle.
    def find(self, value: Any, start: int = 0, stop: int | None = None, /) -> int:
        """Return the lowest index of a matching item or *-1* on failure."""

    def pformat(self) -> str:
        """A nice representation of this region."""
        return f'{self.__class__.__name__}({self!r}, @={self.offset}, #={self.length})'

    def __repr__(self) -> str:
        return repr(self.buffer)

    def __copy__(self) -> Self:
        return self.__class__(self.buffer, self.offset, _check=False)

    def __bool__(self) -> bool:
        """Indicate whether this region is empty or not."""
        return bool(self.buffer)

    def __iter__(self) -> Iterator[str]:
        """An iterator over the string items."""
        return iter(self.buffer)

    def __len__(self) -> int:
        """The number of "atomic" items in this region."""
        return len(self.buffer)

    def __contains__(self, value: object, /) -> bool:
        """Check that an "atomic" value is represented by this region."""
        return value in self.buffer or self.find(value) != -1

    @abc.abstractmethod
    def __lt__(self, other: object, /) -> bool:
        """Check that this region is strictly contained in *other*."""

    def __le__(self, other: object, /) -> bool:
        """Check that this region is contained in *other*.

        By default, ``self == other`` is called before ``self < other``, but
        subclasses should override this method  for an efficient alternative.
        """
        return self == other or self < other

    def __ge__(self, other: object, /) -> bool:
        """Check that *other* is contained by this region.

        By default, ``self == other`` is called before ``self > other``, but
        subclasses should override this method  for an efficient alternative.
        """
        return self == other or self > other

    @abc.abstractmethod
    def __gt__(self, other: object, /) -> bool:
        """Check that this region strictly contains *other*."""


class Line(Region[str]):
    """A line found by :meth:`.LineMatcher.find`.

    A :class:`Line` can be compared to:

    - a :class:`str`, in which case the :attr:`text <.buffer>` is compared,
    - a pair ``(line_content, line_offset)`` where *line_content* is a string
      and *line_offset* is an nonnegative integer, or another :class:`Line`,
      in which case both the offset and the content must match.
    """

    # NOTE(picnixz): this class could be extended to support arbitrary
    # character's types, but it would not be possible to use the C API
    # implementing the :class:`str` interface anymore.

    def __init__(self, line: str = '', /, offset: int = 0, *, _check: bool = True) -> None:
        """Construct a :class:`Line` object."""
        super().__init__(line, offset, _check=_check)

    @property
    def span(self) -> slice:
        """A slice representing this line in its source.

        Example::

            source = ['L1', 'L2', 'L3']
            line = Line('L2', 1)
            assert source[line.span] == ['L2']
        """
        return slice(self.offset, self.offset + 1)

    def count(self, sub: SubStringLike, /) -> int:
        """Count the number of occurrences of a substring or pattern.

        :raise TypeError: *sub* is not a string or a compiled pattern.
        """
        if isinstance(sub, re.Pattern):
            # avoid using sub.findall() since we only want the length
            # of the corresponding iterator (the following lines are
            # more efficient from a memory perspective)
            counter = itertools.count()
            _consume(zip(sub.finditer(self.buffer), counter))
            return next(counter)

        # buffer.count() raises a TypeError if *sub* is not a string
        return self.buffer.count(sub)

    # explicitly add the method since its signature differs from :meth:`Region.index`
    def index(self, sub: SubStringLike, start: int = 0, stop: int | None = None, /) -> int:
        """Find the lowest index of a substring.

        :raise TypeError: *sub* is not a string or a compiled pattern.
        """
        return super().index(sub, start, stop)

    def find(self, sub: SubStringLike, start: int = 0, stop: int | None = None, /) -> int:
        """Find the lowest index of a substring or *-1* on failure.

        :raise TypeError: *sub* is not a string or a compiled pattern.
        """
        if isinstance(sub, re.Pattern):
            # Do not use sub.search(buffer, start, end) since the '^' pattern
            # character matches at the *real* beginning of *buffer* but *not*
            # necessarily at the index where the search is to start.
            #
            # Ref: https://docs.python.org/3/library/re.html#re.Pattern.search
            if match := sub.search(self.buffer[start:stop]):
                # normalize the start position
                start_index, _, _ = slice(start, stop).indices(self.length)
                return match.start() + start_index
            return -1

        # buffer.find() raises a TypeError if *sub* is not a string
        return self.buffer.find(sub, start, stop)

    def startswith(self, prefix: str, start: int = 0, end: int | None = None, /) -> bool:
        """Test whether the line starts with the given *prefix*.

        :param prefix: A line prefix to test.
        :param start: The test start position.
        :param end: The test stop position.
        """
        return self.buffer.startswith(prefix, start, end)

    def endswith(self, suffix: str, start: int = 0, end: int | None = None, /) -> bool:
        """Test whether the line ends with the given *suffix*.

        :param suffix: A line suffix to test.
        :param start: The test start position.
        :param end: The test stop position.
        """
        return self.buffer.endswith(suffix, start, end)

    def __str__(self) -> str:
        """The line as a string."""
        return self.buffer

    def __getitem__(self, index: int | slice, /) -> str:
        return self.buffer[index]

    def __eq__(self, other: object, /) -> bool:
        if isinstance(other, str):
            return self.buffer == other

        other = _parse_non_string(other)
        if other is None:
            return NotImplemented

        # separately check offsets before the buffers for efficiency
        return self.offset == other[1] and self.buffer == other[0]

    def __lt__(self, other: object, /) -> bool:
        if isinstance(other, str):
            return self.buffer < other

        other = _parse_non_string(other)
        if other is None:
            return NotImplemented

        # separately check offsets before the buffers for efficiency
        return self.offset == other[1] and self.buffer < other[0]

    def __gt__(self, other: object, /) -> bool:
        if isinstance(other, str):
            return self.buffer > other

        other = _parse_non_string(other)
        if other is None:
            return NotImplemented

        # separately check offsets before the buffers for efficiency
        return self.offset == other[1] and self.buffer > other[0]


class Block(Region[tuple[str, ...]]):
    """Block found by :meth:`.LineMatcher.find_blocks`.

    A block is a *sequence* of lines comparable to :class:`Line` objects,
    usually given as :class:`str` objects or ``(line, line_offset)`` pairs.

    A block can be compared to pairs ``(block_lines, block_offset)`` where

    - *block_lines* is a sequence of line-like objects, and
    - *block_offset* is an integer (matched against :attr:`.offset`).

    Pairs ``(line, line_offset)`` or ``(block_lines, block_offset)`` are to
    be given as any two-elements sequences (tuple, list, deque, ...), e.g.::

        assert Block(['a', 'b', 'c', 'd'], 2) == [
            'a',
            ('b', 3),
            ['c', 4],
            Line('d', 5),
        ]

    By convention, ``block[i]`` and ``block[i:j]`` return :class:`str`
    and tuples of :class:`str` respectively. Consider using :meth:`at`
    to convert the output to :class:`Line` or :class:`Block` objects.

    Similarly, ``iter(block)`` returns an iterator on strings. Consider
    using :meth:`lines_iterator` to iterate over :class:`Line` objects.
    """

    __slots__ = ('__cached_lines',)

    def __init__(
        self, buffer: Iterable[str] = (), /, offset: int = 0, *, _check: bool = True
    ) -> None:
        # It is more efficient to first consume everything and then
        # iterate over the values for checks rather than to add the
        # validated values one by one.
        buffer = tuple(buffer)
        if _check:
            for line in buffer:
                if not isinstance(line, str):
                    err = f'expecting a native string, got: {line!r}'
                    raise TypeError(err)

        super().__init__(buffer, offset, _check=_check)
        self.__cached_lines: tuple[Line, ...] | None = None
        """This block as a tuple of :class:`Line` objects.

        The rationale behind duplicating the buffer's data is to ease
        comparison by relying on the C API for comparing tuples which
        dispatches to the :class:`Line` comparison operators.
        """

    @property
    def span(self) -> slice:
        """A slice representing this block in its source.

        Example::

            source = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
            block = Block(['4', '5', '6'], 3)
            assert source[block.span] == ['4', '5', '6']
        """
        return slice(self.offset, self.offset + self.length)

    def count(self, target: BlockLineLike, /) -> int:
        """Count the number of occurrences of matching lines.

        For :class:`~re.Pattern` inputs, the following are equivalent::

            block.count(target)
            block.count(target.match)
        """
        if isinstance(target, re.Pattern):
            # Apply the pattern to the entire line unlike :class:`Line`
            # objects that detect non-overlapping matching substrings.
            return self.count(target.match)

        if callable(target):
            counter = itertools.count()
            _consume(zip(filter(target, self.buffer), counter))
            return next(counter)

        return self.buffer.count(target)

    # explicitly add the method since its signature differs from :meth:`Region.index`
    def index(self, target: BlockLineLike, start: int = 0, stop: int | None = None, /) -> int:
        """Find the lowest index of a matching line.

        For :class:`~re.Pattern` inputs, the following are equivalent::

            block.index(target, ...)
            block.index(target.match, ...)
        """
        return super().index(target, start, stop)

    def find(self, target: BlockLineLike, start: int = 0, stop: int | None = None, /) -> int:
        """Find the lowest index of a matching line or *-1* on failure.

        For :class:`~re.Pattern` inputs, the following are equivalent::

            block.find(target, ...)
            block.find(target.match, ...)
        """
        if isinstance(target, re.Pattern):
            return self.find(target.match, start, stop)

        if callable(target):
            start, stop, _ = slice(start, stop).indices(self.length)
            sliced = itertools.islice(self.buffer, start, stop)
            return next(itertools.compress(itertools.count(start), map(target, sliced)), -1)

        with contextlib.suppress(ValueError):
            if stop is None:
                return self.buffer.index(target, start)
            return self.buffer.index(target, start, stop)
        return -1

    def lines(self) -> tuple[Line, ...]:
        """This region as a tuple of :class:`Line` objects."""
        if self.__cached_lines is None:
            self.__cached_lines = tuple(self.lines_iterator())
        return self.__cached_lines

    def lines_iterator(self) -> Iterator[Line]:
        """This region as an iterator of :class:`Line` objects."""
        for index, line in enumerate(self, self.offset):
            yield Line(line, index, _check=False)

    @overload
    def at(self, index: int, /) -> Line: ...  # NoQA: E704
    @overload
    def at(self, index: slice, /) -> Self: ...  # NoQA: E704
    def at(self, index: int | slice, /) -> Line | Block:  # NoQA: E301
        """Get a :class:`Line` or a contiguous region as a :class:`Block`."""
        if isinstance(index, slice):
            # exception for invalid step is handled by __getitem__
            buffer = self[index]
            offset = self.offset + index.indices(self.length)[0]
            return self.__class__(buffer, offset, _check=False)

        # normalize negative index
        start, _, _ = slice(index, -1).indices(self.length)
        return Line(self.buffer[index], self.offset + start, _check=False)

    @overload
    def __getitem__(self, index: int, /) -> str: ...  # NoQA: E704
    @overload
    def __getitem__(self, index: slice, /) -> tuple[str, ...]: ...  # NoQA: E704
    def __getitem__(self, index: int | slice, /) -> str | tuple[str, ...]:  # NoQA: E301
        """Get a line or a contiguous sub-block."""
        if isinstance(index, slice):
            # normalize negative and None slice fields
            _, _, step = index.indices(self.length)
            if step != 1:
                msg = 'only contiguous regions can be extracted'
                raise ValueError(msg)
        return self.buffer[index]

    def __eq__(self, other: object, /) -> bool:
        if isinstance(other, self.__class__):
            # more efficient to first check the offsets
            return (self.offset, self.buffer) == (other.offset, other.buffer)

        other = _parse_non_block(other)
        if other is None:
            return NotImplemented

        lines, offset = other
        # check offsets before computing len(lines)
        if offset != -1 and offset != self.offset:
            return False

        # check the lengths before computing the cached lines if possible
        return self.length == len(lines) and self.lines() == lines

    def __lt__(self, other: object, /) -> bool:
        if isinstance(other, self.__class__):
            # More efficient to first check if the indices are valid before
            # checking the lines using tuple comparisons (both objects have
            # compatible types at runtime).
            aligned = _can_be_strict_in(self.offset, self.length, other.offset, other.length)
            return aligned and self.buffer < other.buffer

        other = _parse_non_block(other)
        if other is None:
            return NotImplemented

        lines, other_offset = other
        if other_offset != -1:
            aligned = _can_be_strict_in(self.offset, self.length, other_offset, len(lines))
            return aligned and self.lines() < lines
        # we want to find this block in the *other* block (at any place)
        return self.lines() < lines

    def __gt__(self, other: object, /) -> bool:
        if isinstance(other, self.__class__):
            return other < self

        other = _parse_non_block(other)
        if other is None:
            return NotImplemented

        lines, other_offset = other
        if other_offset != -1:
            aligned = _can_be_strict_in(other_offset, len(lines), self.offset, self.length)
            return aligned and self.lines() > lines
        return self.lines() > lines


# Those functions are private and are not included in :class:`Line`
# or :class:`Block` to minimize the size of the class dictionary.


def _parse_non_string(other: object, /) -> tuple[str, int] | None:
    """Try to parse *other* as a ``(line_content, line_offset)`` pair.

    Do **NOT** call this method on :class:`str` instances since they are
    handled separately and more efficiently by :class:`Line`'s operators.
    """
    assert not isinstance(other, str)
    if isinstance(other, Line):
        return other.buffer, other.offset
    if isinstance(other, Sequence) and len(other) == 2:
        buffer, offset = other
        if isinstance(buffer, str) and isinstance(offset, int):
            return buffer, offset
    return None


def _is_block_line_like(other: object, /) -> bool:
    if isinstance(other, (str, Line)):
        return True

    if isinstance(other, Sequence) and len(other) == 2:
        buffer, offset = other
        if isinstance(buffer, str) and isinstance(offset, int):
            return True

    return False


def _parse_non_block(other: object, /) -> tuple[tuple[object, ...], int] | None:
    """Try to parse *other* as a pair ``(block lines, block offset)``.

    Do **NOT** call this method on :class:`Block` instances since they are
    handled separately and more efficiently by :class:`Block`'s operators.
    """
    assert not isinstance(other, Block)
    if not isinstance(other, Sequence):
        return None

    if all(map(_is_block_line_like, other)):
        # offset will never be given in this scenario
        return tuple(other), -1

    if len(other) == 2:
        lines, offset = other
        if not isinstance(lines, Sequence) or not isinstance(offset, int):
            return None

        if isinstance(lines, str):
            # do not allow [line, offset] with single string 'line'
            return None

        if not all(map(_is_block_line_like, lines)):
            return None

        return tuple(lines), offset

    return None


def _can_be_strict_in(i1: int, l1: int, i2: int, l2: int) -> bool:
    """Check that a block can be strictly contained in another block.

    :param i1: The address (index) of the first block.
    :param l1: The length of the first block.
    :param i2: The address (index) of the second block.
    :param l2: The length of the second block.
    """
    j1, j2 = i1 + l1, i2 + l2
    # Case 1: i1 == i2 and j1 < j2 (block1 is at most block2[:-1])
    # Case 2: i1 > i2 and j1 <= j2 (block1 is at most block2[1:])
    return l1 < l2 and ((i1 >= i2) and (j1 < j2) or (i1 > i2) and (j1 <= j2))
