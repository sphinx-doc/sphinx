"""
    test_napoleon_iterators
    ~~~~~~~~~~~~~~~~~~~~~~~

    Tests for :mod:`sphinx.ext.napoleon.iterators` module.


    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest import TestCase

from sphinx.ext.napoleon.iterators import modify_iter, peek_iter


class BaseIteratorsTest(TestCase):
    def assertEqualTwice(self, expected, func, *args):
        self.assertEqual(expected, func(*args))
        self.assertEqual(expected, func(*args))

    def assertFalseTwice(self, func, *args):
        self.assertFalse(func(*args))
        self.assertFalse(func(*args))

    def assertNext(self, it, expected, is_last):
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(expected, it.peek)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(expected, it.peek)
        self.assertTrueTwice(it.has_next)
        self.assertEqual(expected, next(it))
        if is_last:
            self.assertFalseTwice(it.has_next)
            self.assertRaisesTwice(StopIteration, it.next)
        else:
            self.assertTrueTwice(it.has_next)

    def assertRaisesTwice(self, exc, func, *args):
        self.assertRaises(exc, func, *args)
        self.assertRaises(exc, func, *args)

    def assertTrueTwice(self, func, *args):
        self.assertTrue(func(*args))
        self.assertTrue(func(*args))


class PeekIterTest(BaseIteratorsTest):
    def test_init_with_sentinel(self):
        a = iter(['1', '2', 'DONE'])
        sentinel = 'DONE'
        self.assertRaises(TypeError, peek_iter, a, sentinel)

        def get_next():
            return next(a)
        it = peek_iter(get_next, sentinel)
        self.assertEqual(it.sentinel, sentinel)
        self.assertNext(it, '1', is_last=False)
        self.assertNext(it, '2', is_last=True)

    def test_iter(self):
        a = ['1', '2', '3']
        it = peek_iter(a)
        self.assertTrue(it is it.__iter__())

        a = []
        b = [i for i in peek_iter(a)]
        self.assertEqual([], b)

        a = ['1']
        b = [i for i in peek_iter(a)]
        self.assertEqual(['1'], b)

        a = ['1', '2']
        b = [i for i in peek_iter(a)]
        self.assertEqual(['1', '2'], b)

        a = ['1', '2', '3']
        b = [i for i in peek_iter(a)]
        self.assertEqual(['1', '2', '3'], b)

    def test_next_with_multi(self):
        a = []
        it = peek_iter(a)
        self.assertFalseTwice(it.has_next)
        self.assertRaisesTwice(StopIteration, it.next, 2)

        a = ['1']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertRaisesTwice(StopIteration, it.next, 2)
        self.assertTrueTwice(it.has_next)

        a = ['1', '2']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqual(['1', '2'], it.next(2))
        self.assertFalseTwice(it.has_next)

        a = ['1', '2', '3']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqual(['1', '2'], it.next(2))
        self.assertTrueTwice(it.has_next)
        self.assertRaisesTwice(StopIteration, it.next, 2)
        self.assertTrueTwice(it.has_next)

        a = ['1', '2', '3', '4']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqual(['1', '2'], it.next(2))
        self.assertTrueTwice(it.has_next)
        self.assertEqual(['3', '4'], it.next(2))
        self.assertFalseTwice(it.has_next)
        self.assertRaisesTwice(StopIteration, it.next, 2)
        self.assertFalseTwice(it.has_next)

    def test_next_with_none(self):
        a = []
        it = peek_iter(a)
        self.assertFalseTwice(it.has_next)
        self.assertRaisesTwice(StopIteration, it.next)
        self.assertFalseTwice(it.has_next)

        a = ['1']
        it = peek_iter(a)
        self.assertEqual('1', it.__next__())

        a = ['1']
        it = peek_iter(a)
        self.assertNext(it, '1', is_last=True)

        a = ['1', '2']
        it = peek_iter(a)
        self.assertNext(it, '1', is_last=False)
        self.assertNext(it, '2', is_last=True)

        a = ['1', '2', '3']
        it = peek_iter(a)
        self.assertNext(it, '1', is_last=False)
        self.assertNext(it, '2', is_last=False)
        self.assertNext(it, '3', is_last=True)

    def test_next_with_one(self):
        a = []
        it = peek_iter(a)
        self.assertFalseTwice(it.has_next)
        self.assertRaisesTwice(StopIteration, it.next, 1)

        a = ['1']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqual(['1'], it.next(1))
        self.assertFalseTwice(it.has_next)
        self.assertRaisesTwice(StopIteration, it.next, 1)

        a = ['1', '2']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqual(['1'], it.next(1))
        self.assertTrueTwice(it.has_next)
        self.assertEqual(['2'], it.next(1))
        self.assertFalseTwice(it.has_next)
        self.assertRaisesTwice(StopIteration, it.next, 1)

    def test_next_with_zero(self):
        a = []
        it = peek_iter(a)
        self.assertFalseTwice(it.has_next)
        self.assertRaisesTwice(StopIteration, it.next, 0)

        a = ['1']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice([], it.next, 0)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice([], it.next, 0)

        a = ['1', '2']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice([], it.next, 0)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice([], it.next, 0)

    def test_peek_with_multi(self):
        a = []
        it = peek_iter(a)
        self.assertFalseTwice(it.has_next)
        self.assertEqualTwice([it.sentinel, it.sentinel], it.peek, 2)
        self.assertFalseTwice(it.has_next)

        a = ['1']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1', it.sentinel], it.peek, 2)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1', it.sentinel, it.sentinel], it.peek, 3)
        self.assertTrueTwice(it.has_next)

        a = ['1', '2']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1', '2'], it.peek, 2)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1', '2', it.sentinel], it.peek, 3)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1', '2', it.sentinel, it.sentinel], it.peek, 4)
        self.assertTrueTwice(it.has_next)

        a = ['1', '2', '3']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1', '2'], it.peek, 2)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1', '2', '3'], it.peek, 3)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1', '2', '3', it.sentinel], it.peek, 4)
        self.assertTrueTwice(it.has_next)
        self.assertEqual('1', next(it))
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['2', '3'], it.peek, 2)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['2', '3', it.sentinel], it.peek, 3)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['2', '3', it.sentinel, it.sentinel], it.peek, 4)
        self.assertTrueTwice(it.has_next)

    def test_peek_with_none(self):
        a = []
        it = peek_iter(a)
        self.assertFalseTwice(it.has_next)
        self.assertEqualTwice(it.sentinel, it.peek)
        self.assertFalseTwice(it.has_next)

        a = ['1']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice('1', it.peek)
        self.assertEqual('1', next(it))
        self.assertFalseTwice(it.has_next)
        self.assertEqualTwice(it.sentinel, it.peek)
        self.assertFalseTwice(it.has_next)

        a = ['1', '2']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice('1', it.peek)
        self.assertEqual('1', next(it))
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice('2', it.peek)
        self.assertEqual('2', next(it))
        self.assertFalseTwice(it.has_next)
        self.assertEqualTwice(it.sentinel, it.peek)
        self.assertFalseTwice(it.has_next)

    def test_peek_with_one(self):
        a = []
        it = peek_iter(a)
        self.assertFalseTwice(it.has_next)
        self.assertEqualTwice([it.sentinel], it.peek, 1)
        self.assertFalseTwice(it.has_next)

        a = ['1']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1'], it.peek, 1)
        self.assertEqual('1', next(it))
        self.assertFalseTwice(it.has_next)
        self.assertEqualTwice([it.sentinel], it.peek, 1)
        self.assertFalseTwice(it.has_next)

        a = ['1', '2']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['1'], it.peek, 1)
        self.assertEqual('1', next(it))
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice(['2'], it.peek, 1)
        self.assertEqual('2', next(it))
        self.assertFalseTwice(it.has_next)
        self.assertEqualTwice([it.sentinel], it.peek, 1)
        self.assertFalseTwice(it.has_next)

    def test_peek_with_zero(self):
        a = []
        it = peek_iter(a)
        self.assertFalseTwice(it.has_next)
        self.assertEqualTwice([], it.peek, 0)

        a = ['1']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice([], it.peek, 0)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice([], it.peek, 0)

        a = ['1', '2']
        it = peek_iter(a)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice([], it.peek, 0)
        self.assertTrueTwice(it.has_next)
        self.assertEqualTwice([], it.peek, 0)


class ModifyIterTest(BaseIteratorsTest):
    def test_init_with_sentinel_args(self):
        a = iter(['1', '2', '3', 'DONE'])
        sentinel = 'DONE'

        def get_next():
            return next(a)
        it = modify_iter(get_next, sentinel, int)
        expected = [1, 2, 3]
        self.assertEqual(expected, [i for i in it])

    def test_init_with_sentinel_kwargs(self):
        a = iter([1, 2, 3, 4])
        sentinel = 4

        def get_next():
            return next(a)
        it = modify_iter(get_next, sentinel, modifier=str)
        expected = ['1', '2', '3']
        self.assertEqual(expected, [i for i in it])

    def test_modifier_default(self):
        a = ['', '  ', '  a  ', 'b  ', '  c', '  ', '']
        it = modify_iter(a)
        expected = ['', '  ', '  a  ', 'b  ', '  c', '  ', '']
        self.assertEqual(expected, [i for i in it])

    def test_modifier_not_callable(self):
        self.assertRaises(TypeError, modify_iter, [1], modifier='not_callable')

    def test_modifier_rstrip(self):
        a = ['', '  ', '  a  ', 'b  ', '  c', '  ', '']
        it = modify_iter(a, modifier=lambda s: s.rstrip())
        expected = ['', '', '  a', 'b', '  c', '', '']
        self.assertEqual(expected, [i for i in it])

    def test_modifier_rstrip_unicode(self):
        a = ['', '  ', '  a  ', 'b  ', '  c', '  ', '']
        it = modify_iter(a, modifier=lambda s: s.rstrip())
        expected = ['', '', '  a', 'b', '  c', '', '']
        self.assertEqual(expected, [i for i in it])
