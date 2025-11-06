"""Test the autodoc extension.  This mainly tests name resolution & parsing."""

from __future__ import annotations

import logging

from sphinx.environment import _CurrentDocument
from sphinx.ext.autodoc._names import _parse_name

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    import pytest

    from sphinx.ext.autodoc._property_types import _AutodocObjType


def parse_name(
    objtype: _AutodocObjType,
    name: str,
    *,
    current_document: _CurrentDocument | None = None,
    ref_context: Mapping[str, str | None] | None = None,
) -> tuple[str, list[str], str | None, str | None] | None:
    if current_document is None:
        current_document = _CurrentDocument()
    if ref_context is None:
        ref_context = {}

    parsed = _parse_name(
        name=name,
        objtype=objtype,
        current_document=current_document,
        ref_context=ref_context,
    )
    if parsed is None:
        return None
    module_name, parts, args, retann = parsed
    return module_name, list(parts), args, retann


def test_parse_module_names(caplog: pytest.LogCaptureFixture) -> None:
    # work around sphinx.util.logging.setup()
    logger = logging.getLogger('sphinx')
    logger.handlers[:] = [caplog.handler]
    caplog.set_level(logging.WARNING)

    parsed = parse_name('module', 'test_ext_autodoc')
    assert parsed == ('test_ext_autodoc', [], None, None)
    parsed = parse_name('module', 'test.test_ext_autodoc')
    assert parsed == ('test.test_ext_autodoc', [], None, None)
    parsed = parse_name('module', 'test(arg)')
    assert parsed is None
    assert 'signature arguments given for automodule' in caplog.messages[0]


def test_parse_function_names() -> None:
    parsed = parse_name('function', 'test_ext_autodoc.raises')
    assert parsed == ('test_ext_autodoc', ['raises'], None, None)
    parsed = parse_name('function', 'test_ext_autodoc.raises(exc) -> None')
    assert parsed == ('test_ext_autodoc', ['raises'], '(exc)', 'None')


def test_parse_function_names_current_document() -> None:
    current_document = _CurrentDocument()
    current_document.autodoc_module = 'test_ext_autodoc'
    parsed = parse_name('function', 'raises', current_document=current_document)
    assert parsed == ('test_ext_autodoc', ['raises'], None, None)


def test_parse_function_names_ref_context() -> None:
    ref_context: dict[str, Any] = {'py:module': 'test_ext_autodoc'}
    parsed = parse_name('function', 'raises', ref_context=ref_context)
    assert parsed == ('test_ext_autodoc', ['raises'], None, None)
    parsed = parse_name('class', 'Base', ref_context=ref_context)
    assert parsed == ('test_ext_autodoc', ['Base'], None, None)


def test_parse_name_members() -> None:
    # for members
    ref_context: dict[str, Any] = {'py:module': 'sphinx.testing.util'}
    parsed = parse_name('method', 'SphinxTestApp.cleanup', ref_context=ref_context)
    assert parsed == ('sphinx.testing.util', ['SphinxTestApp', 'cleanup'], None, None)

    current_document = _CurrentDocument()
    current_document.autodoc_class = 'SphinxTestApp'
    ref_context['py:class'] = 'Foo'
    parsed = parse_name(
        'method', 'cleanup', current_document=current_document, ref_context=ref_context
    )
    assert parsed == ('sphinx.testing.util', ['SphinxTestApp', 'cleanup'], None, None)
    parsed = parse_name(
        'method',
        'SphinxTestApp.cleanup',
        current_document=current_document,
        ref_context=ref_context,
    )
    assert parsed == ('sphinx.testing.util', ['SphinxTestApp', 'cleanup'], None, None)
