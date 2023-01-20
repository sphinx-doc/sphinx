"""Tests util functions."""

from unittest.mock import patch

import pytest

from sphinx.testing.util import strip_escseq
from sphinx.util import logging
from sphinx.util.display import (
    SkipProgressMessage,
    display_chunk,
    progress_message,
    status_iterator,
)


def test_display_chunk():
    assert display_chunk('hello') == 'hello'
    assert display_chunk(['hello']) == 'hello'
    assert display_chunk(['hello', 'sphinx', 'world']) == 'hello .. world'
    assert display_chunk(('hello',)) == 'hello'
    assert display_chunk(('hello', 'sphinx', 'world')) == 'hello .. world'


@pytest.mark.sphinx('dummy')
@patch('sphinx.util.console._tw', 40)  # terminal width = 40
def test_status_iterator(app, status, warning):
    logging.setup(app, status, warning)

    # # test for old_status_iterator
    # status.seek(0)
    # status.truncate(0)
    # yields = list(status_iterator(['hello', 'sphinx', 'world'], 'testing ... '))
    # output = strip_escseq(status.getvalue())
    # assert 'testing ... hello sphinx world \n' in output
    # assert yields == ['hello', 'sphinx', 'world']

    # test for status_iterator (verbosity=0)
    status.seek(0)
    status.truncate(0)
    yields = list(status_iterator(['hello', 'sphinx', 'world'], 'testing ... ',
                                  length=3, verbosity=0))
    output = strip_escseq(status.getvalue())
    assert 'testing ... [ 33%] hello                \r' in output
    assert 'testing ... [ 66%] sphinx               \r' in output
    assert 'testing ... [100%] world                \r\n' in output
    assert yields == ['hello', 'sphinx', 'world']

    # test for status_iterator (verbosity=1)
    status.seek(0)
    status.truncate(0)
    yields = list(status_iterator(['hello', 'sphinx', 'world'], 'testing ... ',
                                  length=3, verbosity=1))
    output = strip_escseq(status.getvalue())
    assert 'testing ... [ 33%] hello\n' in output
    assert 'testing ... [ 66%] sphinx\n' in output
    assert 'testing ... [100%] world\n\n' in output
    assert yields == ['hello', 'sphinx', 'world']


def test_progress_message(app, status, warning):
    logging.setup(app, status, warning)
    logger = logging.getLogger(__name__)

    # standard case
    with progress_message('testing'):
        logger.info('blah ', nonl=True)

    output = strip_escseq(status.getvalue())
    assert 'testing... blah done\n' in output

    # skipping case
    with progress_message('testing'):
        raise SkipProgressMessage('Reason: %s', 'error')

    output = strip_escseq(status.getvalue())
    assert 'testing... skipped\nReason: error\n' in output

    # error case
    try:
        with progress_message('testing'):
            raise
    except Exception:
        pass

    output = strip_escseq(status.getvalue())
    assert 'testing... failed\n' in output

    # decorator
    @progress_message('testing')
    def func():
        logger.info('in func ', nonl=True)

    func()
    output = strip_escseq(status.getvalue())
    assert 'testing... in func done\n' in output
