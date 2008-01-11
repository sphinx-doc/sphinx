# -*- coding: utf-8 -*-
"""
    sphinx.highlighting
    ~~~~~~~~~~~~~~~~~~~

    Highlight code blocks using Pygments.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import cgi
import parser
from collections import defaultdict

try:
    import pygments
    from pygments import highlight
    from pygments.lexers import PythonLexer, PythonConsoleLexer, CLexer, \
         TextLexer, RstLexer
    from pygments.formatters import HtmlFormatter, LatexFormatter
    from pygments.filters import ErrorToken
    from pygments.style import Style
    from pygments.styles.friendly import FriendlyStyle
    from pygments.token import Generic, Comment, Number
except ImportError:
    pygments = None
else:
    class PythonDocStyle(Style):
        """
        Like friendly, but a bit darker to enhance contrast on
        the green background.
        """

        background_color = '#eeffcc'
        default_style = ''

        styles = FriendlyStyle.styles
        styles.update({
            Generic.Output: '#333',
            Comment: 'italic #408090',
            Number: '#208050',
        })

    lexers = defaultdict(TextLexer,
        none = TextLexer(),
        python = PythonLexer(),
        pycon = PythonConsoleLexer(),
        rest = RstLexer(),
        c = CLexer(),
    )
    for _lexer in lexers.values():
        _lexer.add_filter('raiseonerror')

    hfmter = HtmlFormatter(style=PythonDocStyle)
    lfmter = LatexFormatter(style=PythonDocStyle)


def highlight_block(source, lang, dest='html'):
    def unhighlighted():
        if dest == 'html':
            return '<pre>' + cgi.escape(source) + '</pre>\n'
        else:
            return highlight(source, lexers['none'], lfmter)
    if not pygments:
        return unhighlighted()
    if lang == 'python':
        if source.startswith('>>>'):
            # interactive session
            lexer = lexers['pycon']
        else:
            # maybe Python -- try parsing it
            try:
                parser.suite('from __future__ import with_statement\n' +
                             source + '\n')
            except (SyntaxError, UnicodeEncodeError):
                return unhighlighted()
            else:
                lexer = lexers['python']
    else:
        lexer = lexers[lang]
    try:
        return highlight(source, lexer, dest == 'html' and hfmter or lfmter)
    except ErrorToken:
        # this is most probably not Python, so let it pass unhighlighted
        return unhighlighted()

def get_stylesheet(dest='html'):
    return (dest == 'html' and hfmter or lfmter).get_style_defs()
