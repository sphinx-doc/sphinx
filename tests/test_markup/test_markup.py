"""Test various Sphinx-specific markup extensions."""

from __future__ import annotations

import re
from types import SimpleNamespace

import pytest
from docutils import nodes, utils
from docutils.parsers.rst import Parser as RstParser

from sphinx import addnodes
from sphinx.builders.latex import LaTeXBuilder
from sphinx.environment import default_settings
from sphinx.roles import XRefRole
from sphinx.testing.util import assert_node
from sphinx.transforms import SphinxSmartQuotes
from sphinx.util import texescape
from sphinx.util.docutils import _get_settings, sphinx_domains
from sphinx.writers.html import HTMLWriter
from sphinx.writers.html5 import HTML5Translator
from sphinx.writers.latex import LaTeXTranslator, LaTeXWriter

from tests.utils import extract_node

TYPE_CHECKING = False
if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment
    from sphinx.testing.util import SphinxTestApp
    from sphinx.util.docutils import _DocutilsSettings


def new_settings(env: BuildEnvironment) -> _DocutilsSettings:
    texescape.init()  # otherwise done by the latex builder
    settings = _get_settings(
        RstParser, HTMLWriter, LaTeXWriter, defaults=default_settings
    )
    settings.smart_quotes = True
    settings.env = env
    settings.env.current_document.docname = 'dummy'
    settings.contentsname = 'dummy'
    return settings


def new_document(env: BuildEnvironment) -> nodes.document:
    settings = new_settings(env)
    document = utils.new_document('test data', settings)
    document['file'] = 'dummy'
    return document


def new_inliner(env: BuildEnvironment) -> SimpleNamespace:
    document = new_document(env)

    def _get_source_and_line(line: int | None = 1) -> tuple[str, int | None]:
        return 'dummy.rst', line

    document.reporter.get_source_and_line = _get_source_and_line
    return SimpleNamespace(document=document, reporter=document.reporter)


def parse_rst(rst: str, *, env: BuildEnvironment) -> nodes.document:
    document = new_document(env)
    parser = RstParser()
    domain_context = sphinx_domains(env)
    domain_context.enable()
    parser.parse(rst, document)
    domain_context.disable()
    SphinxSmartQuotes(document, startnode=None).apply()
    for msg in list(document.findall(nodes.system_message)):
        if msg['level'] == 1:
            msg.replace_self([])
    return document


# since we're not resolving the markup afterwards, these nodes may remain
class ForgivingTranslator:
    def visit_pending_xref(self, node: nodes.Element) -> None:
        pass

    def depart_pending_xref(self, node: nodes.Element) -> None:
        pass


class ForgivingHTMLTranslator(HTML5Translator, ForgivingTranslator):
    pass


class ForgivingLaTeXTranslator(LaTeXTranslator, ForgivingTranslator):
    pass


def rst_to_html(rst: str, *, app: SphinxTestApp) -> str:
    document = parse_rst(rst, env=app.env)
    html_translator = ForgivingHTMLTranslator(document, app.builder)
    document.walkabout(html_translator)
    html_translated = ''.join(html_translator.fragment).strip()
    return html_translated


def rst_to_latex(rst: str, *, app: SphinxTestApp) -> str:
    document = parse_rst(rst, env=app.env)
    app.builder = LaTeXBuilder(app, app.env)
    app.builder.init()
    theme = app.builder.themes.get('manual')
    latex_translator = ForgivingLaTeXTranslator(document, app.builder, theme)
    latex_translator.first_document = -1  # don't write \begin{document}
    document.walkabout(latex_translator)
    latex_translated = ''.join(latex_translator.body).strip()
    return latex_translated


@pytest.mark.parametrize(
    ('rst', 'html_expected', 'latex_expected'),
    [
        (
            # cve role
            ':cve:`2020-10735`',
            (
                '<p><span class="target" id="index-0"></span><a class="cve reference external" '
                'href="https://www.cve.org/CVERecord?id=CVE-2020-10735">'
                '<strong>CVE 2020-10735</strong></a></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\index{Common Vulnerabilities and Exposures@\\spxentry{Common Vulnerabilities and Exposures}'
                '!CVE 2020\\sphinxhyphen{}10735@\\spxentry{CVE 2020\\sphinxhyphen{}10735}}'
                '\\sphinxhref{https://www.cve.org/CVERecord?id=CVE-2020-10735}'
                '{\\sphinxstylestrong{CVE 2020\\sphinxhyphen{}10735}}'
            ),
        ),
        (
            # cve role with anchor
            ':cve:`2020-10735#id1`',
            (
                '<p><span class="target" id="index-0"></span><a class="cve reference external" '
                'href="https://www.cve.org/CVERecord?id=CVE-2020-10735#id1">'
                '<strong>CVE 2020-10735#id1</strong></a></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\index{Common Vulnerabilities and Exposures@\\spxentry{Common Vulnerabilities and Exposures}'
                '!CVE 2020\\sphinxhyphen{}10735\\#id1@\\spxentry{CVE 2020\\sphinxhyphen{}10735\\#id1}}'
                '\\sphinxhref{https://www.cve.org/CVERecord?id=CVE-2020-10735\\#id1}'
                '{\\sphinxstylestrong{CVE 2020\\sphinxhyphen{}10735\\#id1}}'
            ),
        ),
        (
            # cwe role
            ':cwe:`787`',
            (
                '<p><span class="target" id="index-0"></span><a class="cwe reference external" '
                'href="https://cwe.mitre.org/data/definitions/787.html">'
                '<strong>CWE 787</strong></a></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\index{Common Weakness Enumeration@\\spxentry{Common Weakness Enumeration}'
                '!CWE 787@\\spxentry{CWE 787}}'
                '\\sphinxhref{https://cwe.mitre.org/data/definitions/787.html}'
                '{\\sphinxstylestrong{CWE 787}}'
            ),
        ),
        (
            # cwe role with anchor
            ':cwe:`787#id1`',
            (
                '<p><span class="target" id="index-0"></span><a class="cwe reference external" '
                'href="https://cwe.mitre.org/data/definitions/787.html#id1">'
                '<strong>CWE 787#id1</strong></a></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\index{Common Weakness Enumeration@\\spxentry{Common Weakness Enumeration}'
                '!CWE 787\\#id1@\\spxentry{CWE 787\\#id1}}'
                '\\sphinxhref{https://cwe.mitre.org/data/definitions/787.html\\#id1}'
                '{\\sphinxstylestrong{CWE 787\\#id1}}'
            ),
        ),
        (
            # pep role
            ':pep:`8`',
            (
                '<p><span class="target" id="index-0"></span><a class="pep reference external" '
                'href="https://peps.python.org/pep-0008/"><strong>PEP 8</strong></a></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\index{Python Enhancement Proposals@\\spxentry{Python Enhancement Proposals}'
                '!PEP 8@\\spxentry{PEP 8}}\\sphinxhref{https://peps.python.org/pep-0008/}'
                '{\\sphinxstylestrong{PEP 8}}'
            ),
        ),
        (
            # pep role with anchor
            ':pep:`8#id1`',
            (
                '<p><span class="target" id="index-0"></span><a class="pep reference external" '
                'href="https://peps.python.org/pep-0008/#id1">'
                '<strong>PEP 8#id1</strong></a></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\index{Python Enhancement Proposals@\\spxentry{Python Enhancement Proposals}'
                '!PEP 8\\#id1@\\spxentry{PEP 8\\#id1}}\\sphinxhref'
                '{https://peps.python.org/pep-0008/\\#id1}'
                '{\\sphinxstylestrong{PEP 8\\#id1}}'
            ),
        ),
        (
            # rfc role
            ':rfc:`2324`',
            (
                '<p><span class="target" id="index-0"></span><a class="rfc reference external" '
                'href="https://datatracker.ietf.org/doc/html/rfc2324.html"><strong>RFC 2324</strong></a></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\index{RFC@\\spxentry{RFC}!RFC 2324@\\spxentry{RFC 2324}}'
                '\\sphinxhref{https://datatracker.ietf.org/doc/html/rfc2324.html}'
                '{\\sphinxstylestrong{RFC 2324}}'
            ),
        ),
        (
            # rfc role with anchor
            ':rfc:`2324#section-1`',
            (
                '<p><span class="target" id="index-0"></span><a class="rfc reference external" '
                'href="https://datatracker.ietf.org/doc/html/rfc2324.html#section-1">'
                '<strong>RFC 2324 Section 1</strong></a></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\index{RFC@\\spxentry{RFC}!RFC 2324 Section 1@\\spxentry{RFC 2324 Section 1}}'
                '\\sphinxhref{https://datatracker.ietf.org/doc/html/rfc2324.html\\#section-1}'
                '{\\sphinxstylestrong{RFC 2324 Section 1}}'
            ),
        ),
        (
            # interpolation of arrows in menuselection
            ':menuselection:`a --> b`',
            '<p><span class="menuselection">a \N{TRIANGULAR BULLET} b</span></p>',
            '\\sphinxAtStartPar\n\\sphinxmenuselection{a \\(\\rightarrow\\) b}',
        ),
        (
            # interpolation of ampersands in menuselection
            ':menuselection:`&Foo -&&- &Bar`',
            (
                '<p><span class="menuselection"><span class="accelerator">F</span>oo '
                '-&amp;- <span class="accelerator">B</span>ar</span></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                r'\sphinxmenuselection{\sphinxaccelerator{F}oo \sphinxhyphen{}'
                r'\&\sphinxhyphen{} \sphinxaccelerator{B}ar}'
            ),
        ),
        (
            # interpolation of ampersands in guilabel
            ':guilabel:`&Foo -&&- &Bar`',
            (
                '<p><span class="guilabel"><span class="accelerator">F</span>oo '
                '-&amp;- <span class="accelerator">B</span>ar</span></p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                r'\sphinxguilabel{\sphinxaccelerator{F}oo \sphinxhyphen{}\&\sphinxhyphen{} \sphinxaccelerator{B}ar}'
            ),
        ),
        (
            # no ampersands in guilabel
            ':guilabel:`Foo`',
            '<p><span class="guilabel">Foo</span></p>',
            '\\sphinxAtStartPar\n\\sphinxguilabel{Foo}',
        ),
        (
            # kbd role
            ':kbd:`space`',
            '<p><kbd class="kbd docutils literal notranslate">space</kbd></p>',
            '\\sphinxAtStartPar\n\\sphinxkeyboard{\\sphinxupquote{space}}',
        ),
        (
            # kbd role
            ':kbd:`Control+X`',
            (
                '<p>'
                '<kbd class="kbd docutils literal notranslate">Control</kbd>'
                '+'
                '<kbd class="kbd docutils literal notranslate">X</kbd>'
                '</p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\sphinxkeyboard{\\sphinxupquote{Control}}'
                '+'
                '\\sphinxkeyboard{\\sphinxupquote{X}}'
            ),
        ),
        (
            # kbd role
            ':kbd:`Alt+^`',
            (
                '<p>'
                '<kbd class="kbd docutils literal notranslate">Alt</kbd>'
                '+'
                '<kbd class="kbd docutils literal notranslate">^</kbd>'
                '</p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\sphinxkeyboard{\\sphinxupquote{Alt}}'
                '+'
                '\\sphinxkeyboard{\\sphinxupquote{\\textasciicircum{}}}'
            ),
        ),
        (
            # kbd role
            ':kbd:`M-x  M-s`',
            (
                '<p>'
                '<kbd class="kbd docutils literal notranslate">M</kbd>'
                '-'
                '<kbd class="kbd docutils literal notranslate">x</kbd>'
                '  '
                '<kbd class="kbd docutils literal notranslate">M</kbd>'
                '-'
                '<kbd class="kbd docutils literal notranslate">s</kbd>'
                '</p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\sphinxkeyboard{\\sphinxupquote{M}}'
                '\\sphinxhyphen{}'
                '\\sphinxkeyboard{\\sphinxupquote{x}}'
                '  '
                '\\sphinxkeyboard{\\sphinxupquote{M}}'
                '\\sphinxhyphen{}'
                '\\sphinxkeyboard{\\sphinxupquote{s}}'
            ),
        ),
        (
            # kbd role
            ':kbd:`-`',
            '<p><kbd class="kbd docutils literal notranslate">-</kbd></p>',
            '\\sphinxAtStartPar\n\\sphinxkeyboard{\\sphinxupquote{\\sphinxhyphen{}}}',
        ),
        (
            # kbd role
            ':kbd:`Caps Lock`',
            '<p><kbd class="kbd docutils literal notranslate">Caps Lock</kbd></p>',
            '\\sphinxAtStartPar\n\\sphinxkeyboard{\\sphinxupquote{Caps Lock}}',
        ),
        (
            # kbd role
            ':kbd:`sys   rq`',
            '<p><kbd class="kbd docutils literal notranslate">sys   rq</kbd></p>',
            '\\sphinxAtStartPar\n\\sphinxkeyboard{\\sphinxupquote{sys   rq}}',
        ),
        (
            # kbd role
            ':kbd:`⌘+⇧+M`',
            (
                '<p>'
                '<kbd class="kbd docutils literal notranslate">⌘</kbd>'
                '+'
                '<kbd class="kbd docutils literal notranslate">⇧</kbd>'
                '+'
                '<kbd class="kbd docutils literal notranslate">M</kbd>'
                '</p>'
            ),
            (
                '\\sphinxAtStartPar\n'
                '\\sphinxkeyboard{\\sphinxupquote{⌘}}'
                '+'
                '\\sphinxkeyboard{\\sphinxupquote{⇧}}'
                '+'
                '\\sphinxkeyboard{\\sphinxupquote{M}}'
            ),
        ),
        (
            # verify smarty-pants quotes
            '"John"',
            '<p>“John”</p>',
            '\\sphinxAtStartPar\n“John”',
        ),
        (
            # ... but not in literal text
            '``"John"``',
            (
                '<p><code class="docutils literal notranslate"><span class="pre">'
                '&quot;John&quot;</span></code></p>'
            ),
            '\\sphinxAtStartPar\n\\sphinxcode{\\sphinxupquote{"John"}}',
        ),
        (
            # verify classes for inline roles
            ':manpage:`mp(1)`',
            '<p><em class="manpage">mp(1)</em></p>',
            '\\sphinxAtStartPar\n\\sphinxstyleliteralemphasis{\\sphinxupquote{mp(1)}}',
        ),
        (
            # correct escaping in normal mode
            'Γ\\\\∞$',
            None,
            '\\sphinxAtStartPar\nΓ\\textbackslash{}\\(\\infty\\)\\$',
        ),
        (
            # in verbatim code fragments
            '::\n\n @Γ\\∞${}',
            None,
            (
                '\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n'
                '@Γ\\PYGZbs{}\\(\\infty\\)\\PYGZdl{}\\PYGZob{}\\PYGZcb{}\n'
                '\\end{sphinxVerbatim}'
            ),
        ),
        (
            # description list: simple
            'term\n    description',
            '<dl class="simple">\n<dt>term</dt><dd><p>description</p>\n</dd>\n</dl>',
            None,
        ),
        (
            # description list: with classifiers
            'term : class1 : class2\n    description',
            (
                '<dl class="simple">\n<dt>term<span class="classifier">class1</span>'
                '<span class="classifier">class2</span></dt><dd><p>description</p>\n</dd>\n</dl>'
            ),
            None,
        ),
        (
            # glossary (description list): multiple terms
            '.. glossary::\n\n   term1\n   term2\n       description',
            (
                '<dl class="simple glossary">\n'
                '<dt id="term-term1">term1<a class="headerlink" href="#term-term1"'
                ' title="Link to this term">¶</a></dt>'
                '<dt id="term-term2">term2<a class="headerlink" href="#term-term2"'
                ' title="Link to this term">¶</a></dt>'
                '<dd><p>description</p>\n</dd>\n</dl>'
            ),
            None,
        ),
        (
            # backslash escaping (docutils 0.16)
            r'4 backslashes \\\\',
            r'<p>4 backslashes \\</p>',
            None,
        ),
    ],
)
@pytest.mark.sphinx('html', testroot='_blank')
def test_inline(
    app: SphinxTestApp, rst: str, html_expected: str, latex_expected: str
) -> None:
    if html_expected:
        html_translated = rst_to_html(rst, app=app)
        assert html_expected == html_translated, f'from {rst!r}'
    if latex_expected:
        latex_translated = rst_to_latex(rst, app=app)
        assert latex_expected == latex_translated, f'from {rst!r}'


@pytest.mark.parametrize(
    ('rst', 'html_expected', 'latex_expected'),
    [
        (
            # correct interpretation of code with whitespace
            '``code   sample``',
            (
                '<p><code class="(samp )?docutils literal notranslate"><span class="pre">'
                'code</span>&#160;&#160; <span class="pre">sample</span></code></p>'
            ),
            r'\\sphinxAtStartPar\n\\sphinxcode{\\sphinxupquote{code   sample}}',
        ),
        (
            # non-interpolation of dashes in option role
            ':option:`--with-option`',
            (
                '<p><code( class="xref std std-option docutils literal notranslate")?>'
                '<span class="pre">--with-option</span></code></p>$'
            ),
            (
                r'\\sphinxAtStartPar\n'
                r'\\sphinxcode{\\sphinxupquote{\\sphinxhyphen{}\\sphinxhyphen{}with\\sphinxhyphen{}option}}$'
            ),
        ),
        (
            # in URIs
            '`test <https://www.google.com/~me/>`_',
            None,
            r'\\sphinxAtStartPar\n\\sphinxhref{https://www.google.com/~me/}{test}.*',
        ),
    ],
)
@pytest.mark.sphinx('html', testroot='_blank')
def test_inline_regex(
    app: SphinxTestApp, rst: str, html_expected: str, latex_expected: str
) -> None:
    if html_expected:
        html_translated = rst_to_html(rst, app=app)
        assert re.match(html_expected, html_translated), f'from {rst!r}'
    if latex_expected:
        latex_translated = rst_to_latex(rst, app=app)
        assert re.match(latex_expected, latex_translated), f'from {rst!r}'


@pytest.mark.sphinx(
    'dummy',
    testroot='_blank',
    confoverrides={'latex_engine': 'xelatex'},
)
@pytest.mark.parametrize(
    ('rst', 'latex_expected'),
    [
        (
            # in verbatim code fragments
            '::\n\n @Γ\\∞${}',
            (
                '\\begin{sphinxVerbatim}[commandchars=\\\\\\{\\}]\n'
                '@Γ\\PYGZbs{}∞\\PYGZdl{}\\PYGZob{}\\PYGZcb{}\n'
                '\\end{sphinxVerbatim}'
            ),
        ),
    ],
)
def test_inline_for_unicode_latex_engine(
    app: SphinxTestApp, rst: str, latex_expected: str
) -> None:
    latex_translated = rst_to_latex(rst, app=app)
    assert latex_expected == latex_translated, f'from {rst!r}'


@pytest.mark.sphinx('dummy', testroot='_blank')
def test_samp_role(app: SphinxTestApp) -> None:
    # no braces
    text = ':samp:`a{b}c`'
    doctree = parse_rst(text, env=app.env)
    assert_node(
        doctree[0], [nodes.paragraph, nodes.literal, ('a', [nodes.emphasis, 'b'], 'c')]
    )
    # nested braces
    text = ':samp:`a{{b}}c`'
    doctree = parse_rst(text, env=app.env)
    assert_node(
        doctree[0],
        [nodes.paragraph, nodes.literal, ('a', [nodes.emphasis, '{b'], '}c')],
    )

    # half-opened braces
    text = ':samp:`a{bc`'
    doctree = parse_rst(text, env=app.env)
    assert_node(doctree[0], [nodes.paragraph, nodes.literal, 'a{bc'])

    # escaped braces
    text = ':samp:`a\\\\{b}c`'
    doctree = parse_rst(text, env=app.env)
    assert_node(doctree[0], [nodes.paragraph, nodes.literal, 'a{b}c'])

    # no braces (whitespaces are keeped as is)
    text = ':samp:`code   sample`'
    doctree = parse_rst(text, env=app.env)
    assert_node(doctree[0], [nodes.paragraph, nodes.literal, 'code   sample'])


@pytest.mark.sphinx('dummy', testroot='_blank')
def test_download_role(app: SphinxTestApp) -> None:
    # implicit
    text = ':download:`sphinx.rst`'
    doctree = parse_rst(text, env=app.env)
    assert_node(
        doctree[0],
        [nodes.paragraph, addnodes.download_reference, nodes.literal, 'sphinx.rst'],
    )
    assert_node(
        extract_node(doctree, 0, 0),
        refdoc='dummy',
        refdomain='',
        reftype='download',
        refexplicit=False,
        reftarget='sphinx.rst',
        refwarn=False,
    )
    assert_node(extract_node(doctree, 0, 0, 0), classes=['xref', 'download'])

    # explicit
    text = ':download:`reftitle <sphinx.rst>`'
    doctree = parse_rst(text, env=app.env)
    assert_node(
        doctree[0],
        [nodes.paragraph, addnodes.download_reference, nodes.literal, 'reftitle'],
    )
    assert_node(
        extract_node(doctree, 0, 0),
        refdoc='dummy',
        refdomain='',
        reftype='download',
        refexplicit=True,
        reftarget='sphinx.rst',
        refwarn=False,
    )
    assert_node(extract_node(doctree, 0, 0, 0), classes=['xref', 'download'])


@pytest.mark.sphinx('dummy', testroot='_blank')
def test_XRefRole(app: SphinxTestApp) -> None:
    inliner = new_inliner(app.env)
    role = XRefRole()

    # implicit
    doctrees, errors = role('ref', 'rawtext', 'text', 5, inliner, {}, [])  # type: ignore[arg-type]
    assert len(doctrees) == 1
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'text'])
    assert_node(
        doctrees[0],
        refdoc='dummy',
        refdomain='',
        reftype='ref',
        reftarget='text',
        refexplicit=False,
        refwarn=False,
    )
    assert errors == []

    # explicit
    doctrees, errors = role('ref', 'rawtext', 'title <target>', 5, inliner, {}, [])  # type: ignore[arg-type]
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'title'])
    assert_node(
        doctrees[0],
        refdoc='dummy',
        refdomain='',
        reftype='ref',
        reftarget='target',
        refexplicit=True,
        refwarn=False,
    )

    # bang
    doctrees, errors = role('ref', 'rawtext', '!title <target>', 5, inliner, {}, [])  # type: ignore[arg-type]
    assert_node(doctrees[0], [nodes.literal, 'title <target>'])

    # refdomain
    doctrees, errors = role('test:doc', 'rawtext', 'text', 5, inliner, {}, [])  # type: ignore[arg-type]
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'text'])
    assert_node(
        doctrees[0],
        refdoc='dummy',
        refdomain='test',
        reftype='doc',
        reftarget='text',
        refexplicit=False,
        refwarn=False,
    )

    # fix_parens
    role = XRefRole(fix_parens=True)
    doctrees, errors = role('ref', 'rawtext', 'text()', 5, inliner, {}, [])  # type: ignore[arg-type]
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'text()'])
    assert_node(
        doctrees[0],
        refdoc='dummy',
        refdomain='',
        reftype='ref',
        reftarget='text',
        refexplicit=False,
        refwarn=False,
    )

    # lowercase
    role = XRefRole(lowercase=True)
    doctrees, errors = role('ref', 'rawtext', 'TEXT', 5, inliner, {}, [])  # type: ignore[arg-type]
    assert_node(doctrees[0], [addnodes.pending_xref, nodes.literal, 'TEXT'])
    assert_node(
        doctrees[0],
        refdoc='dummy',
        refdomain='',
        reftype='ref',
        reftarget='text',
        refexplicit=False,
        refwarn=False,
    )


@pytest.mark.sphinx('dummy', testroot='prolog')
def test_rst_prolog(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    rst = app.env.get_doctree('restructuredtext')
    md = app.env.get_doctree('markdown')

    # rst_prolog
    assert isinstance(rst[0], nodes.paragraph)
    assert_node(extract_node(rst, 0, 0), nodes.emphasis)
    assert_node(extract_node(rst, 0, 0, 0), nodes.Text)
    assert extract_node(rst, 0, 0, 0) == 'Hello world'

    # rst_epilog
    assert isinstance(rst[-1], nodes.section)
    assert_node(extract_node(rst, -1, -1), nodes.paragraph)
    assert_node(extract_node(rst, -1, -1, 0), nodes.emphasis)
    assert_node(extract_node(rst, -1, -1, 0, 0), nodes.Text)
    assert extract_node(rst, -1, -1, 0, 0) == 'Good-bye world'

    # rst_prolog & rst_epilog on exlucding reST parser
    assert not md.rawsource.startswith('*Hello world*.')
    assert not md.rawsource.endswith('*Good-bye world*.\n')


@pytest.mark.sphinx('dummy', testroot='keep_warnings')
def test_keep_warnings_is_True(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    doctree = app.env.get_doctree('index')
    assert isinstance(doctree[0], nodes.section)
    assert len(doctree[0]) == 2
    assert_node(extract_node(doctree, 0, 1), nodes.system_message)


@pytest.mark.sphinx(
    'dummy',
    testroot='keep_warnings',
    confoverrides={'keep_warnings': False},
)
def test_keep_warnings_is_False(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    doctree = app.env.get_doctree('index')
    assert isinstance(doctree[0], nodes.section)
    assert len(doctree[0]) == 1


@pytest.mark.sphinx('dummy', testroot='refonly_bullet_list')
def test_compact_refonly_bullet_list(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    doctree = app.env.get_doctree('index')
    assert isinstance(doctree[0], nodes.section)
    assert len(doctree[0]) == 5

    assert extract_node(doctree, 0, 1).astext() == 'List A:'
    assert_node(extract_node(doctree, 0, 2), nodes.bullet_list)
    assert_node(extract_node(doctree, 0, 2, 0, 0), addnodes.compact_paragraph)
    assert extract_node(doctree, 0, 2, 0, 0).astext() == 'genindex'

    assert extract_node(doctree, 0, 3).astext() == 'List B:'
    assert_node(extract_node(doctree, 0, 4), nodes.bullet_list)
    assert_node(extract_node(doctree, 0, 4, 0, 0), nodes.paragraph)
    assert extract_node(doctree, 0, 4, 0, 0).astext() == 'Hello'


@pytest.mark.sphinx('dummy', testroot='default_role')
def test_default_role1(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    # default-role: pep
    doctree = app.env.get_doctree('index')
    assert isinstance(doctree[0], nodes.section)
    assert_node(extract_node(doctree, 0, 1), nodes.paragraph)
    assert_node(extract_node(doctree, 0, 1, 0), addnodes.index)
    assert_node(extract_node(doctree, 0, 1, 1), nodes.target)
    assert_node(extract_node(doctree, 0, 1, 2), nodes.reference, classes=['pep'])

    # no default-role
    doctree = app.env.get_doctree('foo')
    assert isinstance(doctree[0], nodes.section)
    assert_node(extract_node(doctree, 0, 1), nodes.paragraph)
    assert_node(extract_node(doctree, 0, 1, 0), nodes.title_reference)
    assert_node(extract_node(doctree, 0, 1, 1), nodes.Text)


@pytest.mark.sphinx(
    'dummy',
    testroot='default_role',
    confoverrides={'default_role': 'guilabel'},
)
def test_default_role2(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    # default-role directive is stronger than configratuion
    doctree = app.env.get_doctree('index')
    assert isinstance(doctree[0], nodes.section)
    assert_node(extract_node(doctree, 0, 1), nodes.paragraph)
    assert_node(extract_node(doctree, 0, 1, 0), addnodes.index)
    assert_node(extract_node(doctree, 0, 1, 1), nodes.target)
    assert_node(extract_node(doctree, 0, 1, 2), nodes.reference, classes=['pep'])

    # default_role changes the default behavior
    doctree = app.env.get_doctree('foo')
    assert isinstance(doctree[0], nodes.section)
    assert_node(extract_node(doctree, 0, 1), nodes.paragraph)
    assert_node(extract_node(doctree, 0, 1, 0), nodes.inline, classes=['guilabel'])
    assert_node(extract_node(doctree, 0, 1, 1), nodes.Text)
