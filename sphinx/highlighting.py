"""
    sphinx.highlighting
    ~~~~~~~~~~~~~~~~~~~

    Highlight code blocks using Pygments.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from functools import partial
from importlib import import_module

from pygments import highlight
from pygments.filters import ErrorToken
from pygments.formatters import HtmlFormatter, LatexFormatter
from pygments.lexer import Lexer
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.lexers import PythonLexer, Python3Lexer, PythonConsoleLexer, \
    CLexer, TextLexer, RstLexer
from pygments.styles import get_style_by_name
from pygments.util import ClassNotFound

from sphinx.locale import __
from sphinx.pygments_styles import SphinxStyle, NoneStyle
from sphinx.util import logging, texescape

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from pygments.formatter import Formatter  # NOQA
    from pygments.style import Style  # NOQA


logger = logging.getLogger(__name__)

lexers = {}  # type: Dict[str, Lexer]
lexer_classes = {
    'none': partial(TextLexer, stripnl=False),
    'python': partial(PythonLexer, stripnl=False),
    'python3': partial(Python3Lexer, stripnl=False),
    'pycon': partial(PythonConsoleLexer, stripnl=False),
    'pycon3': partial(PythonConsoleLexer, python3=True, stripnl=False),
    'rest': partial(RstLexer, stripnl=False),
    'c': partial(CLexer, stripnl=False),
}  # type: Dict[str, Lexer]


escape_hl_chars = {ord('\\'): '\\PYGZbs{}',
                   ord('{'): '\\PYGZob{}',
                   ord('}'): '\\PYGZcb{}'}

# used if Pygments is available
# use textcomp quote to get a true single quote
_LATEX_ADD_STYLES = r'''
\renewcommand\PYGZsq{\textquotesingle}
'''


class PygmentsBridge:
    # Set these attributes if you want to have different Pygments formatters
    # than the default ones.
    html_formatter = HtmlFormatter
    latex_formatter = LatexFormatter

    def __init__(self, dest='html', stylename='sphinx', latex_engine=None):
        # type: (str, str, str) -> None
        self.dest = dest
        self.latex_engine = latex_engine

        style = self.get_style(stylename)
        self.formatter_args = {'style': style}  # type: Dict[str, Any]
        if dest == 'html':
            self.formatter = self.html_formatter
        else:
            self.formatter = self.latex_formatter
            self.formatter_args['commandprefix'] = 'PYG'

    def get_style(self, stylename):
        # type: (str) -> Style
        if stylename is None or stylename == 'sphinx':
            return SphinxStyle
        elif stylename == 'none':
            return NoneStyle
        elif '.' in stylename:
            module, stylename = stylename.rsplit('.', 1)
            return getattr(import_module(module), stylename)
        else:
            return get_style_by_name(stylename)

    def get_formatter(self, **kwargs):
        # type: (Any) -> Formatter
        kwargs.update(self.formatter_args)
        return self.formatter(**kwargs)

    def get_lexer(self, source, lang, opts=None, force=False, location=None):
        # type: (str, str, Dict, bool, Any) -> Lexer
        if not opts:
            opts = {}

        # find out which lexer to use
        if lang in ('py', 'python'):
            if source.startswith('>>>'):
                # interactive session
                lang = 'pycon'
            else:
                lang = 'python'
        elif lang in ('py3', 'python3', 'default'):
            if source.startswith('>>>'):
                lang = 'pycon3'
            else:
                lang = 'python3'
        elif lang == 'guess':
            try:
                lexer = guess_lexer(source)
            except Exception:
                lexer = lexers['none']

        if lang in lexers:
            # just return custom lexers here (without installing raiseonerror filter)
            return lexers[lang]
        elif lang in lexer_classes:
            lexer = lexer_classes[lang](**opts)
        else:
            try:
                if lang == 'guess':
                    lexer = guess_lexer(lang, **opts)
                else:
                    lexer = get_lexer_by_name(lang, **opts)
            except ClassNotFound:
                logger.warning(__('Pygments lexer name %r is not known'), lang,
                               location=location)
                lexer = lexer_classes['none'](**opts)

        if not force:
            lexer.add_filter('raiseonerror')

        return lexer

    def highlight_block(self, source, lang, opts=None, force=False, location=None, **kwargs):
        # type: (str, str, Dict, bool, Any, Any) -> str
        if not isinstance(source, str):
            source = source.decode()

        lexer = self.get_lexer(source, lang, opts, force, location)

        # highlight via Pygments
        formatter = self.get_formatter(**kwargs)
        try:
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
            lexer = self.get_lexer(source, 'none', opts, force, location)
            hlsource = highlight(source, lexer, formatter)

        if self.dest == 'html':
            return hlsource
        else:
            return texescape.hlescape(hlsource, self.latex_engine)

    def get_stylesheet(self):
        # type: () -> str
        formatter = self.get_formatter()
        if self.dest == 'html':
            return formatter.get_style_defs('.highlight')
        else:
            return formatter.get_style_defs() + _LATEX_ADD_STYLES
