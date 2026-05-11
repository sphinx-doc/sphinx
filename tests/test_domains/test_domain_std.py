"""Tests the std domain"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import mock

import pytest
from docutils import nodes
from docutils.nodes import definition, definition_list, definition_list_item, term

from sphinx import addnodes
from sphinx.addnodes import (
    desc,
    desc_addname,
    desc_content,
    desc_name,
    desc_signature,
    glossary,
    index,
    pending_xref,
)
from sphinx.domains.std import StandardDomain
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

from tests.utils import extract_node

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


def test_process_doc_handle_figure_caption() -> None:
    env = mock.Mock(domaindata={})
    env._registry.enumerable_nodes = {}
    figure_node = nodes.figure(
        '',
        nodes.caption('caption text', 'caption text'),
    )
    document = mock.Mock(
        nametypes={'testname': True},
        nameids={'testname': 'testid'},
        ids={'testid': figure_node},
        citation_refs={},
    )
    document.findall.return_value = []

    domain = StandardDomain(env)
    if 'testname' in domain.data['labels']:
        del domain.data['labels']['testname']
    domain.process_doc(env, 'testdoc', document)
    assert 'testname' in domain.data['labels']
    assert domain.data['labels']['testname'] == ('testdoc', 'testid', 'caption text')


def test_process_doc_handle_table_title() -> None:
    env = mock.Mock(domaindata={})
    env._registry.enumerable_nodes = {}
    table_node = nodes.table(
        '',
        nodes.title('title text', 'title text'),
    )
    document = mock.Mock(
        nametypes={'testname': True},
        nameids={'testname': 'testid'},
        ids={'testid': table_node},
        citation_refs={},
    )
    document.findall.return_value = []

    domain = StandardDomain(env)
    if 'testname' in domain.data['labels']:
        del domain.data['labels']['testname']
    domain.process_doc(env, 'testdoc', document)
    assert 'testname' in domain.data['labels']
    assert domain.data['labels']['testname'] == ('testdoc', 'testid', 'title text')


def test_get_full_qualified_name() -> None:
    env = mock.Mock(domaindata={})
    env._registry.enumerable_nodes = {}
    domain = StandardDomain(env)

    # normal references
    node = nodes.reference()
    assert domain.get_full_qualified_name(node) is None

    # simple reference to options
    node = nodes.reference(reftype='option', reftarget='-l')
    assert domain.get_full_qualified_name(node) is None

    # options with std:program context
    kwargs = {'std:program': 'ls'}
    node = nodes.reference(reftype='option', reftarget='-l', **kwargs)
    assert domain.get_full_qualified_name(node) == 'ls.-l'


@pytest.mark.sphinx('html', testroot='_blank')
def test_cmd_option_with_optional_value(app: SphinxTestApp) -> None:
    text = '.. option:: -j[=N]'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            index,
            [
                desc,
                (
                    [desc_signature, ([desc_name, '-j'], [desc_addname, '[=N]'])],
                    [desc_content, ()],
                ),
            ],
        ),
    )
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[('pair', 'command line option; -j', 'cmdoption-j', '', None)],
    )

    objects = list(app.env.domains.standard_domain.get_objects())
    assert ('-j', '-j', 'cmdoption', 'index', 'cmdoption-j', 1) in objects


@pytest.mark.sphinx('html', testroot='_blank')
def test_cmd_option_starting_with_bracket(app: SphinxTestApp) -> None:
    text = '.. option:: [enable=]PATTERN'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            index,
            [
                desc,
                (
                    [
                        desc_signature,
                        ([desc_name, '[enable'], [desc_addname, '=]PATTERN']),
                    ],
                    [desc_content, ()],
                ),
            ],
        ),
    )
    objects = list(app.env.domains.standard_domain.get_objects())
    assert (
        '[enable',
        '[enable',
        'cmdoption',
        'index',
        'cmdoption-arg-enable',
        1,
    ) in objects


@pytest.mark.sphinx('html', testroot='_blank')
def test_glossary(app):
    text = (
        '.. glossary::\n'
        '\n'
        '   term1\n'
        '   TERM2\n'
        '       description\n'
        '\n'
        '   term3 : classifier\n'
        '       description\n'
        '       description\n'
        '\n'
        '   term4 : class1 : class2\n'
        '       description\n'
    )

    # doctree
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            [
                glossary,
                definition_list,
                (
                    [
                        definition_list_item,
                        (
                            [term, ('term1', index)],
                            [term, ('TERM2', index)],
                            definition,
                        ),
                    ],
                    [definition_list_item, ([term, ('term3', index)], definition)],
                    [definition_list_item, ([term, ('term4', index)], definition)],
                ),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 0, 0, 0, 0, 1),
        entries=[('single', 'term1', 'term-term1', 'main', None)],
    )
    assert_node(
        extract_node(doctree, 0, 0, 0, 1, 1),
        entries=[('single', 'TERM2', 'term-TERM2', 'main', None)],
    )
    assert_node(
        extract_node(doctree, 0, 0, 0, 2), [definition, nodes.paragraph, 'description']
    )
    assert_node(
        extract_node(doctree, 0, 0, 1, 0, 1),
        entries=[('single', 'term3', 'term-term3', 'main', 'classifier')],
    )
    assert_node(
        extract_node(doctree, 0, 0, 1, 1),
        [definition, nodes.paragraph, 'description\ndescription'],
    )
    assert_node(
        extract_node(doctree, 0, 0, 2, 0, 1),
        entries=[('single', 'term4', 'term-term4', 'main', 'class1')],
    )
    assert_node(
        extract_node(doctree, 0, 0, 2, 1),
        [nodes.definition, nodes.paragraph, 'description'],
    )

    # index
    domain = app.env.domains.standard_domain
    objects = list(domain.get_objects())
    assert ('term1', 'term1', 'term', 'index', 'term-term1', -1) in objects
    assert ('TERM2', 'TERM2', 'term', 'index', 'term-TERM2', -1) in objects
    assert ('term3', 'term3', 'term', 'index', 'term-term3', -1) in objects
    assert ('term4', 'term4', 'term', 'index', 'term-term4', -1) in objects

    # term reference (case sensitive)
    refnode = domain.resolve_xref(
        app.env,
        'index',
        app.builder,
        'term',
        'term1',
        pending_xref(),
        nodes.paragraph(),
    )
    assert_node(refnode, nodes.reference, refid='term-term1')

    # term reference (case insensitive)
    refnode = domain.resolve_xref(
        app.env,
        'index',
        app.builder,
        'term',
        'term2',
        pending_xref(),
        nodes.paragraph(),
    )
    assert_node(refnode, nodes.reference, refid='term-TERM2')


@pytest.mark.sphinx('html', testroot='_blank')
def test_glossary_warning(app: SphinxTestApp) -> None:
    # empty line between terms
    text = '.. glossary::\n\n   term1\n\n   term2\n'
    restructuredtext.parse(app, text, 'case1')
    assert (
        'case1.rst:4: WARNING: glossary terms must not be separated by empty lines'
    ) in app.warning.getvalue()

    # glossary starts with indented item
    text = '.. glossary::\n\n       description\n   term\n'
    restructuredtext.parse(app, text, 'case2')
    assert (
        'case2.rst:3: WARNING: glossary term must be preceded by empty line'
    ) in app.warning.getvalue()

    # empty line between terms
    text = '.. glossary::\n\n   term1\n       description\n   term2\n'
    restructuredtext.parse(app, text, 'case3')
    assert (
        'case3.rst:4: WARNING: glossary term must be preceded by empty line'
    ) in app.warning.getvalue()

    # duplicated terms
    text = '.. glossary::\n\n   term-case4\n   term-case4\n'
    restructuredtext.parse(app, text, 'case4')
    assert (
        'case4.rst:3: WARNING: duplicate term description of term-case4, '
        'other instance in case4'
    ) in app.warning.getvalue()


@pytest.mark.sphinx('html', testroot='_blank')
def test_glossary_comment(app):
    text = (
        '.. glossary::\n'
        '\n'
        '   term1\n'
        '       description\n'
        '   .. term2\n'
        '       description\n'
        '       description\n'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            [
                glossary,
                definition_list,
                definition_list_item,
                ([term, ('term1', index)], definition),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 0, 0, 0, 1),
        [nodes.definition, nodes.paragraph, 'description'],
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_glossary_comment2(app):
    text = (
        '.. glossary::\n'
        '\n'
        '   term1\n'
        '       description\n'
        '\n'
        '   .. term2\n'
        '   term3\n'
        '       description\n'
        '       description\n'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            [
                glossary,
                definition_list,
                (
                    [definition_list_item, ([term, ('term1', index)], definition)],
                    [definition_list_item, ([term, ('term3', index)], definition)],
                ),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 0, 0, 0, 1),
        [nodes.definition, nodes.paragraph, 'description'],
    )
    assert_node(
        extract_node(doctree, 0, 0, 1, 1),
        [nodes.definition, nodes.paragraph, 'description\ndescription'],
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_glossary_sorted(app):
    text = (
        '.. glossary::\n'
        '   :sorted:\n'
        '\n'
        '   term3\n'
        '       description\n'
        '\n'
        '   term2\n'
        '   term1\n'
        '       description\n'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            [
                glossary,
                definition_list,
                (
                    [
                        definition_list_item,
                        (
                            [term, ('term2', index)],
                            [term, ('term1', index)],
                            definition,
                        ),
                    ],
                    [definition_list_item, ([term, ('term3', index)], definition)],
                ),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 0, 0, 0, 2),
        [nodes.definition, nodes.paragraph, 'description'],
    )
    assert_node(
        extract_node(doctree, 0, 0, 1, 1),
        [nodes.definition, nodes.paragraph, 'description'],
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_glossary_alphanumeric(app: SphinxTestApp) -> None:
    text = '.. glossary::\n\n   1\n   /\n'
    restructuredtext.parse(app, text)
    objects = list(app.env.domains.standard_domain.get_objects())
    assert ('1', '1', 'term', 'index', 'term-1', -1) in objects
    assert ('/', '/', 'term', 'index', 'term-0', -1) in objects


@pytest.mark.sphinx('html', testroot='_blank')
def test_glossary_conflicted_labels(app: SphinxTestApp) -> None:
    text = '.. _term-foo:\n.. glossary::\n\n   foo\n'
    restructuredtext.parse(app, text)
    objects = list(app.env.domains.standard_domain.get_objects())
    assert ('foo', 'foo', 'term', 'index', 'term-0', -1) in objects


@pytest.mark.sphinx('html', testroot='_blank')
def test_cmdoption(app: SphinxTestApp) -> None:
    text = '.. program:: ls\n\n.. option:: -l\n'
    domain = app.env.domains.standard_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [desc_signature, ([desc_name, '-l'], [desc_addname, ()])],
                    [desc_content, ()],
                ),
            ],
        ),
    )
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[('pair', 'ls command line option; -l', 'cmdoption-ls-l', '', None)],
    )
    assert ('ls', '-l') in domain.progoptions
    assert domain.progoptions['ls', '-l'] == ('index', 'cmdoption-ls-l')


@pytest.mark.sphinx('html', testroot='_blank')
def test_cmdoption_for_None(app: SphinxTestApp) -> None:
    text = '.. program:: ls\n.. program:: None\n\n.. option:: -l\n'
    domain = app.env.domains.standard_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [desc_signature, ([desc_name, '-l'], [desc_addname, ()])],
                    [desc_content, ()],
                ),
            ],
        ),
    )
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[('pair', 'command line option; -l', 'cmdoption-l', '', None)],
    )
    assert (None, '-l') in domain.progoptions
    assert domain.progoptions[None, '-l'] == ('index', 'cmdoption-l')


@pytest.mark.sphinx('html', testroot='_blank')
def test_multiple_cmdoptions(app: SphinxTestApp) -> None:
    text = '.. program:: cmd\n\n.. option:: -o directory, --output directory\n'
    domain = app.env.domains.standard_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [desc_name, '-o'],
                            [desc_addname, ' directory'],
                            [desc_addname, ', '],
                            [desc_name, '--output'],
                            [desc_addname, ' directory'],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
        ),
    )
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[
            ('pair', 'cmd command line option; -o', 'cmdoption-cmd-o', '', None),
            ('pair', 'cmd command line option; --output', 'cmdoption-cmd-o', '', None),
        ],
    )
    assert ('cmd', '-o') in domain.progoptions
    assert ('cmd', '--output') in domain.progoptions
    assert domain.progoptions['cmd', '-o'] == ('index', 'cmdoption-cmd-o')
    assert domain.progoptions['cmd', '--output'] == ('index', 'cmdoption-cmd-o')


@pytest.mark.sphinx('html', testroot='_blank')
def test_disabled_docref(app: SphinxTestApp) -> None:
    text = ':doc:`index`\n:doc:`!index`\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            [
                nodes.paragraph,
                ([pending_xref, nodes.inline, 'index'], '\n', [nodes.inline, 'index']),
            ],
        ),
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_labeled_rubric(app: SphinxTestApp) -> None:
    text = '.. _label:\n.. rubric:: blah *blah* blah\n'
    restructuredtext.parse(app, text)

    domain = app.env.domains.standard_domain
    assert 'label' in domain.labels
    assert domain.labels['label'] == ('index', 'label', 'blah blah blah')


@pytest.mark.sphinx('html', testroot='_blank')
def test_labeled_definition(app: SphinxTestApp) -> None:
    text = (
        '.. _label1:\n'
        '\n'
        'Foo blah *blah* blah\n'
        '  Definition\n'
        '\n'
        '.. _label2:\n'
        '\n'
        'Bar blah *blah* blah\n'
        '  Definition\n'
        '\n'
    )
    restructuredtext.parse(app, text)

    domain = app.env.domains.standard_domain
    assert 'label1' in domain.labels
    assert domain.labels['label1'] == ('index', 'label1', 'Foo blah blah blah')
    assert 'label2' in domain.labels
    assert domain.labels['label2'] == ('index', 'label2', 'Bar blah blah blah')


@pytest.mark.sphinx('html', testroot='_blank')
def test_labeled_field(app: SphinxTestApp) -> None:
    text = (
        '.. _label1:\n'
        '\n'
        ':Foo blah *blah* blah:\n'
        '  Definition\n'
        '\n'
        '.. _label2:\n'
        '\n'
        ':Bar blah *blah* blah:\n'
        '  Definition\n'
        '\n'
    )
    restructuredtext.parse(app, text)

    domain = app.env.domains.standard_domain
    assert 'label1' in domain.labels
    assert domain.labels['label1'] == ('index', 'label1', 'Foo blah blah blah')
    assert 'label2' in domain.labels
    assert domain.labels['label2'] == ('index', 'label2', 'Bar blah blah blah')


@pytest.mark.sphinx(
    'html',
    testroot='manpage_url',
    confoverrides={'manpages_url': 'https://example.com/{page}.{section}'},
)
def test_html_manpage(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<em class="manpage">'
        '<a class="manpage reference external" href="https://example.com/man.1">man(1)</a>'
        '</em>'
    ) in content
    assert (
        '<em class="manpage">'
        '<a class="manpage reference external" href="https://example.com/ls.1">ls.1</a>'
        '</em>'
    ) in content
    assert (
        '<em class="manpage">'
        '<a class="manpage reference external" href="https://example.com/sphinx.">sphinx</a>'
        '</em>'
    ) in content
    assert (
        '<em class="manpage">'
        '<a class="manpage reference external" href="https://example.com/bsd-mailx/mailx.1">mailx(1)</a>'
        '</em>'
    ) in content
    assert '<em class="manpage">man(1)</em>' in content
