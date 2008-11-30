# -*- coding: utf-8 -*-
"""
    test_highlighting
    ~~~~~~~~~~~~~~~~~

    Test the Pygments highlighting bridge.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

from util import *

from pygments.lexer import RegexLexer
from pygments.token import Text, Name

from sphinx.highlighting import PygmentsBridge


class MyLexer(RegexLexer):
    name = 'testlexer'

    tokens = {
        'root': [
            ('a', Name),
            ('b', Text),
        ],
    }


@with_app()
def test_add_lexer(app):
    app.add_lexer('test', MyLexer())

    bridge = PygmentsBridge('html')
    ret = bridge.highlight_block('ab', 'test')
    assert '<span class="n">a</span>b' in ret
