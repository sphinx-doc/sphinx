"""Tests for :mod:`sphinx.ext.napoleon.iterators` module."""

import sys

import pytest

from sphinx.deprecation import RemovedInSphinx70Warning

with pytest.warns(DeprecationWarning,
                  match="sphinx.ext.napoleon.iterators is deprecated."):
    from sphinx.ext.napoleon.iterators import modify_iter, peek_iter


class TestModuleIsDeprecated:
    def test_module_is_deprecated(self):
        sys.modules.pop("sphinx.ext.napoleon.iterators")
        with pytest.warns(RemovedInSphinx70Warning,
                          match="sphinx.ext.napoleon.iterators is deprecated."):
            import sphinx.ext.napoleon.iterators  # noqa: F401


def _assert_equal_twice(expected, func, *args):
    assert expected == func(*args)
    assert expected == func(*args)


def _assert_false_twice(func, *args):
    assert not func(*args)
    assert not func(*args)


def _assert_next(it, expected, is_last):
    _assert_true_twice(it.has_next)
    _assert_equal_twice(expected, it.peek)
    _assert_true_twice(it.has_next)
    _assert_equal_twice(expected, it.peek)
    _assert_true_twice(it.has_next)
    assert expected == next(it)
    if is_last:
        _assert_false_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next)
    else:
        _assert_true_twice(it.has_next)


def _assert_raises_twice(exc, func, *args):
    with pytest.raises(exc):
        func(*args)
    with pytest.raises(exc):
        func(*args)


def _assert_true_twice(func, *args):
    assert func(*args)
    assert func(*args)


class TestPeekIter:
    def test_init_with_sentinel(self):
        a = iter(['1', '2', 'DONE'])
        sentinel = 'DONE'
        with pytest.raises(TypeError):
            peek_iter(a, sentinel)

        def get_next():
            return next(a)
        it = peek_iter(get_next, sentinel)
        assert it.sentinel == sentinel
        _assert_next(it, '1', is_last=False)
        _assert_next(it, '2', is_last=True)

    def test_iter(self):
        a = ['1', '2', '3']
        it = peek_iter(a)
        assert it is it.__iter__()

        a = []
        b = list(peek_iter(a))
        assert [] == b

        a = ['1']
        b = list(peek_iter(a))
        assert ["1"] == b

        a = ['1', '2']
        b = list(peek_iter(a))
        assert ["1", "2"] == b

        a = ['1', '2', '3']
        b = list(peek_iter(a))
        assert ["1", "2", "3"] == b

    def test_next_with_multi(self):
        a = []
        it = peek_iter(a)
        _assert_false_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next, 2)

        a = ['1']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next, 2)
        _assert_true_twice(it.has_next)

        a = ['1', '2']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        assert ["1", "2"] == it.next(2)
        _assert_false_twice(it.has_next)

        a = ['1', '2', '3']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        assert ["1", "2"] == it.next(2)
        _assert_true_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next, 2)
        _assert_true_twice(it.has_next)

        a = ['1', '2', '3', '4']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        assert ["1", "2"] == it.next(2)
        _assert_true_twice(it.has_next)
        assert ["3", "4"] == it.next(2)
        _assert_false_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next, 2)
        _assert_false_twice(it.has_next)

    def test_next_with_none(self):
        a = []
        it = peek_iter(a)
        _assert_false_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next)
        _assert_false_twice(it.has_next)

        a = ['1']
        it = peek_iter(a)
        assert it.__next__() == "1"

        a = ['1']
        it = peek_iter(a)
        _assert_next(it, '1', is_last=True)

        a = ['1', '2']
        it = peek_iter(a)
        _assert_next(it, '1', is_last=False)
        _assert_next(it, '2', is_last=True)

        a = ['1', '2', '3']
        it = peek_iter(a)
        _assert_next(it, '1', is_last=False)
        _assert_next(it, '2', is_last=False)
        _assert_next(it, '3', is_last=True)

    def test_next_with_one(self):
        a = []
        it = peek_iter(a)
        _assert_false_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next, 1)

        a = ['1']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        assert ["1"] == it.next(1)
        _assert_false_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next, 1)

        a = ['1', '2']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        assert ["1"] == it.next(1)
        _assert_true_twice(it.has_next)
        assert ["2"] == it.next(1)
        _assert_false_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next, 1)

    def test_next_with_zero(self):
        a = []
        it = peek_iter(a)
        _assert_false_twice(it.has_next)
        _assert_raises_twice(StopIteration, it.next, 0)

        a = ['1']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice([], it.next, 0)
        _assert_true_twice(it.has_next)
        _assert_equal_twice([], it.next, 0)

        a = ['1', '2']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice([], it.next, 0)
        _assert_true_twice(it.has_next)
        _assert_equal_twice([], it.next, 0)

    def test_peek_with_multi(self):
        a = []
        it = peek_iter(a)
        _assert_false_twice(it.has_next)
        _assert_equal_twice([it.sentinel, it.sentinel], it.peek, 2)
        _assert_false_twice(it.has_next)

        a = ['1']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1', it.sentinel], it.peek, 2)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1', it.sentinel, it.sentinel], it.peek, 3)
        _assert_true_twice(it.has_next)

        a = ['1', '2']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1', '2'], it.peek, 2)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1', '2', it.sentinel], it.peek, 3)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1', '2', it.sentinel, it.sentinel], it.peek, 4)
        _assert_true_twice(it.has_next)

        a = ['1', '2', '3']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1', '2'], it.peek, 2)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1', '2', '3'], it.peek, 3)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1', '2', '3', it.sentinel], it.peek, 4)
        _assert_true_twice(it.has_next)
        assert next(it) == "1"
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['2', '3'], it.peek, 2)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['2', '3', it.sentinel], it.peek, 3)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['2', '3', it.sentinel, it.sentinel], it.peek, 4)
        _assert_true_twice(it.has_next)

    def test_peek_with_none(self):
        a = []
        it = peek_iter(a)
        _assert_false_twice(it.has_next)
        _assert_equal_twice(it.sentinel, it.peek)
        _assert_false_twice(it.has_next)

        a = ['1']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice('1', it.peek)
        assert next(it) == "1"
        _assert_false_twice(it.has_next)
        _assert_equal_twice(it.sentinel, it.peek)
        _assert_false_twice(it.has_next)

        a = ['1', '2']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice('1', it.peek)
        assert next(it) == "1"
        _assert_true_twice(it.has_next)
        _assert_equal_twice('2', it.peek)
        assert next(it) == "2"
        _assert_false_twice(it.has_next)
        _assert_equal_twice(it.sentinel, it.peek)
        _assert_false_twice(it.has_next)

    def test_peek_with_one(self):
        a = []
        it = peek_iter(a)
        _assert_false_twice(it.has_next)
        _assert_equal_twice([it.sentinel], it.peek, 1)
        _assert_false_twice(it.has_next)

        a = ['1']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1'], it.peek, 1)
        assert next(it) == "1"
        _assert_false_twice(it.has_next)
        _assert_equal_twice([it.sentinel], it.peek, 1)
        _assert_false_twice(it.has_next)

        a = ['1', '2']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['1'], it.peek, 1)
        assert next(it) == "1"
        _assert_true_twice(it.has_next)
        _assert_equal_twice(['2'], it.peek, 1)
        assert next(it) == "2"
        _assert_false_twice(it.has_next)
        _assert_equal_twice([it.sentinel], it.peek, 1)
        _assert_false_twice(it.has_next)

    def test_peek_with_zero(self):
        a = []
        it = peek_iter(a)
        _assert_false_twice(it.has_next)
        _assert_equal_twice([], it.peek, 0)

        a = ['1']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice([], it.peek, 0)
        _assert_true_twice(it.has_next)
        _assert_equal_twice([], it.peek, 0)

        a = ['1', '2']
        it = peek_iter(a)
        _assert_true_twice(it.has_next)
        _assert_equal_twice([], it.peek, 0)
        _assert_true_twice(it.has_next)
        _assert_equal_twice([], it.peek, 0)


class TestModifyIter:
    def test_init_with_sentinel_args(self):
        a = iter(['1', '2', '3', 'DONE'])
        sentinel = 'DONE'

        def get_next():
            return next(a)
        it = modify_iter(get_next, sentinel, int)
        expected = [1, 2, 3]
        assert expected == list(it)

    def test_init_with_sentinel_kwargs(self):
        a = iter([1, 2, 3, 4])
        sentinel = 4

        def get_next():
            return next(a)
        it = modify_iter(get_next, sentinel, modifier=str)
        expected = ['1', '2', '3']
        assert expected == list(it)

    def test_modifier_default(self):
        a = ['', '  ', '  a  ', 'b  ', '  c', '  ', '']
        it = modify_iter(a)
        expected = ['', '  ', '  a  ', 'b  ', '  c', '  ', '']
        assert expected == list(it)

    def test_modifier_not_callable(self):
        with pytest.raises(TypeError):
            modify_iter([1], modifier='not_callable')

    def test_modifier_rstrip(self):
        a = ['', '  ', '  a  ', 'b  ', '  c', '  ', '']
        it = modify_iter(a, modifier=lambda s: s.rstrip())
        expected = ['', '', '  a', 'b', '  c', '', '']
        assert expected == list(it)

    def test_modifier_rstrip_unicode(self):
        a = ['', '  ', '  a  ', 'b  ', '  c', '  ', '']
        it = modify_iter(a, modifier=lambda s: s.rstrip())
        expected = ['', '', '  a', 'b', '  c', '', '']
        assert expected == list(it)
