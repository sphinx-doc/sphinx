"""Test the autodoc extension.  This tests mainly for autodoc events"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.ext.autodoc import between, cut_lines

from tests.test_ext_autodoc.autodoc_util import FakeEvents, do_autodoc

if TYPE_CHECKING:
    from typing import Any

    from sphinx.application import Sphinx
    from sphinx.ext.autodoc._property_types import _AutodocObjType

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')


def test_process_docstring() -> None:
    def on_process_docstring(
        app: Sphinx,
        what: _AutodocObjType,
        name: str,
        obj: Any,
        options: Any,
        lines: list[str],
    ) -> None:
        lines.clear()
        lines.append('my docstring')

    events = FakeEvents()
    events.connect('autodoc-process-docstring', on_process_docstring)

    actual = do_autodoc('function', 'target.process_docstring.func', events=events)
    assert actual == [
        '',
        '.. py:function:: func()',
        '   :module: target.process_docstring',
        '',
        '   my docstring',
        '',
    ]


def test_process_docstring_for_nondatadescriptor() -> None:
    def on_process_docstring(
        app: Sphinx,
        what: _AutodocObjType,
        name: str,
        obj: Any,
        options: Any,
        lines: list[str],
    ) -> None:
        raise RuntimeError

    events = FakeEvents()
    events.connect('autodoc-process-docstring', on_process_docstring)

    actual = do_autodoc('attribute', 'target.AttCls.a1', events=events)
    assert actual == [
        '',
        '.. py:attribute:: AttCls.a1',
        '   :module: target',
        '   :value: hello world',
        '',
    ]


def test_cut_lines() -> None:
    events = FakeEvents()
    events.connect('autodoc-process-docstring', cut_lines(2, 2, ['function']))

    actual = do_autodoc('function', 'target.process_docstring.func', events=events)
    assert actual == [
        '',
        '.. py:function:: func()',
        '   :module: target.process_docstring',
        '',
        '   second line',
        '',
    ]


def test_cut_lines_no_objtype() -> None:
    docstring_lines = [
        'first line',
        '---',
        'second line',
        '---',
        'third line ',
        '',
    ]
    process = cut_lines(2)

    process(None, 'function', 'func', None, {}, docstring_lines)  # type: ignore[arg-type]
    assert docstring_lines == [
        'second line',
        '---',
        'third line ',
        '',
    ]


def test_between() -> None:
    events = FakeEvents()
    events.connect('autodoc-process-docstring', between('---', ['function']))

    actual = do_autodoc('function', 'target.process_docstring.func', events=events)
    assert actual == [
        '',
        '.. py:function:: func()',
        '   :module: target.process_docstring',
        '',
        '   second line',
        '',
    ]


def test_between_exclude() -> None:
    events = FakeEvents()
    events.connect(
        'autodoc-process-docstring', between('---', ['function'], exclude=True)
    )

    actual = do_autodoc('function', 'target.process_docstring.func', events=events)
    assert actual == [
        '',
        '.. py:function:: func()',
        '   :module: target.process_docstring',
        '',
        '   first line',
        '   third line',
        '',
    ]


def test_skip_module_member() -> None:
    def autodoc_skip_member(
        app: Sphinx,
        what: _AutodocObjType,
        name: str,
        obj: Any,
        skip: bool,
        options: Any,
    ) -> bool | None:
        if name == 'Class':
            return True  # Skip "Class" class in __all__
        elif name == 'raises':
            return False  # Show "raises()" function (not in __all__)
        return None

    events = FakeEvents()
    events.connect('autodoc-skip-member', autodoc_skip_member)

    options = {'members': None}
    actual = do_autodoc('module', 'target', events=events, options=options)
    assert actual == [
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
