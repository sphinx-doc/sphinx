# -*- coding: utf-8 -*-
"""
    test_highlighting
    ~~~~~~~~~~~~~~~~~

    Test the Pygments highlighting bridge.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments.lexer import RegexLexer
from pygments.token import Text, Name
from pygments.filters import ErrorToken
from pygments.formatters.html import HtmlFormatter

from sphinx.highlighting import PygmentsBridge

from util import with_app


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
def test_add_lexer(app, status, warning):
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


def test_lexer_options():
    bridge = PygmentsBridge('html')
    ret = bridge.highlight_block('//comment', 'php', opts={'startinline': True})
    assert '<span class="c1">//comment</span>' in ret


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


def test_default_highlight():
    bridge = PygmentsBridge('html')

    # default: highlights as python3
    ret = bridge.highlight_block('print "Hello sphinx world"', 'default')
    assert ret == ('<div class="highlight"><pre><span></span><span class="nb">print</span> '
                   '<span class="s2">&quot;Hello sphinx world&quot;</span>\n</pre></div>\n')

    # default: fallbacks to none if highlighting failed
    ret = bridge.highlight_block('reST ``like`` text', 'default')
    assert ret == '<div class="highlight"><pre><span></span>reST ``like`` text\n</pre></div>\n'

    # python3: highlights as python3
    ret = bridge.highlight_block('print "Hello sphinx world"', 'python3')
    assert ret == ('<div class="highlight"><pre><span></span><span class="nb">print</span> '
                   '<span class="s2">&quot;Hello sphinx world&quot;</span>\n</pre></div>\n')

    # python3: raises error if highlighting failed
    try:
        ret = bridge.highlight_block('reST ``like`` text', 'python3')
        assert False, "highlight_block() does not raise any exceptions"
    except ErrorToken:
        pass  # raise parsing error
