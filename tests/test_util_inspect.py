# -*- coding: utf-8 -*-
"""
    test_util_inspect
    ~~~~~~~~~~~~~~~

    Tests util.inspect functions.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from unittest import TestCase

from sphinx.util import inspect


class TestSafeGetAttr(TestCase):
    def test_safe_getattr_with_default(self):
        class Foo(object):
            def __getattr__(self, item):
                raise Exception

        obj = Foo()

        result = inspect.safe_getattr(obj, 'bar', 'baz')

        assert result == 'baz'

    def test_safe_getattr_with_exception(self):
        class Foo(object):
            def __getattr__(self, item):
                raise Exception

        obj = Foo()

        with self.assertRaisesRegexp(AttributeError, 'bar'):
            inspect.safe_getattr(obj, 'bar')

    def test_safe_getattr_with_property_exception(self):
        class Foo(object):
            @property
            def bar(self):
                raise Exception

        obj = Foo()

        with self.assertRaisesRegexp(AttributeError, 'bar'):
            inspect.safe_getattr(obj, 'bar')

    def test_safe_getattr_with___dict___override(self):
        class Foo(object):
            @property
            def __dict__(self):
                raise Exception

        obj = Foo()

        with self.assertRaisesRegexp(AttributeError, 'bar'):
            inspect.safe_getattr(obj, 'bar')
