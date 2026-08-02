"""Tests util functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx._cli.util.colour import disable_colour, enable_colour
from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.util import logging
from sphinx.util.display import (
    SkipProgressMessage,
    display_chunk,
    progress_message,
    status_iterator,
)

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


def test_display_chunk() -> None:
    assert display_chunk('hello') == 'hello'
    assert display_chunk(['hello']) == 'hello'
    assert display_chunk(['hello', 'sphinx', 'world']) == 'hello .. world'
    assert display_chunk(('hello',)) == 'hello'
    assert display_chunk(('hello', 'sphinx', 'world')) == 'hello .. world'


@pytest.mark.sphinx('dummy', testroot='root')
def test_status_iterator_length_0(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)

    # test for status_iterator (length=0)
    app.status.seek(0)
    app.status.truncate(0)
    yields = list(status_iterator(['hello', 'sphinx', 'world'], 'testing ... '))
    output = strip_escape_sequences(app.status.getvalue())
    assert 'testing ... hello sphinx world \n' in output
    assert yields == ['hello', 'sphinx', 'world']


@pytest.mark.sphinx('dummy', testroot='root')
def test_status_iterator_verbosity_0(
    app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv('FORCE_COLOR', '1')
    logging.setup(app, app.status, app.warning)

    # test for status_iterator (verbosity=0)
    app.status.seek(0)
    app.status.truncate(0)
    yields = status_iterator(
        ['hello', 'sphinx', 'world'], 'testing ... ', length=3, verbosity=0
    )
    assert list(yields) == ['hello', 'sphinx', 'world']
    output = strip_escape_sequences(app.status.getvalue())
    assert 'testing ... [ 33%] hello\r' in output
    assert 'testing ... [ 67%] sphinx\r' in output
    assert 'testing ... [100%] world\r\n' in output


@pytest.mark.sphinx('dummy', testroot='root')
def test_status_iterator_verbosity_1(
    app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv('FORCE_COLOR', '1')
    logging.setup(app, app.status, app.warning)

    # test for status_iterator (verbosity=1)
    app.status.seek(0)
    app.status.truncate(0)
    yields = status_iterator(
        ['hello', 'sphinx', 'world'], 'testing ... ', length=3, verbosity=1
    )
    assert list(yields) == ['hello', 'sphinx', 'world']
    output = strip_escape_sequences(app.status.getvalue())
    assert 'testing ... [ 33%] hello\n' in output
    assert 'testing ... [ 67%] sphinx\n' in output
    assert 'testing ... [100%] world\n\n' in output


@pytest.mark.sphinx('dummy', testroot='root')
def test_status_iterator_colour_disabled(
    app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch
) -> None:
    # ``--no-color`` disables colouring without setting NO_COLOR, so the
    # terminal still reports colour support. The single-line progress output
    # must not emit ANSI control sequences in that case.
    monkeypatch.setenv('FORCE_COLOR', '1')
    logging.setup(app, app.status, app.warning)

    app.status.seek(0)
    app.status.truncate(0)
    disable_colour()
    try:
        yields = status_iterator(
            ['hello', 'sphinx', 'world'], 'testing ... ', length=3, verbosity=0
        )
        assert list(yields) == ['hello', 'sphinx', 'world']
    finally:
        enable_colour()

    output = app.status.getvalue()
    assert 'testing ... [100%] world' in output
    assert output == strip_escape_sequences(output)


@pytest.mark.sphinx('html', testroot='root')
def test_progress_message(app: SphinxTestApp) -> None:
    logging.setup(app, app.status, app.warning)
    logger = logging.getLogger(__name__)

    # standard case
    with progress_message('testing'):
        logger.info('blah ', nonl=True)

    output = strip_escape_sequences(app.status.getvalue())
    assert 'testing... blah done\n' in output

    # skipping case
    with progress_message('testing'):
        raise SkipProgressMessage('Reason: %s', 'error')  # NoQA: EM101,TRY003

    output = strip_escape_sequences(app.status.getvalue())
    assert 'testing... skipped\nReason: error\n' in output

    # error case
    try:
        with progress_message('testing'):
            raise RuntimeError  # NoQA: TRY301
    except Exception:
        pass

    output = strip_escape_sequences(app.status.getvalue())
    assert 'testing... failed\n' in output

    # decorator
    @progress_message('testing')
    def func() -> None:
        logger.info('in func ', nonl=True)

    func()
    output = strip_escape_sequences(app.status.getvalue())
    assert 'testing... in func done\n' in output
