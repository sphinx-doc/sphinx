from __future__ import annotations

__all__ = ('Line', 'Block')

import abc
import itertools
import operator
from collections.abc import Sequence
from typing import TYPE_CHECKING, Generic, TypeVar, final, overload

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from typing_extensions import Self

_T = TypeVar('_T', bound=Sequence[str])


class SourceView(Generic[_T], abc.ABC):
    """A string or a sequence of strings implementing rich comparison.

    Given an implicit *source* as a list of strings, a :class:`SourceView`
    is a subset  of that implicit *source* starting at some :attr:`offset`.

    :meta private:
    """

    # add __weakref__ to allow the object being weak-referencable
    __slots__ = ('__buffer', '__offset', '__weakref__')

    def __init__(self, buffer: _T, offset: int = 0, /, *, _check: bool = True) -> None:
        """Construct a :class:`SourceView`.

        :param buffer: The view's content (a string or a list of strings).
        :param offset: The view's offset with respect to the original source.
        :param _check: An internal parameter used for validating inputs.

        The *_check* parameter is only meant for internal usage and strives
        to speed-up the construction of :class:`SourceView` objects for which
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

    def __repr__(self) -> str:
        return repr(self.buffer)

    def __copy__(self) -> Self:
        return self.__class__(self.buffer, self.offset, _check=False)

    def __bool__(self) -> bool:
        """Indicate whether this view is empty or not."""
        return bool(len(self))

    def __iter__(self) -> Iterator[str]:
        """An iterator over the view's items."""
        return iter(self.buffer)

    def __len__(self) -> int:
        """The number of "atomic" items in this view."""
        return len(self.buffer)

    def __contains__(self, value: object, /) -> bool:
        """Check that an "atomic" value is represented by this view."""
        return value in self.buffer

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
        return self == other or self < other

    def __ge__(self, other: object, /) -> bool:
        """Check that *other* is contained by this view.

        By default, ``self == other`` is called before ``self > other``, but
        subclasses should override this method  for an efficient alternative.
        """
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

    def __init__(self, line: str = '', offset: int = 0, /, *, _check: bool = True) -> None:
        """Construct a :class:`Line` object."""
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
        line = line if isinstance(line, str) else str(line)
        return cls(line, index, _check=_check)

    # dunder methods

    def __str__(self) -> str:
        """The line as a string."""
        return self.buffer

    def __getitem__(self, index: int | slice, /) -> str:
        return self.buffer[index]

    def __eq__(self, other: object, /) -> bool:
        if isinstance(other, str):
            return self.buffer == other

        other = self.__parse_non_string(other)
        if other is None:
            return NotImplemented

        # separately check offsets before the buffers for efficiency
        return self.offset == other[1] and self.buffer == other[0]

    def __lt__(self, other: object, /) -> bool:
        if isinstance(other, str):
            return self.buffer < other

        other = self.__parse_non_string(other)
        if other is None:
            return NotImplemented

        # separately check offsets before the buffers for efficiency
        return self.offset == other[1] and self.buffer < other[0]

    def __gt__(self, other: object, /) -> bool:
        if isinstance(other, str):
            return self.buffer > other

        other = self.__parse_non_string(other)
        if other is None:
            return NotImplemented

        # separately check offsets before the buffers for efficiency
        return self.offset == other[1] and self.buffer > other[0]

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

    def count(self, sub: str, start: int = 0, end: int | None = None, /) -> int:
        """Count the number of non-overlapping occurrences of a substring.

        :param sub: A substring to locate.
        :param start: The test start position.
        :param end: The test stop position.
        """
        return self.buffer.count(sub, start, end)

    def index(self, sub: str, start: int = 0, end: int | None = None, /) -> int:
        """Get the lowest index of the substring *sub* in ``self[start:end]``.

        :raise ValueError: The substring is not found in ``self[start:end]``.

        .. seealso:: :meth:`find`
        """
        return self.buffer.index(sub, start, end)

    def rindex(self, sub: str, start: int = 0, end: int | None = None, /) -> int:
        """Get the highest index of the substring *sub* in ``self[start:end]``.

        :raise ValueError: The substring is not found in ``self[start:end]``.

        .. seealso:: :meth:`rfind`
        """
        return self.buffer.rindex(sub, start, end)

    def find(self, sub: str, start: int = 0, end: int | None = None, /) -> int:
        """Get the lowest index of the substring *sub* in ``self[start:end]``.

        If the substring is not found, this returns ``-1``.

        .. seealso:: :meth:`index`
        """
        return self.buffer.find(sub, start, end)

    def rfind(self, sub: str, start: int = 0, end: int | None = None, /) -> int:
        """Get the highest index of the substring *sub* in ``self[start:end]``.

        If the substring is not found, this returns ``-1``.

        .. seealso:: :meth:`rindex`
        """
        return self.buffer.rfind(sub, start, end)

    def __parse_non_string(self, other: object, /) -> tuple[str, int] | None:
        """Try to parse *other* as a ``line`` or a ``(line, offset)`` pair."""
        if isinstance(other, self.__class__):
            return other.buffer, other.offset
        if isinstance(other, Sequence) and len(other) == 2:
            buffer, offset = other
            if isinstance(buffer, str) and isinstance(offset, int):
                return buffer, offset
        return None


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

    def __init__(
        self, buffer: Iterable[str] = (), offset: int = 0, /, *, _check: bool = True
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

    @classmethod
    def view(cls, index: int, buffer: Iterable[str], /, *, _check: bool = True) -> Self:
        """Alternative constructor flipping the order of the arguments.

        This is typically useful with :func:`enumerate`, namely this makes::

            from itertools import starmap
            blocks = list(starmap(Block.view, enumerate(src))

        equivalent to::

            blocks = [Block(lines, index) for index, lines in enumerate(src)]
        """
        return cls(buffer, index, _check=_check)

    @property
    def window(self) -> slice:
        """A slice representing this block in its source.

        If *source* is the original source this block is contained within,
        then ``assert source[block.window] == block`` is always satisfied.

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
        block_stop = self.offset + self.length
        before_slice = slice(max(0, self.offset - delta), min(self.offset, limit))
        after_slice = slice(min(block_stop, limit), min(block_stop + delta, limit))
        return before_slice, after_slice

    def count(self, line: object, /) -> int:
        """Count the number of occurences of a *line*."""
        return self.buffer.count(line)

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

        other = self.__parse_non_block(other)
        if other is None:
            return NotImplemented

        lines, offset = other
        # check offsets before computing len(lines) or len(self)
        if offset != -1 and offset != self.offset:
            return False

        if len(lines) == self.length:
            # match the lines one by one, possibly using a rich comparison
            expect = self.__lines_iterator(0, self.length)
            return all(map(operator.__eq__, expect, lines))
        return False

    def __lt__(self, other: object, /) -> bool:
        if isinstance(other, self.__class__):
            # more efficient to first check if the indices are valid before checking the lines
            if _can_be_strict_in(self.offset, self.length, other.offset, other.length):
                return self.buffer < other.buffer
            return False

        other = self.__parse_non_block(other)
        if other is None:
            return NotImplemented

        lines, offset = other
        max_length = len(lines)
        if self.length >= max_length:
            # By Dirichlet's box principle, *other* must have strictly more
            # items than *self* for the latter to be strictly contained.
            return False

        # convert this block into its lines so that we use a rich comparison
        # with the items in *other* (we do not know their exact type)
        actual = self.__lines(0, self.length)

        if offset != -1:
            if _can_be_strict_in(self.offset, self.length, offset, max_length):
                return actual < lines
            return False

        # we want to find this block in the *other* block (at any place)
        for start in range(max_length - self.length + 1):
            region = itertools.islice(lines, start, start + self.length)
            if all(map(operator.__eq__, actual, region)):
                return True
        return False

    def __gt__(self, other: object, /) -> bool:
        if isinstance(other, self.__class__):
            return other < self

        other = self.__parse_non_block(other)
        if other is None:
            return NotImplemented

        # nothing can be a strict subset of the empty block (this check
        # must be done *after* we decided whether *other* is correct)
        if not self:
            return False

        lines, other_offset = other
        other_length = len(lines)

        if self.length <= other_length:
            # By Dirichlet's box principle, *self* must have strictly more
            # items than *other* for the latter to be strictly contained.
            return False

        if other_offset != -1:
            # we want to find *other* at a given offset
            if _can_be_strict_in(other_offset, other_length, self.offset, self.length):
                # dispatch to C implementation of list.__lt__
                actual = self.__lines(other_offset, other_length)
                return actual > lines

        # we want to find *other* in this block (at any place)
        for start in range(self.length - other_length + 1):
            if self.__lines(start, other_length) > lines:
                return True
        return False

    # Do not annotate with list[Line] since otherwise mypy complains
    # when comparing with a right-hand side that is a list of objects.
    def __lines(self, start: int, count: int) -> list[object]:
        """Same as :func:`__lines_iterator` but return a list instead."""
        return list(self.__lines_iterator(start, count))

    def __lines_iterator(self, start: int, count: int) -> Iterator[Line]:
        """Yield some lines in this block as :class:`Line` objects."""
        region = itertools.islice(self.buffer, start, start + count)
        for index, line in enumerate(region, self.offset + start):
            yield Line(line, index, _check=False)

    def __parse_non_block(self, other: object, /) -> tuple[list[object], int] | None:
        """Try to parse *other* as a pair ``(block lines, block offset)``.

        For efficiency, do *not* call this method on :class:`Block` instances
        since they can be handled separately more efficiently.
        """
        if not isinstance(other, Sequence):
            return None

        # given as (lines, offset) with lines = sequence of line-like objects
        if len(other) == 2 and isinstance(other[0], Sequence) and isinstance(other[1], int):
            if isinstance(other[0], str):
                return None
            # mypy does not know how to deduce that the length is 2
            return list(other[0]), other[1]
        return list(other), -1


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
