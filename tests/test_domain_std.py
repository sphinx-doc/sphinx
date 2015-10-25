# -*- coding: utf-8 -*-
"""
    test_domain_std
    ~~~~~~~~~~~~~~~

    Tests the std domain

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

from sphinx.domains.std import StandardDomain
from util import mock


def test_process_doc_handle_figure_caption():
    env = mock.Mock(domaindata={})
    figure_node = nodes.figure(
        '',
        nodes.caption('caption text', 'caption text'),
    )
    document = mock.Mock(
        nametypes={'testname': True},
        nameids={'testname': 'testid'},
        ids={'testid': figure_node},
    )

    domain = StandardDomain(env)
    if 'testname' in domain.data['labels']:
        del domain.data['labels']['testname']
    domain.process_doc(env, 'testdoc', document)
    assert 'testname' in domain.data['labels']
    assert domain.data['labels']['testname'] == (
        'testdoc', 'testid', 'caption text')

def test_process_doc_handle_explicit_ref_default():
    env = mock.Mock(domaindata={})
    env.config.section_titles_as_targets = False
    section_node = nodes.section(
        '',
        nodes.title('title text', 'title text'),
        names="test_section")
    document = mock.Mock(
        nametypes={'test_section': None},
        nameids={'test_section': 'test_section_id'},
        ids={'test_section_id': section_node},
    )

    domain = StandardDomain(env)
    if 'test_section' in domain.data['labels']:
        del domain.data['labels']['test_section']
    domain.process_doc(env, 'testdoc', document)
    assert "test_section" not in domain.data["labels"]

def test_process_doc_handle_explicit_ref_section_titles_as_targets():
    env = mock.Mock(domaindata={})
    env.config.section_titles_as_targets = True
    section_node = nodes.section(
        '',
        nodes.title('title text', 'title text'),
        names="test_section")
    document = mock.Mock(
        nametypes={'test_section': None},
        nameids={'test_section': 'test_section_id'},
        ids={'test_section_id': section_node},
    )

    domain = StandardDomain(env)
    if 'test_section' in domain.data['labels']:
        del domain.data['labels']['test_section']
    domain.process_doc(env, 'testdoc', document)
    assert 'test_section' in domain.data['labels']
    assert domain.data['labels']['test_section'] == (
        'testdoc', 'test_section_id', 'title text')

def test_process_doc_handle_image_parent_figure_caption():
    env = mock.Mock(domaindata={})
    img_node = nodes.image('', alt='image alt')
    figure_node = nodes.figure(
        '',
        nodes.caption('caption text', 'caption text'),
        img_node,
    )
    document = mock.Mock(
        nametypes={'testname': True},
        nameids={'testname': 'testid'},
        ids={'testid': img_node},
    )

    domain = StandardDomain(env)
    if 'testname' in domain.data['labels']:
        del domain.data['labels']['testname']
    domain.process_doc(env, 'testdoc', document)
    assert 'testname' in domain.data['labels']
    assert domain.data['labels']['testname'] == (
        'testdoc', 'testid', 'caption text')


def test_process_doc_handle_table_title():
    env = mock.Mock(domaindata={})
    table_node = nodes.table(
        '',
        nodes.title('title text', 'title text'),
    )
    document = mock.Mock(
        nametypes={'testname': True},
        nameids={'testname': 'testid'},
        ids={'testid': table_node},
    )

    domain = StandardDomain(env)
    if 'testname' in domain.data['labels']:
        del domain.data['labels']['testname']
    domain.process_doc(env, 'testdoc', document)
    assert 'testname' in domain.data['labels']
    assert domain.data['labels']['testname'] == (
        'testdoc', 'testid', 'title text')
