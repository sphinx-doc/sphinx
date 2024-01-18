"""Test the HTML builder and check output against XPath."""

import re

import pytest

from tests.test_builders.test_build_html import check_xpath, flat_dict


def tail_check(check):
    rex = re.compile(check)

    def checker(nodes):
        for node in nodes:
            if node.tail and rex.search(node.tail):
                return True
        msg = f'{check!r} not found in tail of any nodes {nodes}'
        raise AssertionError(msg)
    return checker


@pytest.mark.parametrize(("fname", "expect"), flat_dict({
    'images.html': [
        (".//img[@src='_images/img.png']", ''),
        (".//img[@src='_images/img1.png']", ''),
        (".//img[@src='_images/simg.png']", ''),
        (".//img[@src='_images/svgimg.svg']", ''),
        (".//a[@href='_sources/images.txt']", ''),
    ],
    'subdir/images.html': [
        (".//img[@src='../_images/img1.png']", ''),
        (".//img[@src='../_images/rimg.png']", ''),
    ],
    'subdir/includes.html': [
        (".//a[@class='reference download internal']", ''),
        (".//img[@src='../_images/img.png']", ''),
        (".//p", 'This is an include file.'),
        (".//pre/span", 'line 1'),
        (".//pre/span", 'line 2'),
    ],
    'includes.html': [
        (".//pre", 'Max Strauß'),
        (".//a[@class='reference download internal']", ''),
        (".//pre/span", '"quotes"'),
        (".//pre/span", "'included'"),
        (".//pre/span[@class='s2']", 'üöä'),
        (".//div[@class='inc-pyobj1 highlight-text notranslate']//pre",
         r'^class Foo:\n    pass\n\s*$'),
        (".//div[@class='inc-pyobj2 highlight-text notranslate']//pre",
         r'^    def baz\(\):\n        pass\n\s*$'),
        (".//div[@class='inc-lines highlight-text notranslate']//pre",
         r'^class Foo:\n    pass\nclass Bar:\n$'),
        (".//div[@class='inc-startend highlight-text notranslate']//pre",
         '^foo = "Including Unicode characters: üöä"\\n$'),
        (".//div[@class='inc-preappend highlight-text notranslate']//pre",
         r'(?m)^START CODE$'),
        (".//div[@class='inc-pyobj-dedent highlight-python notranslate']//span",
         r'def'),
        (".//div[@class='inc-tab3 highlight-text notranslate']//pre",
         r'-| |-'),
        (".//div[@class='inc-tab8 highlight-python notranslate']//pre/span",
         r'-|      |-'),
    ],
    'autodoc.html': [
        (".//dl[@class='py class']/dt[@id='autodoc_target.Class']", ''),
        (".//dl[@class='py function']/dt[@id='autodoc_target.function']/em/span/span", r'\*\*'),
        (".//dl[@class='py function']/dt[@id='autodoc_target.function']/em/span/span", r'kwds'),
        (".//dd/p", r'Return spam\.'),
    ],
    'extapi.html': [
        (".//strong", 'from class: Bar'),
    ],
    'markup.html': [
        (".//title", 'set by title directive'),
        (".//p/em", 'Section author: Georg Brandl'),
        (".//p/em", 'Module author: Georg Brandl'),
        # created by the meta directive
        (".//meta[@name='author'][@content='Me']", ''),
        (".//meta[@name='keywords'][@content='docs, sphinx']", ''),
        # a label created by ``.. _label:``
        (".//div[@id='label']", ''),
        # code with standard code blocks
        (".//pre", '^some code$'),
        # an option list
        (".//span[@class='option']", '--help'),
        # admonitions
        (".//p[@class='admonition-title']", 'My Admonition'),
        (".//div[@class='admonition note']/p", 'Note text.'),
        (".//div[@class='admonition warning']/p", 'Warning text.'),
        # inline markup
        (".//li/p/strong", r'^command\\n$'),
        (".//li/p/strong", r'^program\\n$'),
        (".//li/p/em", r'^dfn\\n$'),
        (".//li/p/kbd", r'^kbd\\n$'),
        (".//li/p/span", 'File \N{TRIANGULAR BULLET} Close'),
        (".//li/p/code/span[@class='pre']", '^a/$'),
        (".//li/p/code/em/span[@class='pre']", '^varpart$'),
        (".//li/p/code/em/span[@class='pre']", '^i$'),
        (".//a[@href='https://peps.python.org/pep-0008/']"
         "[@class='pep reference external']/strong", 'PEP 8'),
        (".//a[@href='https://peps.python.org/pep-0008/']"
         "[@class='pep reference external']/strong",
         'Python Enhancement Proposal #8'),
        (".//a[@href='https://datatracker.ietf.org/doc/html/rfc1.html']"
         "[@class='rfc reference external']/strong", 'RFC 1'),
        (".//a[@href='https://datatracker.ietf.org/doc/html/rfc1.html']"
         "[@class='rfc reference external']/strong", 'Request for Comments #1'),
        (".//a[@href='objects.html#envvar-HOME']"
         "[@class='reference internal']/code/span[@class='pre']", 'HOME'),
        (".//a[@href='#with']"
         "[@class='reference internal']/code/span[@class='pre']", '^with$'),
        (".//a[@href='#grammar-token-try_stmt']"
         "[@class='reference internal']/code/span", '^statement$'),
        (".//a[@href='#some-label'][@class='reference internal']/span", '^here$'),
        (".//a[@href='#some-label'][@class='reference internal']/span", '^there$'),
        (".//a[@href='subdir/includes.html']"
         "[@class='reference internal']/span", 'Including in subdir'),
        (".//a[@href='objects.html#cmdoption-python-c']"
         "[@class='reference internal']/code/span[@class='pre']", '-c'),
        # abbreviations
        (".//abbr[@title='abbreviation']", '^abbr$'),
        # version stuff
        (".//div[@class='versionadded']/p/span", 'New in version 0.6: '),
        (".//div[@class='versionadded']/p/span",
         tail_check('First paragraph of versionadded')),
        (".//div[@class='versionchanged']/p/span",
         tail_check('First paragraph of versionchanged')),
        (".//div[@class='versionchanged']/p",
         'Second paragraph of versionchanged'),
        # footnote reference
        (".//a[@class='footnote-reference brackets']", r'1'),
        # created by reference lookup
        (".//a[@href='index.html#ref1']", ''),
        # ``seealso`` directive
        (".//div/p[@class='admonition-title']", 'See also'),
        # a ``hlist`` directive
        (".//table[@class='hlist']/tbody/tr/td/ul/li/p", '^This$'),
        # a ``centered`` directive
        (".//p[@class='centered']/strong", 'LICENSE'),
        # a glossary
        (".//dl/dt[@id='term-boson']", 'boson'),
        (".//dl/dt[@id='term-boson']/a", '¶'),
        # a production list
        (".//pre/strong", 'try_stmt'),
        (".//pre/a[@href='#grammar-token-try1_stmt']/code/span", 'try1_stmt'),
        # tests for ``only`` directive
        (".//p", 'A global substitution!'),
        (".//p", 'In HTML.'),
        (".//p", 'In both.'),
        (".//p", 'Always present'),
        # tests for ``any`` role
        (".//a[@href='#with']/span", 'headings'),
        (".//a[@href='objects.html#func_without_body']/code/span", 'objects'),
        # tests for numeric labels
        (".//a[@href='#id1'][@class='reference internal']/span", 'Testing various markup'),
        # tests for smartypants
        (".//li/p", 'Smart “quotes” in English ‘text’.'),
        (".//li/p", 'Smart — long and – short dashes.'),
        (".//li/p", 'Ellipsis…'),
        (".//li/p/code/span[@class='pre']", 'foo--"bar"...'),
        (".//p", 'Этот «абзац» должен использовать „русские“ кавычки.'),
        (".//p", 'Il dit : « C’est “super” ! »'),
    ],
    'objects.html': [
        (".//dt[@id='mod.Cls.meth1']", ''),
        (".//dt[@id='errmod.Error']", ''),
        (".//dt/span[@class='sig-name descname']/span[@class='pre']", r'long\(parameter,'),
        (".//dt/span[@class='sig-name descname']/span[@class='pre']", r'list\)'),
        (".//dt/span[@class='sig-name descname']/span[@class='pre']", 'another'),
        (".//dt/span[@class='sig-name descname']/span[@class='pre']", 'one'),
        (".//a[@href='#mod.Cls'][@class='reference internal']", ''),
        (".//dl[@class='std userdesc']", ''),
        (".//dt[@id='userdesc-myobj']", ''),
        (".//a[@href='#userdesc-myobj'][@class='reference internal']", ''),
        # docfields
        (".//a[@class='reference internal'][@href='#TimeInt']/em", 'TimeInt'),
        (".//a[@class='reference internal'][@href='#Time']", 'Time'),
        (".//a[@class='reference internal'][@href='#errmod.Error']/strong", 'Error'),
        # C references
        (".//span[@class='pre']", 'CFunction()'),
        (".//a[@href='#c.Sphinx_DoSomething']", ''),
        (".//a[@href='#c.SphinxStruct.member']", ''),
        (".//a[@href='#c.SPHINX_USE_PYTHON']", ''),
        (".//a[@href='#c.SphinxType']", ''),
        (".//a[@href='#c.sphinx_global']", ''),
        # test global TOC created by toctree()
        (".//ul[@class='current']/li[@class='toctree-l1 current']/a[@href='#']",
         'Testing object descriptions'),
        (".//li[@class='toctree-l1']/a[@href='markup.html']",
         'Testing various markup'),
        # test unknown field names
        (".//dt[@class='field-odd']", 'Field_name'),
        (".//dt[@class='field-even']", 'Field_name all lower'),
        (".//dt[@class='field-odd']", 'FIELD_NAME'),
        (".//dt[@class='field-even']", 'FIELD_NAME ALL CAPS'),
        (".//dt[@class='field-odd']", 'Field_Name'),
        (".//dt[@class='field-even']", 'Field_Name All Word Caps'),
        (".//dt[@class='field-odd']", 'Field_name'),
        (".//dt[@class='field-even']", 'Field_name First word cap'),
        (".//dt[@class='field-odd']", 'FIELd_name'),
        (".//dt[@class='field-even']", 'FIELd_name PARTial caps'),
        # custom sidebar
        (".//h4", 'Custom sidebar'),
        # docfields
        (".//dd[@class='field-odd']/p/strong", '^moo$'),
        (".//dd[@class='field-odd']/p/strong", tail_check(r'\(Moo\) .* Moo')),
        (".//dd[@class='field-odd']/ul/li/p/strong", '^hour$'),
        (".//dd[@class='field-odd']/ul/li/p/em", '^DuplicateType$'),
        (".//dd[@class='field-odd']/ul/li/p/em", tail_check(r'.* Some parameter')),
        # others
        (".//a[@class='reference internal'][@href='#cmdoption-perl-arg-p']/code/span",
         'perl'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-arg-p']/code/span",
         '\\+p'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-ObjC']/code/span",
         '--ObjC\\+\\+'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-plugin.option']/code/span",
         '--plugin.option'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-arg-create-auth-token']"
         "/code/span",
         'create-auth-token'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-arg-arg']/code/span",
         'arg'),
        (".//a[@class='reference internal'][@href='#cmdoption-perl-j']/code/span",
         '-j'),
        (".//a[@class='reference internal'][@href='#cmdoption-hg-arg-commit']/code/span",
         'hg'),
        (".//a[@class='reference internal'][@href='#cmdoption-hg-arg-commit']/code/span",
         'commit'),
        (".//a[@class='reference internal'][@href='#cmdoption-git-commit-p']/code/span",
         'git'),
        (".//a[@class='reference internal'][@href='#cmdoption-git-commit-p']/code/span",
         'commit'),
        (".//a[@class='reference internal'][@href='#cmdoption-git-commit-p']/code/span",
         '-p'),
    ],
    'index.html': [
        (".//meta[@name='hc'][@content='hcval']", ''),
        (".//meta[@name='hc_co'][@content='hcval_co']", ''),
        (".//li[@class='toctree-l1']/a", 'Testing various markup'),
        (".//li[@class='toctree-l2']/a", 'Inline markup'),
        (".//title", 'Sphinx <Tests>'),
        (".//div[@class='footer']", 'copyright text credits'),
        (".//a[@href='https://python.org/']"
         "[@class='reference external']", ''),
        (".//li/p/a[@href='genindex.html']/span", 'Index'),
        (".//li/p/a[@href='py-modindex.html']/span", 'Module Index'),
        # custom sidebar only for contents
        (".//h4", 'Contents sidebar'),
        # custom JavaScript
        (".//script[@src='file://moo.js']", ''),
        # URL in contents
        (".//a[@class='reference external'][@href='https://sphinx-doc.org/']",
         'https://sphinx-doc.org/'),
        (".//a[@class='reference external'][@href='https://sphinx-doc.org/latest/']",
         'Latest reference'),
        # Indirect hyperlink targets across files
        (".//a[@href='markup.html#some-label'][@class='reference internal']/span",
         '^indirect hyperref$'),
    ],
    'bom.html': [
        (".//title", " File with UTF-8 BOM"),
    ],
    'extensions.html': [
        (".//a[@href='https://python.org/dev/']", "https://python.org/dev/"),
        (".//a[@href='https://bugs.python.org/issue1000']", "issue 1000"),
        (".//a[@href='https://bugs.python.org/issue1042']", "explicit caption"),
    ],
    'genindex.html': [
        # index entries
        (".//a/strong", "Main"),
        (".//a/strong", "[1]"),
        (".//a/strong", "Other"),
        (".//a", "entry"),
        (".//li/a", "double"),
    ],
    'otherext.html': [
        (".//h1", "Generated section"),
        (".//a[@href='_sources/otherext.foo.txt']", ''),
    ],
    'search.html': [
        (".//meta[@name='robots'][@content='noindex']", ''),
    ],
}))
@pytest.mark.sphinx('html', tags=['testtag'],
                    confoverrides={'html_context.hckey_co': 'hcval_co'})
@pytest.mark.test_params(shared_result='test_build_html_output')
def test_html5_output(app, cached_etree_parse, fname, expect):
    app.build()
    check_xpath(cached_etree_parse(app.outdir / fname), fname, *expect)
