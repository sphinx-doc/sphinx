"""
    test_util
    ~~~~~~~~~~~~~~~

    Tests util functions.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from sphinx.errors import ExtensionError
from sphinx.testing.util import strip_escseq
from sphinx.util import (SkipProgressMessage, display_chunk, encode_uri, ensuredir,
                         import_object, logging, parselinenos, progress_message,
                         status_iterator, xmlname_checker)


def test_encode_uri():
    expected = ('https://ru.wikipedia.org/wiki/%D0%A1%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D0%B0_'
                '%D1%83%D0%BF%D1%80%D0%B0%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D1%8F_'
                '%D0%B1%D0%B0%D0%B7%D0%B0%D0%BC%D0%B8_%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D1%85')
    uri = ('https://ru.wikipedia.org/wiki'
           '/Система_управления_базами_данных')
    assert expected == encode_uri(uri)

    expected = ('https://github.com/search?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+is%3A'
                'sprint-friendly+user%3Ajupyter&type=Issues&ref=searchresults')
    uri = ('https://github.com/search?utf8=✓&q=is%3Aissue+is%3Aopen+is%3A'
           'sprint-friendly+user%3Ajupyter&type=Issues&ref=searchresults')
    assert expected == encode_uri(uri)


def test_ensuredir():
    with tempfile.TemporaryDirectory() as tmp_path:
        # Does not raise an exception for an existing directory.
        ensuredir(tmp_path)

        path = os.path.join(tmp_path, 'a', 'b', 'c')
        ensuredir(path)
        assert os.path.isdir(path)

    with tempfile.NamedTemporaryFile() as tmp:
        with pytest.raises(OSError):
            ensuredir(tmp.name)


def test_display_chunk():
    assert display_chunk('hello') == 'hello'
    assert display_chunk(['hello']) == 'hello'
    assert display_chunk(['hello', 'sphinx', 'world']) == 'hello .. world'
    assert display_chunk(('hello',)) == 'hello'
    assert display_chunk(('hello', 'sphinx', 'world')) == 'hello .. world'


def test_import_object():
    module = import_object('sphinx')
    assert module.__name__ == 'sphinx'

    module = import_object('sphinx.application')
    assert module.__name__ == 'sphinx.application'

    obj = import_object('sphinx.application.Sphinx')
    assert obj.__name__ == 'Sphinx'

    with pytest.raises(ExtensionError) as exc:
        import_object('sphinx.unknown_module')
    assert exc.value.args[0] == 'Could not import sphinx.unknown_module'

    with pytest.raises(ExtensionError) as exc:
        import_object('sphinx.unknown_module', 'my extension')
    assert exc.value.args[0] == ('Could not import sphinx.unknown_module '
                                 '(needed for my extension)')


@pytest.mark.sphinx('dummy')
@patch('sphinx.util.console._tw', 40)  # terminal width = 40
def test_status_iterator(app, status, warning):
    logging.setup(app, status, warning)

    # test for old_status_iterator
    status.truncate(0)
    yields = list(status_iterator(['hello', 'sphinx', 'world'], 'testing ... '))
    output = strip_escseq(status.getvalue())
    assert 'testing ... hello sphinx world \n' in output
    assert yields == ['hello', 'sphinx', 'world']

    # test for status_iterator (verbosity=0)
    status.truncate(0)
    yields = list(status_iterator(['hello', 'sphinx', 'world'], 'testing ... ',
                                  length=3, verbosity=0))
    output = strip_escseq(status.getvalue())
    assert 'testing ... [ 33%] hello                \r' in output
    assert 'testing ... [ 66%] sphinx               \r' in output
    assert 'testing ... [100%] world                \r\n' in output
    assert yields == ['hello', 'sphinx', 'world']

    # test for status_iterator (verbosity=1)
    status.truncate(0)
    yields = list(status_iterator(['hello', 'sphinx', 'world'], 'testing ... ',
                                  length=3, verbosity=1))
    output = strip_escseq(status.getvalue())
    assert 'testing ... [ 33%] hello\n' in output
    assert 'testing ... [ 66%] sphinx\n' in output
    assert 'testing ... [100%] world\n\n' in output
    assert yields == ['hello', 'sphinx', 'world']


def test_parselinenos():
    assert parselinenos('1,2,3', 10) == [0, 1, 2]
    assert parselinenos('4, 5, 6', 10) == [3, 4, 5]
    assert parselinenos('-4', 10) == [0, 1, 2, 3]
    assert parselinenos('7-9', 10) == [6, 7, 8]
    assert parselinenos('7-', 10) == [6, 7, 8, 9]
    assert parselinenos('1,7-', 10) == [0, 6, 7, 8, 9]
    assert parselinenos('7-7', 10) == [6]
    assert parselinenos('11-', 10) == [10]
    with pytest.raises(ValueError):
        parselinenos('1-2-3', 10)
    with pytest.raises(ValueError):
        parselinenos('abc-def', 10)
    with pytest.raises(ValueError):
        parselinenos('-', 10)
    with pytest.raises(ValueError):
        parselinenos('3-1', 10)


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


def test_xmlname_check():
    checker = xmlname_checker()
    assert checker.match('id-pub')
    assert checker.match('webpage')
    assert not checker.match('1bfda21')
