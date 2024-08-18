"""Test the Pygments highlighting bridge."""

from unittest import mock

import pygments
import pytest
from pygments.formatters.html import HtmlFormatter
from pygments.lexer import RegexLexer
from pygments.token import Name, Text

from sphinx.highlighting import PygmentsBridge

if tuple(map(int, pygments.__version__.split('.')))[:2] < (2, 18):
    from pygments.formatter import Formatter

    Formatter.__class_getitem__ = classmethod(lambda cls, name: cls)  # type: ignore[attr-defined]


class MyLexer(RegexLexer):
    name = 'testlexer'

    tokens = {
        'root': [
            ('a', Name),
            ('b', Text),
        ],
    }


class MyFormatter(HtmlFormatter[str]):
    def format(self, tokensource, outfile):
        for tok in tokensource:
            outfile.write(tok[1])


class ComplainOnUnhighlighted(PygmentsBridge):
    def unhighlighted(self, source):
        raise AssertionError('should highlight %r' % source)


@pytest.mark.sphinx('html', testroot='root')
def test_add_lexer(app):
    app.add_lexer('test', MyLexer)

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
        assert ret.startswith('<div class="highlight">')


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


@mock.patch('sphinx.highlighting.logger')
def test_default_highlight(logger):
    bridge = PygmentsBridge('html')

    # default: highlights as python3
    ret = bridge.highlight_block('print "Hello sphinx world"', 'default')
    assert ret == (
        '<div class="highlight"><pre><span></span><span class="nb">print</span> '
        '<span class="s2">&quot;Hello sphinx world&quot;</span>\n</pre></div>\n'
    )

    # default: fallbacks to none if highlighting failed
    ret = bridge.highlight_block('reST ``like`` text', 'default')
    assert ret == (
        '<div class="highlight"><pre><span></span>reST ``like`` text\n</pre></div>\n'
    )

    # python: highlights as python3
    ret = bridge.highlight_block('print("Hello sphinx world")', 'python')
    assert ret == (
        '<div class="highlight"><pre><span></span><span class="nb">print</span>'
        '<span class="p">(</span>'
        '<span class="s2">&quot;Hello sphinx world&quot;</span>'
        '<span class="p">)</span>\n</pre></div>\n'
    )

    # python3: highlights as python3
    ret = bridge.highlight_block('print("Hello sphinx world")', 'python3')
    assert ret == (
        '<div class="highlight"><pre><span></span><span class="nb">print</span>'
        '<span class="p">(</span>'
        '<span class="s2">&quot;Hello sphinx world&quot;</span>'
        '<span class="p">)</span>\n</pre></div>\n'
    )

    # python: raises error if highlighting failed
    ret = bridge.highlight_block('reST ``like`` text', 'python')
    logger.warning.assert_called_with(
        'Lexing literal_block %r as "%s" resulted in an error at token: %r. '
        'Retrying in relaxed mode.',
        'reST ``like`` text',
        'python',
        '`',
        type='misc',
        subtype='highlighting_failure',
        location=None,
    )
