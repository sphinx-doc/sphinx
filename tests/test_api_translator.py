"""
    test_api_translator
    ~~~~~~~~~~~~~~~~~~~

    Test the Sphinx API for translator.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

import pytest

from sphinx.util import docutils


@pytest.fixture(scope='module', autouse=True)
def setup_module(rootdir):
    p = rootdir / 'test-api-set-translator'
    sys.path.insert(0, p)
    yield
    sys.path.remove(p)


@pytest.mark.sphinx('html')
def test_html_translator(app, status, warning):
    # no set_translator()
    translator_class = app.builder.get_translator_class()
    assert translator_class
    if docutils.__version_info__ < (0, 13):
        assert translator_class.__name__ == 'HTMLTranslator'
    else:
        assert translator_class.__name__ == 'HTML5Translator'


@pytest.mark.sphinx('html', testroot='api-set-translator')
def test_html_with_set_translator_for_html_(app, status, warning):
    # use set_translator()
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfHTMLTranslator'


@pytest.mark.sphinx('singlehtml', testroot='api-set-translator')
def test_singlehtml_set_translator_for_singlehtml(app, status, warning):
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfSingleHTMLTranslator'


@pytest.mark.sphinx('pickle', testroot='api-set-translator')
def test_pickle_set_translator_for_pickle(app, status, warning):
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfPickleTranslator'


@pytest.mark.sphinx('json', testroot='api-set-translator')
def test_json_set_translator_for_json(app, status, warning):
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfJsonTranslator'


@pytest.mark.sphinx('latex', testroot='api-set-translator')
def test_html_with_set_translator_for_latex(app, status, warning):
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfLaTeXTranslator'


@pytest.mark.sphinx('man', testroot='api-set-translator')
def test_html_with_set_translator_for_man(app, status, warning):
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfManualPageTranslator'


@pytest.mark.sphinx('texinfo', testroot='api-set-translator')
def test_html_with_set_translator_for_texinfo(app, status, warning):
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfTexinfoTranslator'


@pytest.mark.sphinx('text', testroot='api-set-translator')
def test_html_with_set_translator_for_text(app, status, warning):
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfTextTranslator'


@pytest.mark.sphinx('xml', testroot='api-set-translator')
def test_html_with_set_translator_for_xml(app, status, warning):
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfXMLTranslator'


@pytest.mark.sphinx('pseudoxml', testroot='api-set-translator')
def test_html_with_set_translator_for_pseudoxml(app, status, warning):
    translator_class = app.builder.get_translator_class()
    assert translator_class
    assert translator_class.__name__ == 'ConfPseudoXMLTranslator'
