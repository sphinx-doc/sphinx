# -*- coding: utf-8 -*-
"""
    sphinx.highlighting
    ~~~~~~~~~~~~~~~~~~~

    Highlight code blocks using Pygments.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import cgi
import re
import textwrap

try:
    import parser
except ImportError:
    # parser is not available on Jython
    parser = None

from sphinx.util.texescape import tex_hl_escape_map_old, tex_hl_escape_map_new

try:
    import pygments
    from pygments import highlight
    from pygments.lexers import PythonLexer, PythonConsoleLexer, CLexer, \
         TextLexer, RstLexer
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter, LatexFormatter
    from pygments.filters import ErrorToken
    from pygments.style import Style
    from pygments.styles import get_style_by_name
    from pygments.styles.friendly import FriendlyStyle
    from pygments.token import Generic, Comment, Number
    from pygments.util import ClassNotFound
except ImportError:
    pygments = None
    lexers = None
    HtmlFormatter = LatexFormatter = None
else:
    class SphinxStyle(Style):
        """
        Like friendly, but a bit darker to enhance contrast on the green
        background.
        """

        background_color = '#eeffcc'
        default_style = ''

        styles = FriendlyStyle.styles
        styles.update({
            Generic.Output: '#333',
            Comment: 'italic #408090',
            Number: '#208050',
        })

    class NoneStyle(Style):
        """Style without any styling."""

    lexers = dict(
        none = TextLexer(),
        python = PythonLexer(),
        pycon = PythonConsoleLexer(),
        # the python3 option exists as of Pygments 1.0,
        # but it doesn't do any harm in previous versions
        pycon3 = PythonConsoleLexer(python3=True),
        rest = RstLexer(),
        c = CLexer(),
    )
    for _lexer in lexers.values():
        _lexer.add_filter('raiseonerror')


escape_hl_chars = {ord(u'@'): u'@PYGZat[]',
                   ord(u'['): u'@PYGZlb[]',
                   ord(u']'): u'@PYGZrb[]'}

# used if Pygments is not available
_LATEX_STYLES = r'''
\newcommand\PYGZat{@}
\newcommand\PYGZlb{[}
\newcommand\PYGZrb{]}
'''


parsing_exceptions = (SyntaxError, UnicodeEncodeError)
if sys.version_info < (2, 5):
    # Python <= 2.4 raises MemoryError when parsing an
    # invalid encoding cookie
    parsing_exceptions += MemoryError,


class PygmentsBridge(object):
    # Set these attributes if you want to have different Pygments formatters
    # than the default ones.
    html_formatter = HtmlFormatter
    latex_formatter = LatexFormatter

    def __init__(self, dest='html', stylename='sphinx'):
        self.dest = dest
        if not pygments:
            return
        if stylename is None or stylename == 'sphinx':
            style = SphinxStyle
        elif stylename == 'none':
            style = NoneStyle
        elif '.' in stylename:
            module, stylename = stylename.rsplit('.', 1)
            style = getattr(__import__(module, None, None, ['__name__']),
                            stylename)
        else:
            style = get_style_by_name(stylename)
        if dest == 'html':
            self.fmter = {False: self.html_formatter(style=style),
                          True: self.html_formatter(style=style, linenos=True)}
        else:
            self.fmter = {False: self.latex_formatter(style=style,
                                                      commandprefix='PYG'),
                          True: self.latex_formatter(style=style, linenos=True,
                                                     commandprefix='PYG')}

    def unhighlighted(self, source):
        if self.dest == 'html':
            return '<pre>' + cgi.escape(source) + '</pre>\n'
        else:
            # first, escape highlighting characters like Pygments does
            source = source.translate(escape_hl_chars)
            # then, escape all characters nonrepresentable in LaTeX
            source = source.translate(tex_hl_escape_map_old)
            return '\\begin{Verbatim}[commandchars=@\\[\\]]\n' + \
                   source + '\\end{Verbatim}\n'

    def try_parse(self, src):
        # Make sure it ends in a newline
        src += '\n'

        # Ignore consistent indentation.
        if src.lstrip('\n').startswith(' '):
            src = textwrap.dedent(src)

        # Replace "..." by a mark which is also a valid python expression
        # (Note, the highlighter gets the original source, this is only done
        #  to allow "..." in code and still highlight it as Python code.)
        mark = "__highlighting__ellipsis__"
        src = src.replace("...", mark)

        # lines beginning with "..." are probably placeholders for suite
        src = re.sub(r"(?m)^(\s*)" + mark + "(.)", r"\1"+ mark + r"# \2", src)

        # if we're using 2.5, use the with statement
        if sys.version_info >= (2, 5):
            src = 'from __future__ import with_statement\n' + src

        if isinstance(src, unicode):
            # Non-ASCII chars will only occur in string literals
            # and comments.  If we wanted to give them to the parser
            # correctly, we'd have to find out the correct source
            # encoding.  Since it may not even be given in a snippet,
            # just replace all non-ASCII characters.
            src = src.encode('ascii', 'replace')

        if parser is None:
            return True

        try:
            parser.suite(src)
        except parsing_exceptions:
            return False
        else:
            return True

    def highlight_block(self, source, lang, linenos=False, warn=None):
        if isinstance(source, str):
            source = source.decode()
        if not pygments:
            return self.unhighlighted(source)
        if lang in ('py', 'python'):
            if source.startswith('>>>'):
                # interactive session
                lexer = lexers['pycon']
            else:
                # maybe Python -- try parsing it
                if self.try_parse(source):
                    lexer = lexers['python']
                else:
                    return self.unhighlighted(source)
        elif lang in ('python3', 'py3') and source.startswith('>>>'):
            # for py3, recognize interactive sessions, but do not try parsing...
            lexer = lexers['pycon3']
        elif lang == 'guess':
            try:
                lexer = guess_lexer(source)
            except Exception:
                return self.unhighlighted(source)
        else:
            if lang in lexers:
                lexer = lexers[lang]
            else:
                try:
                    lexer = lexers[lang] = get_lexer_by_name(lang)
                except ClassNotFound:
                    if warn:
                        warn('Pygments lexer name %s is not known' % lang)
                        return self.unhighlighted(source)
                    else:
                        raise
                else:
                    lexer.add_filter('raiseonerror')
        try:
            if self.dest == 'html':
                return highlight(source, lexer, self.fmter[bool(linenos)])
            else:
                hlsource = highlight(source, lexer, self.fmter[bool(linenos)])
                if hlsource.startswith(r'\begin{Verbatim}[commandchars=\\\{\}'):
                    # Pygments >= 1.2
                    return hlsource.translate(tex_hl_escape_map_new)
                return hlsource.translate(tex_hl_escape_map_old)
        except ErrorToken:
            # this is most probably not the selected language,
            # so let it pass unhighlighted
            return self.unhighlighted(source)

    def get_stylesheet(self):
        if not pygments:
            if self.dest == 'latex':
                return _LATEX_STYLES
            # no HTML styles needed
            return ''
        if self.dest == 'html':
            return self.fmter[0].get_style_defs()
        else:
            styledefs = self.fmter[0].get_style_defs()
            # workaround for Pygments < 0.12
            if styledefs.startswith('\\newcommand\\at{@}'):
                styledefs += _LATEX_STYLES
            return styledefs
