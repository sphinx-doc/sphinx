"""Tests for ``sphinx.util._files``."""

from __future__ import annotations

import os.path
import pickle
from typing import TYPE_CHECKING

from sphinx.util._files import FilenameUniqDict

if TYPE_CHECKING:
    import pytest


def test_add_file() -> None:
    d = FilenameUniqDict()
    assert d.add_file('doc', 'A/image.png') == 'image.png'
    # the same file is only added once
    assert d.add_file('doc', 'A/image.png') == 'image.png'
    assert d.add_file('doc', 'B/picture.png') == 'picture.png'


def test_add_file_case_insensitive_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    """Names differing only in case collide, as on Windows or macOS."""
    # simulate a case-insensitive filesystem, as on Windows
    monkeypatch.setattr(os.path, 'normcase', str.lower)
    d = FilenameUniqDict()
    assert d.add_file('doc', 'A/image.png') == 'image.png'
    # #14817: this used to keep the name ``Image.png``, which overwrote
    # ``image.png`` in the output on case-insensitive filesystems
    assert d.add_file('doc', 'B/Image.png') == 'Image1.png'
    assert d.add_file('doc', 'C/image.PNG') == 'image2.PNG'


def test_add_file_case_sensitive_filesystem(monkeypatch: pytest.MonkeyPatch) -> None:
    """On a case-sensitive filesystem, both files keep their own names."""
    # simulate a case-sensitive filesystem, as on Linux
    monkeypatch.setattr(os.path, 'normcase', lambda s: s)
    d = FilenameUniqDict()
    assert d.add_file('doc', 'A/image.png') == 'image.png'
    assert d.add_file('doc', 'B/Image.png') == 'Image.png'


def test_add_file_unique_names_differ_under_normcase() -> None:
    """Unique names must not collide under the local filesystem's rules."""
    d = FilenameUniqDict()
    first = d.add_file('doc', 'A/image.png')
    second = d.add_file('doc', 'B/Image.png')
    assert os.path.normcase(first) != os.path.normcase(second)


def test_purge_doc_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    """Purging frees names for reuse, compared case-insensitively."""
    monkeypatch.setattr(os.path, 'normcase', str.lower)
    d = FilenameUniqDict()
    d.add_file('doc1', 'A/image.png')
    d.add_file('doc2', 'B/Image.png')
    d.purge_doc('doc1')
    d.purge_doc('doc2')
    assert d.add_file('doc3', 'C/Image.png') == 'Image.png'


def test_pickle_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environments pickled before the fix are normalised when loaded."""
    monkeypatch.setattr(os.path, 'normcase', str.lower)
    d = FilenameUniqDict()
    # an environment pickled by an older Sphinx stored un-normalised names
    d.__setstate__({'Image.png'})
    assert d.add_file('doc', 'A/image.png') == 'image1.png'

    d = FilenameUniqDict()
    d.add_file('doc', 'A/image.png')
    d.add_file('doc', 'B/Image.png')
    restored = pickle.loads(pickle.dumps(d))
    assert restored.add_file('doc', 'A/image.png') == 'image.png'
    assert restored.add_file('doc', 'B/Image.png') == 'Image1.png'
