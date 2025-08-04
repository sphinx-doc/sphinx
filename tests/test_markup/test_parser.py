"""Tests parsers module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from sphinx.parsers import RSTParser
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
