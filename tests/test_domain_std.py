"""
    test_domain_std
    ~~~~~~~~~~~~~~~

    Tests the std domain

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest import mock

import pytest
from docutils import nodes
from docutils.nodes import definition, definition_list, definition_list_item, term
from html5lib import HTMLParser

from sphinx import addnodes
from sphinx.addnodes import (desc, desc_addname, desc_content, desc_name, desc_signature,
                             glossary, index, pending_xref)
from sphinx.domains.std import StandardDomain
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


def test_process_doc_handle_figure_caption():
    env = mock.Mock(domaindata={})
    env.app.registry.enumerable_nodes = {}
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
    assert domain.data['labels']['testname'] == (
        'testdoc', 'testid', 'caption text')


def test_process_doc_handle_table_title():
    env = mock.Mock(domaindata={})
    env.app.registry.enumerable_nodes = {}
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
    assert domain.data['labels']['testname'] == (
        'testdoc', 'testid', 'title text')


def test_get_full_qualified_name():
    env = mock.Mock(domaindata={})
    env.app.registry.enumerable_nodes = {}
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


def test_cmd_option_with_optional_value(app):
    text = ".. option:: -j[=N]"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (index,
                          [desc, ([desc_signature, ([desc_name, '-j'],
                                                    [desc_addname, '[=N]'])],
                                  [desc_content, ()])]))
    assert_node(doctree[0], addnodes.index,
                entries=[('pair', 'command line option; -j', 'cmdoption-j', '', None)])

    objects = list(app.env.get_domain("std").get_objects())
    assert ('-j', '-j', 'cmdoption', 'index', 'cmdoption-j', 1) in objects


def test_cmd_option_starting_with_bracket(app):
    text = ".. option:: [enable=]PATTERN"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (index,
                          [desc, ([desc_signature, ([desc_name, '[enable'],
                                                    [desc_addname, '=]PATTERN'])],
                                  [desc_content, ()])]))
    objects = list(app.env.get_domain("std").get_objects())
    assert ('[enable', '[enable', 'cmdoption', 'index', 'cmdoption-arg-enable', 1) in objects


def test_glossary(app):
    text = (".. glossary::\n"
            "\n"
            "   term1\n"
            "   TERM2\n"
            "       description\n"
            "\n"
            "   term3 : classifier\n"
            "       description\n"
            "       description\n"
            "\n"
            "   term4 : class1 : class2\n"
            "       description\n")

    # doctree
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        [glossary, definition_list, ([definition_list_item, ([term, ("term1",
                                                                     index)],
                                                             [term, ("TERM2",
                                                                     index)],
                                                             definition)],
                                     [definition_list_item, ([term, ("term3",
                                                                     index)],
                                                             definition)],
                                     [definition_list_item, ([term, ("term4",
                                                                     index)],
                                                             definition)])],
    ))
    assert_node(doctree[0][0][0][0][1],
                entries=[("single", "term1", "term-term1", "main", None)])
    assert_node(doctree[0][0][0][1][1],
                entries=[("single", "TERM2", "term-TERM2", "main", None)])
    assert_node(doctree[0][0][0][2],
                [definition, nodes.paragraph, "description"])
    assert_node(doctree[0][0][1][0][1],
                entries=[("single", "term3", "term-term3", "main", "classifier")])
    assert_node(doctree[0][0][1][1],
                [definition, nodes.paragraph, ("description\n"
                                               "description")])
    assert_node(doctree[0][0][2][0][1],
                entries=[("single", "term4", "term-term4", "main", "class1")])
    assert_node(doctree[0][0][2][1],
                [nodes.definition, nodes.paragraph, "description"])

    # index
    domain = app.env.get_domain("std")
    objects = list(domain.get_objects())
    assert ("term1", "term1", "term", "index", "term-term1", -1) in objects
    assert ("TERM2", "TERM2", "term", "index", "term-TERM2", -1) in objects
    assert ("term3", "term3", "term", "index", "term-term3", -1) in objects
    assert ("term4", "term4", "term", "index", "term-term4", -1) in objects

    # term reference (case sensitive)
    refnode = domain.resolve_xref(app.env, 'index', app.builder, 'term', 'term1',
                                  pending_xref(), nodes.paragraph())
    assert_node(refnode, nodes.reference, refid="term-term1")

    # term reference (case insensitive)
    refnode = domain.resolve_xref(app.env, 'index', app.builder, 'term', 'term2',
                                  pending_xref(), nodes.paragraph())
    assert_node(refnode, nodes.reference, refid="term-TERM2")


def test_glossary_warning(app, status, warning):
    # empty line between terms
    text = (".. glossary::\n"
            "\n"
            "   term1\n"
            "\n"
            "   term2\n")
    restructuredtext.parse(app, text, "case1")
    assert ("case1.rst:4: WARNING: glossary terms must not be separated by empty lines"
            in warning.getvalue())

    # glossary starts with indented item
    text = (".. glossary::\n"
            "\n"
            "       description\n"
            "   term\n")
    restructuredtext.parse(app, text, "case2")
    assert ("case2.rst:3: WARNING: glossary term must be preceded by empty line"
            in warning.getvalue())

    # empty line between terms
    text = (".. glossary::\n"
            "\n"
            "   term1\n"
            "       description\n"
            "   term2\n")
    restructuredtext.parse(app, text, "case3")
    assert ("case3.rst:4: WARNING: glossary term must be preceded by empty line"
            in warning.getvalue())

    # duplicated terms
    text = (".. glossary::\n"
            "\n"
            "   term-case4\n"
            "   term-case4\n")
    restructuredtext.parse(app, text, "case4")
    assert ("case4.rst:3: WARNING: duplicate term description of term-case4, "
            "other instance in case4" in warning.getvalue())


def test_glossary_comment(app):
    text = (".. glossary::\n"
            "\n"
            "   term1\n"
            "       description\n"
            "   .. term2\n"
            "       description\n"
            "       description\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        [glossary, definition_list, definition_list_item, ([term, ("term1",
                                                                   index)],
                                                           definition)],
    ))
    assert_node(doctree[0][0][0][1],
                [nodes.definition, nodes.paragraph, "description"])


def test_glossary_comment2(app):
    text = (".. glossary::\n"
            "\n"
            "   term1\n"
            "       description\n"
            "\n"
            "   .. term2\n"
            "   term3\n"
            "       description\n"
            "       description\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        [glossary, definition_list, ([definition_list_item, ([term, ("term1",
                                                                     index)],
                                                             definition)],
                                     [definition_list_item, ([term, ("term3",
                                                                     index)],
                                                             definition)])],
    ))
    assert_node(doctree[0][0][0][1],
                [nodes.definition, nodes.paragraph, "description"])
    assert_node(doctree[0][0][1][1],
                [nodes.definition, nodes.paragraph, ("description\n"
                                                     "description")])


def test_glossary_sorted(app):
    text = (".. glossary::\n"
            "   :sorted:\n"
            "\n"
            "   term3\n"
            "       description\n"
            "\n"
            "   term2\n"
            "   term1\n"
            "       description\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        [glossary, definition_list, ([definition_list_item, ([term, ("term2",
                                                                     index)],
                                                             [term, ("term1",
                                                                     index)],
                                                             definition)],
                                     [definition_list_item, ([term, ("term3",
                                                                     index)],
                                                             definition)])],
    ))
    assert_node(doctree[0][0][0][2],
                [nodes.definition, nodes.paragraph, "description"])
    assert_node(doctree[0][0][1][1],
                [nodes.definition, nodes.paragraph, "description"])


def test_glossary_alphanumeric(app):
    text = (".. glossary::\n"
            "\n"
            "   1\n"
            "   /\n")
    restructuredtext.parse(app, text)
    objects = list(app.env.get_domain("std").get_objects())
    assert ("1", "1", "term", "index", "term-1", -1) in objects
    assert ("/", "/", "term", "index", "term-0", -1) in objects


def test_glossary_conflicted_labels(app):
    text = (".. _term-foo:\n"
            ".. glossary::\n"
            "\n"
            "   foo\n")
    restructuredtext.parse(app, text)
    objects = list(app.env.get_domain("std").get_objects())
    assert ("foo", "foo", "term", "index", "term-0", -1) in objects


def test_cmdoption(app):
    text = (".. program:: ls\n"
            "\n"
            ".. option:: -l\n")
    domain = app.env.get_domain('std')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "-l"],
                                                    [desc_addname, ()])],
                                  [desc_content, ()])]))
    assert_node(doctree[0], addnodes.index,
                entries=[('pair', 'ls command line option; -l', 'cmdoption-ls-l', '', None)])
    assert ('ls', '-l') in domain.progoptions
    assert domain.progoptions[('ls', '-l')] == ('index', 'cmdoption-ls-l')


def test_cmdoption_for_None(app):
    text = (".. program:: ls\n"
            ".. program:: None\n"
            "\n"
            ".. option:: -l\n")
    domain = app.env.get_domain('std')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "-l"],
                                                    [desc_addname, ()])],
                                  [desc_content, ()])]))
    assert_node(doctree[0], addnodes.index,
                entries=[('pair', 'command line option; -l', 'cmdoption-l', '', None)])
    assert (None, '-l') in domain.progoptions
    assert domain.progoptions[(None, '-l')] == ('index', 'cmdoption-l')


def test_multiple_cmdoptions(app):
    text = (".. program:: cmd\n"
            "\n"
            ".. option:: -o directory, --output directory\n")
    domain = app.env.get_domain('std')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "-o"],
                                                    [desc_addname, " directory"],
                                                    [desc_addname, ", "],
                                                    [desc_name, "--output"],
                                                    [desc_addname, " directory"])],
                                  [desc_content, ()])]))
    assert_node(doctree[0], addnodes.index,
                entries=[('pair', 'cmd command line option; -o', 'cmdoption-cmd-o', '', None),
                         ('pair', 'cmd command line option; --output', 'cmdoption-cmd-o', '', None)])
    assert ('cmd', '-o') in domain.progoptions
    assert ('cmd', '--output') in domain.progoptions
    assert domain.progoptions[('cmd', '-o')] == ('index', 'cmdoption-cmd-o')
    assert domain.progoptions[('cmd', '--output')] == ('index', 'cmdoption-cmd-o')


@pytest.mark.sphinx(testroot='productionlist')
def test_productionlist(app, status, warning):
    app.builder.build_all()

    warnings = warning.getvalue().split("\n")
    assert len(warnings) == 2
    assert warnings[-1] == ''
    assert "Dup2.rst:4: WARNING: duplicate token description of Dup, other instance in Dup1" in warnings[0]

    with (app.outdir / 'index.html').open('rb') as f:
        etree = HTMLParser(namespaceHTMLElements=False).parse(f)
    ul = list(etree.iter('ul'))[1]
    cases = []
    for li in list(ul):
        assert len(list(li)) == 1
        p = list(li)[0]
        assert p.tag == 'p'
        text = str(p.text).strip(' :')
        assert len(list(p)) == 1
        a = list(p)[0]
        assert a.tag == 'a'
        link = a.get('href')
        assert len(list(a)) == 1
        code = list(a)[0]
        assert code.tag == 'code'
        assert len(list(code)) == 1
        span = list(code)[0]
        assert span.tag == 'span'
        linkText = span.text.strip()
        cases.append((text, link, linkText))
    assert cases == [
        ('A', 'Bare.html#grammar-token-A', 'A'),
        ('B', 'Bare.html#grammar-token-B', 'B'),
        ('P1:A', 'P1.html#grammar-token-P1-A', 'P1:A'),
        ('P1:B', 'P1.html#grammar-token-P1-B', 'P1:B'),
        ('P2:A', 'P1.html#grammar-token-P1-A', 'P1:A'),
        ('P2:B', 'P2.html#grammar-token-P2-B', 'P2:B'),
        ('Explicit title A, plain', 'Bare.html#grammar-token-A', 'MyTitle'),
        ('Explicit title A, colon', 'Bare.html#grammar-token-A', 'My:Title'),
        ('Explicit title P1:A, plain', 'P1.html#grammar-token-P1-A', 'MyTitle'),
        ('Explicit title P1:A, colon', 'P1.html#grammar-token-P1-A', 'My:Title'),
        ('Tilde A', 'Bare.html#grammar-token-A', 'A'),
        ('Tilde P1:A', 'P1.html#grammar-token-P1-A', 'A'),
        ('Tilde explicit title P1:A', 'P1.html#grammar-token-P1-A', '~MyTitle'),
        ('Tilde, explicit title P1:A', 'P1.html#grammar-token-P1-A', 'MyTitle'),
        ('Dup', 'Dup2.html#grammar-token-Dup', 'Dup'),
        ('FirstLine', 'firstLineRule.html#grammar-token-FirstLine', 'FirstLine'),
        ('SecondLine', 'firstLineRule.html#grammar-token-SecondLine', 'SecondLine'),
    ]

    text = (app.outdir / 'LineContinuation.html').read_text()
    assert "A</strong> ::=  B C D    E F G" in text


def test_productionlist2(app):
    text = (".. productionlist:: P2\n"
            "   A: `:A` `A`\n"
            "   B: `P1:B` `~P1:B`\n")
    doctree = restructuredtext.parse(app, text)
    refnodes = list(doctree.findall(pending_xref))
    assert_node(refnodes[0], pending_xref, reftarget="A")
    assert_node(refnodes[1], pending_xref, reftarget="P2:A")
    assert_node(refnodes[2], pending_xref, reftarget="P1:B")
    assert_node(refnodes[3], pending_xref, reftarget="P1:B")
    assert_node(refnodes[0], [pending_xref, nodes.literal, "A"])
    assert_node(refnodes[1], [pending_xref, nodes.literal, "A"])
    assert_node(refnodes[2], [pending_xref, nodes.literal, "P1:B"])
    assert_node(refnodes[3], [pending_xref, nodes.literal, "B"])


def test_disabled_docref(app):
    text = (":doc:`index`\n"
            ":doc:`!index`\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, ([nodes.paragraph, ([pending_xref, nodes.inline, "index"],
                                             "\n",
                                             [nodes.inline, "index"])],))


def test_labeled_rubric(app):
    text = (".. _label:\n"
            ".. rubric:: blah *blah* blah\n")
    restructuredtext.parse(app, text)

    domain = app.env.get_domain("std")
    assert 'label' in domain.labels
    assert domain.labels['label'] == ('index', 'label', 'blah blah blah')


def test_inline_target(app):
    text = "blah _`inline target` blah\n"
    restructuredtext.parse(app, text)

    domain = app.env.get_domain("std")
    assert 'inline target' in domain.labels
    assert domain.labels['inline target'] == ('index', 'inline-target', 'inline target')
