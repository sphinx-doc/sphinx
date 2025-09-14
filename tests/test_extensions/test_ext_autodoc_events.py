"""Test the autodoc extension.  This tests mainly for autodoc events"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.ext.autodoc import between, cut_lines

from tests.test_extensions.autodoc_util import do_autodoc

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_process_docstring(app: SphinxTestApp) -> None:
    def on_process_docstring(app, what, name, obj, options, lines):
        lines.clear()
        lines.append('my docstring')

    app.connect('autodoc-process-docstring', on_process_docstring)

    actual = do_autodoc(app, 'function', 'target.process_docstring.func')
    assert list(actual) == [
        '',
        '.. py:function:: func()',
        '   :module: target.process_docstring',
        '',
        '   my docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_process_docstring_for_nondatadescriptor(app: SphinxTestApp) -> None:
    def on_process_docstring(app, what, name, obj, options, lines):
        raise RuntimeError

    app.connect('autodoc-process-docstring', on_process_docstring)

    actual = do_autodoc(app, 'attribute', 'target.AttCls.a1')
    assert list(actual) == [
        '',
        '.. py:attribute:: AttCls.a1',
        '   :module: target',
        '   :value: hello world',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_cut_lines(app: SphinxTestApp) -> None:
    app.connect('autodoc-process-docstring', cut_lines(2, 2, ['function']))

    actual = do_autodoc(app, 'function', 'target.process_docstring.func')
    assert list(actual) == [
        '',
        '.. py:function:: func()',
        '   :module: target.process_docstring',
        '',
        '   second line',
        '',
    ]


def test_cut_lines_no_objtype():
    docstring_lines = [
        'first line',
        '---',
        'second line',
        '---',
        'third line ',
        '',
    ]
    process = cut_lines(2)

    process(None, 'function', 'func', None, {}, docstring_lines)
    assert docstring_lines == [
        'second line',
        '---',
        'third line ',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_between(app: SphinxTestApp) -> None:
    app.connect('autodoc-process-docstring', between('---', ['function']))

    actual = do_autodoc(app, 'function', 'target.process_docstring.func')
    assert list(actual) == [
        '',
        '.. py:function:: func()',
        '   :module: target.process_docstring',
        '',
        '   second line',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_between_exclude(app: SphinxTestApp) -> None:
    app.connect('autodoc-process-docstring', between('---', ['function'], exclude=True))

    actual = do_autodoc(app, 'function', 'target.process_docstring.func')
    assert list(actual) == [
        '',
        '.. py:function:: func()',
        '   :module: target.process_docstring',
        '',
        '   first line',
        '   third line',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_skip_module_member(app: SphinxTestApp) -> None:
    def autodoc_skip_member(app, what, name, obj, skip, options):
        if name == 'Class':
            return True  # Skip "Class" class in __all__
        elif name == 'raises':
            return False  # Show "raises()" function (not in __all__)
        return None

    app.connect('autodoc-skip-member', autodoc_skip_member)

    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target', options)
    assert list(actual) == [
        '',
        '.. py:module:: target',
        '',
        # TODO: consider.
        # '',
        # '.. py:function:: raises(exc, func, *args, **kwds)',
        # '   :module: target',
        # '',
        # '   Raise AssertionError if ``func(*args, **kwds)`` does not raise *exc*.',
        # '',
    ]
