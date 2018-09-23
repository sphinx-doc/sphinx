# -*- coding: utf-8 -*-
"""
    test_domain_std
    ~~~~~~~~~~~~~~~

    Tests the std domain

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import mock
from docutils import nodes

from sphinx.domains.std import StandardDomain


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
    document.traverse.return_value = []

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
    document.traverse.return_value = []

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
