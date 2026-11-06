"""Tests for ``sphinx.util._files``."""

from __future__ import annotations

import pickle

from sphinx.util._files import FilenameUniqDict


def test_add_file() -> None:
    d = FilenameUniqDict()
    assert d.add_file('doc', 'A/image.png') == 'image.png'
    # the same file is only added once
    assert d.add_file('doc', 'A/image.png') == 'image.png'
    assert d.add_file('doc', 'B/picture.png') == 'picture.png'


def test_add_file_case_collision() -> None:
    """Names differing only in case collide on every platform."""
    d = FilenameUniqDict()
    assert d.add_file('doc', 'A/image.png') == 'image.png'
    # #14817: this used to keep the name ``Image.png``, which overwrote
    # ``image.png`` in the output on case-insensitive filesystems; the
    # comparison now always folds case so the output is portable
    assert d.add_file('doc', 'B/Image.png') == 'Image1.png'
    assert d.add_file('doc', 'C/image.PNG') == 'image2.PNG'


def test_add_file_keeps_original_spelling() -> None:
    """Only the comparison key is folded; stored names keep their case."""
    d = FilenameUniqDict()
    d.add_file('doc', 'A/image.png')
    assert d.add_file('doc', 'B/Image.png') == 'Image1.png'
    assert d['B/Image.png'] == ({'doc'}, 'Image1.png')


def test_add_file_no_full_unicode_case_folding() -> None:
    """Folding matches filesystems, not full Unicode case folding."""
    d = FilenameUniqDict()
    # ``str.casefold`` would equate ``ß`` and ``ss``, but they are
    # distinct names on every real filesystem
    assert d.add_file('doc', 'A/straße.png') == 'straße.png'
    assert d.add_file('doc', 'B/STRASSE.png') == 'STRASSE.png'


def test_purge_doc_case_folded() -> None:
    """Purging frees names for reuse, compared case-insensitively."""
    d = FilenameUniqDict()
    d.add_file('doc1', 'A/image.png')
    d.add_file('doc2', 'B/Image.png')
    d.purge_doc('doc1')
    d.purge_doc('doc2')
    assert d.add_file('doc3', 'C/Image.png') == 'Image.png'


def test_pickle_roundtrip() -> None:
    """Environments pickled before the fix are normalised when loaded."""
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
