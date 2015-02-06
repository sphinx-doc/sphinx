# -*- coding: utf-8 -*-
## set this by test
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

from sphinx.writers.html import HTMLTranslator
from sphinx.writers.latex import LaTeXTranslator
from sphinx.writers.manpage import ManualPageTranslator
from sphinx.writers.texinfo import TexinfoTranslator
from sphinx.writers.text import TextTranslator
from sphinx.writers.websupport import WebSupportTranslator
from docutils.writers.docutils_xml import XMLTranslator


project = 'test'
master_doc = 'index'


class ConfHTMLTranslator(HTMLTranslator):
    pass


class ConfDirHTMLTranslator(HTMLTranslator):
    pass


class ConfSingleHTMLTranslator(HTMLTranslator):
    pass


class ConfPickleTranslator(HTMLTranslator):
    pass


class ConfJsonTranslator(HTMLTranslator):
    pass


class ConfLaTeXTranslator(LaTeXTranslator):
    pass


class ConfManualPageTranslator(ManualPageTranslator):
    pass


class ConfTexinfoTranslator(TexinfoTranslator):
    pass


class ConfTextTranslator(TextTranslator):
    pass


class ConfWebSupportTranslator(WebSupportTranslator):
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
    app.set_translator('websupport', ConfWebSupportTranslator)
    app.set_translator('xml', ConfXMLTranslator)
    app.set_translator('pseudoxml', ConfPseudoXMLTranslator)
