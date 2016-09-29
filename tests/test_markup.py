# -*- coding: utf-8 -*-
"""
    test_markup
    ~~~~~~~~~~~

    Test various Sphinx-specific markup extensions.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import pickle

from docutils import frontend, utils, nodes
from docutils.parsers import rst

from sphinx import addnodes
from sphinx.util import texescape
from sphinx.util.docutils import sphinx_domains
from sphinx.writers.html import HTMLWriter, SmartyPantsHTMLTranslator
from sphinx.writers.latex import LaTeXWriter, LaTeXTranslator

from util import TestApp, with_app, assert_node


app = settings = parser = domain_context = None


def setup_module():
    global app, settings, parser, domain_context
    texescape.init()  # otherwise done by the latex builder
    app = TestApp()
    optparser = frontend.OptionParser(
        components=(rst.Parser, HTMLWriter, LaTeXWriter))
    settings = optparser.get_default_values()
    settings.env = app.builder.env
    settings.env.temp_data['docname'] = 'dummy'
    parser = rst.Parser()
    domain_context = sphinx_domains(settings.env)
    domain_context.enable()


def teardown_module():
    app.cleanup()
    domain_context.disable()


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
    document = utils.new_document(b'test data', settings)
    document['file'] = 'dummy'
    parser.parse(rst, document)
    for msg in document.traverse(nodes.system_message):
        if msg['level'] == 1:
            msg.replace_self([])

    if html_expected:
        html_translator = ForgivingHTMLTranslator(app.builder, document)
        document.walkabout(html_translator)
        html_translated = ''.join(html_translator.fragment).strip()
        assert re.match(html_expected, html_translated), 'from ' + rst

    if latex_expected:
        latex_translator = ForgivingLaTeXTranslator(document, app.builder)
        latex_translator.first_document = -1  # don't write \begin{document}
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
    _html = ('<p><code class="(samp )?docutils literal"><span class="pre">'
             'code</span>&#160;&#160; <span class="pre">sample</span></code></p>')
    yield verify_re, '``code   sample``', _html, r'\\sphinxcode{code   sample}'
    yield verify_re, ':samp:`code   sample`', _html, r'\\sphinxcode{code   sample}'

    # interpolation of braces in samp and file roles (HTML only)
    yield (verify, ':samp:`a{b}c`',
           '<p><code class="samp docutils literal"><span class="pre">a</span>'
           '<em><span class="pre">b</span></em>'
           '<span class="pre">c</span></code></p>',
           '\\sphinxcode{a\\sphinxstyleemphasis{b}c}')

    # interpolation of arrows in menuselection
    yield (verify, ':menuselection:`a --> b`',
           u'<p><span class="menuselection">a \N{TRIANGULAR BULLET} b</span></p>',
           '\\sphinxmenuselection{a \\(\\rightarrow\\) b}')

    # interpolation of ampersands in guilabel/menuselection
    yield (verify, ':guilabel:`&Foo -&&- &Bar`',
           u'<p><span class="guilabel"><span class="accelerator">F</span>oo '
           '-&amp;- <span class="accelerator">B</span>ar</span></p>',
           r'\sphinxmenuselection{\sphinxaccelerator{F}oo -\&- \sphinxaccelerator{B}ar}')

    # non-interpolation of dashes in option role
    yield (verify_re, ':option:`--with-option`',
           '<p><code( class="xref std std-option docutils literal")?>'
           '<span class="pre">--with-option</span></code></p>$',
           r'\\sphinxcode{-{-}with-option}$')

    # verify smarty-pants quotes
    yield verify, '"John"', '<p>&#8220;John&#8221;</p>', "``John''"
    # ... but not in literal text
    yield (verify, '``"John"``',
           '<p><code class="docutils literal"><span class="pre">'
           '&quot;John&quot;</span></code></p>',
           '\\sphinxcode{"John"}')

    # verify classes for inline roles
    yield (verify, ':manpage:`mp(1)`',
           '<p><em class="manpage">mp(1)</em></p>',
           '\\sphinxstyleliteralemphasis{mp(1)}')


def test_latex_escaping():
    # correct escaping in normal mode
    yield (verify, u'Γ\\\\∞$', None,
           r'\(\Gamma\)\textbackslash{}\(\infty\)\$')
    # in verbatim code fragments
    yield (verify, u'::\n\n @Γ\\∞${}', None,
           u'\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n'
           u'@\\(\\Gamma\\)\\PYGZbs{}\\(\\infty\\)\\PYGZdl{}\\PYGZob{}\\PYGZcb{}\n'
           u'\\end{sphinxVerbatim}')
    # in URIs
    yield (verify_re, u'`test <http://example.com/~me/>`_', None,
           r'\\href{http://example.com/~me/}{test}.*')


@with_app(buildername='dummy', testroot='prolog')
def test_rst_prolog(app, status, warning):
    app.builder.build_all()
    rst = pickle.loads((app.doctreedir / 'restructuredtext.doctree').bytes())
    md = pickle.loads((app.doctreedir / 'markdown.doctree').bytes())

    # rst_prolog
    assert_node(rst[0], nodes.paragraph)
    assert_node(rst[0][0], nodes.emphasis)
    assert_node(rst[0][0][0], nodes.Text)
    assert rst[0][0][0] == 'Hello world'

    # rst_epilog
    assert_node(rst[-1], nodes.section)
    assert_node(rst[-1][-1], nodes.paragraph)
    assert_node(rst[-1][-1][0], nodes.emphasis)
    assert_node(rst[-1][-1][0][0], nodes.Text)
    assert rst[-1][-1][0][0] == 'Good-bye world'

    # rst_prolog & rst_epilog on exlucding reST parser
    assert not md.rawsource.startswith('*Hello world*.')
    assert not md.rawsource.endswith('*Good-bye world*.\n')


@with_app(buildername='dummy', testroot='keep_warnings')
def test_keep_warnings_is_True(app, status, warning):
    app.builder.build_all()
    doctree = pickle.loads((app.doctreedir / 'index.doctree').bytes())
    assert_node(doctree[0], nodes.section)
    assert len(doctree[0]) == 2
    assert_node(doctree[0][1], nodes.system_message)


@with_app(buildername='dummy', testroot='keep_warnings',
          confoverrides={'keep_warnings': False})
def test_keep_warnings_is_False(app, status, warning):
    app.builder.build_all()
    doctree = pickle.loads((app.doctreedir / 'index.doctree').bytes())
    assert_node(doctree[0], nodes.section)
    assert len(doctree[0]) == 1


@with_app(buildername='dummy', testroot='refonly_bullet_list')
def test_compact_refonly_bullet_list(app, status, warning):
    app.builder.build_all()
    doctree = pickle.loads((app.doctreedir / 'index.doctree').bytes())
    assert_node(doctree[0], nodes.section)
    assert len(doctree[0]) == 5

    assert doctree[0][1].astext() == 'List A:'
    assert_node(doctree[0][2], nodes.bullet_list)
    assert_node(doctree[0][2][0][0], addnodes.compact_paragraph)
    assert doctree[0][2][0][0].astext() == 'genindex'

    assert doctree[0][3].astext() == 'List B:'
    assert_node(doctree[0][4], nodes.bullet_list)
    assert_node(doctree[0][4][0][0], nodes.paragraph)
    assert doctree[0][4][0][0].astext() == 'Hello'
