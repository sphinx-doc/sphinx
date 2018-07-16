# -*- coding: utf-8 -*-
"""
    test_markup
    ~~~~~~~~~~~

    Test various Sphinx-specific markup extensions.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pickle
import re

import pytest
from docutils import frontend, utils, nodes
from docutils.parsers.rst import Parser as RstParser
from docutils.transforms.universal import SmartQuotes

from sphinx import addnodes
from sphinx.testing.util import assert_node
from sphinx.util import texescape
from sphinx.util.docutils import sphinx_domains
from sphinx.writers.html import HTMLWriter, HTMLTranslator
from sphinx.writers.latex import LaTeXWriter, LaTeXTranslator


@pytest.fixture
def settings(app):
    texescape.init()  # otherwise done by the latex builder
    optparser = frontend.OptionParser(
        components=(RstParser, HTMLWriter, LaTeXWriter))
    settings = optparser.get_default_values()
    settings.smart_quotes = True
    settings.env = app.builder.env
    settings.env.temp_data['docname'] = 'dummy'
    domain_context = sphinx_domains(settings.env)
    domain_context.enable()
    yield settings
    domain_context.disable()


@pytest.fixture
def parse(settings):
    def parse_(rst):
        document = utils.new_document(b'test data', settings)
        document['file'] = 'dummy'
        parser = RstParser()
        parser.parse(rst, document)
        SmartQuotes(document, startnode=None).apply()
        for msg in document.traverse(nodes.system_message):
            if msg['level'] == 1:
                msg.replace_self([])
        return document
    return parse_


# since we're not resolving the markup afterwards, these nodes may remain
class ForgivingTranslator:
    def visit_pending_xref(self, node):
        pass

    def depart_pending_xref(self, node):
        pass


class ForgivingHTMLTranslator(HTMLTranslator, ForgivingTranslator):
    pass


class ForgivingLaTeXTranslator(LaTeXTranslator, ForgivingTranslator):
    pass


@pytest.fixture
def verify_re_html(app, parse):
    def verify(rst, html_expected):
        document = parse(rst)
        html_translator = ForgivingHTMLTranslator(app.builder, document)
        document.walkabout(html_translator)
        html_translated = ''.join(html_translator.fragment).strip()
        assert re.match(html_expected, html_translated), 'from ' + rst
    return verify


@pytest.fixture
def verify_re_latex(app, parse):
    def verify(rst, latex_expected):
        document = parse(rst)
        latex_translator = ForgivingLaTeXTranslator(document, app.builder)
        latex_translator.first_document = -1  # don't write \begin{document}
        document.walkabout(latex_translator)
        latex_translated = ''.join(latex_translator.body).strip()
        assert re.match(latex_expected, latex_translated), 'from ' + repr(rst)
    return verify


@pytest.fixture
def verify_re(verify_re_html, verify_re_latex):
    def verify_re_(rst, html_expected, latex_expected):
        if html_expected:
            verify_re_html(rst, html_expected)
        if latex_expected:
            verify_re_latex(rst, latex_expected)
    return verify_re_


@pytest.fixture
def verify(verify_re_html, verify_re_latex):
    def verify_(rst, html_expected, latex_expected):
        if html_expected:
            verify_re_html(rst, re.escape(html_expected) + '$')
        if latex_expected:
            verify_re_latex(rst, re.escape(latex_expected) + '$')
    return verify_


@pytest.fixture
def get_verifier(verify, verify_re):
    v = {
        'verify': verify,
        'verify_re': verify_re,
    }

    def get(name):
        return v[name]
    return get


@pytest.mark.parametrize('type,rst,html_expected,latex_expected', [
    (
        # correct interpretation of code with whitespace
        'verify_re',
        '``code   sample``',
        ('<p><code class="(samp )?docutils literal notranslate"><span class="pre">'
         'code</span>&#160;&#160; <span class="pre">sample</span></code></p>'),
        r'\\sphinxcode{\\sphinxupquote{code   sample}}',
    ),
    (
        # correct interpretation of code with whitespace
        'verify_re',
        ':samp:`code   sample`',
        ('<p><code class="(samp )?docutils literal notranslate"><span class="pre">'
         'code</span>&#160;&#160; <span class="pre">sample</span></code></p>'),
        r'\\sphinxcode{\\sphinxupquote{code   sample}}',
    ),
    (
        # interpolation of braces in samp and file roles (HTML only)
        'verify',
        ':samp:`a{b}c`',
        ('<p><code class="samp docutils literal notranslate">'
         '<span class="pre">a</span>'
         '<em><span class="pre">b</span></em>'
         '<span class="pre">c</span></code></p>'),
        '\\sphinxcode{\\sphinxupquote{a\\sphinxstyleemphasis{b}c}}',
    ),
    (
        # interpolation of arrows in menuselection
        'verify',
        ':menuselection:`a --> b`',
        (u'<p><span class="menuselection">a \N{TRIANGULAR BULLET} b</span></p>'),
        '\\sphinxmenuselection{a \\(\\rightarrow\\) b}',
    ),
    (
        # interpolation of ampersands in menuselection
        'verify',
        ':menuselection:`&Foo -&&- &Bar`',
        (u'<p><span class="menuselection"><span class="accelerator">F</span>oo '
         '-&amp;- <span class="accelerator">B</span>ar</span></p>'),
        r'\sphinxmenuselection{\sphinxaccelerator{F}oo -\&- \sphinxaccelerator{B}ar}',
    ),
    (
        # interpolation of ampersands in guilabel
        'verify',
        ':guilabel:`&Foo -&&- &Bar`',
        (u'<p><span class="guilabel"><span class="accelerator">F</span>oo '
         '-&amp;- <span class="accelerator">B</span>ar</span></p>'),
        r'\sphinxguilabel{\sphinxaccelerator{F}oo -\&- \sphinxaccelerator{B}ar}',
    ),
    (
        # non-interpolation of dashes in option role
        'verify_re',
        ':option:`--with-option`',
        ('<p><code( class="xref std std-option docutils literal notranslate")?>'
         '<span class="pre">--with-option</span></code></p>$'),
        r'\\sphinxcode{\\sphinxupquote{-{-}with-option}}$',
    ),
    (
        # verify smarty-pants quotes
        'verify',
        '"John"',
        u'<p>“John”</p>',
        u"“John”",
    ),
    (
        # ... but not in literal text
        'verify',
        '``"John"``',
        ('<p><code class="docutils literal notranslate"><span class="pre">'
         '&quot;John&quot;</span></code></p>'),
        '\\sphinxcode{\\sphinxupquote{"John"}}',
    ),
    (
        # verify classes for inline roles
        'verify',
        ':manpage:`mp(1)`',
        '<p><em class="manpage">mp(1)</em></p>',
        '\\sphinxstyleliteralemphasis{\\sphinxupquote{mp(1)}}',
    ),
    (
        # correct escaping in normal mode
        'verify',
        u'Γ\\\\∞$',
        None,
        r'\(\Gamma\)\textbackslash{}\(\infty\)\$',
    ),
    (
        # in verbatim code fragments
        'verify',
        u'::\n\n @Γ\\∞${}',
        None,
        (u'\\fvset{hllines={, ,}}%\n'
         u'\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n'
         u'@\\(\\Gamma\\)\\PYGZbs{}\\(\\infty\\)\\PYGZdl{}\\PYGZob{}\\PYGZcb{}\n'
         u'\\end{sphinxVerbatim}'),
    ),
    (
        # in URIs
        'verify_re',
        u'`test <http://example.com/~me/>`_',
        None,
        r'\\sphinxhref{http://example.com/~me/}{test}.*',
    ),
])
def test_inline(get_verifier, type, rst, html_expected, latex_expected):
    verifier = get_verifier(type)
    verifier(rst, html_expected, latex_expected)


@pytest.mark.sphinx('dummy', testroot='prolog')
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


@pytest.mark.sphinx('dummy', testroot='keep_warnings')
def test_keep_warnings_is_True(app, status, warning):
    app.builder.build_all()
    doctree = pickle.loads((app.doctreedir / 'index.doctree').bytes())
    assert_node(doctree[0], nodes.section)
    assert len(doctree[0]) == 2
    assert_node(doctree[0][1], nodes.system_message)


@pytest.mark.sphinx('dummy', testroot='keep_warnings',
                    confoverrides={'keep_warnings': False})
def test_keep_warnings_is_False(app, status, warning):
    app.builder.build_all()
    doctree = pickle.loads((app.doctreedir / 'index.doctree').bytes())
    assert_node(doctree[0], nodes.section)
    assert len(doctree[0]) == 1


@pytest.mark.sphinx('dummy', testroot='refonly_bullet_list')
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


@pytest.mark.sphinx('dummy', testroot='default_role')
def test_default_role1(app, status, warning):
    app.builder.build_all()

    # default-role: pep
    doctree = pickle.loads((app.doctreedir / 'index.doctree').bytes())
    assert_node(doctree[0], nodes.section)
    assert_node(doctree[0][1], nodes.paragraph)
    assert_node(doctree[0][1][0], addnodes.index)
    assert_node(doctree[0][1][1], nodes.target)
    assert_node(doctree[0][1][2], nodes.reference, classes=["pep"])

    # no default-role
    doctree = pickle.loads((app.doctreedir / 'foo.doctree').bytes())
    assert_node(doctree[0], nodes.section)
    assert_node(doctree[0][1], nodes.paragraph)
    assert_node(doctree[0][1][0], nodes.title_reference)
    assert_node(doctree[0][1][1], nodes.Text)


@pytest.mark.sphinx('dummy', testroot='default_role',
                    confoverrides={'default_role': 'guilabel'})
def test_default_role2(app, status, warning):
    app.builder.build_all()

    # default-role directive is stronger than configratuion
    doctree = pickle.loads((app.doctreedir / 'index.doctree').bytes())
    assert_node(doctree[0], nodes.section)
    assert_node(doctree[0][1], nodes.paragraph)
    assert_node(doctree[0][1][0], addnodes.index)
    assert_node(doctree[0][1][1], nodes.target)
    assert_node(doctree[0][1][2], nodes.reference, classes=["pep"])

    # default_role changes the default behavior
    doctree = pickle.loads((app.doctreedir / 'foo.doctree').bytes())
    assert_node(doctree[0], nodes.section)
    assert_node(doctree[0][1], nodes.paragraph)
    assert_node(doctree[0][1][0], nodes.inline, classes=["guilabel"])
    assert_node(doctree[0][1][1], nodes.Text)
