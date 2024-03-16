from __future__ import annotations

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
    from collections.abc import Callable, Iterator, Mapping, Sequence
    from typing import Any, Final

    from _pytest.pytester import Pytester, RunResult
    from typing_extensions import Unpack


def _parse_path(path: str) -> tuple[str, str, int, str]:
    fspath = Path(path)
    checksum = fspath.parent.stem  # can be '0' or a 32-bit numeric string
    if not checksum or not checksum.isnumeric():
        pytest.fail(f'cannot extract configuration checksum from: {path!r}')

    contnode = fspath.parent.parent.stem  # can be '-' or a hex string
    if contnode != '-':
        if not set(contnode).issubset(string.hexdigits):
            pytest.fail(f'cannot extract container node ID from: {path!r} '
                        'expecting %r or a hexadecimal string, got %r' % ('-', contnode))
        if len(contnode) != UID_HEXLEN:
            pytest.fail(f'cannot extract container node ID from: {path!r} '
                        f'({contnode!r} must be of length {UID_HEXLEN}, got {len(contnode)})')

    return str(fspath), contnode, int(checksum), fspath.stem


@final
class SourceInfo(tuple[str, str, int, str]):
    """View on the sources directory path's components."""

    # We do not use a NamedTuple nor a dataclass since we we want an immutable
    # class in which its constructor checks the format of its unique argument.
    __slots__ = ()

    def __new__(cls, path: str) -> SourceInfo:
        return tuple.__new__(cls, _parse_path(path))

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
    passed: int
    skipped: int
    failed: int
    errors: int
    xpassed: int
    xfailed: int
    warnings: int
    deselected: int


def _assert_outcomes(actual: Mapping[str, int], expect: Outcome) -> None:
    __tracebackhide__ = True

    for status in ('passed', 'xpassed'):
        # for successful tests, we do not care if the count is not given
        obtained = actual.get(status, 0)
        expected = expect.get(status, obtained)
        assert obtained == expected, (status, actual, expect)

    for status in ('skipped', 'failed', 'errors', 'xfailed', 'warnings', 'deselected'):
        obtained = actual.get(status, 0)
        expected = expect.get(status, 0)
        assert obtained == expected, (status, actual, expect)


def _make_testable_name(name: str) -> str:
    return name if name.startswith('test_') else f'test_{name}'


def _make_testable_path(path: str | os.PathLike[str]) -> str:
    return os.path.join(*map(_make_testable_name, Path(path).parts))


@final
class E2E:
    """End-to-end integration test interface."""

    def __init__(self, pytester: Pytester) -> None:
        self._pytester = pytester

    def makepyfile(self, *args: Any, **kwargs: Any) -> Path:
        """Delegate to :meth:`_pytest.pytester.Pytester.makepyfile`."""
        return self._pytester.makepyfile(*args, **kwargs)

    def makepytest(self, *args: Any, **kwargs: Any) -> Path:
        """Same as :meth:`makepyfile` but add ``test_`` prefixes to files if needed."""
        kwargs = {_make_testable_path(dest): source for dest, source in kwargs.items()}
        return self.makepyfile(*args, **kwargs)

    def runpytest(self, *args: str, plugins: Sequence[str] = ()) -> RunResult:
        """Run the pytester in the same process.

        When *silent* is true, the pytester internal output is suprressed.
        """
        # runpytest() does not accept 'plugins' if the method is 'subprocess'
        plugins = (SPHINX_PLUGIN_NAME, MAGICO_PLUGIN_NAME, *plugins)
        return self._pytester.runpytest_inprocess(*args, plugins=plugins)

    @overload
    def write(self, main_case: str | Sequence[str], /) -> Path:
        ...

    @overload
    def write(self, dest: str, /, *cases: str | Sequence[str]) -> Path:
        ...

    def write(self, dest: Sequence[str], /, *cases: str | Sequence[str]) -> Path:
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
            dest, cases = 'main', (dest,)

        assert isinstance(dest, str)
        path = _make_testable_path(dest)

        sources = [[case] if isinstance(case, str) else case for case in cases]
        lines = (self._getpysource(path), *chain.from_iterable(sources))
        suite = '\n'.join(filter(None, lines)).strip()
        return self.makepyfile(**{path: suite})

    def run(self, /, **outcomes: Unpack[Outcome]) -> MagicOutput:
        """Run the internal pytester object without ``xdist``."""
        res = self.runpytest('-rA', plugins=['no:xdist'])
        _assert_outcomes(res.parseoutcomes(), outcomes)
        return MagicOutput(res)

    def xdist_run(self, /, *, jobs: int = 2, **outcomes: Unpack[Outcome]) -> MagicOutput:
        """Run the internal pytester object with ``xdist``."""
        # The :option:`!-r` pytest option is set to ``A`` since we need
        # to intercept the report sections and the distribution policy
        # is ``loadgroup`` to ensure that ``xdist_group`` is supported.
        args = ('-rA', '--numprocesses', str(jobs), '--dist', 'loadgroup')
        res = self.runpytest(*args, plugins=['xdist'])
        _assert_outcomes(res.parseoutcomes(), outcomes)
        return MagicOutput(res)

    def _getpysource(self, path: str) -> str:
        curr = self._pytester.path.joinpath(path).with_suffix('.py')
        if curr.exists():
            return curr.read_text(encoding='utf-8').strip()
        return ''


###############################################################################
# magic I/O for xdist support
###############################################################################


_VALUE_CHANNEL: Final[str] = '<sphinx-magic::value>'
"""Name of the channel where variables are printed."""
_PRINT_CHANNEL: Final[str] = '<sphinx-magic::print>'
"""Name of the channel where print-like messages are printed."""

CAPTURE_STATE: Final[str] = 'teardown'
"""The capturing state when the special report sections are added."""

TXT_TAG: Final[str] = 'txt'
"""Special string in a section title indicating the beginning of that section."""
END_TAG: Final[str] = 'end'
"""Special string in a section title indicating the section ending the previous one.

For instance, the output lines consist of blocks formatted as::

    SPECIAL SECTION TITLE WITH ``_TXT_TAG``
    <content>
    ...
    <content>
    SPECIAL SECTION TITLE WITH ``_END_TAG``
    SINGLE LINE CONTAINING ``_STOPLINE``
    ANOTHER SPECIAL SECTION TITLE WITH ``_TXT_TAG``
"""
STOPLINE: Final[str] = '@EOM'
"""Special line in a section taggeed with ``_END_TAG`` indicating the end of that section."""


def _format_message(prefix: str, *args: Any, sep: str, end: str) -> str:
    return f'{prefix} {sep.join(map(str, args))}{end}'


def format_message_for_value_channel(varname: str, value: Any, *, end: str = '\n') -> str:
    return _format_message(_VALUE_CHANNEL, varname, value, sep='=', end=end)


def format_message_for_print_channel(*args: Any, sep: str = ' ', end: str = '\n') -> str:
    return _format_message(_PRINT_CHANNEL, *args, sep=sep, end=end)


@lru_cache(maxsize=128)
def _compile_pattern_for_value_channel(varname: str, pattern: str) -> re.Pattern[str]:
    channel, varname = re.escape(_VALUE_CHANNEL), re.escape(varname)
    return re.compile(rf'^{channel} {varname}=({pattern})$')


@lru_cache(maxsize=128)
def _compile_pattern_for_print_channel(pattern: str) -> re.Pattern[str]:
    channel = re.escape(_PRINT_CHANNEL)
    return re.compile(rf'^{channel} ({pattern})$')


def magic_section(nodeid: str, channel: str, tag: str) -> str:
    return f'{channel}@{tag} -- {nodeid}'


@lru_cache(maxsize=256)
def _compile_nodeid_pattern(nodeid: str) -> str:
    return fnmatch.translate(nodeid).rstrip(r'\Z')  # remove the \Z marker


@lru_cache(maxsize=256)
def _get_magic_patterns(nodeid: str, channel: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    channel = re.escape(channel)

    def get_pattern(tag: str) -> re.Pattern[str]:
        title = magic_section(nodeid, channel, re.escape(tag))
        return re.compile(f'{title} {CAPTURE_STATE}')

    return get_pattern(TXT_TAG), get_pattern(END_TAG)


def _create_magic_teardownsection(item: pytest.Item, channel: str, content: str) -> None:
    if content:
        txt_section = magic_section(item.nodeid, channel, TXT_TAG)
        item.add_report_section(CAPTURE_STATE, txt_section, content)
        # a fake section is added in order to know where to stop
        end_section = magic_section(item.nodeid, channel, END_TAG)
        item.add_report_section(CAPTURE_STATE, end_section, STOPLINE)


@final
class MagicWriter:
    """I/O stream responsible for messages to include in a report section."""

    _lock = RLock()

    def __init__(self) -> None:
        self._vals = StringIO()
        self._info = StringIO()

    def __call__(self, varname: str, value: Any, /) -> None:
        """Store the value of a variable at the call site.

        .. seealso::

           :meth:`MagicOutput.find`
           :meth:`MagicOutput.findall`
        """
        payload = format_message_for_value_channel(varname, value)
        self._write(self._vals, payload)

    def info(self, *args: Any, sep: str = ' ', end: str = '\n') -> None:
        """Emulate a ``print()`` in a pytester test.

        .. seealso::

           :meth:`MagicOutput.message`
           :meth:`MagicOutput.messages`
        """
        payload = format_message_for_print_channel(*args, sep=sep, end=end)
        self._write(self._info, payload)

    @classmethod
    def _write(cls, dest: StringIO, line: str) -> None:
        with cls._lock:
            dest.write(line)

    def pytest_runtest_teardown(self, item: pytest.Item) -> None:
        """Called when tearing down a pytest item.

        This is *not* registered as a pytest but the implementation is kept
        here since :class:`MagicOutput` intimely depends on this class.
        """
        _create_magic_teardownsection(item, _VALUE_CHANNEL, self._vals.getvalue())
        _create_magic_teardownsection(item, _PRINT_CHANNEL, self._info.getvalue())


_T = TypeVar('_T')


class MagicOutput:
    """The output of a :class:`_pytest.pytster.Pytester` execution."""

    def __init__(self, res: RunResult) -> None:
        self.res = res
        self.lines: Sequence[str] = list(res.outlines)

    @overload
    def find(
        self, name: str, expr: str = ..., *, nodeid: str | None = ..., t: None = ...,
    ) -> str:
        ...

    @overload
    def find(
        self, name: str, expr: str = ..., *, nodeid: str | None = ..., t: Callable[[str], _T],
    ) -> _T:
        ...

    def find(
        self,
        name: str,
        expr: str = r'.*',
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
        values = self._findall(name, expr, nodeid=nodeid)
        value = next(values, None)
        assert value is not None, (name, expr, nodeid)
        return value if t is None else t(value)

    @overload
    def findall(
        self, name: str, expr: str = ..., *, nodeid: str | None = ..., t: None = ...,
    ) -> list[str]:
        ...

    @overload
    def findall(
        self, name: str, expr: str = ..., *, nodeid: str | None = ..., t: Callable[[str], _T],
    ) -> list[_T]:
        ...

    def findall(
        self,
        name: str,
        expr: str = r'.*', *,
        nodeid: str | None = None,
        t: Callable[[str], Any] | None = None,
    ) -> list[Any]:
        """Find the all occurrences of a variable value.

        :param name: A variable name.
        :param expr: A variable value pattern.
        :param nodeid: Optional node ID to filter messages.
        :param t: Optional adapter function.
        :return: The variable values (possibly converted via *t*).
        """
        values = self._findall(name, expr, nodeid=nodeid)
        return list(values) if t is None else list(map(t, values))

    def _findall(self, name: str, expr: str, *, nodeid: str | None) -> Iterator[str]:
        pattern = _compile_pattern_for_value_channel(name, expr)
        yield from self._parselines(pattern, nodeid, _VALUE_CHANNEL)

    def message(self, expr: str = r'.*', *, nodeid: str | None = None) -> str | None:
        """Find the first occurrence of a print-like message.

        Messages for printing variables are not included.

        :param expr: A message pattern.
        :param nodeid: Optional node ID to filter messages.
        :return: A message or ``None``.
        """
        return next(self._messages(expr, nodeid=nodeid), None)

    def messages(self, expr: str = r'.*', *, nodeid: str | None = None) -> list[str]:
        """Find all occurrences of print-like messages.

        Messages for printing variables are not included.

        :param expr: A message pattern.
        :param nodeid: Optional node ID to filter messages.
        :return: A list of messages.
        """
        return list(self._messages(expr, nodeid=nodeid))

    def _messages(self, expr: str, *, nodeid: str | None) -> Iterator[str]:
        pattern = _compile_pattern_for_print_channel(expr)
        yield from self._parselines(pattern, nodeid, _PRINT_CHANNEL)

    def _parselines(
        self, pattern: re.Pattern[str], nodeid: str | None, channel: str,
    ) -> Iterator[str]:
        assert pattern.groups == 1, (pattern, nodeid, channel)

        if nodeid is None:
            lines_dict = find_teardown_sections(self.lines, channel)
            lines: Sequence[str] = list(chain.from_iterable(lines_dict.values()))
        else:
            lines = find_teardown_section(self.lines, nodeid, channel)

        for match in filter(None, map(pattern.match, lines)):
            value = match.group(1)
            assert isinstance(value, str), (pattern, nodeid, channel)
            yield value


def find_teardown_section(lines: Sequence[str], nodeid: str, channel: str) -> Sequence[str]:
    """Parse a pytest report to extract a special teardown section."""
    nodeid = _compile_nodeid_pattern(nodeid)
    main_pattern, stop_pattern = _get_magic_patterns(nodeid, channel)

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
            if stop == index - 1 and line == STOPLINE:
                return lines[start:stop]

            state = 0  # try again
            start, stop = None, None

    return []


def find_teardown_sections(lines: Sequence[str], channel: str) -> dict[str, Sequence[str]]:
    """Find all teardown sections in *line* for *channel*.

    >>> find_teardown_sections(lines, _VALUE_CHANNEL)  # doctest: +NORMALIZE_WHITESPACE
    {'test_a': ['<sphinx-magic::value> test_a.x=1', '<sphinx-magic::value> test_a.y=2'],
     'test_b': ['<sphinx-magic::value> test_b.x=1', '<sphinx-magic::value> test_b.y=2']}

    >>> find_teardown_sections(lines, _PRINT_CHANNEL)  # doctest: +NORMALIZE_WHITESPACE
    {'test_a': ['<sphinx-magic::print> some message for test_a',
                '<sphinx-magic::print> test_a.value: 2']}
    """
    main_pattern, stop_pattern = _get_magic_patterns(r'(?P<nodeid>(\S+::)?\S+)', channel)

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
            nodeid = m.group(1)
            if curid == nodeid:  # found a corresponding section
                positions[nodeid] = (positions[nodeid][0], index)
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
            if line != STOPLINE:
                # we did not have the expected end content (note that
                # this implementation does not support having end-markers
                # inside another section)
                del positions[curid]
                # next loop iteration will retry the same line but in state 0
                index = prev_bot_index

            # reset the state and the ID we were looking for
            state, curid = 0, None

        index += 1

    return {n: lines[i:j] for n, (i, j) in positions.items() if j is not None}
