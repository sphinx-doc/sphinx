# -*- coding: utf-8 -*-
"""
    sphinx.highlighting
    ~~~~~~~~~~~~~~~~~~~

    Highlight code blocks using Pygments.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""

import cgi
import parser
from collections import defaultdict

try:
    import pygments
    from pygments import highlight
    from pygments.lexers import PythonLexer, PythonConsoleLexer, CLexer, \
         TextLexer, RstLexer
    from pygments.formatters import HtmlFormatter
    from pygments.filters import ErrorToken
    from pygments.style import Style
    from pygments.styles.friendly import FriendlyStyle
    from pygments.token import Generic, Comment
except ImportError:
    pygments = None
else:
    class PythonDocStyle(Style):
        """
        Like friendly, but a bit darker to enhance contrast on the green background.
        """

        background_color = '#eeffcc'
        default_style = ''

        styles = FriendlyStyle.styles
        styles.update({
            Generic.Output: 'italic #333',
            Comment: 'italic #408090',
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

    fmter = HtmlFormatter(style=PythonDocStyle)


def highlight_block(source, lang):
    if not pygments:
        return '<pre>' + cgi.escape(source) + '</pre>\n'
    if lang == 'python':
        if source.startswith('>>>'):
            # interactive session
            lexer = lexers['pycon']
        else:
            # maybe Python -- try parsing it
            try:
                parser.suite(source + '\n')
            except (SyntaxError, UnicodeEncodeError):
                return '<pre>' + cgi.escape(source) + '</pre>\n'
            else:
                lexer = lexers['python']
    else:
        lexer = lexers[lang]
    try:
        return highlight(source, lexer, fmter)
    except ErrorToken:
        # this is most probably not Python, so let it pass unhighlighted
        return '<pre>' + cgi.escape(source) + '</pre>\n'

def get_stylesheet():
    return fmter.get_style_defs()
