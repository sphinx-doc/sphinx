from __future__ import annotations

from sphinx.testing._matcher import cleaner


def test_strip_function():
    assert cleaner.strip_chars('abaaa\n') == 'abaaa'
    assert cleaner.strip_chars('abaaa\n', False) == 'abaaa\n'
    assert cleaner.strip_chars('abaaa', 'a') == 'b'
    assert cleaner.strip_chars('abaaa', 'ab') == ''


def test_strip_lines_function():
    assert list(cleaner.strip_lines(['aba\n', 'aba\n'])) == ['aba', 'aba']
    assert list(cleaner.strip_lines(['aba\n', 'aba\n'], False)) == ['aba\n', 'aba\n']
    assert list(cleaner.strip_lines(['aba', 'aba'], 'a')) == ['b', 'b']
    assert list(cleaner.strip_lines(['aba', 'aba'], 'ab')) == ['', '']


def test_filterlines():
    src = ['a', 'a', '', 'a', 'b', 'c', 'a']
    assert list(cleaner.filterlines(src, empty=False, compress=True)) == ['a', 'b', 'c', 'a']
    assert list(cleaner.filterlines(src, empty=False, unique=True)) == ['a', 'b', 'c']

    expect = ['a', '', 'a', 'b', 'c', 'a']
    assert list(cleaner.filterlines(src, empty=True, compress=True)) == expect

    assert list(cleaner.filterlines(src, empty=True, unique=True)) == ['a', '', 'b', 'c']
