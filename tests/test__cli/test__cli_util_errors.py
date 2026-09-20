from __future__ import annotations

import itertools
import operator
from io import StringIO
from typing import TYPE_CHECKING

import pytest

from sphinx._cli.util.colour import blue, reset
from sphinx._cli.util.errors import handle_exception, strip_escape_sequences
from sphinx.errors import ConfigError, ExtensionError

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Final

    from sphinx.errors import SphinxError

CURSOR_UP: Final[str] = '\x1b[2A'  # ignored ANSI code
ERASE_LINE: Final[str] = '\x1b[2K'  # supported ANSI code
TEXT: Final[str] = '\x07 ß Hello world!'


def test_strip_escape_sequences() -> None:
    # double ERASE_LINE so that the tested strings may have 2 of them
    ansi_base_blocks = [
        TEXT,
        blue(TEXT),
        reset(TEXT),
        ERASE_LINE,
        ERASE_LINE,
        CURSOR_UP,
    ]
    # :func:`strip_escape_sequences` strips ANSI codes known by Sphinx
    text_base_blocks = [
        TEXT,
        TEXT,
        TEXT,
        '',
        '',
        CURSOR_UP,
    ]

    assert len(text_base_blocks) == len(ansi_base_blocks)
    N = len(ansi_base_blocks)

    def next_ansi_blocks(choices: Sequence[str], n: int) -> Sequence[str]:
        # Get a list of *n* words from a cyclic sequence of *choices*.
        #
        # For instance ``next_ansi_blocks(['a', 'b'], 3) == ['a', 'b', 'a']``.
        stream = itertools.cycle(choices)
        return list(map(operator.itemgetter(0), zip(stream, range(n), strict=False)))

    # generate all permutations of length N
    for sigma in itertools.permutations(range(N), N):
        # apply the permutation on the blocks with ANSI codes
        ansi_blocks = list(map(ansi_base_blocks.__getitem__, sigma))
        # apply the permutation on the blocks with stripped codes
        text_blocks = list(map(text_base_blocks.__getitem__, sigma))

        for glue, n in itertools.product(['.', '\n', '\r\n'], range(4 * N)):
            ansi_strings = next_ansi_blocks(ansi_blocks, n)
            text_strings = next_ansi_blocks(text_blocks, n)
            assert len(ansi_strings) == len(text_strings) == n

            ansi_string = glue.join(ansi_strings)
            text_string = glue.join(text_strings)
            assert strip_escape_sequences(ansi_string) == text_string


def test_strip_ansi_short_forms() -> None:
    # In Sphinx, we always "normalize" the color codes so that they
    # match "\x1b\[(\d\d;){0,2}(\d\d)m" but it might happen that
    # some messages use '\x1b[0m' instead of ``reset(s)``, so we
    # test whether this alternative form is supported or not.

    for strip_function in strip_escape_sequences, strip_escape_sequences:
        # \x1b[m and \x1b[0m are equivalent to \x1b[00m
        assert strip_function('\x1b[m') == ''
        assert strip_function('\x1b[0m') == ''

        # \x1b[1m is equivalent to \x1b[01m
        assert strip_function('\x1b[1mbold\x1b[0m') == 'bold'

    # \x1b[K is equivalent to \x1b[0K
    assert strip_escape_sequences('\x1b[K') == ''


def _handle(exception: BaseException, **kwargs: object) -> str:
    stderr = StringIO()
    handle_exception(exception, stderr=stderr, **kwargs)  # type: ignore[arg-type]
    return stderr.getvalue()


def _raised(exception: BaseException) -> BaseException:
    """Return *exception* with a real traceback attached."""

    def _raise() -> None:
        raise exception

    try:
        _raise()
    except BaseException as exc:
        return exc
    msg = 'unreachable'
    raise AssertionError(msg)


@pytest.mark.parametrize('exception', [ExtensionError('boom'), ConfigError('boom')])
def test_handle_exception_nice_errors_are_short(exception: SphinxError) -> None:
    # SphinxError subclasses are expected errors: only the category and the
    # message are shown, so extensions and conf.py can report problems without
    # implying that Sphinx itself is broken. Refs: #14543
    out = _handle(_raised(exception))

    assert exception.category in out
    assert 'boom' in out
    assert 'Versions' not in out
    assert 'Loaded Extensions' not in out
    assert 'Traceback' not in out
    assert 'full traceback has been saved' not in out
    assert 'report this error to the developers' not in out


def test_handle_exception_nice_error_no_traceback_with_T() -> None:
    # -T prints on the console the traceback that would otherwise be written to
    # a temporary file. A nice error saves no such file, so -T must not print
    # one either: an extension reporting a user error should not show a
    # traceback.
    out = _handle(_raised(ExtensionError('boom')), print_traceback=True)

    assert 'boom' in out
    assert 'in _raise' not in out
    assert 'Traceback' not in out
    assert 'full traceback has been saved' not in out
    assert 'report this error to the developers' not in out


def test_handle_exception_unexpected_error_traceback_with_T(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # For an unexpected exception -T does print the traceback it would have
    # saved.
    monkeypatch.setattr(
        'sphinx._cli.util.errors.write_temporary_file',
        lambda content: 'sphinx-err-fake.log',
    )
    out = _handle(_raised(RuntimeError('boom')), print_traceback=True)

    assert 'in _raise' in out


def test_handle_exception_unexpected_errors_are_verbose(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Exceptions that are not SphinxError subclasses are unexpected, and keep
    # the full context and the bug report prompt.
    monkeypatch.setattr(
        'sphinx._cli.util.errors.write_temporary_file',
        lambda content: 'sphinx-err-fake.log',
    )
    out = _handle(_raised(RuntimeError('boom')))

    assert 'Versions' in out
    assert 'Loaded Extensions' in out
    assert 'full traceback has been saved' in out
    assert 'report this error to the developers' in out
