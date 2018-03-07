# -*- coding: utf-8 -*-
"""
    test_sphinx_io
    ~~~~~~~~~~~~~~

    Tests io modules.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
from six import StringIO

from sphinx.io import SphinxRSTFileInput


@pytest.mark.sphinx(testroot='basic')
def test_SphinxRSTFileInput(app):
    app.env.temp_data['docname'] = 'index'

    # normal case
    text = ('hello Sphinx world\n'
            'Sphinx is a document generator')
    source = SphinxRSTFileInput(app, app.env, source=StringIO(text),
                                source_path='dummy.rst', encoding='utf-8')
    result = source.read()
    assert result.data == ['hello Sphinx world',
                           'Sphinx is a document generator']
    assert result.info(0) == ('dummy.rst', 0)
    assert result.info(1) == ('dummy.rst', 1)
    assert result.info(2) == ('dummy.rst', None)  # out of range

    # having rst_prolog ends without CR
    app.env.config.rst_prolog = 'this is rst_prolog\nhello reST!'
    source = SphinxRSTFileInput(app, app.env, source=StringIO(text),
                                source_path='dummy.rst', encoding='utf-8')
    result = source.read()
    assert result.data == ['this is rst_prolog',
                           'hello reST!',
                           '',
                           'hello Sphinx world',
                           'Sphinx is a document generator']
    assert result.info(0) == ('<rst_prolog>', 0)
    assert result.info(1) == ('<rst_prolog>', 1)
    assert result.info(2) == ('<generated>', 0)
    assert result.info(3) == ('dummy.rst', 0)
    assert result.info(4) == ('dummy.rst', 1)

    # having rst_prolog ends with CR
    app.env.config.rst_prolog = 'this is rst_prolog\nhello reST!\n'
    source = SphinxRSTFileInput(app, app.env, source=StringIO(text),
                                source_path='dummy.rst', encoding='utf-8')
    result = source.read()
    assert result.data == ['this is rst_prolog',
                           'hello reST!',
                           '',
                           'hello Sphinx world',
                           'Sphinx is a document generator']

    # having docinfo and rst_prolog
    docinfo_text = (':title: test of SphinxFileInput\n'
                    ':author: Sphinx team\n'
                    '\n'
                    'hello Sphinx world\n'
                    'Sphinx is a document generator\n')
    app.env.config.rst_prolog = 'this is rst_prolog\nhello reST!'
    source = SphinxRSTFileInput(app, app.env, source=StringIO(docinfo_text),
                                source_path='dummy.rst', encoding='utf-8')
    result = source.read()
    assert result.data == [':title: test of SphinxFileInput',
                           ':author: Sphinx team',
                           '',
                           'this is rst_prolog',
                           'hello reST!',
                           '',
                           '',
                           'hello Sphinx world',
                           'Sphinx is a document generator']
    assert result.info(0) == ('dummy.rst', 0)
    assert result.info(1) == ('dummy.rst', 1)
    assert result.info(2) == ('<generated>', 0)
    assert result.info(3) == ('<rst_prolog>', 0)
    assert result.info(4) == ('<rst_prolog>', 1)
    assert result.info(5) == ('<generated>', 0)
    assert result.info(6) == ('dummy.rst', 2)
    assert result.info(7) == ('dummy.rst', 3)
    assert result.info(8) == ('dummy.rst', 4)
    assert result.info(9) == ('dummy.rst', None)  # out of range

    # having rst_epilog
    app.env.config.rst_prolog = None
    app.env.config.rst_epilog = 'this is rst_epilog\ngood-bye reST!'
    source = SphinxRSTFileInput(app, app.env, source=StringIO(text),
                                source_path='dummy.rst', encoding='utf-8')
    result = source.read()
    assert result.data == ['hello Sphinx world',
                           'Sphinx is a document generator',
                           '',
                           'this is rst_epilog',
                           'good-bye reST!']
    assert result.info(0) == ('dummy.rst', 0)
    assert result.info(1) == ('dummy.rst', 1)
    assert result.info(2) == ('<generated>', 0)
    assert result.info(3) == ('<rst_epilog>', 0)
    assert result.info(4) == ('<rst_epilog>', 1)
    assert result.info(5) == ('<rst_epilog>', None)  # out of range

    # expandtabs / convert whitespaces
    app.env.config.rst_prolog = None
    app.env.config.rst_epilog = None
    text = ('\thello Sphinx world\n'
            '\v\fSphinx is a document generator')
    source = SphinxRSTFileInput(app, app.env, source=StringIO(text),
                                source_path='dummy.rst', encoding='utf-8')
    result = source.read()
    assert result.data == ['        hello Sphinx world',
                           '  Sphinx is a document generator']
