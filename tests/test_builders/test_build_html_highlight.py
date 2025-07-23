from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import ANY, call, patch

import pytest

from sphinx.builders.html import StandaloneHTMLBuilder

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='basic', confoverrides={'html_theme': 'alabaster'})
def test_html_pygments_style_default(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    style = app.builder.highlighter.formatter_args.get('style')
    assert style is not None
    assert style.__name__ == 'Alabaster'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'pygments_style': 'sphinx'},
)
def test_html_pygments_style_manually(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    style = app.builder.highlighter.formatter_args.get('style')
    assert style is not None
    assert style.__name__ == 'SphinxStyle'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    confoverrides={'html_theme': 'classic'},
)
def test_html_pygments_for_classic_theme(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    style = app.builder.highlighter.formatter_args.get('style')
    assert style is not None
    assert style.__name__ == 'SphinxStyle'


@pytest.mark.sphinx('html', testroot='basic')
def test_html_dark_pygments_style_default(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    assert app.builder.dark_highlighter is None


@pytest.mark.sphinx('html', testroot='highlight_options')
def test_highlight_options(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    subject = app.builder.highlighter
    with patch.object(
        subject,
        'highlight_block',
        wraps=subject.highlight_block,
    ) as highlight:
        app.build()

        call_args = highlight.call_args_list
        assert len(call_args) == 3
        assert call_args[0] == call(
            ANY,
            'default',
            force=False,
            linenos=False,
            location=ANY,
            opts={'default_option': True},
        )
        assert call_args[1] == call(
            ANY,
            'python',
            force=False,
            linenos=False,
            location=ANY,
            opts={'python_option': True},
        )
        assert call_args[2] == call(
            ANY,
            'java',
            force=False,
            linenos=False,
            location=ANY,
            opts={},
        )


@pytest.mark.sphinx(
    'html',
    testroot='highlight_options',
    confoverrides={'highlight_options': {'default_option': True}},
)
def test_highlight_options_old(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    subject = app.builder.highlighter
    with patch.object(
        subject,
        'highlight_block',
        wraps=subject.highlight_block,
    ) as highlight:
        app.build()

        call_args = highlight.call_args_list
        assert len(call_args) == 3
        assert call_args[0] == call(
            ANY,
            'default',
            force=False,
            linenos=False,
            location=ANY,
            opts={'default_option': True},
        )
        assert call_args[1] == call(
            ANY,
            'python',
            force=False,
            linenos=False,
            location=ANY,
            opts={},
        )
        assert call_args[2] == call(
            ANY,
            'java',
            force=False,
            linenos=False,
            location=ANY,
            opts={},
        )
