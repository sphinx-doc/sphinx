# -*- coding: utf-8 -*-
"""
    test_markup
    ~~~~~~~~~~~

    Test various Sphinx-specific markup extensions.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

import re

from util import *

from docutils import frontend, utils, nodes
from docutils.parsers import rst

from sphinx import addnodes
from sphinx.htmlwriter import HTMLWriter, SmartyPantsHTMLTranslator
from sphinx.latexwriter import LaTeXWriter, LaTeXTranslator

def setup_module():
    global app, settings, parser
    app = TestApp()
    optparser = frontend.OptionParser(components=(rst.Parser, HTMLWriter, LaTeXWriter))
    settings = optparser.get_default_values()
    settings.env = app.builder.env
    parser = rst.Parser()

def teardown_module():
    app.cleanup()

# since we're not resolving the markup afterwards, these nodes may remain
class ForgivingTranslator:
    def visit_pending_xref(self, node):
        pass
    def depart_pending_xref(self, node):
        pass

class ForgivingHTMLTranslator(SmartyPantsHTMLTranslator, ForgivingTranslator):
    pass

class ForgivingLaTeXTranslator(LaTeXTranslator, ForgivingTranslator):
    pass


def verify_re(rst, html_expected, latex_expected):
    document = utils.new_document('test data', settings)
    parser.parse(rst, document)
    for msg in document.traverse(nodes.system_message):
        if msg['level'] == 1:
            msg.replace_self([])

    if html_expected:
        html_translator = ForgivingHTMLTranslator(app.builder, document)
        document.walkabout(html_translator)
        html_translated = ''.join(html_translator.fragment).strip()
        assert re.match(html_expected, html_translated), 'from' + rst

    if latex_expected:
        latex_translator = ForgivingLaTeXTranslator(document, app.builder)
        latex_translator.first_document = -1 # don't write \begin{document}
        document.walkabout(latex_translator)
        latex_translated = ''.join(latex_translator.body).strip()
        assert re.match(latex_expected, latex_translated), 'from ' + rst

def verify(rst, html_expected, latex_expected):
    verify_re(rst, re.escape(html_expected) + '$', re.escape(latex_expected) + '$')


def test_inline():
    # correct interpretation of code with whitespace
    _html = ('<p><tt class="docutils literal"><span class="pre">'
             'code</span>&nbsp;&nbsp; <span class="pre">sample</span></tt></p>')
    verify('``code   sample``', _html, '\\code{code   sample}')
    verify(':samp:`code   sample`', _html, '\\samp{code   sample}')

    # interpolation of braces in samp and file roles (HTML only)
    verify(':samp:`a{b}c`',
           '<p><tt class="docutils literal"><span class="pre">a</span>'
           '<em><span class="pre">b</span></em><span class="pre">c</span></tt></p>',
           '\\samp{abc}')

    # interpolation of arrows in menuselection
    verify(':menuselection:`a --> b`',
           u'<p><em>a \N{TRIANGULAR BULLET} b</em></p>',
           '\\emph{a $\\rightarrow$ b}')

    # non-interpolation of dashes in option role
    verify_re(':option:`--with-option`',
              '<p><em( class="xref")?>--with-option</em></p>$',
              r'\\emph{\\texttt{--with-option}}$')

    # verify smarty-pants quotes
    verify('"John"', '<p>&#8220;John&#8221;</p>', "``John''")
    # ... but not in literal text
    verify('``"John"``',
           '<p><tt class="docutils literal"><span class="pre">'
           '&quot;John&quot;</span></tt></p>',
           '\\code{"John"}')
