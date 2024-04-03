from __future__ import annotations

__all__ = ('Line', 'Block')

import abc
import contextlib
import itertools
import operator
import re
import sys
from collections.abc import Sequence
from typing import TYPE_CHECKING, Generic, TypeVar, final, overload

from sphinx.testing._matcher import util

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator
    from typing import Any, Union

    from typing_extensions import Self

    LineText = Union[str, re.Pattern[str]]
    """A line's substring or a compiled substring pattern."""

    BlockMatch = Union[object, str, re.Pattern[str], Callable[[str], object]]
    """A block's line, a compiled pattern or a predicate."""

_T = TypeVar('_T', bound=Sequence[str])


class SourceView(Generic[_T], Sequence[str], abc.ABC):
    """A string or a sequence of strings implementing rich comparison.

    Given an implicit *source* as a list of strings, a :class:`SourceView`
    is a subset  of that implicit *source* starting at some :attr:`offset`.

    :meta private:
    """

    __tracebackhide__: bool = True
    """A flag to hide the traceback frames in pytest output."""

    # add __weakref__ to allow the object being weak-referencable
    __slots__ = ('__buffer', '__offset', '__weakref__')

    def __init__(self, buffer: _T, /, offset: int = 0, *, _check: bool = True) -> None:
        """Construct a :class:`SourceView`.

        :param buffer: The view's content (a string or a list of strings).
        :param offset: The view's offset with respect to the original source.
        :param _check: An internal parameter used for validating inputs.

        The *_check* parameter is only meant for internal usage and strives
        to speed-up the construction of :class:`SourceView` objects for which
        their constructor arguments are known to be valid at call time.
        """
        __tracebackhide__ = self.__tracebackhide__
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
    def buffer(self) -> _T:
        """The internal (immutable) buffer."""
        return self.__buffer

    @property
    def offset(self) -> int:
        """The index of this object in the original source."""
        return self.__offset

    @property
    def length(self) -> int:
        """The number of items in this object."""
        return len(self)

    def pformat(self) -> str:
        """A nice representation of this object."""
        return '{0.__class__.__name__}({0!r}, @={0.offset}, #={0.length})'.format(self)

    @abc.abstractmethod
    # The 'value' is 'Any' so that subclasses do not violate Liskov's substitution principle
    def count(self, value: Any, /) -> int:
        """Count the number of occurences of matching item."""

    # The 'value' is 'Any' so that subclasses do not violate Liskov's substitution principle
    def index(self, value: Any, start: int = 0, stop: int = sys.maxsize, /) -> int:
        """Return the lowest index of a matching item.

        :raise ValueError: The value does not exist.

        .. seealso:: :meth:`find`
        """
        __tracebackhide__ = self.__tracebackhide__
        index = self.find(value, start, stop)
        if index == -1:
            raise ValueError(value)
        return index

    @abc.abstractmethod
    # The 'value' is 'Any' so that subclasses do not violate Liskov's substitution principle.
    def find(self, value: Any, start: int = 0, stop: int = sys.maxsize, /) -> int:
        """Return the lowest index of a matching item or *-1* on failure.

        .. seealso:: :meth:`index`
        """

    def __repr__(self) -> str:
        return repr(self.buffer)

    def __copy__(self) -> Self:
        return self.__class__(self.buffer, self.offset, _check=False)

    def __bool__(self) -> bool:
        """Indicate whether this view is empty or not."""
        return bool(len(self))

    @final
    def __iter__(self) -> Iterator[str]:
        """An iterator over the string items."""
        return iter(self.buffer)

    def __len__(self) -> int:
        """The number of "atomic" items in this view."""
        return len(self.buffer)

    def __contains__(self, value: object, /) -> bool:
        """Check that an "atomic" value is represented by this view."""
        return value in self.buffer or self.find(value) != -1

    @abc.abstractmethod
    def __lt__(self, other: object, /) -> bool:
        """Check that this view is strictly contained in *other*.

        Subclasses implementing the :class:`SourceView` interface
        should describe the expected types for *object*.
        """

    def __le__(self, other: object, /) -> bool:
        """Check that this view is contained in *other*.

        By default, ``self == other`` is called before ``self < other``, but
        subclasses should override this method  for an efficient alternative.
        """
        __tracebackhide__ = self.__tracebackhide__
        return self == other or self < other

    def __ge__(self, other: object, /) -> bool:
        """Check that *other* is contained by this view.

        By default, ``self == other`` is called before ``self > other``, but
        subclasses should override this method  for an efficient alternative.
        """
        __tracebackhide__ = self.__tracebackhide__
        return self == other or self > other

    @abc.abstractmethod
    def __gt__(self, other: object, /) -> bool:
        """Check that this view strictly contains *other*.

        Subclasses implementing the :class:`SourceView` interface
        should describe the expected types for *object*.
        """


@final
class Line(SourceView[str]):
    """A line found by :meth:`~sphinx.testing.matcher.LineMatcher.match`.

    A :class:`Line` can be compared to :class:`str`, :class:`Line` objects or
    a pair (i.e., a two-length sequence) ``(line, line_offset)`` where

    - *line* is a :class:`str` object, and
    - *line_offset* is an nonnegative integer.

    By convention, the comparison result (except for ``!=``) of :class:`Line`
    objects with distinct :attr:`offset` is always ``False``. Use :class:`str`
    objects instead if the offset is not relevant.
    """

    # NOTE(picnixz): this class could be extended to support arbitrary
    # character's types, but it would not be possible to use the C API
    # implementing the :class:`str` interface anymore.

    def __init__(self, line: str = '', /, offset: int = 0, *, _check: bool = True) -> None:
        """Construct a :class:`Line` object."""
        __tracebackhide__ = self.__tracebackhide__
        super().__init__(line, offset, _check=_check)

    @classmethod
    def view(cls, index: int, line: str, /, *, _check: bool = True) -> Self:
        """Alternative constructor flipping the order of the arguments.

        This is typically useful with :func:`enumerate`, namely this makes::

            from itertools import starmap
            lines = list(starmap(Line.view, enumerate(src))

        equivalent to::

            def cast(line: object) -> str:
                return line if isinstance(line, str) else str(line)

            lines = [Line(cast(line), index) for index, line in enumerate(src)]
        """
        __tracebackhide__ = cls.__tracebackhide__
        line = line if isinstance(line, str) else str(line)
        return cls(line, index, _check=_check)

    # dunder methods

    def __str__(self) -> str:
        """The line as a string."""
        return self.buffer

    def __getitem__(self, index: int | slice, /) -> str:
        __tracebackhide__ = self.__tracebackhide__
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
        __tracebackhide__ = self.__tracebackhide__

        if isinstance(other, str):
            return self.buffer < other

        other = _parse_non_string(other)
        if other is None:
            return NotImplemented

        # separately check offsets before the buffers for efficiency
        return self.offset == other[1] and self.buffer < other[0]

    def __gt__(self, other: object, /) -> bool:
        __tracebackhide__ = self.__tracebackhide__

        if isinstance(other, str):
            return self.buffer > other

        other = _parse_non_string(other)
        if other is None:
            return NotImplemented

        # separately check offsets before the buffers for efficiency
        return self.offset == other[1] and self.buffer > other[0]

    def startswith(self, prefix: str, start: int = 0, end: int = sys.maxsize, /) -> bool:
        """Test whether the line starts with the given *prefix*.

        :param prefix: A line prefix to test.
        :param start: The test start position.
        :param end: The test stop position.
        """
        __tracebackhide__ = self.__tracebackhide__
        return self.buffer.startswith(prefix, start, end)

    def endswith(self, suffix: str, start: int = 0, end: int = sys.maxsize, /) -> bool:
        """Test whether the line ends with the given *suffix*.

        :param suffix: A line suffix to test.
        :param start: The test start position.
        :param end: The test stop position.
        """
        __tracebackhide__ = self.__tracebackhide__
        return self.buffer.endswith(suffix, start, end)

    def count(self, sub: LineText, /) -> int:
        """Count the number of occurrences of a substring or pattern.

        :raise TypeError: *sub* is not a string or a compiled pattern.
        """
        if isinstance(sub, re.Pattern):
            # avoid using value.findall() since we only want the length
            # of the corresponding iterator (the following lines are more
            # efficient from a memory perspective)
            counter = itertools.count()
            util.consume(zip(sub.finditer(self.buffer), counter))
            return next(counter)

        __tracebackhide__ = self.__tracebackhide__
        return self.buffer.count(sub)  # raise a TypeError if *sub* is not a string

    # explicitly add the method since its signature differs from :meth:`SourceView.index`
    def index(self, sub: LineText, start: int = 0, stop: int = sys.maxsize, /) -> int:
        """Find the lowest index of a substring.

        :raise TypeError: *sub* is not a string or a compiled pattern.
        """
        __tracebackhide__ = self.__tracebackhide__
        return super().index(sub, start, stop)

    def find(self, sub: LineText, start: int = 0, stop: int = sys.maxsize, /) -> int:
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

        __tracebackhide__ = self.__tracebackhide__
        return self.buffer.find(sub, start, stop)  # raise a TypeError if *sub* is not a string


@final
class Block(SourceView[tuple[str, ...]], Sequence[str]):
    """Block found by :meth:`~sphinx.testing.matcher.LineMatcher.find`.

    A block is a sequence of lines comparable to :class:`Line`, generally a
    string (the line content) or a pair ``(line, line_offset)``. In addition,
    a block can be compared to pair ``(block_lines, block_offset)`` where:

    - *block_lines* is a sequence of lines-like objects, and
    - *block_offset* is an integer (matched against :attr:`offset`).

    Whenever a pair ``(line, line_offset)`` or ``(block, block_offset)``
    is needed, it can be any two-element sequence (e.g., tuple or list).

    For instance,::

        assert Block(['a', 'b', 'c'], 2) == ['a', ('b', 3), Line('c', 4)]

    .. note::

       By convention, ``block[i]`` or ``block[i:j]`` returns :class:`str`
       or sequences of :class:`str`. Consider using :meth:`at` to get the
       corresponding :class:`Line` or :class:`Block` values.
    """

    __slots__ = ('__cached_lines',)

    def __init__(
        self, buffer: Iterable[str] = (), /, offset: int = 0, *, _check: bool = True
    ) -> None:
        __tracebackhide__ = self.__tracebackhide__
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
        self.__cached_lines: list[object] | None = None

    @classmethod
    def view(cls, index: int, buffer: Iterable[str], /, *, _check: bool = True) -> Self:
        """Alternative constructor flipping the order of the arguments.

        This is typically useful with :func:`enumerate`, namely this makes::

            from itertools import starmap
            blocks = list(starmap(Block.view, enumerate(src))

        equivalent to::

            blocks = [Block(lines, index) for index, lines in enumerate(src)]
        """
        __tracebackhide__ = cls.__tracebackhide__
        return cls(buffer, index, _check=_check)

    @property
    def window(self) -> slice:
        """A slice representing this block in its source.

        If *source* is the original source this block is contained within,
        then ``assert source[block.window] == block`` is satisfied.

        Example::

            source = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
            block = Block(['4', '5', '6'], 3)
            assert source[block.window] == ['4', '5', '6']
        """
        return slice(self.offset, self.offset + self.length)

    def context(self, delta: int, limit: int) -> tuple[slice, slice]:
        """A slice object indicating a context around this block.

        :param delta: The number of context lines to show.
        :param limit: The number of lines in the source the block belongs to.
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

        before_start, before_stop = max(0, self.offset - delta), min(self.offset, limit)
        before_slice = slice(before_start, before_stop)

        block_stop = self.offset + self.length
        after_start, after_stop = min(block_stop, limit), min(block_stop + delta, limit)
        after_slice = slice(after_start, after_stop)

        return before_slice, after_slice

    def count(self, target: BlockMatch, /) -> int:
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
            util.consume(zip(filter(target, self.buffer), counter))
            return next(counter)

        return self.buffer.count(target)

    # explicitly add the method since its signature differs from :meth:`SourceView.index`
    def index(self, target: BlockMatch, start: int = 0, stop: int = sys.maxsize, /) -> int:
        """Find the lowest index of a matching line.

        For :class:`~re.Pattern` inputs, the following are equivalent::

            block.index(target, ...)
            block.index(target.match, ...)
        """
        __tracebackhide__ = self.__tracebackhide__
        return super().index(target, start, stop)

    def find(self, target: BlockMatch, start: int = 0, stop: int = sys.maxsize, /) -> int:
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
            return self.buffer.index(target, start, stop)
        return -1

    # fmt: off
    @overload
    def at(self, index: int, /) -> Line: ...  # NoQA: E704
    @overload
    def at(self, index: slice, /) -> Self: ...  # NoQA: E704
    # fmt: on
    def at(self, index: int | slice, /) -> Line | Block:  # NoQA: E301
        """Get a :class:`Line` or a contiguous sub-:class:`Block`."""
        if isinstance(index, slice):
            # exception for invalid step is handled by __getitem__
            buffer = self[index]
            offset = self.offset + index.indices(self.length)[0]
            return self.__class__(buffer, offset, _check=False)

        # normalize negative index
        start, _, _ = slice(index, -1).indices(self.length)
        return Line(self.buffer[index], self.offset + start, _check=False)

    # fmt: off
    @overload
    def __getitem__(self, index: int, /) -> str: ...  # NoQA: E704
    @overload
    def __getitem__(self, index: slice, /) -> Sequence[str]: ...  # NoQA: E704
    # fmt: on
    def __getitem__(self, index: int | slice, /) -> str | Sequence[str]:  # NoQA: E301
        """Get a line or a contiguous sub-block."""
        __tracebackhide__ = self.__tracebackhide__
        if isinstance(index, slice):
            # normalize negative and None slice fields
            _, _, step = index.indices(self.length)
            if step != 1:
                msg = 'only contiguous regions can be extracted'
                raise ValueError(msg)
        return self.buffer[index]

    def __eq__(self, other: object, /) -> bool:
        __tracebackhide__ = self.__tracebackhide__

        if isinstance(other, self.__class__):
            # more efficient to first check the offsets
            return (self.offset, self.buffer) == (other.offset, other.buffer)

        other = _parse_non_block(other)
        if other is None:
            return NotImplemented

        lines, offset = other
        # check offsets before computing len(lines) or len(self)
        if offset != -1 and offset != self.offset:
            return False

        if len(lines) == self.length:
            # match the lines one by one, possibly using a rich comparison
            expect = self.__lines_iterator()
            return all(map(operator.__eq__, expect, lines))
        return False

    def __lt__(self, other: object, /) -> bool:
        __tracebackhide__ = self.__tracebackhide__

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
            return aligned and self.__lines() < lines
        # we want to find this block in the *other* block (at any place)
        return self.__lines() < lines

    def __gt__(self, other: object, /) -> bool:
        __tracebackhide__ = self.__tracebackhide__

        if isinstance(other, self.__class__):
            return other < self

        other = _parse_non_block(other)
        if other is None:
            return NotImplemented

        lines, other_offset = other
        if other_offset != -1:
            aligned = _can_be_strict_in(other_offset, len(lines), self.offset, self.length)
            return aligned and self.__lines() > lines
        return self.__lines() > lines

    # Do not annotate with list[Line] since otherwise mypy complains
    # when comparing with a right-hand side that is a list of objects.
    def __lines(self) -> list[object]:
        """This block as a list of :class:`Line` objects."""
        if self.__cached_lines is None:
            self.__cached_lines = list(self.__lines_iterator())
        return self.__cached_lines

    def __lines_iterator(self) -> Iterator[Line]:
        """This block as a list of :class:`Line` objects."""
        for index, line in enumerate(self, self.offset):
            yield Line(line, index, _check=False)


def _parse_non_string(other: object, /) -> tuple[str, int] | None:
    """Try to parse *other* as a ``line`` or a ``(line, offset)`` pair.

    For efficiency, do *not* call this method on :class:`str` instances
    since they will be handled separately more efficiently.
    """
    if isinstance(other, Line):
        return other.buffer, other.offset
    if isinstance(other, Sequence) and len(other) == 2:
        buffer, offset = other
        if isinstance(buffer, str) and isinstance(offset, int):
            return buffer, offset
    return None


def _is_block_line_compatible(other: object, /) -> bool:
    if isinstance(other, (str, Line)):
        return True

    if isinstance(other, Sequence) and len(other) == 2:
        buffer, offset = other
        if isinstance(buffer, str) and isinstance(offset, int):
            return True

    return False


def _parse_non_block(other: object, /) -> tuple[list[object], int] | None:
    """Try to parse *other* as a pair ``(block lines, block offset)``.

    For efficiency, do *not* call this method on :class:`Block` instances
    since they will be handled separately more efficiently.
    """
    if not isinstance(other, Sequence):
        return None

    if all(map(_is_block_line_compatible, other)):
        # offset will never be given in this scenario
        return list(other), -1

    if len(other) == 2:
        lines, offset = other
        if not isinstance(lines, Sequence) or not isinstance(offset, int):
            return None

        if isinstance(lines, str):
            # do not allow [line, offset] with single string 'line'
            return None

        if not all(map(_is_block_line_compatible, lines)):
            return None

        return list(lines), offset

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
