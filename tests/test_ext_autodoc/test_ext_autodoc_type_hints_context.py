from __future__ import annotations

import sys
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest

from sphinx.ext.autodoc._type_hints import _get_type_hints

from tests.test_ext_autodoc.autodoc_util import FakeEvents, do_autodoc

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path
    from types import ModuleType
    from typing import Any

    from sphinx.application import Sphinx
    from sphinx.testing.util import SphinxTestApp


def test_type_hints_context_surrounds_evaluation() -> None:
    events = FakeEvents()
    calls = []

    def subject(value: int) -> None:
        pass

    subject.__annotations__['value'] = 'Transient'

    @contextmanager
    def supply_name(app: Sphinx, obj: object) -> Generator[None]:
        assert obj is subject
        calls.append('enter')
        subject.__globals__['Transient'] = int
        try:
            yield
        finally:
            del subject.__globals__['Transient']
            calls.append('exit')

    events.connect('autodoc-type-hints-context', supply_name)
    assert _get_type_hints(events, subject) == {'value': int, 'return': type(None)}
    assert calls == ['enter', 'exit']
    assert 'Transient' not in subject.__globals__


@pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')
def test_type_hints_context_in_dynamic_attribute_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / 'autodoc_context_target.py').write_text(
        'from __future__ import annotations\nclass Item:\n    value: Missing\n',
        encoding='utf-8',
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    events = FakeEvents()
    visited = []

    @contextmanager
    def supply_name(app: Sphinx, obj: Any) -> Generator[None]:
        module: ModuleType = sys.modules[obj.__module__]
        visited.append(obj)
        module.__dict__['Missing'] = int
        try:
            yield
        finally:
            del module.__dict__['Missing']

    events.connect('autodoc-type-hints-context', supply_name)
    output = do_autodoc('attribute', 'autodoc_context_target.Item.value', events=events)
    assert any(':type: int' in line for line in output)
    assert visited
    assert 'Missing' not in sys.modules['autodoc_context_target'].__dict__


def test_type_hints_context_in_legacy_attribute_import(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, make_app: Any
) -> None:
    (tmp_path / 'conf.py').write_text('', encoding='utf-8')
    (tmp_path / 'index.rst').write_text(
        '.. autoattribute:: autodoc_legacy_context_target.Item.value\n',
        encoding='utf-8',
    )
    (tmp_path / 'autodoc_legacy_context_target.py').write_text(
        'from __future__ import annotations\nclass Item:\n    value: Missing\n',
        encoding='utf-8',
    )
    monkeypatch.syspath_prepend(str(tmp_path))
    app: SphinxTestApp = make_app(
        buildername='text',
        srcdir=tmp_path,
        confoverrides={
            'extensions': ['sphinx.ext.autodoc'],
            'autodoc_use_legacy_class_based': True,
        },
    )
    visited = []

    @contextmanager
    def supply_name(app: Sphinx, obj: Any) -> Generator[None]:
        module: ModuleType = sys.modules[obj.__module__]
        visited.append(obj)
        module.__dict__['Missing'] = int
        try:
            yield
        finally:
            del module.__dict__['Missing']

    app.connect('autodoc-type-hints-context', supply_name)
    app.build()
    output = (app.outdir / 'index.txt').read_text(encoding='utf-8')
    assert 'value' in output
    assert 'int' in output
    assert visited
    assert 'Missing' not in sys.modules['autodoc_legacy_context_target'].__dict__
