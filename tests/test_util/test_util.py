"""Tests util functions."""

from __future__ import annotations

from sphinx.util.osutil import ensuredir


def test_ensuredir(tmp_path):
    # Does not raise an exception for an existing directory.
    ensuredir(tmp_path)

    path = tmp_path / 'a' / 'b' / 'c'
    ensuredir(path)
    assert path.is_dir()
