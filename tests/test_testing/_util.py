from __future__ import annotations

import abc
import fnmatch
import os
import re
import string
from functools import lru_cache
from io import StringIO
from itertools import chain
from pathlib import Path
from threading import RLock
from typing import TYPE_CHECKING, TypedDict, TypeVar, final, overload

import pytest

from sphinx.testing._internal.util import UID_HEXLEN

from tests.test_testing._const import MAGICO_PLUGIN_NAME, SPHINX_PLUGIN_NAME

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
    from typing import Any, ClassVar, Final, Literal

    from _pytest.pytester import Pytester, RunResult
    from typing_extensions import Unpack


def _parse_source_info_path(path: str) -> tuple[str, str, int, str]:
    """Implementation of :class:`SourceInfo` constructor.

    The implementation is kept outside of the class to minimize its size.
    """
    fspath = Path(path)
    checksum = fspath.parent.stem  # can be '0' or a 32-bit numeric string
    if not checksum or not checksum.isnumeric():
        pytest.fail(f'cannot extract configuration checksum from: {path!r}')

    contnode = fspath.parent.parent.stem  # can be '-' or a hex string
    if contnode != '-':
        if not set(contnode).issubset(string.hexdigits):
            pytest.fail(
                f'cannot extract container node ID from: {path!r} '
                f"(expecting '-' or a hexadecimal string, got {contnode!r})"
            )
        if len(contnode) != UID_HEXLEN:
            pytest.fail(
                f'cannot extract container node ID from {path!r} '
                f'({contnode!r} must be of length {UID_HEXLEN}, got {len(contnode)})'
            )

    return str(fspath), contnode, int(checksum), fspath.stem


@final
class SourceInfo(tuple[str, str, int, str]):
    """View on the sources directory path's components."""

    # We do not use a NamedTuple nor a dataclass since we we want an immutable
    # class in which its constructor checks the format of its unique argument.
    __slots__ = ()

    def __new__(cls, path: str, /) -> SourceInfo:
        return tuple.__new__(cls, _parse_source_info_path(path))

    @property
    def realpath(self) -> str:
        """The absolute path to the sources directory."""
        return self[0]

    @property
    def contnode(self) -> str:
        """The node container's identifier."""
        return self[1]

    @property
    def checksum(self) -> int:
        """The Sphinx configuration checksum."""
        return self[2]

    @property
    def filename(self) -> str:
        """The sources directory name."""
        return self[3]


@final
class Outcome(TypedDict, total=False):
    """Expected outcomes for :class:`_pytest.pytester.Pytester`."""

    passed: int
    xpassed: int

    skipped: int
    failed: int
    errors: int
    xfailed: int
    warnings: int
    deselected: int


def assert_outcomes(actual: Mapping[str, int], expect: Outcome) -> None:
    """Check that the actual outcomes match the expected ones.

    This differs from the native logic of ``pytester`` in the following sense:

    - if ``expect['passed']`` is missing, then ``actual['passed']`` is
      not checked (a simliar argument applies to ``expect['xpassde']`).
    - for any other *outcome*, the default value of ``expect[outcome]`` is *0*.
    """
    __tracebackhide__ = True
    success_outcomes = {'passed', 'xpassed'}

    for status in success_outcomes:
        # for successful tests, we do not care if the count is not given
        obtained = actual.get(status, 0)
        expected = expect.get(status, obtained)
        assert obtained == expected, (status, actual, expect)

    for status in Outcome.__annotations__.keys() - success_outcomes:
        obtained = actual.get(status, 0)
        expected = expect.get(status, 0)
        assert obtained == expected, (status, actual, expect)


def _make_testable_path(path: str | os.PathLike[str]) -> str:
    """Prepend ``test_`` to all fragments of *path*."""

    def make_testable_name(name: str) -> str:
        return f'test_{name.removeprefix("test_")}'

    return os.path.join(*map(make_testable_name, Path(path).parts))


@final
class E2E:
    """End-to-end integration test interface."""

    def __init__(self, pytester: Pytester) -> None:
        self._pytester = pytester
        """The :class:`~_pytest.pytester.Pytester` instance obtained from the fixture."""

        self._default_testname = 'main'
        """The default test file suffix name (will be named ``test_main.py``)."""

    def makepyfile(self, /, *args: Any, **kwargs: Any) -> Path:
        """Delegate to :meth:`_pytest.pytester.Pytester.makepyfile`."""
        return self._pytester.makepyfile(*args, **kwargs)

    def makepytest(self, /, **modules: str) -> Sequence[Path]:
        """Similar to :meth:`makepyfile` but add ``test_`` prefixes to files if needed.

        :param modules: The test module names and their content.
        :return: The real and absolute paths that were written to.
        """
        files = {_make_testable_path(dest): source for dest, source in modules.items()}
        self.makepyfile(**files)
        return tuple(Path(file).absolute() for file in files)

    def runpytest(self, *args: str, plugins: Sequence[str] = ()) -> RunResult:
        """Run the pytester in the same process.

        :param plugins: A sequence of additional plugin commands.
        :return: The pytester's result.

        Each entry in *plugins* is either a plugin name (to enable) or a
        plugin name prefixed by ``no:`` (to disable), e.g., ``no:xdist``.
        """
        # runpytest() does not accept 'plugins' if the method is 'subprocess'
        plugins = (SPHINX_PLUGIN_NAME, MAGICO_PLUGIN_NAME, *plugins)
        return self._pytester.runpytest_inprocess(*args, plugins=plugins)

    @overload
    def write(self, main_case: str | Sequence[str], /) -> Path: ...  # NoQA: E704
    @overload
    def write(self, dest: str, /, *cases: str | Sequence[str]) -> Path: ...  # NoQA: E704
    def write(self, dest: Sequence[str], /, *cases: str | Sequence[str]) -> Path:  # NoQA: E301
        """Write a Python test file.

        When *dest* is specified, it should indicate where the test file is to
        be written, possibly omitting ``test_`` prefixes, e.g.::

            e2e.write('pkg/foo', '...')  # writes to 'test_pkg/test_foo.py'

        When *dest* is not specified, its default value is 'main'.

        :param dest: The destination identifier.
        :param cases: The content parts to write.
        :return: The path where the cases where written to.
        """
        if not cases:
            dest, cases = self._default_testname, (dest,)

        assert isinstance(dest, str)
        path = _make_testable_path(dest)

        sources = [[case] if isinstance(case, str) else case for case in cases]
        # extend the current source with the new cases
        lines = (self._getpysource(path), *chain.from_iterable(sources))
        suite = '\n'.join(filter(None, lines)).strip()
        return self.makepyfile(**{path: suite})

    def run(self, /, **outcomes: Unpack[Outcome]) -> MagicOutput:
        """Run the internal pytester object without ``xdist``.

        :param outcomes: The expected outcomes (see :func:`assert_outcomes`).
        :return: The output view.
        """
        # The :option:`!-r` pytest option is set to ``A`` since we need
        # to intercept the report sections for all tests.
        res = self.runpytest('-rA', plugins=['no:xdist'])
        assert_outcomes(res.parseoutcomes(), outcomes)
        return MagicOutput(res)

    def xdist_run(self, /, *, jobs: int = 2, **outcomes: Unpack[Outcome]) -> MagicOutput:
        """Run the internal pytester object with ``xdist``.

        :param jobs: The number of parallel jobs to run (default: *2*).
        :param outcomes: The expected outcomes (see :func:`assert_outcomes`).
        :return: The output view.
        """
        # The :option:`!-r` pytest option is set to ``A`` since we need
        # to intercept the report sections and the distribution policy
        # is ``loadgroup`` to ensure that ``xdist_group`` is supported.
        args = ('-rA', '--numprocesses', str(jobs), '--dist', 'loadgroup')
        res = self.runpytest(*args, plugins=['xdist'])
        assert_outcomes(res.parseoutcomes(), outcomes)
        return MagicOutput(res)

    def _getpysource(self, relpath: str, /) -> str:
        """Get the content of Python source file, stripped from whitespaces.

        :param relpath: A relative path to the pytester's path.
        :return: The source content.
        """
        curr = self._pytester.path.joinpath(relpath).with_suffix('.py')
        if curr.exists():
            return curr.read_text(encoding='utf-8').strip()
        return ''


###############################################################################
# magic I/O for xdist support
###############################################################################

_CAPTURE_STATE: Final[Literal['setup', 'call', 'teardown']] = 'teardown'
"""The capturing state when the special report sections are added."""

_MAIN_TAG: Final[str] = 'main'
"""Special string in a section title indicating the beginning of that section."""
_STOP_TAG: Final[str] = 'stop'
"""Special string in a section title indicating the section ending the previous one."""
_STOPLINE: Final[str] = '@EOM'
"""Special line in a section taggeed with ``_END_TAG`` indicating the end of that section."""


class _MagicChannelMixin:
    __slots__ = ()

    channel: ClassVar[str]
    """A unique string to prefix to lines written in report sections.

    This is only used to identify how extracted lines are to be parsed.
    """


class _DataChannelMixin(_MagicChannelMixin):
    __slots__ = ()

    channel = '<sphinx-magic::data>'
    """Name of the channel where variables are printed."""


class _TextChannelMixin(_MagicChannelMixin):
    __slots__ = ()

    channel = '<sphinx-magic::text>'
    """Name of the channel where print-like messages are printed."""


class _MagicEncoderMixin(_MagicChannelMixin):
    __slots__ = ()

    @classmethod
    def encode(cls, /, *args: Any, sep: str, end: str) -> str:
        return f'{cls.channel} {sep.join(map(str, args))}{end}'

    @classmethod
    def header(
        cls,
        nodeid: str,
        tag: str,
        *,
        escape_static: bool = False,
        include_state: bool = False,
    ) -> str:
        channel = cls.channel
        suffix: str = _CAPTURE_STATE if include_state else ''
        if escape_static:
            channel, tag, suffix = re.escape(channel), re.escape(tag), re.escape(suffix)
        return ' '.join(filter(None, (f'{channel}@{tag}', '--', nodeid, suffix)))


class MagicWriter(_MagicEncoderMixin, abc.ABC):
    __slots__ = ('_buffer',)

    def __init__(self) -> None:
        self._buffer = StringIO()

    @final
    def sections(self, nodeid: str) -> Sequence[tuple[str, str]]:
        """Get the report sections to write for a given node.

        :param nodeid: A test node ID.
        :return: A sequence of ``(section key, section text)``.
        """
        if content := self._buffer.getvalue():
            return [
                (self.header(nodeid, _MAIN_TAG), content),
                # a fake section is added in order to know where to stop
                (self.header(nodeid, _STOP_TAG), _STOPLINE),
            ]
        return []

    @final
    def lines(self, nodeid: str) -> Sequence[str]:
        """Get the lines that pytest would write in the report sections.

        :param nodeid: A test node ID.
        :return: The report section lines.
        """
        if not (content := self._buffer.getvalue()):
            return []

        return [
            self.header(nodeid, _MAIN_TAG, include_state=True),
            *content.splitlines(),
            self.header(nodeid, _STOP_TAG, include_state=True),
            _STOPLINE,
        ]

    @classmethod
    @abc.abstractmethod
    def format(cls, /, *args: Any, **kwargs: Any) -> str:
        """Format a line to write in the report section."""

    def write(self, /, *args: Any, **kwargs: Any) -> None:
        """Write a formatted line in the report section."""
        self.writeline(self.format(*args, **kwargs))

    @final
    def writeline(self, line: str, /) -> None:
        """Write a line in the report section."""
        self._buffer.write(line)

    @final
    def writelines(self, lines: Iterable[str], /) -> None:
        """Write the lines in the report section."""
        self._buffer.writelines(lines)


@final
class DataWriter(_DataChannelMixin, MagicWriter):
    @classmethod
    def format(cls, name: str, value: Any, *, namespace: str = '', end: str = '') -> str:
        """The line to write to the data channel.

        :param name: The variable name.
        :param value: The variable value.
        :param namespace: Optional namespace prefixed to *name* with a period.
        :param end: Character to write at the end.
        :return: The formatted line to write.
        """
        varname = '.'.join(filter(None, (namespace, name)))
        return cls.encode(varname, value, sep='=', end=end)

    def write(self, name: str, value: Any, *, namespace: str = '', end: str = '\n') -> None:
        super().write(name, value, namespace=namespace, end=end)


@final
class TextWriter(_TextChannelMixin, MagicWriter):
    @classmethod
    def format(cls, *args: Any, sep: str = ' ', end: str = '') -> str:
        """The line to write to the text channel.

        The arguments have the same meaning as for :func:`print`.

        :return: The formatted line to write.
        """
        return cls.encode(*args, sep=sep, end=end)

    def write(self, *args: Any, sep: str = ' ', end: str = '\n') -> None:
        super().write(*args, sep=sep, end=end)


@final
class MagicStream:
    """I/O stream responsible for messages to include in a report section."""

    _lock = RLock()

    def __init__(self) -> None:
        self._data = DataWriter()
        self._text = TextWriter()

    def __call__(self, varname: str, value: Any, /, *, namespace: str = '') -> None:
        """Store the value of a variable at the call site.

        .. seealso::

           :meth:`DataWriter.format`
           :meth:`MagicOutput.find`
           :meth:`MagicOutput.findall`
        """
        with self._lock:
            self._data.write(varname, value, namespace=namespace, end='\n')

    def text(self, /, *args: Any, sep: str = ' ', end: str = '\n') -> None:
        """Emulate a ``print()`` in a pytester test.

        .. seealso::

           :meth:`TextWriter.format`
           :meth:`MagicOutput.message`
           :meth:`MagicOutput.messages`
        """
        with self._lock:
            self._text.write(*args, sep=sep, end=end)

    def pytest_runtest_teardown(self, item: pytest.Item) -> None:
        """Called when tearing down a pytest item.

        This is *not* registered by ``pytest`` but the implementation is kept
        here instead of having a separate plugin since :class:`MagicOutput`
        intimely depends on this class.
        """
        for writer in (self._data, self._text):
            for key, section in writer.sections(item.nodeid):
                item.add_report_section(_CAPTURE_STATE, key, section)


_T = TypeVar('_T')


class MagicOutput:
    """The output of a :class:`_pytest.pytester.Pytester` execution."""

    def __init__(self, res: RunResult, /) -> None:
        self.res = res
        self.lines: Sequence[str] = list(res.outlines)

    @overload
    def find(  # NoQA: E704
        self, name: str, expr: str = ..., /, *, nodeid: str | None = ..., t: None = ...
    ) -> str: ...

    @overload
    def find(  # NoQA: E704
        self,
        name: str,
        expr: str = ...,
        /,
        *,
        nodeid: str | None = ...,
        t: Callable[[str], _T],
    ) -> _T: ...

    def find(
        self,
        name: str,
        expr: str = r'.*',
        /,
        *,
        nodeid: str | None = None,
        t: Callable[[str], Any] | None = None,
    ) -> Any:
        """Find the first occurrence of a variable value.

        :param name: A variable name.
        :param expr: A variable value pattern.
        :param nodeid: Optional node ID to filter messages.
        :param t: Optional adapter function.
        :return: The variable value (possibly converted via *t*).
        """
        values = self.iterfind(name, expr, nodeid=nodeid)
        value = next(values, None)
        assert value is not None, (name, expr, nodeid)
        return value if t is None else t(value)

    @overload
    def findall(  # NoQA: E704
        self, name: str, expr: str = ..., /, *, nodeid: str | None = ..., t: None = ...
    ) -> list[str]: ...

    @overload
    def findall(  # NoQA: E704
        self,
        name: str,
        expr: str = ...,
        /,
        *,
        nodeid: str | None = ...,
        t: Callable[[str], _T],
    ) -> list[_T]: ...

    def findall(
        self,
        name: str,
        expr: str = r'.*',
        /,
        *,
        nodeid: str | None = None,
        t: Callable[[str], Any] | None = None,
    ) -> list[Any]:
        """Find all occurrences of a variable value.

        :param name: A variable name.
        :param expr: A variable value pattern.
        :param nodeid: Optional node ID to filter messages.
        :param t: Optional adapter function.
        :return: The variable values (possibly converted via *t*).
        """
        return list(self.iterfind(name, expr, nodeid=nodeid, t=t))

    @overload
    def iterfind(  # NoQA: E704
        self, name: str, expr: str = ..., /, *, nodeid: str | None = ..., t: None = ...
    ) -> Iterator[str]: ...

    @overload
    def iterfind(  # NoQA: E704
        self,
        name: str,
        expr: str = ...,
        /,
        *,
        nodeid: str | None = ...,
        t: Callable[[str], _T],
    ) -> Iterator[_T]: ...

    def iterfind(
        self,
        name: str,
        expr: str = r'.*',
        /,
        *,
        nodeid: str | None = None,
        t: Callable[[str], Any] | None = None,
    ) -> Iterator[Any]:
        """Same as :meth:`findall`, but returns an iterator instead."""
        prefix = re.escape(f'{DataWriter.channel} {name}')
        pattern = re.compile(rf'^{prefix}=({expr})$')
        values = DataFinder.find(self.lines, pattern, nodeid=nodeid)
        return values if t is None else map(t, values)

    def message(self, expr: str = r'.*', /, *, nodeid: str | None = None) -> str | None:
        """Find the first occurrence of a print-like message.

        Messages for printing variables are not included.

        :param expr: A message pattern.
        :param nodeid: Optional node ID to filter messages.
        :return: A message or ``None``.
        """
        return next(self.itertext(expr, nodeid=nodeid), None)

    def messages(self, expr: str = r'.*', /, *, nodeid: str | None = None) -> list[str]:
        """Find all occurrences of print-like messages.

        Messages for printing variables are not included.

        :param expr: A message pattern.
        :param nodeid: Optional node ID to filter messages.
        :return: A list of messages.
        """
        return list(self.itertext(expr, nodeid=nodeid))

    def itertext(self, expr: str = r'.*', /, *, nodeid: str | None = None) -> Iterator[str]:
        """Same as :meth:`messages`, but returns an iterator instead."""
        pattern = re.compile(rf'^{re.escape(TextWriter.channel)} ({expr})$')
        return TextFinder.find(self.lines, pattern, nodeid=nodeid)


@lru_cache(maxsize=256)
def _compile_nodeid_pattern(nodeid: str) -> str:
    return fnmatch.translate(nodeid).removesuffix(r'\Z')  # remove the \Z marker


class MagicFinder(_MagicEncoderMixin, _MagicChannelMixin):
    """Helper class responsible for parsing the actual pytester result lines."""

    @classmethod
    def find(
        cls, lines: Sequence[str], pattern: re.Pattern[str], *, nodeid: str | None = None
    ) -> Iterator[str]:
        r"""Match the *lines* corresponding to *nodeid* or all if none is given.

        Lines that are not part of the same :attr:`channel` are ignored.

        :param lines: The pytester's result lines.
        :param pattern: A pattern to match on the section's lines.
        :param nodeid: Optional test node ID.

        The *pattern* must contain a single matching group and should match
        a magic section's line. More generally, the *lines* are expected to
        contain blocks formatted as::

            SPECIAL SECTION TITLE WITH SOME NODE ID AND THE 'TXT' MARKER
            <content>  <-- to be matched by *pattern*
            ...
            <content>  <-- to be matched by *pattern*
            SPECIAL SECTION TITLE WITH SOME NODE ID AND THE 'END' MARKER
            SINGLE LINE CONTAINING SOME SPECIAL 'STOP' STRING

        The lines matched by *pattern* consist the 'main' part and the (single)
        line containing the 'STOP' marker is called the 'stop' line.
        """
        assert pattern.groups == 1, (pattern, nodeid, cls.channel)

        if nodeid is None:
            lines_dict = cls.find_teardown_sections(lines)
            found: Iterable[str] = chain.from_iterable(lines_dict.values())
        else:
            found = cls.find_teardown_section(lines, nodeid=nodeid)

        for match in filter(None, map(pattern.match, found)):
            value = match.group(1)
            assert isinstance(value, str), (pattern, nodeid, cls.channel)
            yield value

    @classmethod
    def find_teardown_section(cls, lines: Sequence[str], *, nodeid: str) -> Sequence[str]:
        """Extract from *lines* the block corresponding to *nodeid*.

        :param lines: The lines to parse.
        :return: A mapping from node ID to a block of lines.

        .. note:: See :meth:`find` for the format of a single block.
        """
        nodeid = _compile_nodeid_pattern(nodeid)
        main_pattern, stop_pattern = cls._compile_patterns(nodeid)

        state = 0
        start, stop = None, None  # type: (int | None, int | None)
        for index, line in enumerate(lines):
            if state == 0 and main_pattern.search(line):
                start = index + 1  # skip the header itself
                state = 1

            elif state == 1 and stop_pattern.search(line):
                stop = index
                state = 2

            elif state == 2:
                if stop == index - 1 and line == _STOPLINE:
                    block = lines[start:stop]
                    cls._check_block(block, start)
                    return block

                state = 0  # try again
                start, stop = None, None

        return []

    @classmethod
    def find_teardown_sections(cls, lines: Sequence[str]) -> dict[str, Sequence[str]]:
        """Extract from *lines* all special blocks.

        :param lines: The lines to parse.
        :return: A mapping from node ID to a block of lines.

        .. note:: See :meth:`find` for the format of a single block.
        """
        main_pattern, stop_pattern = cls._compile_patterns(r'(?P<nodeid>(\S+::)?\S+)')

        state, curid = 0, None
        positions: dict[str, tuple[int | None, int | None]] = {}
        index = 0
        while index < len(lines):
            line = lines[index]

            if state == 0 and (m := main_pattern.search(line)) is not None:
                assert curid is None
                curid = m.group(1)
                assert curid is not None
                assert curid not in positions
                # we ignore the header in the output
                positions[curid] = (index + 1, None)
                state = 1

            elif state == 1 and (m := stop_pattern.search(line)) is not None:
                assert curid is not None
                if curid == m.group(1):  # found a corresponding section
                    positions[curid] = (positions[curid][0], index)
                    state = 2  # check that the content of the end section is correct
                else:
                    # something went wrong :(
                    prev_top_index, _ = positions.pop(curid)
                    # reset the state and the ID we were looking for
                    state, curid = 0, None
                    # next loop iteration will retry the whole block
                    assert prev_top_index is not None
                    index = prev_top_index

            elif state == 2:
                assert curid is not None
                assert curid in positions
                _, prev_bot_index = positions[curid]
                assert prev_bot_index == index - 1
                # check that the previous line was the header
                if line != _STOPLINE:
                    # we did not have the expected end content (note that
                    # this implementation does not support having end-markers
                    # inside another section)
                    del positions[curid]
                    # next loop iteration will retry the same line but in state 0
                    index = prev_bot_index

                # reset the state and the ID we were looking for
                state, curid = 0, None

            index += 1

        blocks = {}
        for nodeid, (i, j) in positions.items():
            if j is None:
                continue

            block = lines[i:j]
            cls._check_block(block, i)
            blocks[nodeid] = block
        return blocks

    @classmethod
    def _compile_patterns(cls, nodeid: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
        """The patterns for matching the 'main' and 'stop' parts of a block.

        :param nodeid: The node id (possibly a fnmatch-like pattern).
        :return: The compiled patterns for the 'main' and 'stop' lines.
        """
        # do not escape *nodeid* as this could contain a regular expression
        main_pattern = cls.header(nodeid, _MAIN_TAG, escape_static=True, include_state=True)
        stop_pattern = cls.header(nodeid, _STOP_TAG, escape_static=True, include_state=True)
        return re.compile(main_pattern), re.compile(stop_pattern)

    @classmethod
    def _check_block(cls, block: Sequence[str], offset: int | None) -> None:
        """Check that the extracted block is valid."""
        for index, line in enumerate(block):
            if not line.startswith(cls.channel):
                msg = f'L:{(offset or 0) + index}: invalid line: {line!r}'
                raise AssertionError(msg)


@final
class DataFinder(_DataChannelMixin, MagicFinder):
    """Object responsible for extracting variables."""


@final
class TextFinder(_TextChannelMixin, MagicFinder):
    """Object responsible for extracting print-like messages."""
