from __future__ import annotations

import pytest

from sphinx.errors import ConfigError


@pytest.mark.sphinx('html', testroot='basic')
def test_default_html_math_renderer(app) -> None:
    assert app.builder.math_renderer_name == 'mathjax'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.mathjax']},
)
def test_html_math_renderer_is_mathjax(app) -> None:
    assert app.builder.math_renderer_name == 'mathjax'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.imgmath']},
)
def test_html_math_renderer_is_imgmath(app) -> None:
    assert app.builder.math_renderer_name == 'imgmath'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'extensions': ['sphinxcontrib.jsmath', 'sphinx.ext.imgmath']},
)
def test_html_math_renderer_is_duplicated(make_app, app_params) -> None:
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
def test_html_math_renderer_is_duplicated2(app) -> None:
    # case of both mathjax and another math_renderer is loaded
    assert app.builder.math_renderer_name == 'imgmath'  # The another one is chosen


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={
        'extensions': ['sphinxcontrib.jsmath', 'sphinx.ext.imgmath'],
        'html_math_renderer': 'imgmath',
    },
)
def test_html_math_renderer_is_chosen(app) -> None:
    assert app.builder.math_renderer_name == 'imgmath'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={
        'extensions': ['sphinxcontrib.jsmath', 'sphinx.ext.mathjax'],
        'html_math_renderer': 'imgmath',
    },
)
def test_html_math_renderer_is_mismatched(make_app, app_params) -> None:
    args, kwargs = app_params
    with pytest.raises(
        ConfigError,
        match=r"Unknown math_renderer 'imgmath' is given\.",
    ):
        make_app(*args, **kwargs)
