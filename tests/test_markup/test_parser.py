"""Tests parsers module."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from sphinx.deprecation import RemovedInSphinx10Warning
from sphinx.parsers import Parser, RSTParser
from sphinx.util.docutils import new_document

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='basic')
@patch('docutils.parsers.rst.states.RSTStateMachine')
def test_RSTParser_prolog_epilog(RSTStateMachine: Mock, app: SphinxTestApp) -> None:
    document = new_document('dummy.rst')
    document.settings = Mock(tab_width=8, language_code='')
    parser = RSTParser()
    parser._config = app.config
    parser._env = app.env

    # normal case
    text = 'hello Sphinx world\nSphinx is a document generator'
    parser.parse(text, document)
    (content, _), _ = RSTStateMachine().run.call_args

    assert list(content.xitems()) == [
        ('dummy.rst', 0, 'hello Sphinx world'),
        ('dummy.rst', 1, 'Sphinx is a document generator'),
    ]

    # with rst_prolog
    app.config.rst_prolog = 'this is rst_prolog\nhello reST!'
    parser.parse(text, document)
    (content, _), _ = RSTStateMachine().run.call_args
    assert list(content.xitems()) == [
        ('<rst_prologue>', 0, 'this is rst_prolog'),
        ('<rst_prologue>', 1, 'hello reST!'),
        ('<generated>', 0, ''),
        ('dummy.rst', 0, 'hello Sphinx world'),
        ('dummy.rst', 1, 'Sphinx is a document generator'),
    ]

    # with rst_epilog
    app.config.rst_prolog = None
    app.config.rst_epilog = 'this is rst_epilog\ngood-bye reST!'
    parser.parse(text, document)
    (content, _), _ = RSTStateMachine().run.call_args
    assert list(content.xitems()) == [
        ('dummy.rst', 0, 'hello Sphinx world'),
        ('dummy.rst', 1, 'Sphinx is a document generator'),
        ('dummy.rst', 2, ''),
        ('<rst_epilogue>', 0, 'this is rst_epilog'),
        ('<rst_epilogue>', 1, 'good-bye reST!'),
    ]

    # expandtabs / convert whitespaces
    app.config.rst_prolog = None
    app.config.rst_epilog = None
    text = '\thello Sphinx world\n\v\fSphinx is a document generator'
    parser.parse(text, document)
    (content, _), _ = RSTStateMachine().run.call_args
    assert list(content.xitems()) == [
        ('dummy.rst', 0, '        hello Sphinx world'),
        ('dummy.rst', 1, '  Sphinx is a document generator'),
    ]


@pytest.mark.sphinx('html', testroot='basic')
def test_parser_config_env_populated_by_registry(app: SphinxTestApp) -> None:
    """Parsers built via the registry expose config/env without warning (#14371).

    This goes through the real construction path in
    :meth:`.SphinxComponentRegistry.create_source_parser` so a regression in
    that code path (for example, removal of the ``isinstance(..., SphinxParser)``
    gate) would be caught here.
    """
    parser = app.registry.create_source_parser(
        'restructuredtext', config=app.config, env=app.env
    )
    # ``create_source_parser`` is typed as ``docutils.parsers.Parser``; narrow
    # to the Sphinx base class so ``config`` / ``env`` access type-checks and
    # so a future regression that stops wrapping Sphinx parsers is caught here.
    assert isinstance(parser, Parser)

    with warnings.catch_warnings():
        warnings.simplefilter('error', RemovedInSphinx10Warning)
        assert parser.config is app.config
        assert parser.env is app.env


@pytest.mark.sphinx('html', testroot='basic')
def test_parser_set_application_still_deprecated(app: SphinxTestApp) -> None:
    """``Parser.set_application`` must still emit a deprecation warning (#14371)."""
    parser = RSTParser()
    with pytest.warns(RemovedInSphinx10Warning, match='set_application'):
        parser.set_application(app)
    assert parser.config is app.config
    assert parser.env is app.env
