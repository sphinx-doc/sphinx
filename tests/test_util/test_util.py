"""Tests util functions."""

import os
import tempfile

import pytest

from sphinx.util import parselinenos
from sphinx.util.osutil import ensuredir


def test_ensuredir():
    with tempfile.TemporaryDirectory() as tmp_path:
        # Does not raise an exception for an existing directory.
        ensuredir(tmp_path)

        path = os.path.join(tmp_path, 'a', 'b', 'c')
        ensuredir(path)
        assert os.path.isdir(path)


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
