"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

from functools import singledispatchmethod
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from sphinx.ext.autodoc import Options

# NEVER import these objects from sphinx.ext.autodoc directly
from sphinx.ext.autodoc.directive import DocumenterBridge
from sphinx.util.inspect import is_singledispatch_method

from tests.test_extensions.autodoc_util import do_autodoc

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


class Foo:
    """docstring"""

    @singledispatchmethod
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
    obj = Foo.__dict__['meth']
    assert isinstance(obj, singledispatchmethod)


def make_directive_bridge(env: BuildEnvironment) -> DocumenterBridge:
    options = Options(
        inherited_members=False,
        undoc_members=False,
        private_members=False,
        special_members=False,
        imported_members=False,
        show_inheritance=False,
        no_index=False,
        annotation=None,
        synopsis='',
        platform='',
        deprecated=False,
        members=[],
        member_order='alphabetical',
        exclude_members=set(),
        ignore_module_all=False,
    )

    directive = DocumenterBridge(
        env=env,
        reporter=None,
        options=options,
        lineno=0,
        state=Mock(),
    )
    directive.state.document.settings.tab_width = 8

    return directive


processed_signatures = []


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
