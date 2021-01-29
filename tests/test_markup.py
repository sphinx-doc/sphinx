"""
    test_markup
    ~~~~~~~~~~~

    Test various Sphinx-specific markup extensions.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest
from docutils import frontend, nodes, utils
from docutils.parsers.rst import Parser as RstParser

from sphinx import addnodes
from sphinx.builders.html.transforms import KeyboardTransform
from sphinx.builders.latex import LaTeXBuilder
from sphinx.roles import XRefRole
from sphinx.testing.util import Struct, assert_node
from sphinx.transforms import SphinxSmartQuotes
from sphinx.util import docutils, texescape
from sphinx.util.docutils import sphinx_domains
from sphinx.writers.html import HTMLTranslator, HTMLWriter
from sphinx.writers.latex import LaTeXTranslator, LaTeXWriter


@pytest.fixture
def settings(app):
    texescape.init()  # otherwise done by the latex builder
    optparser = frontend.OptionParser(
        components=(RstParser, HTMLWriter, LaTeXWriter))
    settings = optparser.get_default_values()
    settings.smart_quotes = True
    settings.env = app.builder.env
    settings.env.temp_data['docname'] = 'dummy'
    settings.contentsname = 'dummy'
    settings.rfc_base_url = 'http://tools.ietf.org/html/'
    domain_context = sphinx_domains(settings.env)
    domain_context.enable()
    yield settings
    domain_context.disable()


@pytest.fixture
def new_document(settings):
    def create():
        document = utils.new_document('test data', settings)
        document['file'] = 'dummy'
        return document

    return create


@pytest.fixture
def inliner(new_document):
    document = new_document()
    document.reporter.get_source_and_line = lambda line=1: ('dummy.rst', line)
    return Struct(document=document, reporter=document.reporter)


@pytest.fixture
def parse(new_document):
    def parse_(rst):
        document = new_document()
        parser = RstParser()
        parser.parse(rst, document)
        SphinxSmartQuotes(document, startnode=None).apply()
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
        KeyboardTransform(document).apply()
        html_translator = ForgivingHTMLTranslator(document, app.builder)
        document.walkabout(html_translator)
        html_translated = ''.join(html_translator.fragment).strip()
        assert re.match(html_expected, html_translated), 'from ' + rst
    return verify


@pytest.fixture
def verify_re_latex(app, parse):
    def verify(rst, latex_expected):
        document = parse(rst)
        app.builder = LaTeXBuilder(app)
        app.builder.set_environment(app.env)
        app.builder.init()
        theme = app.builder.themes.get('manual')
        latex_translator = ForgivingLaTeXTranslator(document, app.builder, theme)
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
        # pep role
        'verify',
        ':pep:`8`',
        ('<p><span class="target" id="index-0"></span><a class="pep reference external" '
         'href="http://www.python.org/dev/peps/pep-0008"><strong>PEP 8</strong></a></p>'),
        ('\\sphinxAtStartPar\n'
         '\\index{Python Enhancement Proposals@\\spxentry{Python Enhancement Proposals}'
         '!PEP 8@\\spxentry{PEP 8}}\\sphinxhref{http://www.python.org/dev/peps/pep-0008}'
         '{\\sphinxstylestrong{PEP 8}}')
    ),
    (
        # pep role with anchor
        'verify',
        ':pep:`8#id1`',
        ('<p><span class="target" id="index-0"></span><a class="pep reference external" '
         'href="http://www.python.org/dev/peps/pep-0008#id1">'
         '<strong>PEP 8#id1</strong></a></p>'),
        ('\\sphinxAtStartPar\n'
         '\\index{Python Enhancement Proposals@\\spxentry{Python Enhancement Proposals}'
         '!PEP 8\\#id1@\\spxentry{PEP 8\\#id1}}\\sphinxhref'
         '{http://www.python.org/dev/peps/pep-0008\\#id1}'
         '{\\sphinxstylestrong{PEP 8\\#id1}}')
    ),
    (
        # rfc role
        'verify',
        ':rfc:`2324`',
        ('<p><span class="target" id="index-0"></span><a class="rfc reference external" '
         'href="http://tools.ietf.org/html/rfc2324.html"><strong>RFC 2324</strong></a></p>'),
        ('\\sphinxAtStartPar\n'
         '\\index{RFC@\\spxentry{RFC}!RFC 2324@\\spxentry{RFC 2324}}'
         '\\sphinxhref{http://tools.ietf.org/html/rfc2324.html}'
         '{\\sphinxstylestrong{RFC 2324}}')
    ),
    (
        # rfc role with anchor
        'verify',
        ':rfc:`2324#id1`',
        ('<p><span class="target" id="index-0"></span><a class="rfc reference external" '
         'href="http://tools.ietf.org/html/rfc2324.html#id1">'
         '<strong>RFC 2324#id1</strong></a></p>'),
        ('\\sphinxAtStartPar\n'
         '\\index{RFC@\\spxentry{RFC}!RFC 2324\\#id1@\\spxentry{RFC 2324\\#id1}}'
         '\\sphinxhref{http://tools.ietf.org/html/rfc2324.html\\#id1}'
         '{\\sphinxstylestrong{RFC 2324\\#id1}}')
    ),
    (
        # correct interpretation of code with whitespace
        'verify_re',
        '``code   sample``',
        ('<p><code class="(samp )?docutils literal notranslate"><span class="pre">'
         'code</span>&#160;&#160; <span class="pre">sample</span></code></p>'),
        r'\\sphinxAtStartPar\n\\sphinxcode{\\sphinxupquote{code   sample}}',
    ),
    (
        # interpolation of arrows in menuselection
        'verify',
        ':menuselection:`a --> b`',
        ('<p><span class="menuselection">a \N{TRIANGULAR BULLET} b</span></p>'),
        '\\sphinxAtStartPar\n\\sphinxmenuselection{a \\(\\rightarrow\\) b}',
    ),
    (
        # interpolation of ampersands in menuselection
        'verify',
        ':menuselection:`&Foo -&&- &Bar`',
        ('<p><span class="menuselection"><span class="accelerator">F</span>oo '
         '-&amp;- <span class="accelerator">B</span>ar</span></p>'),
        ('\\sphinxAtStartPar\n'
         r'\sphinxmenuselection{\sphinxaccelerator{F}oo \sphinxhyphen{}'
         r'\&\sphinxhyphen{} \sphinxaccelerator{B}ar}'),
    ),
    (
        # interpolation of ampersands in guilabel
        'verify',
        ':guilabel:`&Foo -&&- &Bar`',
        ('<p><span class="guilabel"><span class="accelerator">F</span>oo '
         '-&amp;- <span class="accelerator">B</span>ar</span></p>'),
        ('\\sphinxAtStartPar\n'
         r'\sphinxguilabel{\sphinxaccelerator{F}oo \sphinxhyphen{}\&\sphinxhyphen{} \sphinxaccelerator{B}ar}'),
    ),
    (
        # no ampersands in guilabel
        'verify',
        ':guilabel:`Foo`',
        '<p><span class="guilabel">Foo</span></p>',
        '\\sphinxAtStartPar\n\\sphinxguilabel{Foo}',
    ),
    (
        # kbd role
        'verify',
        ':kbd:`space`',
        '<p><kbd class="kbd docutils literal notranslate">space</kbd></p>',
        '\\sphinxAtStartPar\n\\sphinxkeyboard{\\sphinxupquote{space}}',
    ),
    (
        # kbd role
        'verify',
        ':kbd:`Control+X`',
        ('<p><kbd class="kbd compound docutils literal notranslate">'
         '<kbd class="kbd docutils literal notranslate">Control</kbd>'
         '+'
         '<kbd class="kbd docutils literal notranslate">X</kbd>'
         '</kbd></p>'),
        '\\sphinxAtStartPar\n\\sphinxkeyboard{\\sphinxupquote{Control+X}}',
    ),
    (
        # kbd role
        'verify',
        ':kbd:`Alt+^`',
        ('<p><kbd class="kbd compound docutils literal notranslate">'
         '<kbd class="kbd docutils literal notranslate">Alt</kbd>'
         '+'
         '<kbd class="kbd docutils literal notranslate">^</kbd>'
         '</kbd></p>'),
        ('\\sphinxAtStartPar\n'
         '\\sphinxkeyboard{\\sphinxupquote{Alt+\\textasciicircum{}}}'),
    ),
    (
        # kbd role
        'verify',
        ':kbd:`M-x  M-s`',
        ('<p><kbd class="kbd compound docutils literal notranslate">'
         '<kbd class="kbd docutils literal notranslate">M</kbd>'
         '-'
         '<kbd class="kbd docutils literal notranslate">x</kbd>'
         '  '
         '<kbd class="kbd docutils literal notranslate">M</kbd>'
         '-'
         '<kbd class="kbd docutils literal notranslate">s</kbd>'
         '</kbd></p>'),
        ('\\sphinxAtStartPar\n'
         '\\sphinxkeyboard{\\sphinxupquote{M\\sphinxhyphen{}x  M\\sphinxhyphen{}s}}'),
    ),
    (
        # kbd role
        'verify',
        ':kbd:`-`',
        '<p><kbd class="kbd docutils literal notranslate">-</kbd></p>',
        ('\\sphinxAtStartPar\n'
         '\\sphinxkeyboard{\\sphinxupquote{\\sphinxhyphen{}}}'),
    ),
    (
        # kbd role
        'verify',
        ':kbd:`Caps Lock`',
        '<p><kbd class="kbd docutils literal notranslate">Caps Lock</kbd></p>',
        ('\\sphinxAtStartPar\n'
         '\\sphinxkeyboard{\\sphinxupquote{Caps Lock}}'),
    ),
    (
        # non-interpolation of dashes in option role
        'verify_re',
        ':option:`--with-option`',
        ('<p><code( class="xref std std-option docutils literal notranslate")?>'
         '<span class="pre">--with-option</span></code></p>$'),
        (r'\\sphinxAtStartPar\n'
         r'\\sphinxcode{\\sphinxupquote{\\sphinxhyphen{}\\sphinxhyphen{}with\\sphinxhyphen{}option}}$'),
    ),
    (
        # verify smarty-pants quotes
        'verify',
        '"John"',
        '<p>“John”</p>',
        "\\sphinxAtStartPar\n“John”",
    ),
    (
        # ... but not in literal text
        'verify',
        '``"John"``',
        ('<p><code class="docutils literal notranslate"><span class="pre">'
         '&quot;John&quot;</span></code></p>'),
        '\\sphinxAtStartPar\n\\sphinxcode{\\sphinxupquote{"John"}}',
    ),
    (
        # verify classes for inline roles
        'verify',
        ':manpage:`mp(1)`',
        '<p><em class="manpage">mp(1)</em></p>',
        '\\sphinxAtStartPar\n\\sphinxstyleliteralemphasis{\\sphinxupquote{mp(1)}}',
    ),
    (
        # correct escaping in normal mode
        'verify',
        'Γ\\\\∞$',
        None,
        '\\sphinxAtStartPar\nΓ\\textbackslash{}\\(\\infty\\)\\$',
    ),
    (
        # in verbatim code fragments
        'verify',
        '::\n\n @Γ\\∞${}',
        None,
        ('\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n'
         '@Γ\\PYGZbs{}\\(\\infty\\)\\PYGZdl{}\\PYGZob{}\\PYGZcb{}\n'
         '\\end{sphinxVerbatim}'),
    ),
    (
        # in URIs
        'verify_re',
        '`test <https://www.google.com/~me/>`_',
        None,
        r'\\sphinxAtStartPar\n\\sphinxhref{https://www.google.com/~me/}{test}.*',
    ),
    (
        # description list: simple
        'verify',
        'term\n    description',
        '<dl class="docutils">\n<dt>term</dt><dd>description</dd>\n</dl>',
        None,
    ),
    (
        # description list: with classifiers
        'verify',
        'term : class1 : class2\n    description',
        ('<dl class="docutils">\n<dt>term<span class="classifier">class1</span>'
         '<span class="classifier">class2</span></dt><dd>description</dd>\n</dl>'),
        None,
    ),
    (
        # glossary (description list): multiple terms
        'verify',
        '.. glossary::\n\n   term1\n   term2\n       description',
        ('<dl class="glossary docutils">\n'
         '<dt id="term-term1">term1<a class="headerlink" href="#term-term1"'
         ' title="Permalink to this term">¶</a></dt>'
         '<dt id="term-term2">term2<a class="headerlink" href="#term-term2"'
         ' title="Permalink to this term">¶</a></dt>'
         '<dd>description</dd>\n</dl>'),
        None,
    ),
])
def test_inline(get_verifier, type, rst, html_expected, latex_expected):
    verifier = get_verifier(type)
    verifier(rst, html_expected, latex_expected)


@pytest.mark.parametrize('type,rst,html_expected,latex_expected', [
    (
        'verify',
        r'4 backslashes \\\\',
        r'<p>4 backslashes \\</p>',
        None,
    ),
])
@pytest.mark.skipif(docutils.__version_info__ < (0, 16),
                    reason='docutils-0.16 or above is required')
def test_inline_docutils16(get_verifier, type, rst, html_expected, latex_expected):
    verifier = get_verifier(type)
    verifier(rst, html_expected, latex_expected)


@pytest.mark.sphinx(confoverrides={'latex_engine': 'xelatex'})
@pytest.mark.parametrize('type,rst,html_expected,latex_expected', [
    (
        # in verbatim code fragments
        'verify',
        '::\n\n @Γ\\∞${}',
        None,
        ('\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n'
         '@Γ\\PYGZbs{}∞\\PYGZdl{}\\PYGZob{}\\PYGZcb{}\n'
         '\\end{sphinxVerbatim}'),
    ),
])
def test_inline_for_unicode_latex_engine(get_verifier, type, rst,
                                         html_expected, latex_expected):
    verifier = get_verifier(type)
    verifier(rst, html_expected, latex_expected)


def test_samp_role(parse):
    # no braces
    text = ':samp:`a{b}c`'
    doctree = parse(text)
    assert_node(doctree[0], [nodes.paragraph, nodes.literal, ("a",
                                                              [nodes.emphasis, "b"],
                                                              "c")])
    # nested braces
    text = ':samp:`a{{b}}c`'
    doctree = parse(text)
    assert_node(doctree[0], [nodes.paragraph, nodes.literal, ("a",
                                                              [nodes.emphasis, "{b"],
                                                              "}c")])

    # half-opened braces
    text = ':samp:`a{bc`'
    doctree = parse(text)
    assert_node(doctree[0], [nodes.paragraph, nodes.literal, "a{bc"])

    # escaped braces
    text = ':samp:`a\\\\{b}c`'
    doctree = parse(text)
    assert_node(doctree[0], [nodes.paragraph, nodes.literal, "a{b}c"])

    # no braces (whitespaces are keeped as is)
    text = ':samp:`code   sample`'
    doctree = parse(text)
    assert_node(doctree[0], [nodes.paragraph, nodes.literal, "code   sample"])


def test_download_role(parse):
    # implicit
    text = ':download:`sphinx.rst`'
    doctree = parse(text)
    assert_node(doctree[0], [nodes.paragraph, addnodes.download_reference,
                             nodes.literal, "sphinx.rst"])
    assert_node(doctree[0][0], refdoc='dummy', refdomain='', reftype='download',
                refexplicit=False, reftarget='sphinx.rst', refwarn=False)
    assert_node(doctree[0][0][0], classes=['xref', 'download'])

    # explicit
    text = ':download:`reftitle <sphinx.rst>`'
    doctree = parse(text)
    assert_node(doctree[0], [nodes.paragraph, addnodes.download_reference,
                             nodes.literal, "reftitle"])
    assert_node(doctree[0][0], refdoc='dummy', refdomain='', reftype='download',
                refexplicit=True, reftarget='sphinx.rst', refwarn=False)
    assert_node(doctree[0][0][0], classes=['xref', 'download'])


def test_XRefRole(inliner):
    role = XRefRole()

    # implicit
    doctrees, errors = role('ref', 'rawtext', 'text', 5, inliner, {}, [])
    assert len(doctrees) == 1
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'text'])
    assert_node(doctrees[0], refdoc='dummy', refdomain='', reftype='ref', reftarget='text',
                refexplicit=False, refwarn=False)
    assert errors == []

    # explicit
    doctrees, errors = role('ref', 'rawtext', 'title <target>', 5, inliner, {}, [])
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'title'])
    assert_node(doctrees[0], refdoc='dummy', refdomain='', reftype='ref', reftarget='target',
                refexplicit=True, refwarn=False)

    # bang
    doctrees, errors = role('ref', 'rawtext', '!title <target>', 5, inliner, {}, [])
    assert_node(doctrees[0], [nodes.literal, 'title <target>'])

    # refdomain
    doctrees, errors = role('test:doc', 'rawtext', 'text', 5, inliner, {}, [])
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'text'])
    assert_node(doctrees[0], refdoc='dummy', refdomain='test', reftype='doc', reftarget='text',
                refexplicit=False, refwarn=False)

    # fix_parens
    role = XRefRole(fix_parens=True)
    doctrees, errors = role('ref', 'rawtext', 'text()', 5, inliner, {}, [])
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'text()'])
    assert_node(doctrees[0], refdoc='dummy', refdomain='', reftype='ref', reftarget='text',
                refexplicit=False, refwarn=False)

    # lowercase
    role = XRefRole(lowercase=True)
    doctrees, errors = role('ref', 'rawtext', 'TEXT', 5, inliner, {}, [])
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'TEXT'])
    assert_node(doctrees[0], refdoc='dummy', refdomain='', reftype='ref', reftarget='text',
                refexplicit=False, refwarn=False)


@pytest.mark.sphinx('dummy', testroot='prolog')
def test_rst_prolog(app, status, warning):
    app.builder.build_all()
    rst = app.env.get_doctree('restructuredtext')
    md = app.env.get_doctree('markdown')

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
    doctree = app.env.get_doctree('index')
    assert_node(doctree[0], nodes.section)
    assert len(doctree[0]) == 2
    assert_node(doctree[0][1], nodes.system_message)


@pytest.mark.sphinx('dummy', testroot='keep_warnings',
                    confoverrides={'keep_warnings': False})
def test_keep_warnings_is_False(app, status, warning):
    app.builder.build_all()
    doctree = app.env.get_doctree('index')
    assert_node(doctree[0], nodes.section)
    assert len(doctree[0]) == 1


@pytest.mark.sphinx('dummy', testroot='refonly_bullet_list')
def test_compact_refonly_bullet_list(app, status, warning):
    app.builder.build_all()
    doctree = app.env.get_doctree('index')
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
    doctree = app.env.get_doctree('index')
    assert_node(doctree[0], nodes.section)
    assert_node(doctree[0][1], nodes.paragraph)
    assert_node(doctree[0][1][0], addnodes.index)
    assert_node(doctree[0][1][1], nodes.target)
    assert_node(doctree[0][1][2], nodes.reference, classes=["pep"])

    # no default-role
    doctree = app.env.get_doctree('foo')
    assert_node(doctree[0], nodes.section)
    assert_node(doctree[0][1], nodes.paragraph)
    assert_node(doctree[0][1][0], nodes.title_reference)
    assert_node(doctree[0][1][1], nodes.Text)


@pytest.mark.sphinx('dummy', testroot='default_role',
                    confoverrides={'default_role': 'guilabel'})
def test_default_role2(app, status, warning):
    app.builder.build_all()

    # default-role directive is stronger than configratuion
    doctree = app.env.get_doctree('index')
    assert_node(doctree[0], nodes.section)
    assert_node(doctree[0][1], nodes.paragraph)
    assert_node(doctree[0][1][0], addnodes.index)
    assert_node(doctree[0][1][1], nodes.target)
    assert_node(doctree[0][1][2], nodes.reference, classes=["pep"])

    # default_role changes the default behavior
    doctree = app.env.get_doctree('foo')
    assert_node(doctree[0], nodes.section)
    assert_node(doctree[0][1], nodes.paragraph)
    assert_node(doctree[0][1][0], nodes.inline, classes=["guilabel"])
    assert_node(doctree[0][1][1], nodes.Text)
