# -*- coding: utf-8 -*-
"""
    sphinx.highlighting
    ~~~~~~~~~~~~~~~~~~~

    Highlight code blocks using Pygments.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import re
import textwrap

try:
    import parser
except ImportError:
    # parser is not available on Jython
    parser = None

from sphinx.util.pycompat import htmlescape
from sphinx.util.texescape import tex_hl_escape_map_new
from sphinx.ext import doctest

try:
    import pygments
    from pygments import highlight
    from pygments.lexers import PythonLexer, PythonConsoleLexer, CLexer, \
         TextLexer, RstLexer
    from pygments.lexers import get_lexer_by_name, guess_lexer
    from pygments.formatters import HtmlFormatter, LatexFormatter
    from pygments.filters import ErrorToken
    from pygments.styles import get_style_by_name
    from pygments.util import ClassNotFound
    from sphinx.pygments_styles import SphinxStyle, NoneStyle
except ImportError:
    pygments = None
    lexers = None
    HtmlFormatter = LatexFormatter = None
else:

    lexers = dict(
        none = TextLexer(),
        python = PythonLexer(),
        pycon = PythonConsoleLexer(),
        pycon3 = PythonConsoleLexer(python3=True),
        rest = RstLexer(),
        c = CLexer(),
    )
    for _lexer in lexers.values():
        _lexer.add_filter('raiseonerror')


escape_hl_chars = {ord(u'\\'): u'\\PYGZbs{}',
                   ord(u'{'): u'\\PYGZob{}',
                   ord(u'}'): u'\\PYGZcb{}'}

# used if Pygments is not available
_LATEX_STYLES = r'''
\newcommand\PYGZbs{\char`\\}
\newcommand\PYGZob{\char`\{}
\newcommand\PYGZcb{\char`\}}
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

    def __init__(self, dest='html', stylename='sphinx',
                 trim_doctest_flags=False):
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
        self.trim_doctest_flags = trim_doctest_flags
        self.formatter_args = {'style' : style}
        if dest == 'html':
            self.formatter = self.html_formatter
        else:
            self.formatter = self.latex_formatter
            self.formatter_args['commandprefix'] = 'PYG'

    def get_formatter(self, **kwargs):
        kwargs.update(self.formatter_args)
        return self.formatter(**kwargs)

    def unhighlighted(self, source):
        if self.dest == 'html':
            return '<pre>' + htmlescape(source) + '</pre>\n'
        else:
            # first, escape highlighting characters like Pygments does
            source = source.translate(escape_hl_chars)
            # then, escape all characters nonrepresentable in LaTeX
            source = source.translate(tex_hl_escape_map_new)
            return '\\begin{Verbatim}[commandchars=\\\\\\{\\}]\n' + \
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

        if sys.version_info < (3, 0) and isinstance(src, unicode):
            # Non-ASCII chars will only occur in string literals
            # and comments.  If we wanted to give them to the parser
            # correctly, we'd have to find out the correct source
            # encoding.  Since it may not even be given in a snippet,
            # just replace all non-ASCII characters.
            src = src.encode('ascii', 'replace')

        if (3, 0) <= sys.version_info < (3, 2):
            # Python 3.1 can't process '\r' as linesep.
            # `parser.suite("print('hello')\r\n")` cause error.
            if '\r\n' in src:
                src = src.replace('\r\n', '\n')

        if parser is None:
            return True

        try:
            parser.suite(src)
        except parsing_exceptions:
            return False
        else:
            return True

    def highlight_block(self, source, lang, warn=None, force=False, **kwargs):
        if not isinstance(source, unicode):
            source = source.decode()
        if not pygments:
            return self.unhighlighted(source)

        # find out which lexer to use
        if lang in ('py', 'python'):
            if source.startswith('>>>'):
                # interactive session
                lexer = lexers['pycon']
            elif not force:
                # maybe Python -- try parsing it
                if self.try_parse(source):
                    lexer = lexers['python']
                else:
                    lexer = lexers['none']
            else:
                lexer = lexers['python']
        elif lang in ('python3', 'py3') and source.startswith('>>>'):
            # for py3, recognize interactive sessions, but do not try parsing...
            lexer = lexers['pycon3']
        elif lang == 'guess':
            try:
                lexer = guess_lexer(source)
            except Exception:
                lexer = lexers['none']
        else:
            if lang in lexers:
                lexer = lexers[lang]
            else:
                try:
                    lexer = lexers[lang] = get_lexer_by_name(lang)
                except ClassNotFound:
                    if warn:
                        warn('Pygments lexer name %r is not known' % lang)
                        lexer = lexers['none']
                    else:
                        raise
                else:
                    lexer.add_filter('raiseonerror')

        # trim doctest options if wanted
        if isinstance(lexer, PythonConsoleLexer) and self.trim_doctest_flags:
            source = doctest.blankline_re.sub('', source)
            source = doctest.doctestopt_re.sub('', source)

        # highlight via Pygments
        formatter = self.get_formatter(**kwargs)
        try:
            hlsource = highlight(source, lexer, formatter)
        except ErrorToken:
            # this is most probably not the selected language,
            # so let it pass unhighlighted
            hlsource = highlight(source, lexers['none'], formatter)
        if self.dest == 'html':
            return hlsource
        else:
            if not isinstance(hlsource, unicode):  # Py2 / Pygments < 1.6
                hlsource = hlsource.decode()
            return hlsource.translate(tex_hl_escape_map_new)

    def get_stylesheet(self):
        if not pygments:
            if self.dest == 'latex':
                return _LATEX_STYLES
            # no HTML styles needed
            return ''
        formatter = self.get_formatter()
        if self.dest == 'html':
            return formatter.get_style_defs('.highlight')
        else:
            return formatter.get_style_defs()
