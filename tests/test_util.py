"""Tests util functions."""

import os
import tempfile

import pytest

from sphinx.errors import ExtensionError
from sphinx.util import encode_uri, ensuredir, import_object, parselinenos


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


def test_parselinenos():
    assert parselinenos('1,2,3', 10) == [0, 1, 2]
    assert parselinenos('4, 5, 6', 10) == [3, 4, 5]
    assert parselinenos('-4', 10) == [0, 1, 2, 3]
    assert parselinenos('7-9', 10) == [6, 7, 8]
    assert parselinenos('7-', 10) == [6, 7, 8, 9]
    assert parselinenos('1,7-', 10) == [0, 6, 7, 8, 9]
    assert parselinenos('7-7', 10) == [6]
    assert parselinenos('11-', 10) == [10]
    with pytest.raises(ValueError, match="invalid line number spec: '1-2-3'"):
        parselinenos('1-2-3', 10)
    with pytest.raises(ValueError, match="invalid line number spec: 'abc-def'"):
        parselinenos('abc-def', 10)
    with pytest.raises(ValueError, match="invalid line number spec: '-'"):
        parselinenos('-', 10)
    with pytest.raises(ValueError, match="invalid line number spec: '3-1'"):
        parselinenos('3-1', 10)
