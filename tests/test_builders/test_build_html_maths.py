from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.errors import ConfigError

if TYPE_CHECKING:
    from collections.abc import Callable

    from sphinx.testing.fixtures import _app_params
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='basic')
def test_default_html_math_renderer(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    assert app.builder.math_renderer_name == 'mathjax'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_html_math_renderer_is_mathjax(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    assert app.builder.math_renderer_name == 'mathjax'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.imgmath']},
)
def test_html_math_renderer_is_imgmath(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    assert app.builder.math_renderer_name == 'imgmath'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'extensions': ['sphinxcontrib.jsmath', 'sphinx.ext.imgmath']},
)
def test_html_math_renderer_is_duplicated(
    make_app: Callable[..., SphinxTestApp], app_params: _app_params
) -> None:
    args, kwargs = app_params
    with pytest.raises(
        ConfigError,
        match=r'Many math_renderers are registered\. But no math_renderer is selected\.',
    ):
        make_app(*args, **kwargs)


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.imgmath', 'sphinx.ext.mathjax']},
)
def test_html_math_renderer_is_duplicated2(app: SphinxTestApp) -> None:
    # case of both mathjax and another math_renderer is loaded
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    assert app.builder.math_renderer_name == 'imgmath'  # The another one is chosen


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={
        'extensions': ['sphinxcontrib.jsmath', 'sphinx.ext.imgmath'],
        'html_math_renderer': 'imgmath',
    },
)
def test_html_math_renderer_is_chosen(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    assert app.builder.math_renderer_name == 'imgmath'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={
        'extensions': ['sphinxcontrib.jsmath', 'sphinx.ext.mathjax'],
        'html_math_renderer': 'imgmath',
    },
)
def test_html_math_renderer_is_mismatched(
    make_app: Callable[..., SphinxTestApp], app_params: _app_params
) -> None:
    args, kwargs = app_params
    with pytest.raises(
        ConfigError,
        match=r"Unknown math_renderer 'imgmath' is given\.",
    ):
        make_app(*args, **kwargs)
