"""
    test_sphinx_parsers
    ~~~~~~~~~~~~~~~~~~~

    Tests parsers module.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest.mock import Mock, patch

import pytest

from sphinx.parsers import RSTParser
from sphinx.util.docutils import new_document


@pytest.mark.sphinx(testroot='basic')
@patch('docutils.parsers.rst.states.RSTStateMachine')
def test_RSTParser_prolog_epilog(RSTStateMachine, app):
    document = new_document('dummy.rst')
    document.settings = Mock(tab_width=8, language_code='')
    parser = RSTParser()
    parser.set_application(app)

    # normal case
    text = ('hello Sphinx world\n'
            'Sphinx is a document generator')
    parser.parse(text, document)
    (content, _), _ = RSTStateMachine().run.call_args

    assert list(content.xitems()) == [('dummy.rst', 0, 'hello Sphinx world'),
                                      ('dummy.rst', 1, 'Sphinx is a document generator')]

    # with rst_prolog
    app.env.config.rst_prolog = 'this is rst_prolog\nhello reST!'
    parser.parse(text, document)
    (content, _), _ = RSTStateMachine().run.call_args
    assert list(content.xitems()) == [('<rst_prolog>', 0, 'this is rst_prolog'),
                                      ('<rst_prolog>', 1, 'hello reST!'),
                                      ('<generated>', 0, ''),
                                      ('dummy.rst', 0, 'hello Sphinx world'),
                                      ('dummy.rst', 1, 'Sphinx is a document generator')]

    # with rst_epilog
    app.env.config.rst_prolog = None
    app.env.config.rst_epilog = 'this is rst_epilog\ngood-bye reST!'
    parser.parse(text, document)
    (content, _), _ = RSTStateMachine().run.call_args
    assert list(content.xitems()) == [('dummy.rst', 0, 'hello Sphinx world'),
                                      ('dummy.rst', 1, 'Sphinx is a document generator'),
                                      ('dummy.rst', 2, ''),
                                      ('<rst_epilog>', 0, 'this is rst_epilog'),
                                      ('<rst_epilog>', 1, 'good-bye reST!')]

    # expandtabs / convert whitespaces
    app.env.config.rst_prolog = None
    app.env.config.rst_epilog = None
    text = ('\thello Sphinx world\n'
            '\v\fSphinx is a document generator')
    parser.parse(text, document)
    (content, _), _ = RSTStateMachine().run.call_args
    assert list(content.xitems()) == [('dummy.rst', 0, '        hello Sphinx world'),
                                      ('dummy.rst', 1, '  Sphinx is a document generator')]
