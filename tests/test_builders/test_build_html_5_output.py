"""Test the HTML builder and check output against XPath."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx import addnodes
from tests.test_builders.xpath_util import check_xpath

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path
    from typing import Literal
    from xml.etree.ElementTree import Element, ElementTree

    from sphinx.testing.util import SphinxTestApp


def tail_check(check: str) -> Callable[[Iterable[Element]], Literal[True]]:
    rex = re.compile(check)

    def checker(nodes: Iterable[Element]) -> Literal[True]:
        for node in nodes:
            if node.tail and rex.search(node.tail):
                return True
        msg = f'{check!r} not found in tail of any nodes {nodes}'
        raise AssertionError(msg)

    return checker


@pytest.mark.parametrize(
    ('fname', 'path', 'check'),
    [
        ('images.html', ".//img[@src='_images/img.png']", ''),
        ('images.html', ".//img[@src='_images/img1.png']", ''),
        ('images.html', ".//img[@src='_images/simg.png']", ''),
        ('images.html', ".//img[@src='_images/svgimg.svg']", ''),
        ('images.html', ".//a[@href='_sources/images.txt']", ''),
        # Check svg options
        ('images.html', ".//img[@src='_images/svgimg.svg'][@style='width: 2cm;']", ''),
        ('images.html', ".//img[@src='_images/svgimg.svg'][@style='height: 2cm;']", ''),
        ('subdir/images.html', ".//img[@src='../_images/img1.png']", ''),
        ('subdir/images.html', ".//img[@src='../_images/rimg.png']", ''),
        ('subdir/includes.html', ".//a[@class='reference download internal']", ''),
        ('subdir/includes.html', ".//img[@src='../_images/img.png']", ''),
        ('subdir/includes.html', './/p', 'This is an include file.'),
        ('subdir/includes.html', './/pre/span', 'line 1'),
        ('subdir/includes.html', './/pre/span', 'line 2'),
        ('includes.html', './/pre', 'Max Strauß'),
        ('includes.html', ".//a[@class='reference download internal']", ''),
        ('includes.html', './/pre/span', '"quotes"'),
        ('includes.html', './/pre/span', "'included'"),
        ('includes.html', ".//pre/span[@class='s2']", 'üöä'),
        (
            'includes.html',
            ".//div[@class='inc-pyobj1 highlight-text notranslate']//pre",
            r'^class Foo:\n    pass\n\s*$',
        ),
        (
            'includes.html',
            ".//div[@class='inc-pyobj2 highlight-text notranslate']//pre",
            r'^    def baz\(\):\n        pass\n\s*$',
        ),
        (
            'includes.html',
            ".//div[@class='inc-lines highlight-text notranslate']//pre",
            r'^class Foo:\n    pass\nclass Bar:\n$',
        ),
        (
            'includes.html',
            ".//div[@class='inc-startend highlight-text notranslate']//pre",
            '^foo = "Including Unicode characters: üöä"\\n$',
        ),
        (
            'includes.html',
            ".//div[@class='inc-preappend highlight-text notranslate']//pre",
            r'(?m)^START CODE$',
        ),
        (
            'includes.html',
            ".//div[@class='inc-pyobj-dedent highlight-python notranslate']//span",
            r'def',
        ),
        (
            'includes.html',
            ".//div[@class='inc-tab3 highlight-text notranslate']//pre",
            r'-| |-',
        ),
        (
            'includes.html',
            ".//div[@class='inc-tab8 highlight-python notranslate']//pre/span",
            r'-|      |-',
        ),
        ('autodoc.html', ".//dl[@class='py class']/dt[@id='autodoc_target.Class']", ''),
        (
            'autodoc.html',
            ".//dl[@class='py function']/dt[@id='autodoc_target.function']/em/span/span",
            r'\*\*',
        ),
        (
            'autodoc.html',
            ".//dl[@class='py function']/dt[@id='autodoc_target.function']/em/span/span",
            r'kwds',
        ),
        ('autodoc.html', './/dd/p', r'Return spam\.'),
        ('extapi.html', './/strong', 'from class: Bar'),
        ('markup.html', './/title', 'set by title directive'),
        ('markup.html', './/p/em', 'Section author: Georg Brandl'),
        ('markup.html', './/p/em', 'Module author: Georg Brandl'),
        # created by the meta directive
        ('markup.html', ".//meta[@name='author'][@content='Me']", ''),
        ('markup.html', ".//meta[@name='keywords'][@content='docs, sphinx']", ''),
        # a label created by ``.. _label:``
        ('markup.html', ".//div[@id='label']", ''),
        # code with standard code blocks
        ('markup.html', './/pre', '^some code$'),
        # an option list
        ('markup.html', ".//span[@class='option']", '--help'),
        # admonitions
        ('markup.html', ".//p[@class='admonition-title']", 'My Admonition'),
        ('markup.html', ".//div[@class='admonition note']/p", 'Note text.'),
        ('markup.html', ".//div[@class='admonition warning']/p", 'Warning text.'),
        # inline markup
        ('markup.html', './/li/p/strong', r'^command\\n$'),
        ('markup.html', './/li/p/strong', r'^program\\n$'),
        ('markup.html', './/li/p/em', r'^dfn\\n$'),
        ('markup.html', './/li/p/kbd', r'^kbd\\n$'),
        ('markup.html', './/li/p/span', 'File \N{TRIANGULAR BULLET} Close'),
        ('markup.html', ".//li/p/code/span[@class='pre']", '^a/$'),
        ('markup.html', ".//li/p/code/em/span[@class='pre']", '^varpart$'),
        ('markup.html', ".//li/p/code/em/span[@class='pre']", '^i$'),
        (
            'markup.html',
            ".//a[@href='https://peps.python.org/pep-0008/']"
            "[@class='pep reference external']/strong",
            'PEP 8',
        ),
        (
            'markup.html',
            ".//a[@href='https://peps.python.org/pep-0008/']"
            "[@class='pep reference external']/strong",
            'Python Enhancement Proposal #8',
        ),
        (
            'markup.html',
            ".//a[@href='https://datatracker.ietf.org/doc/html/rfc1.html']"
            "[@class='rfc reference external']/strong",
            'RFC 1',
        ),
        (
            'markup.html',
            ".//a[@href='https://datatracker.ietf.org/doc/html/rfc1.html']"
            "[@class='rfc reference external']/strong",
            'Request for Comments #1',
        ),
        (
            'markup.html',
            ".//a[@href='objects.html#envvar-HOME']"
            "[@class='reference internal']/code/span[@class='pre']",
            'HOME',
        ),
        (
            'markup.html',
            ".//a[@href='#with'][@class='reference internal']/code/span[@class='pre']",
            '^with$',
        ),
        (
            'markup.html',
            ".//a[@href='#grammar-token-try_stmt']"
            "[@class='reference internal']/code/span",
            '^statement$',
        ),
        (
            'markup.html',
            ".//a[@href='#some-label'][@class='reference internal']/span",
            '^here$',
        ),
        (
            'markup.html',
            ".//a[@href='#some-label'][@class='reference internal']/span",
            '^there$',
        ),
        (
            'markup.html',
            ".//a[@href='subdir/includes.html'][@class='reference internal']/span",
            'Including in subdir',
        ),
        (
            'markup.html',
            ".//a[@href='objects.html#cmdoption-python-c']"
            "[@class='reference internal']/code/span[@class='pre']",
            '-c',
        ),
        # abbreviations
        ('markup.html', ".//abbr[@title='abbreviation']", '^abbr$'),
        # version stuff
        (
            'markup.html',
            ".//div[@class='versionadded']/p/span",
            'Added in version 0.6: ',
        ),
        (
            'markup.html',
            ".//div[@class='versionadded']/p/span",
            tail_check('First paragraph of version-added'),
        ),
        (
            'markup.html',
            ".//div[@class='versionadded']/p/span",
            tail_check('Deprecated alias for version-added'),
        ),
        (
            'markup.html',
            ".//div[@class='versionchanged']/p/span",
            tail_check('First paragraph of version-changed'),
        ),
        (
            'markup.html',
            ".//div[@class='versionchanged']/p",
            'Second paragraph of version-changed',
        ),
        (
            'markup.html',
            ".//div[@class='versionchanged']/p/span",
            tail_check('Deprecated alias for version-changed'),
        ),
        (
            'markup.html',
            ".//div[@class='deprecated']/p/span",
            'Deprecated since version 0.6: ',
        ),
        (
            'markup.html',
            ".//div[@class='deprecated']/p/span",
            tail_check('Boring stuff.'),
        ),
        (
            'markup.html',
            ".//div[@class='deprecated']/p/span",
            tail_check('Deprecated alias for version-deprecated'),
        ),
        (
            'markup.html',
            ".//div[@class='versionremoved']/p/span",
            'Removed in version 0.6: ',
        ),
        (
            'markup.html',
            ".//div[@class='versionremoved']/p/span",
            tail_check('Deprecated alias for version-removed'),
        ),
        # footnote reference
        ('markup.html', ".//a[@class='footnote-reference brackets']", r'1'),
        # created by reference lookup
        ('markup.html', ".//a[@href='index.html#ref1']", ''),
        # ``seealso`` directive
        ('markup.html', ".//div/p[@class='admonition-title']", 'See also'),
        # a ``hlist`` directive
        ('markup.html', ".//table[@class='hlist']/tr/td/ul/li/p", '^This$'),
        # a ``centered`` directive
        ('markup.html', ".//p[@class='centered']/strong", 'LICENSE'),
        # a glossary
        ('markup.html', ".//dl/dt[@id='term-boson']", 'boson'),
        ('markup.html', ".//dl/dt[@id='term-boson']/a", '¶'),
        # a production list
        ('markup.html', './/pre/strong', 'try_stmt'),
        (
            'markup.html',
            ".//pre/a[@href='#grammar-token-try1_stmt']/code/span",
            'try1_stmt',
        ),
        # tests for ``only`` directive
        ('markup.html', './/p', 'A global substitution!'),
        ('markup.html', './/p', 'In HTML.'),
        ('markup.html', './/p', 'In both.'),
        ('markup.html', './/p', 'Always present'),
        # tests for ``any`` role
        ('markup.html', ".//a[@href='#with']/span", 'headings'),
        (
            'markup.html',
            ".//a[@href='objects.html#func_without_body']/code/span",
            'objects',
        ),
        # tests for numeric labels
        (
            'markup.html',
            ".//a[@href='#id1'][@class='reference internal']/span",
            'Testing various markup',
        ),
        # tests for smartypants
        ('markup.html', './/li/p', 'Smart “quotes” in English ‘text’.'),
        ('markup.html', './/li/p', 'Smart — long and – short dashes.'),
        ('markup.html', './/li/p', 'Ellipsis…'),
        ('markup.html', ".//li/p/code/span[@class='pre']", 'foo--"bar"...'),
        ('markup.html', './/p', 'Этот «абзац» должен использовать „русские“ кавычки.'),
        ('markup.html', './/p', 'Il dit : « C’est “super” ! »'),
        ('objects.html', ".//dt[@id='mod.Cls.meth1']", ''),
        ('objects.html', ".//dt[@id='errmod.Error']", ''),
        (
            'objects.html',
            ".//dt/span[@class='sig-name descname']/span[@class='pre']",
            r'long\(parameter,',
        ),
        (
            'objects.html',
            ".//dt/span[@class='sig-name descname']/span[@class='pre']",
            r'list\)',
        ),
        (
            'objects.html',
            ".//dt/span[@class='sig-name descname']/span[@class='pre']",
            'another',
        ),
        (
            'objects.html',
            ".//dt/span[@class='sig-name descname']/span[@class='pre']",
            'one',
        ),
        ('objects.html', ".//a[@href='#mod.Cls'][@class='reference internal']", ''),
        ('objects.html', ".//dl[@class='std userdesc']", ''),
        ('objects.html', ".//dt[@id='userdesc-myobj']", ''),
        (
            'objects.html',
            ".//a[@href='#userdesc-myobj'][@class='reference internal']",
            '',
        ),
        # docfields
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#TimeInt']/em",
            'TimeInt',
        ),
        ('objects.html', ".//a[@class='reference internal'][@href='#Time']", 'Time'),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#errmod.Error']/strong",
            'Error',
        ),
        # C references
        ('objects.html', ".//span[@class='pre']", 'CFunction()'),
        ('objects.html', ".//a[@href='#c.Sphinx_DoSomething']", ''),
        ('objects.html', ".//a[@href='#c.SphinxStruct.member']", ''),
        ('objects.html', ".//a[@href='#c.SPHINX_USE_PYTHON']", ''),
        ('objects.html', ".//a[@href='#c.SphinxType']", ''),
        ('objects.html', ".//a[@href='#c.sphinx_global']", ''),
        # test global TOC created by toctree()
        (
            'objects.html',
            ".//ul[@class='current']/li[@class='toctree-l1 current']/a[@href='#']",
            'Testing object descriptions',
        ),
        (
            'objects.html',
            ".//li[@class='toctree-l1']/a[@href='markup.html']",
            'Testing various markup',
        ),
        # test unknown field names
        ('objects.html', ".//dt[@class='field-odd']", 'Field_name'),
        ('objects.html', ".//dt[@class='field-even']", 'Field_name all lower'),
        ('objects.html', ".//dt[@class='field-odd']", 'FIELD_NAME'),
        ('objects.html', ".//dt[@class='field-even']", 'FIELD_NAME ALL CAPS'),
        ('objects.html', ".//dt[@class='field-odd']", 'Field_Name'),
        ('objects.html', ".//dt[@class='field-even']", 'Field_Name All Word Caps'),
        # ('objects.html', ".//dt[@class='field-odd']", 'Field_name'), (duplicate)
        ('objects.html', ".//dt[@class='field-even']", 'Field_name First word cap'),
        ('objects.html', ".//dt[@class='field-odd']", 'FIELd_name'),
        ('objects.html', ".//dt[@class='field-even']", 'FIELd_name PARTial caps'),
        # custom sidebar
        ('objects.html', './/h4', 'Custom sidebar'),
        # docfields
        ('objects.html', ".//dd[@class='field-odd']/p/strong", '^moo$'),
        (
            'objects.html',
            ".//dd[@class='field-odd']/p/strong",
            tail_check(r'\(Moo\) .* Moo'),
        ),
        ('objects.html', ".//dd[@class='field-odd']/ul/li/p/strong", '^hour$'),
        ('objects.html', ".//dd[@class='field-odd']/ul/li/p/em", '^DuplicateType$'),
        (
            'objects.html',
            ".//dd[@class='field-odd']/ul/li/p/em",
            tail_check(r'.* Some parameter'),
        ),
        # others
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-perl-arg-p']/code/span",
            'perl',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-perl-arg-p']/code/span",
            '\\+p',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-perl-ObjC']/code/span",
            '--ObjC\\+\\+',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-perl-plugin.option']/code/span",
            '--plugin.option',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-perl-arg-create-auth-token']"
            '/code/span',
            'create-auth-token',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-perl-arg-arg']/code/span",
            'arg',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-perl-j']/code/span",
            '-j',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-hg-arg-commit']/code/span",
            'hg',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-hg-arg-commit']/code/span",
            'commit',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-git-commit-p']/code/span",
            'git',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-git-commit-p']/code/span",
            'commit',
        ),
        (
            'objects.html',
            ".//a[@class='reference internal'][@href='#cmdoption-git-commit-p']/code/span",
            '-p',
        ),
        ('index.html', ".//meta[@name='hc'][@content='hcval']", ''),
        ('index.html', ".//meta[@name='hc_co'][@content='hcval_co']", ''),
        ('index.html', ".//li[@class='toctree-l1']/a", 'Testing various markup'),
        ('index.html', ".//li[@class='toctree-l2']/a", 'Inline markup'),
        ('index.html', './/title', 'Sphinx <Tests>'),
        ('index.html', ".//div[@class='footer']", 'copyright text credits'),
        (
            'index.html',
            ".//a[@href='https://python.org/'][@class='reference external']",
            '',
        ),
        ('index.html', ".//li/p/a[@href='genindex.html']/span", 'Index'),
        ('index.html', ".//li/p/a[@href='py-modindex.html']/span", 'Module Index'),
        # custom sidebar only for contents
        ('index.html', './/h4', 'Contents sidebar'),
        # custom JavaScript
        ('index.html', ".//script[@src='file://moo.js']", ''),
        # URL in contents
        (
            'index.html',
            ".//a[@class='reference external'][@href='https://sphinx-doc.org/']",
            'https://sphinx-doc.org/',
        ),
        (
            'index.html',
            ".//a[@class='reference external'][@href='https://sphinx-doc.org/latest/']",
            'Latest reference',
        ),
        # Indirect hyperlink targets across files
        (
            'index.html',
            ".//a[@href='markup.html#some-label'][@class='reference internal']/span",
            '^indirect hyperref$',
        ),
        ('bom.html', './/title', ' File with UTF-8 BOM'),
        (
            'extensions.html',
            ".//a[@href='https://python.org/dev/']",
            'https://python.org/dev/',
        ),
        (
            'extensions.html',
            ".//a[@href='https://bugs.python.org/issue1000']",
            'issue 1000',
        ),
        (
            'extensions.html',
            ".//a[@href='https://bugs.python.org/issue1042']",
            'explicit caption',
        ),
        (
            'extensions.html',
            ".//a[@class='extlink-pyurl reference external']",
            'https://python.org/dev/',
        ),
        (
            'extensions.html',
            ".//a[@class='extlink-issue reference external']",
            'issue 1000',
        ),
        # index entries
        ('genindex.html', './/a/strong', 'Main'),
        ('genindex.html', './/a/strong', '[1]'),
        ('genindex.html', './/a/strong', 'Other'),
        ('genindex.html', './/a', 'entry'),
        ('genindex.html', './/li/a', 'double'),
        ('otherext.html', './/h1', 'Generated section'),
        ('otherext.html', ".//a[@href='_sources/otherext.foo.txt']", ''),
        ('search.html', ".//meta[@name='robots'][@content='noindex']", ''),
    ],
)
@pytest.mark.sphinx(
    'html',
    testroot='root',
    tags=['testtag'],
    confoverrides={'html_context.hckey_co': 'hcval_co'},
)
def test_html5_output(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
    fname: str,
    path: str,
    check: str,
) -> None:
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, path, check)


@pytest.mark.sphinx('html', testroot='markup-rubric')
def test_html5_rubric(app: SphinxTestApp) -> None:
    def insert_invalid_rubric_heading_level(
        app: SphinxTestApp,
        doctree: nodes.document,
        docname: str,
    ) -> None:
        if docname != 'index':
            return
        new_node = nodes.rubric('', 'INSERTED RUBRIC')
        new_node['heading-level'] = 7
        section = doctree[0]
        assert isinstance(section, nodes.Element)
        section.append(new_node)

    app.connect('doctree-resolved', insert_invalid_rubric_heading_level)
    app.build()

    warnings = app.warning.getvalue()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<p class="rubric">This is a rubric</p>' in content
    assert '<h2 class="myclass rubric">A rubric with a heading level 2</h2>' in content

    # directive warning
    assert '"7" unknown' in warnings

    # html writer warning
    assert 'WARNING: unsupported rubric heading level: 7' in warnings
    assert '</h7>' not in content
    assert '<p class="rubric">INSERTED RUBRIC</p>' in content


@pytest.mark.parametrize(
    ('node_type', 'version', 'lineno'),
    [
        # argument-style content (no blank line after directive)
        ('versionadded', '0.6', 296),
        ('versionadded', '0.6.1', 299),
        # body content (blank line after directive)
        ('versionadded', '1.2', 314),
        ('versionadded', '1.2.1', 318),
        # inline content (text on same line as directive)
        ('versionchanged', '3.14', 326),
        ('versionchanged', '3.1416', 328),
    ],
)
@pytest.mark.sphinx('dummy', testroot='root')
def test_versionadded_paragraph_source_info(
    app: SphinxTestApp,
    node_type: str,
    version: str,
    lineno: int,
) -> None:
    app.build()
    doctree = app.env.get_doctree('markup')
    for node in doctree.findall(addnodes.versionmodified):
        if node['type'] == node_type and node['version'] == version:
            assert node[0].line == lineno
            break
    else:
        pytest.fail(f'{node_type} {version} node not found')
