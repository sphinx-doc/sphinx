from __future__ import annotations

import functools
import sys
import types

import pytest

from tests.test_extensions.autodoc_util import do_autodoc


class Foo:
    """docstring"""

    @functools.singledispatchmethod
    def meth(self, arg, kwarg=None):
        """A method for general use."""
        pass

    @meth.register(int)
    @meth.register(float)
    def _meth_int(self, arg, kwarg=None):
        """A method for int."""
        pass

    @meth.register(str)
    def _meth_str(self, arg, kwarg=None):
        """A method for str."""
        pass

    @meth.register
    def _meth_dict(self, arg: dict, kwarg=None):
        """A method for dict."""
        # This function tests for specifying type through annotations
        pass


def test_is_singledispatch_method():
    print(sys.version_info)
    assert isinstance(Foo.__dict__['meth'], functools.singledispatchmethod)
    if sys.version_info >= (3, 14, 0, 'alpha', 6):
        assert isinstance(Foo.meth, functools._singledispatchmethod_get)
    else:
        assert isinstance(Foo.meth, types.FunctionType)
    meth = Foo.__dict__['meth']
    assert len(meth.dispatcher.registry) == 5
    assert list(meth.dispatcher.registry) == [object, float, int, str, dict]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatch(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.singledispatch', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.singledispatch',
        '',
        '',
        '.. py:function:: func(arg, kwarg=None)',
        '                 func(arg: float, kwarg=None)',
        '                 func(arg: int, kwarg=None)',
        '                 func(arg: str, kwarg=None)',
        '                 func(arg: dict, kwarg=None)',
        '   :module: target.singledispatch',
        '',
        '   A function for general use.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatchmethod(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.singledispatchmethod', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.singledispatchmethod',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.singledispatchmethod',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Foo.meth(arg, kwarg=None)',
        '                  Foo.meth(arg: float, kwarg=None)',
        '                  Foo.meth(arg: int, kwarg=None)',
        '                  Foo.meth(arg: str, kwarg=None)',
        '                  Foo.meth(arg: dict, kwarg=None)',
        '      :module: target.singledispatchmethod',
        '',
        '      A method for general use.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatchmethod_automethod(app):
    options = {}
    actual = do_autodoc(app, 'method', 'target.singledispatchmethod.Foo.meth', options)
    assert list(actual) == [
        '',
        '.. py:method:: Foo.meth(arg, kwarg=None)',
        '               Foo.meth(arg: float, kwarg=None)',
        '               Foo.meth(arg: int, kwarg=None)',
        '               Foo.meth(arg: str, kwarg=None)',
        '               Foo.meth(arg: dict, kwarg=None)',
        '   :module: target.singledispatchmethod',
        '',
        '   A method for general use.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatchmethod_classmethod(app):
    options = {'members': None}
    actual = do_autodoc(
        app, 'module', 'target.singledispatchmethod_classmethod', options
    )

    assert list(actual) == [
        '',
        '.. py:module:: target.singledispatchmethod_classmethod',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.singledispatchmethod_classmethod',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Foo.class_meth(arg, kwarg=None)',
        '                  Foo.class_meth(arg: float, kwarg=None)',
        '                  Foo.class_meth(arg: int, kwarg=None)',
        '                  Foo.class_meth(arg: str, kwarg=None)',
        '                  Foo.class_meth(arg: dict, kwarg=None)',
        '      :module: target.singledispatchmethod_classmethod',
        '      :classmethod:',
        '',
        '      A class method for general use.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatchmethod_classmethod_automethod(app):
    options = {}
    actual = do_autodoc(
        app, 'method', 'target.singledispatchmethod_classmethod.Foo.class_meth', options
    )

    assert list(actual) == [
        '',
        '.. py:method:: Foo.class_meth(arg, kwarg=None)',
        '               Foo.class_meth(arg: float, kwarg=None)',
        '               Foo.class_meth(arg: int, kwarg=None)',
        '               Foo.class_meth(arg: str, kwarg=None)',
        '               Foo.class_meth(arg: dict, kwarg=None)',
        '   :module: target.singledispatchmethod_classmethod',
        '   :classmethod:',
        '',
        '   A class method for general use.',
        '',
    ]
