# -*- coding: utf-8 -*-
"""
    test_metadata
    ~~~~~~~~~~~~~

    Test our ahndling of metadata in files with bibliographic metadata

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""



# adapted from an example of bibliographic metadata at http://docutils.sourceforge.net/docs/user/rst/demo.txt
BIBLIOGRAPHIC_FIELDS_REST = """:Author: David Goodger
:Address: 123 Example Street
          Example, EX  Canada
          A1B 2C3
:Contact: goodger@python.org
:Authors: Me; Myself; I
:organization: humankind
:date: $Date: 2006-05-21 22:44:42 +0200 (Son, 21 Mai 2006) $
:status: This is a "work in progress"
:revision: $Revision: 4564 $
:version: 1
:copyright: This document has been placed in the public domain. You
            may do with it as you wish. You may copy, modify,
            redistribute, reattribute, sell, buy, rent, lease,
            destroy, or improve it, quote it at length, excerpt,
            incorporate, collate, fold, staple, or mutilate it, or do
            anything else to it that your or anyone else's heart
            desires.
:field name: This is a generic bibliographic field.
:field name 2:
    Generic bibliographic fields may contain multiple body elements.

    Like this.

:Dedication:

    For Docutils users & co-developers.

:abstract:

    This document is a demonstration of the reStructuredText markup
    language, containing examples of all basic reStructuredText
    constructs and many advanced constructs.

.. meta::
   :keywords: reStructuredText, demonstration, demo, parser
   :description lang=en: A demonstration of the reStructuredText
       markup language, containing examples of all basic
       constructs and many advanced constructs.

================================
reStructuredText Demonstration
================================

Above is the document title.
"""

import re

from util import *

from docutils import frontend, utils, nodes
from docutils.parsers import rst

from sphinx import addnodes
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


def test_bibliographic_fields():
    # correct parsing of doc metadata
    document = utils.new_document('test data', settings)
    document['file'] = 'dummy'
    parser.parse(BIBLIOGRAPHIC_FIELDS_REST, document)
    import pdb; pdb.set_trace()
    for msg in document.traverse(nodes.system_message):
        if msg['level'] == 1:
            msg.replace_self([])
    _html = ('<p><tt class="docutils literal"><span class="pre">'
             'code</span>&nbsp;&nbsp; <span class="pre">sample</span></tt></p>')
    yield verify, '``code   sample``', _html, '\\code{code   sample}'
    yield verify, ':samp:`code   sample`', _html, '\\samp{code   sample}'

