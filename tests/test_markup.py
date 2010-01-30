# -*- coding: utf-8 -*-
"""
    test_markup
    ~~~~~~~~~~~

    Test various Sphinx-specific markup extensions.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from util import *

from docutils import frontend, utils, nodes
from docutils.parsers import rst

from sphinx.util import texescape
from sphinx.writers.html import HTMLWriter, SmartyPantsHTMLTranslator
from sphinx.writers.latex import LaTeXWriter, LaTeXTranslator

def setup_module():
    global app, settings, parser
    texescape.init()  # otherwise done by the latex builder
    app = TestApp(cleanenv=True)
    optparser = frontend.OptionParser(
        components=(rst.Parser, HTMLWriter, LaTeXWriter))
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
    document['file'] = 'dummy'
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
        assert re.match(latex_expected, latex_translated), 'from ' + repr(rst)

def verify(rst, html_expected, latex_expected):
    if html_expected:
        html_expected = re.escape(html_expected) + '$'
    if latex_expected:
        latex_expected = re.escape(latex_expected) + '$'
    verify_re(rst, html_expected, latex_expected)


def test_inline():
    # correct interpretation of code with whitespace
    _html = ('<p><tt class="docutils literal"><span class="pre">'
             'code</span>&nbsp;&nbsp; <span class="pre">sample</span></tt></p>')
    yield verify, '``code   sample``', _html, '\\code{code   sample}'
    yield verify, ':samp:`code   sample`', _html, '\\samp{code   sample}'

    # interpolation of braces in samp and file roles (HTML only)
    yield (verify, ':samp:`a{b}c`',
           '<p><tt class="docutils literal"><span class="pre">a</span>'
           '<em><span class="pre">b</span></em>'
           '<span class="pre">c</span></tt></p>',
           '\\samp{abc}')

    # interpolation of arrows in menuselection
    yield (verify, ':menuselection:`a --> b`',
           u'<p><em>a \N{TRIANGULAR BULLET} b</em></p>',
           '\\emph{a \\(\\rightarrow\\) b}')

    # non-interpolation of dashes in option role
    yield (verify_re, ':option:`--with-option`',
           '<p><em( class="xref")?>--with-option</em></p>$',
           r'\\emph{\\texttt{-{-}with-option}}$')

    # verify smarty-pants quotes
    yield verify, '"John"', '<p>&#8220;John&#8221;</p>', "``John''"
    # ... but not in literal text
    yield (verify, '``"John"``',
           '<p><tt class="docutils literal"><span class="pre">'
           '&quot;John&quot;</span></tt></p>',
           '\\code{"John"}')

def test_latex_escaping():
    # correct escaping in normal mode
    yield (verify, u'Γ\\\\∞$', None,
                   ur'\(\Gamma\)\textbackslash{}\(\infty\)\$')
    # in verbatim code fragments
    yield (verify, u'::\n\n @Γ\\∞$[]', None,
           u'\\begin{Verbatim}[commandchars=@\\[\\]]\n'
           u'@PYGZat[]@(@Gamma@)\\@(@infty@)@$@PYGZlb[]@PYGZrb[]\n'
           u'\\end{Verbatim}')
    # in URIs
    yield (verify, u'`test <http://example.com/~me/>`_', None,
           u'\\href{http://example.com/~me/}{test}')
