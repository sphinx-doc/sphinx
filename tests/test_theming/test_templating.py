"""Test templating."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

    from sphinx.testing.fixtures import _app_params
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='templating', copy_test_root=True)
def test_layout_overloading(
    make_app: Callable[..., SphinxTestApp], app_params: _app_params
) -> None:
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    app.build()

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<!-- layout overloading -->' in result


@pytest.mark.sphinx('html', testroot='templating', copy_test_root=True)
def test_autosummary_class_template_overloading(
    make_app: Callable[..., SphinxTestApp], app_params: _app_params
) -> None:
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    app.build()

    result = (
        app.outdir / 'generated' / 'sphinx.application.TemplateBridge.html'
    ).read_text(encoding='utf8')
    assert 'autosummary/class.rst method block overloading' in result
    assert 'foobar' not in result


@pytest.mark.sphinx(
    'html',
    testroot='templating',
    confoverrides={'autosummary_context': {'sentence': 'foobar'}},
    copy_test_root=True,
)
def test_autosummary_context(
    make_app: Callable[..., SphinxTestApp], app_params: _app_params
) -> None:
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    app.build()

    result = (
        app.outdir / 'generated' / 'sphinx.application.TemplateBridge.html'
    ).read_text(encoding='utf8')
    assert 'autosummary/class.rst method block overloading' in result
    assert 'foobar' in result
