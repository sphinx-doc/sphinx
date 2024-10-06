"""Tests util functions."""

import os
import tempfile

from sphinx.util.osutil import ensuredir


def test_ensuredir():
    with tempfile.TemporaryDirectory() as tmp_path:
        # Does not raise an exception for an existing directory.
        ensuredir(tmp_path)

        path = os.path.join(tmp_path, 'a', 'b', 'c')
        ensuredir(path)
        assert os.path.isdir(path)
