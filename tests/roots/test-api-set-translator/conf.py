# set this by test
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path.cwd().resolve()))

from docutils.writers.docutils_xml import XMLTranslator

from sphinx.writers.html import HTML5Translator
from sphinx.writers.latex import LaTeXTranslator
from sphinx.writers.manpage import ManualPageTranslator
from sphinx.writers.texinfo import TexinfoTranslator
from sphinx.writers.text import TextTranslator

project = 'test'


class ConfHTMLTranslator(HTML5Translator):
    pass


class ConfDirHTMLTranslator(HTML5Translator):
    pass


class ConfSingleHTMLTranslator(HTML5Translator):
    pass


class ConfPickleTranslator(HTML5Translator):
    pass


class ConfJsonTranslator(HTML5Translator):
    pass


class ConfLaTeXTranslator(LaTeXTranslator):
    pass


class ConfManualPageTranslator(ManualPageTranslator):
    pass


class ConfTexinfoTranslator(TexinfoTranslator):
    pass


class ConfTextTranslator(TextTranslator):
    pass


class ConfXMLTranslator(XMLTranslator):
    pass


class ConfPseudoXMLTranslator(XMLTranslator):
    pass


def setup(app):
    app.set_translator('html', ConfHTMLTranslator)
    app.set_translator('dirhtml', ConfDirHTMLTranslator)
    app.set_translator('singlehtml', ConfSingleHTMLTranslator)
    app.set_translator('pickle', ConfPickleTranslator)
    app.set_translator('json', ConfJsonTranslator)
    app.set_translator('latex', ConfLaTeXTranslator)
    app.set_translator('man', ConfManualPageTranslator)
    app.set_translator('texinfo', ConfTexinfoTranslator)
    app.set_translator('text', ConfTextTranslator)
    app.set_translator('xml', ConfXMLTranslator)
    app.set_translator('pseudoxml', ConfPseudoXMLTranslator)
