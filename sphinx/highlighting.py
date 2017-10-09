# -*- coding: utf-8 -*-
"""
    sphinx.highlighting
    ~~~~~~~~~~~~~~~~~~~

    Highlight code blocks using Pygments.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pygments import highlight
from pygments.filters import Filter, ErrorToken
from pygments.formatters import HtmlFormatter, LatexFormatter
from pygments.lexer import Lexer  # NOQA
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.lexers import PythonLexer, Python3Lexer, PythonConsoleLexer, \
    CLexer, TextLexer, RstLexer
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound
from six import text_type

from sphinx.ext import doctest
from sphinx.locale import __
from sphinx.pygments_styles import SphinxStyle, NoneStyle
from sphinx.util import logging
from sphinx.util.pycompat import htmlescape
from sphinx.util.texescape import tex_hl_escape_map_new

if False:
    # For type annotation
    from typing import Any, Dict, List  # NOQA
    from pygments.formatter import Formatter  # NOQA


logger = logging.getLogger(__name__)


def _default_lexers():
    # type: () -> Dict[unicode, Lexer]
    lexers = dict(
        none = TextLexer(stripnl=False),
        python = PythonLexer(stripnl=False),
        python3 = Python3Lexer(stripnl=False),
        pycon = PythonConsoleLexer(stripnl=False),
        pycon3 = PythonConsoleLexer(python3=True, stripnl=False),
        rest = RstLexer(stripnl=False),
        c = CLexer(stripnl=False),
    )  # type: Dict[unicode, Lexer]
    return lexers


escape_hl_chars = {ord(u'\\'): u'\\PYGZbs{}',
                   ord(u'{'): u'\\PYGZob{}',
                   ord(u'}'): u'\\PYGZcb{}'}

# used if Pygments is available
# use textcomp quote to get a true single quote
_LATEX_ADD_STYLES = r'''
\renewcommand\PYGZsq{\textquotesingle}
'''


class PygmentsBridge(object):
    # Set these attributes if you want to have different Pygments formatters
    # than the default ones.
    html_formatter = HtmlFormatter
    latex_formatter = LatexFormatter

    # Due to the streaming nature of the Pygments API, our filter require side-effects to
    # bubble some reports back up to the PygmentsBridge context by side-channel. Requires a
    # 1-to-1 relationship between PygmentsBridge instance and filter instance.
    class BridgeFilter(Filter):
        def __init__(self, policy, **options):
            Filter.__init__(self, **options)
            self.policy = policy
            self.substitute = options.get('subtitute', None)
            self.reports = []  # type: List[unicode]

        def filter(self, lexer, stream):
            from pygments.token import Error, Text

            policy = self.policy
            substitute = self.substitute or Text
            for ttype, value in stream:
                if ttype is Error:
                    if policy in ['highlight', 'hide']:
                        self.reports.append(value)
                        if policy == 'hide':
                            ttype = substitute
                    else:  # default policy: 'skip_block'
                        raise ErrorToken(value)
                yield ttype, value

    def __init__(self, dest='html', stylename='sphinx', trim_doctest_flags=False,
                 extra_lexers=None, failure_policy='skip_block'):
        # type: (unicode, unicode, bool, Dict[unicode, Lexer], unicode) -> None
        self.dest = dest
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
        self.formatter_args = {'style': style}  # type: Dict[unicode, Any]
        if dest == 'html':
            self.formatter = self.html_formatter
        else:
            self.formatter = self.latex_formatter
            self.formatter_args['commandprefix'] = 'PYG'

        self.filter = self.BridgeFilter(failure_policy)
        self.lexers = _default_lexers()
        for lexer in self.lexers.values():
            lexer.add_filter(self.filter)
        if extra_lexers:
            self.lexers.update(extra_lexers)

    def get_formatter(self, **kwargs):
        # type: (Any) -> Formatter
        kwargs.update(self.formatter_args)  # type: ignore
        return self.formatter(**kwargs)

    def unhighlighted(self, source):
        # type: (unicode) -> unicode
        if self.dest == 'html':
            return '<pre>' + htmlescape(source) + '</pre>\n'
        else:
            # first, escape highlighting characters like Pygments does
            source = source.translate(escape_hl_chars)
            # then, escape all characters nonrepresentable in LaTeX
            source = source.translate(tex_hl_escape_map_new)
            return '\\begin{Verbatim}[commandchars=\\\\\\{\\}]\n' + \
                   source + '\\end{Verbatim}\n'

    def highlight_block(self, source, lang, opts=None, location=None, force=False, **kwargs):
        # type: (unicode, unicode, Any, Any, bool, Any) -> unicode
        if not isinstance(source, text_type):
            source = source.decode()

        lexers = self.lexers

        # find out which lexer to use
        if lang in ('py', 'python'):
            if source.startswith('>>>'):
                # interactive session
                lexer = lexers['pycon']
            else:
                lexer = lexers['python']
        elif lang in ('py3', 'python3', 'default'):
            if source.startswith('>>>'):
                lexer = lexers['pycon3']
            else:
                lexer = lexers['python3']
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
                    lexer = lexers[lang] = get_lexer_by_name(lang, **(opts or {}))
                except ClassNotFound:
                    logger.warning(__('Pygments lexer name %r is not known'), lang,
                                   location=location)
                    lexer = lexers['none']
                else:
                    lexer.add_filter(self.filter)

        # trim doctest options if wanted
        if isinstance(lexer, PythonConsoleLexer) and self.trim_doctest_flags:
            source = doctest.blankline_re.sub('', source)  # type: ignore
            source = doctest.doctestopt_re.sub('', source)  # type: ignore

        # highlight via Pygments
        formatter = self.get_formatter(**kwargs)
        try:
            self.filter.reports = []
            hlsource = highlight(source, lexer, formatter)
        except ErrorToken:
            # this is most probably not the selected language,
            # so let it pass unhighlighted
            if lang == 'default':
                pass  # automatic highlighting failed.
            else:
                logger.warning(__('Could not lex literal_block as "%s". '
                                  'Highlighting skipped.'), lang,
                               type='misc', subtype='highlighting_failure',
                               location=location)
            hlsource = highlight(source, lexers['none'], formatter)
            self.filter.reports = []
        if self.filter.reports:
            reports = '\n  '.join(self.filter.reports)
            msg = 'Some parts of literal_block could not be highlighted as "%s":\n  ' + reports
            logger.warning(msg, lang,
                           type='misc', subtype='highlighting_failure',
                           location=location)
        if self.dest == 'html':
            return hlsource
        else:
            if not isinstance(hlsource, text_type):  # Py2 / Pygments < 1.6
                hlsource = hlsource.decode()
            return hlsource.translate(tex_hl_escape_map_new)

    def get_stylesheet(self):
        # type: () -> unicode
        formatter = self.get_formatter()
        if self.dest == 'html':
            return formatter.get_style_defs('.highlight')
        else:
            return formatter.get_style_defs() + _LATEX_ADD_STYLES
