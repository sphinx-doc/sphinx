"""Test the Sphinx API for translator."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp


@pytest.fixture(scope='module', autouse=True)
def _setup_module(rootdir: Path) -> Iterator[None]:
    saved_path = sys.path.copy()
    sys.path.insert(0, str(rootdir / 'test-api-set-translator'))
    yield
    sys.path[:] = saved_path


@pytest.mark.sphinx('html', testroot='root')
def test_html_translator(app: SphinxTestApp) -> None:
    # no set_translator()
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'HTML5Translator'


@pytest.mark.sphinx('html', testroot='api-set-translator')
def test_html_with_set_translator_for_html_(app: SphinxTestApp) -> None:
    # use set_translator()
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfHTMLTranslator'


@pytest.mark.sphinx('singlehtml', testroot='api-set-translator')
def test_singlehtml_set_translator_for_singlehtml(app: SphinxTestApp) -> None:
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfSingleHTMLTranslator'


@pytest.mark.sphinx('pickle', testroot='api-set-translator')
def test_pickle_set_translator_for_pickle(app: SphinxTestApp) -> None:
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfPickleTranslator'


@pytest.mark.sphinx('json', testroot='api-set-translator')
def test_json_set_translator_for_json(app: SphinxTestApp) -> None:
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfJsonTranslator'


@pytest.mark.sphinx('latex', testroot='api-set-translator')
def test_html_with_set_translator_for_latex(app: SphinxTestApp) -> None:
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfLaTeXTranslator'


@pytest.mark.sphinx('man', testroot='api-set-translator')
def test_html_with_set_translator_for_man(app: SphinxTestApp) -> None:
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfManualPageTranslator'


@pytest.mark.sphinx('texinfo', testroot='api-set-translator')
def test_html_with_set_translator_for_texinfo(app: SphinxTestApp) -> None:
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfTexinfoTranslator'


@pytest.mark.sphinx('text', testroot='api-set-translator')
def test_html_with_set_translator_for_text(app: SphinxTestApp) -> None:
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfTextTranslator'


@pytest.mark.sphinx('xml', testroot='api-set-translator')
def test_html_with_set_translator_for_xml(app: SphinxTestApp) -> None:
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfXMLTranslator'


@pytest.mark.sphinx('pseudoxml', testroot='api-set-translator')
def test_html_with_set_translator_for_pseudoxml(app: SphinxTestApp) -> None:
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfPseudoXMLTranslator'
