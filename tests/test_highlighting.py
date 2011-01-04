# -*- coding: utf-8 -*-
"""
    test_highlighting
    ~~~~~~~~~~~~~~~~~

    Test the Pygments highlighting bridge.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import *

try:
    import pygments
except ImportError:
    from nose.plugins.skip import SkipTest
    raise SkipTest('pygments not available')

from pygments.lexer import RegexLexer
from pygments.token import Text, Name
from pygments.formatters.html import HtmlFormatter

from sphinx.highlighting import PygmentsBridge


class MyLexer(RegexLexer):
    name = 'testlexer'

    tokens = {
        'root': [
            ('a', Name),
            ('b', Text),
        ],
    }


class MyFormatter(HtmlFormatter):
    def format(self, tokensource, outfile):
        for tok in tokensource:
            outfile.write(tok[1])


class ComplainOnUnhighlighted(PygmentsBridge):
    def unhighlighted(self, source):
        raise AssertionError("should highlight %r" % source)


@with_app()
def test_add_lexer(app):
    app.add_lexer('test', MyLexer())

    bridge = PygmentsBridge('html')
    ret = bridge.highlight_block('ab', 'test')
    assert '<span class="n">a</span>b' in ret

def test_detect_interactive():
    bridge = ComplainOnUnhighlighted('html')
    blocks = [
        """
        >>> testing()
        True
        """,
        ]
    for block in blocks:
        ret = bridge.highlight_block(block.lstrip(), 'python')
        assert ret.startswith("<div class=\"highlight\">")

def test_set_formatter():
    PygmentsBridge.html_formatter = MyFormatter
    try:
        bridge = PygmentsBridge('html')
        ret = bridge.highlight_block('foo\n', 'python')
        assert ret == 'foo\n'
    finally:
        PygmentsBridge.html_formatter = HtmlFormatter

def test_trim_doctest_flags():
    PygmentsBridge.html_formatter = MyFormatter
    try:
        bridge = PygmentsBridge('html', trim_doctest_flags=True)
        ret = bridge.highlight_block('>>> 1+2 # doctest: SKIP\n3\n', 'pycon')
        assert ret == '>>> 1+2 \n3\n'
    finally:
        PygmentsBridge.html_formatter = HtmlFormatter
