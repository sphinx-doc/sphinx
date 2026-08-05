"""Test the sphinx.environment.adapters.toctree."""

from __future__ import annotations

from typing import TYPE_CHECKING

import docutils
import pytest
from docutils import nodes
from docutils.nodes import bullet_list, list_item, literal, reference, title

from sphinx import addnodes
from sphinx.addnodes import compact_paragraph, only
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.environment.adapters.toctree import (
    _toctree_copy,
    document_toc,
    global_toctree_for_doc,
)
from sphinx.testing.util import assert_node
from sphinx.util.tags import Tags

from tests.utils import extract_node

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_process_doc(app):
    app.build()
    # tocs
    toctree = app.env.tocs['index']
    assert_node(
        toctree,
        [
            bullet_list,
            (
                [
                    list_item,  # [0]
                    (
                        compact_paragraph,  # [0][0]
                        [
                            bullet_list,  # [0][1]
                            (
                                addnodes.toctree,  # [0][1][0]
                                only,  # [0][1][1]
                                list_item,  # [0][1][2]
                            ),
                        ],
                    ),
                ],
                [
                    list_item,  # [1]
                    (
                        compact_paragraph,  # [1][0]
                        [
                            bullet_list,  # [1][1]
                            (
                                addnodes.toctree,  # [1][1][0]
                                addnodes.toctree,  # [1][1][1]
                            ),
                        ],
                    ),
                ],
                list_item,  # [2]
            ),
        ],
    )

    assert_node(
        extract_node(toctree, 0, 0),
        [compact_paragraph, reference, 'Welcome to Sphinx Tests’s documentation!'],
    )
    assert_node(extract_node(toctree, 0, 0, 0), reference, anchorname='')
    assert_node(
        extract_node(toctree, 0, 1, 0),
        addnodes.toctree,
        caption='Table of Contents',
        glob=False,
        hidden=False,
        titlesonly=False,
        maxdepth=2,
        numbered=999,
        entries=[
            (None, 'foo'),
            (None, 'bar'),
            (None, 'https://sphinx-doc.org/'),
            (None, 'self'),
        ],
        includefiles=['foo', 'bar'],
    )

    # only branch
    assert_node(extract_node(toctree, 0, 1, 1), addnodes.only, expr='html')
    assert_node(
        extract_node(toctree, 0, 1, 1),
        [
            only,
            list_item,
            (
                [compact_paragraph, reference, 'Section for HTML'],
                [bullet_list, addnodes.toctree],
            ),
        ],
    )
    assert_node(
        extract_node(toctree, 0, 1, 1, 0, 0, 0),
        reference,
        anchorname='#section-for-html',
    )
    assert_node(
        extract_node(toctree, 0, 1, 1, 0, 1, 0),
        addnodes.toctree,
        caption=None,
        glob=False,
        hidden=False,
        entries=[(None, 'baz')],
        includefiles=['baz'],
        titlesonly=False,
        maxdepth=-1,
        numbered=0,
    )
    assert_node(
        extract_node(toctree, 0, 1, 2),
        (
            [compact_paragraph, reference, 'subsection'],
            [bullet_list, list_item, compact_paragraph, reference, 'subsubsection'],
        ),
    )

    assert_node(
        extract_node(toctree, 1, 0),
        [
            compact_paragraph,
            reference,
            'Test for combination of ‘globaltoc.html’ and hidden toctree',
        ],
    )
    assert_node(
        extract_node(toctree, 1, 0, 0),
        reference,
        anchorname='#test-for-combination-of-globaltoc-html-and-hidden-toctree',
    )
    assert_node(
        extract_node(toctree, 1, 1, 0),
        addnodes.toctree,
        caption=None,
        entries=[],
        glob=False,
        hidden=False,
        titlesonly=False,
        maxdepth=-1,
        numbered=0,
    )
    assert_node(
        extract_node(toctree, 1, 1, 1),
        addnodes.toctree,
        caption=None,
        glob=False,
        hidden=True,
        titlesonly=False,
        maxdepth=-1,
        numbered=0,
        entries=[
            ('Latest reference', 'https://sphinx-doc.org/latest/'),
            ('Python', 'https://python.org/'),
        ],
    )

    assert_node(
        extract_node(toctree, 2, 0),
        [compact_paragraph, reference, 'Indices and tables'],
    )

    # other collections
    assert app.env.toc_num_entries['index'] == 6
    assert app.env.toctree_includes['index'] == ['foo', 'bar', 'baz']
    assert app.env.files_to_rebuild['foo'] == {'index'}
    assert app.env.files_to_rebuild['bar'] == {'index'}
    assert app.env.files_to_rebuild['baz'] == {'index'}
    assert app.env.glob_toctrees == set()
    assert app.env.numbered_toctrees == {'index'}

    # qux has no section title
    assert len(app.env.tocs['qux']) == 0
    assert_node(app.env.tocs['qux'], nodes.bullet_list)
    assert app.env.toc_num_entries['qux'] == 0
    assert 'qux' not in app.env.toctree_includes


@pytest.mark.sphinx('dummy', testroot='toctree-glob')
def test_glob(app):
    includefiles = [
        'foo',
        'bar/index',
        'bar/bar_1',
        'bar/bar_2',
        'bar/bar_3',
        'baz',
        'qux/index',
    ]

    app.build()

    # tocs
    toctree = app.env.tocs['index']
    assert_node(
        toctree,
        [
            bullet_list,
            list_item,
            (
                compact_paragraph,  # [0][0]
                [
                    bullet_list,
                    (
                        list_item,  # [0][1][0]
                        list_item,  # [0][1][1]
                    ),
                ],
            ),
        ],
    )

    assert_node(
        extract_node(toctree, 0, 0), [compact_paragraph, reference, 'test-toctree-glob']
    )
    assert_node(
        extract_node(toctree, 0, 1, 0),
        [
            list_item,
            (
                [compact_paragraph, reference, 'normal order'],
                [bullet_list, addnodes.toctree],  # [0][1][0][1][0]
            ),
        ],
    )
    assert_node(
        extract_node(toctree, 0, 1, 0, 1, 0),
        addnodes.toctree,
        caption=None,
        glob=True,
        hidden=False,
        titlesonly=False,
        maxdepth=-1,
        numbered=0,
        includefiles=includefiles,
        entries=[
            (None, 'foo'),
            (None, 'bar/index'),
            (None, 'bar/bar_1'),
            (None, 'bar/bar_2'),
            (None, 'bar/bar_3'),
            (None, 'baz'),
            (None, 'qux/index'),
            ('hyperref', 'https://sphinx-doc.org/?q=sphinx'),
        ],
    )
    assert_node(
        extract_node(toctree, 0, 1, 1),
        [
            list_item,
            (
                [compact_paragraph, reference, 'reversed order'],
                [bullet_list, addnodes.toctree],  # [0][1][1][1][0]
            ),
        ],
    )
    assert_node(
        extract_node(toctree, 0, 1, 1, 1, 0),
        addnodes.toctree,
        caption=None,
        glob=True,
        hidden=False,
        titlesonly=False,
        maxdepth=-1,
        numbered=0,
        includefiles=list(reversed(includefiles)),
        entries=[
            (None, 'qux/index'),
            (None, 'baz'),
            (None, 'bar/bar_3'),
            (None, 'bar/bar_2'),
            (None, 'bar/bar_1'),
            (None, 'bar/index'),
            (None, 'foo'),
        ],
    )

    # other collections
    assert app.env.toc_num_entries['index'] == 3
    assert app.env.toctree_includes['index'] == includefiles + list(
        reversed(includefiles)
    )
    for file in includefiles:
        assert 'index' in app.env.files_to_rebuild[file]
    assert 'index' in app.env.glob_toctrees
    assert app.env.numbered_toctrees == set()


@pytest.mark.sphinx('dummy', testroot='toctree-domain-objects')
def test_domain_objects(app):
    app.build()

    assert app.env.toc_num_entries['index'] == 0
    assert app.env.toc_num_entries['domains'] == 9
    assert app.env.toctree_includes['index'] == ['domains', 'document_scoping']
    assert 'index' in app.env.files_to_rebuild['domains']
    assert app.env.glob_toctrees == set()
    assert app.env.numbered_toctrees == {'index'}

    # tocs
    toctree = app.env.tocs['domains']
    assert_node(
        toctree,
        [
            bullet_list,
            list_item,
            (
                compact_paragraph,  # [0][0]
                [
                    bullet_list,  # [0][1]
                    (
                        list_item,  # [0][1][0]
                        [
                            list_item,  # [0][1][1]
                            (
                                compact_paragraph,  # [0][1][1][0]
                                [
                                    bullet_list,  # [0][1][1][1]
                                    (
                                        list_item,  # [0][1][1][1][0]
                                        list_item,
                                        list_item,
                                        list_item,  # [0][1][1][1][3]
                                    ),
                                ],
                            ),
                        ],
                        list_item,
                        list_item,  # [0][1][1]
                    ),
                ],
            ),
        ],
    )

    assert_node(
        extract_node(toctree, 0, 0),
        [compact_paragraph, reference, 'test-domain-objects'],
    )

    assert_node(
        extract_node(toctree, 0, 1, 0),
        [list_item, ([compact_paragraph, reference, literal, 'world()'])],
    )

    assert_node(
        extract_node(toctree, 0, 1, 1, 1, 3),
        [
            list_item,
            ([compact_paragraph, reference, literal, 'HelloWorldPrinter.print()']),
        ],
    )


@pytest.mark.sphinx('dummy', testroot='toctree-domain-objects')
def test_domain_objects_document_scoping(app: SphinxTestApp) -> None:
    app.build()

    # tocs
    toctree = app.env.tocs['document_scoping']
    assert_node(
        toctree,
        [
            bullet_list,
            list_item,
            (
                compact_paragraph,  # [0][0]
                [
                    bullet_list,  # [0][1]
                    (
                        [
                            list_item,  # [0][1][0]
                            compact_paragraph,
                            reference,
                            literal,
                            'ClassLevel1a',
                        ],
                        [
                            list_item,  # [0][1][1]
                            (
                                [
                                    compact_paragraph,  # [0][1][1][0]
                                    reference,
                                    literal,
                                    'ClassLevel1b',
                                ],
                                [
                                    bullet_list,
                                    list_item,  # [0][1][1][1][0]
                                    compact_paragraph,
                                    reference,
                                    literal,
                                    'ClassLevel1b.f()',
                                ],
                            ),
                        ],
                        [
                            list_item,  # [0][1][2]
                            compact_paragraph,
                            reference,
                            literal,
                            'ClassLevel1a.g()',
                        ],
                        [
                            list_item,  # [0][1][3]
                            compact_paragraph,
                            reference,
                            literal,
                            'ClassLevel1b.g()',
                        ],
                        [
                            list_item,  # [0][1][4]
                            (
                                [
                                    compact_paragraph,  # [0][1][4][0]
                                    reference,
                                    'Level 2',
                                ],
                                [
                                    bullet_list,  # [0][1][4][1]
                                    (
                                        [
                                            list_item,  # [0][1][4][1][0]
                                            compact_paragraph,
                                            reference,
                                            literal,
                                            'ClassLevel2a',
                                        ],
                                        [
                                            list_item,  # [0][1][4][1][1]
                                            (
                                                [
                                                    compact_paragraph,  # [0][1][4][1][1][0]
                                                    reference,
                                                    literal,
                                                    'ClassLevel2b',
                                                ],
                                                [
                                                    bullet_list,
                                                    list_item,  # [0][1][4][1][1][1][0]
                                                    compact_paragraph,
                                                    reference,
                                                    literal,
                                                    'ClassLevel2b.f()',
                                                ],
                                            ),
                                        ],
                                        [
                                            list_item,  # [0][1][4][1][2]
                                            compact_paragraph,
                                            reference,
                                            literal,
                                            'ClassLevel2a.g()',
                                        ],
                                        [
                                            list_item,  # [0][1][4][1][3]
                                            compact_paragraph,
                                            reference,
                                            literal,
                                            'ClassLevel2b.g()',
                                        ],
                                    ),
                                ],
                            ),
                        ],
                    ),
                ],
            ),
        ],
    )


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_document_toc(app):
    app.build()
    toctree = document_toc(app.env, 'index', app.tags)

    assert_node(
        toctree,
        [
            bullet_list,
            (
                [
                    list_item,
                    (
                        compact_paragraph,  # [0][0]
                        [
                            bullet_list,
                            (
                                addnodes.toctree,  # [0][1][0]
                                list_item,  # [0][1][1]
                            ),
                        ],
                    ),
                ],
                [
                    list_item,
                    (
                        compact_paragraph,  # [1][0]
                        [bullet_list, (addnodes.toctree, addnodes.toctree)],
                    ),
                ],
                [list_item, compact_paragraph],  # [2][0]
            ),
        ],
    )
    assert_node(
        extract_node(toctree, 0, 0),
        [compact_paragraph, reference, 'Welcome to Sphinx Tests’s documentation!'],
    )
    assert_node(
        extract_node(toctree, 0, 1, 1),
        (
            [compact_paragraph, reference, 'subsection'],
            [bullet_list, list_item, compact_paragraph, reference, 'subsubsection'],
        ),
    )
    assert_node(
        extract_node(toctree, 1, 0),
        [
            compact_paragraph,
            reference,
            'Test for combination of ‘globaltoc.html’ and hidden toctree',
        ],
    )
    assert_node(
        extract_node(toctree, 2, 0),
        [compact_paragraph, reference, 'Indices and tables'],
    )


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_document_toc_only(app):
    app.build()
    StandaloneHTMLBuilder(app, app.env)  # adds format/builder tags
    toctree = document_toc(app.env, 'index', app.tags)

    assert_node(
        toctree,
        [
            bullet_list,
            (
                [
                    list_item,
                    (
                        compact_paragraph,  # [0][0]
                        [
                            bullet_list,
                            (
                                addnodes.toctree,  # [0][1][0]
                                list_item,  # [0][1][1]
                                list_item,  # [0][1][2]
                            ),
                        ],
                    ),
                ],
                [
                    list_item,
                    (
                        compact_paragraph,  # [1][0]
                        [bullet_list, (addnodes.toctree, addnodes.toctree)],
                    ),
                ],
                [list_item, compact_paragraph],  # [2][0]
            ),
        ],
    )
    assert_node(
        extract_node(toctree, 0, 0),
        [compact_paragraph, reference, 'Welcome to Sphinx Tests’s documentation!'],
    )
    assert_node(
        extract_node(toctree, 0, 1, 1),
        (
            [compact_paragraph, reference, 'Section for HTML'],
            [bullet_list, addnodes.toctree],
        ),
    )
    assert_node(
        extract_node(toctree, 0, 1, 2),
        (
            [compact_paragraph, reference, 'subsection'],
            [bullet_list, list_item, compact_paragraph, reference, 'subsubsection'],
        ),
    )
    assert_node(
        extract_node(toctree, 1, 0),
        [
            compact_paragraph,
            reference,
            'Test for combination of ‘globaltoc.html’ and hidden toctree',
        ],
    )
    assert_node(
        extract_node(toctree, 2, 0),
        [compact_paragraph, reference, 'Indices and tables'],
    )


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_document_toc_tocdepth(app):
    app.build()
    toctree = document_toc(app.env, 'tocdepth', app.tags)

    assert_node(
        toctree,
        [
            bullet_list,
            list_item,
            (
                compact_paragraph,  # [0][0]
                bullet_list,  # [0][1]
            ),
        ],
    )
    assert_node(extract_node(toctree, 0, 0), [compact_paragraph, reference, 'level 1'])
    assert_node(
        extract_node(toctree, 0, 1),
        [bullet_list, list_item, compact_paragraph, reference, 'level 2'],
    )


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_global_toctree_for_doc(app):
    app.build()
    toctree = global_toctree_for_doc(
        app.env, 'index', app.builder, tags=app.tags, collapse=False
    )
    assert_node(
        toctree,
        [
            compact_paragraph,
            ([title, 'Table of Contents'], bullet_list, bullet_list, bullet_list),
        ],
    )

    assert_node(
        toctree[1],
        (
            [list_item, ([compact_paragraph, reference, 'foo'], bullet_list)],
            [list_item, compact_paragraph, reference, 'bar'],
            [list_item, compact_paragraph, reference, 'https://sphinx-doc.org/'],
            [
                list_item,
                compact_paragraph,
                reference,
                'Welcome to Sphinx Tests’s documentation!',
            ],
        ),
    )
    assert_node(
        extract_node(toctree, 1, 0, 1),
        (
            [list_item, compact_paragraph, reference, 'quux'],
            [list_item, compact_paragraph, reference, 'foo.1'],
            [list_item, compact_paragraph, reference, 'foo.2'],
        ),
    )

    assert_node(
        extract_node(toctree, 1, 0, 0, 0), reference, refuri='foo', secnumber=[1]
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 0, 0, 0),
        reference,
        refuri='quux',
        secnumber=[1, 1],
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 1, 0, 0),
        reference,
        refuri='foo#foo-1',
        secnumber=[1, 2],
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 2, 0, 0),
        reference,
        refuri='foo#foo-2',
        secnumber=[1, 3],
    )
    assert_node(
        extract_node(toctree, 1, 1, 0, 0), reference, refuri='bar', secnumber=[2]
    )
    assert_node(
        extract_node(toctree, 1, 2, 0, 0), reference, refuri='https://sphinx-doc.org/'
    )
    assert_node(extract_node(toctree, 1, 3, 0, 0), reference, refuri='')

    assert_node(
        toctree[2], [bullet_list, list_item, compact_paragraph, reference, 'baz']
    )
    assert_node(
        toctree[3],
        (
            [list_item, compact_paragraph, reference, 'Latest reference'],
            [list_item, compact_paragraph, reference, 'Python'],
        ),
    )
    assert_node(
        extract_node(toctree, 3, 0, 0, 0),
        reference,
        refuri='https://sphinx-doc.org/latest/',
    )
    assert_node(
        extract_node(toctree, 3, 1, 0, 0), reference, refuri='https://python.org/'
    )


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_global_toctree_for_doc_collapse(app):
    app.build()
    toctree = global_toctree_for_doc(
        app.env, 'index', app.builder, tags=app.tags, collapse=True
    )
    assert_node(
        toctree,
        [
            compact_paragraph,
            ([title, 'Table of Contents'], bullet_list, bullet_list, bullet_list),
        ],
    )

    assert_node(
        toctree[1],
        (
            [list_item, compact_paragraph, reference, 'foo'],
            [list_item, compact_paragraph, reference, 'bar'],
            [list_item, compact_paragraph, reference, 'https://sphinx-doc.org/'],
            [
                list_item,
                compact_paragraph,
                reference,
                'Welcome to Sphinx Tests’s documentation!',
            ],
        ),
    )
    assert_node(
        extract_node(toctree, 1, 0, 0, 0), reference, refuri='foo', secnumber=[1]
    )
    assert_node(
        extract_node(toctree, 1, 1, 0, 0), reference, refuri='bar', secnumber=[2]
    )
    assert_node(
        extract_node(toctree, 1, 2, 0, 0), reference, refuri='https://sphinx-doc.org/'
    )
    assert_node(extract_node(toctree, 1, 3, 0, 0), reference, refuri='')

    assert_node(
        toctree[2], [bullet_list, list_item, compact_paragraph, reference, 'baz']
    )
    assert_node(
        toctree[3],
        (
            [list_item, compact_paragraph, reference, 'Latest reference'],
            [list_item, compact_paragraph, reference, 'Python'],
        ),
    )
    assert_node(
        extract_node(toctree, 3, 0, 0, 0),
        reference,
        refuri='https://sphinx-doc.org/latest/',
    )
    assert_node(
        extract_node(toctree, 3, 1, 0, 0), reference, refuri='https://python.org/'
    )


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_global_toctree_for_doc_maxdepth(app):
    app.build()
    toctree = global_toctree_for_doc(
        app.env, 'index', app.builder, tags=app.tags, collapse=False, maxdepth=3
    )
    assert_node(
        toctree,
        [
            compact_paragraph,
            (
                [title, 'Table of Contents'],
                bullet_list,
                bullet_list,
                bullet_list,
            ),
        ],
    )

    assert_node(
        toctree[1],
        (
            [
                list_item,
                (
                    [compact_paragraph, reference, 'foo'],
                    bullet_list,
                ),
            ],
            [list_item, compact_paragraph, reference, 'bar'],
            [list_item, compact_paragraph, reference, 'https://sphinx-doc.org/'],
            [
                list_item,
                compact_paragraph,
                reference,
                'Welcome to Sphinx Tests’s documentation!',
            ],
        ),
    )
    assert_node(
        extract_node(toctree, 1, 0, 1),
        (
            [list_item, compact_paragraph, reference, 'quux'],
            [
                list_item,
                (
                    [compact_paragraph, reference, 'foo.1'],
                    bullet_list,
                ),
            ],
            [list_item, compact_paragraph, reference, 'foo.2'],
        ),
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 1, 1),
        [bullet_list, list_item, compact_paragraph, reference, 'foo.1-1'],
    )

    assert_node(
        extract_node(toctree, 1, 0, 0, 0), reference, refuri='foo', secnumber=[1]
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 0, 0, 0),
        reference,
        refuri='quux',
        secnumber=[1, 1],
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 1, 0, 0),
        reference,
        refuri='foo#foo-1',
        secnumber=[1, 2],
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 1, 1, 0, 0, 0),
        reference,
        refuri='foo#foo-1-1',
        secnumber=[1, 2, 1],
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 2, 0, 0),
        reference,
        refuri='foo#foo-2',
        secnumber=[1, 3],
    )
    assert_node(
        extract_node(toctree, 1, 1, 0, 0), reference, refuri='bar', secnumber=[2]
    )
    assert_node(
        extract_node(toctree, 1, 2, 0, 0), reference, refuri='https://sphinx-doc.org/'
    )
    assert_node(extract_node(toctree, 1, 3, 0, 0), reference, refuri='')

    assert_node(
        toctree[2], [bullet_list, list_item, compact_paragraph, reference, 'baz']
    )
    assert_node(
        toctree[3],
        (
            [list_item, compact_paragraph, reference, 'Latest reference'],
            [list_item, compact_paragraph, reference, 'Python'],
        ),
    )
    assert_node(
        extract_node(toctree, 3, 0, 0, 0),
        reference,
        refuri='https://sphinx-doc.org/latest/',
    )
    assert_node(
        extract_node(toctree, 3, 1, 0, 0), reference, refuri='https://python.org/'
    )


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_global_toctree_for_doc_includehidden(app):
    app.build()
    toctree = global_toctree_for_doc(
        app.env,
        'index',
        app.builder,
        tags=app.tags,
        collapse=False,
        includehidden=False,
    )
    assert_node(
        toctree,
        [
            compact_paragraph,
            (
                [title, 'Table of Contents'],
                bullet_list,
                bullet_list,
            ),
        ],
    )

    assert_node(
        toctree[1],
        (
            [
                list_item,
                (
                    [compact_paragraph, reference, 'foo'],
                    bullet_list,
                ),
            ],
            [list_item, compact_paragraph, reference, 'bar'],
            [list_item, compact_paragraph, reference, 'https://sphinx-doc.org/'],
            [
                list_item,
                compact_paragraph,
                reference,
                'Welcome to Sphinx Tests’s documentation!',
            ],
        ),
    )
    assert_node(
        extract_node(toctree, 1, 0, 1),
        (
            [list_item, compact_paragraph, reference, 'quux'],
            [list_item, compact_paragraph, reference, 'foo.1'],
            [list_item, compact_paragraph, reference, 'foo.2'],
        ),
    )

    assert_node(
        extract_node(toctree, 1, 0, 0, 0), reference, refuri='foo', secnumber=[1]
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 0, 0, 0),
        reference,
        refuri='quux',
        secnumber=[1, 1],
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 1, 0, 0),
        reference,
        refuri='foo#foo-1',
        secnumber=[1, 2],
    )
    assert_node(
        extract_node(toctree, 1, 0, 1, 2, 0, 0),
        reference,
        refuri='foo#foo-2',
        secnumber=[1, 3],
    )
    assert_node(
        extract_node(toctree, 1, 1, 0, 0), reference, refuri='bar', secnumber=[2]
    )
    assert_node(
        extract_node(toctree, 1, 2, 0, 0), reference, refuri='https://sphinx-doc.org/'
    )

    assert_node(
        toctree[2], [bullet_list, list_item, compact_paragraph, reference, 'baz']
    )


@pytest.mark.sphinx('xml', testroot='toctree-index')
def test_toctree_index(app):
    app.build()
    toctree = app.env.tocs['index']
    assert_node(
        toctree,
        [
            bullet_list,
            ([
                list_item,
                (
                    compact_paragraph,  # [0][0]
                    [
                        bullet_list,
                        (
                            addnodes.toctree,  # [0][1][0]
                            addnodes.toctree,  # [0][1][1]
                        ),
                    ],
                ),
            ]),
        ],
    )
    assert_node(
        extract_node(toctree, 0, 1, 1),
        addnodes.toctree,
        caption='Indices',
        glob=False,
        hidden=False,
        titlesonly=False,
        maxdepth=-1,
        numbered=0,
        entries=[(None, 'genindex'), (None, 'modindex'), (None, 'search')],
    )


@pytest.mark.sphinx('dummy', testroot='toctree-only')
def test_toctree_only(app):
    # regression test for https://github.com/sphinx-doc/sphinx/issues/13022
    # we mainly care that this doesn't fail

    if docutils.__version_info__[:2] >= (0, 22):
        true = '1'
    else:
        true = 'True'
    expected_pformat = f"""\
<bullet_list>
  <list_item>
    <compact_paragraph>
      <reference anchorname="" internal="{true}" refuri="#">
        test-toctree-only
    <bullet_list>
      <list_item>
        <compact_paragraph skip_section_number="{true}">
          <reference anchorname="#test_toctree_only1" internal="{true}" refuri="#test_toctree_only1">
            <literal>
              test_toctree_only1
      <list_item>
        <compact_paragraph skip_section_number="{true}">
          <reference anchorname="#test_toctree_only2" internal="{true}" refuri="#test_toctree_only2">
            <literal>
              test_toctree_only2
      <list_item>
        <compact_paragraph skip_section_number="{true}">
          <reference anchorname="#id0" internal="{true}" refuri="#id0">
            <literal>
              test_toctree_only2
"""
    app.build()
    toc = document_toc(app.env, 'index', app.tags)
    assert toc.pformat('  ') == expected_pformat


def test_toctree_copy_only():
    # regression test for https://github.com/sphinx-doc/sphinx/issues/13022
    # ensure ``_toctree_copy()`` properly filters out ``only`` nodes,
    # including nested nodes.
    node = nodes.literal('lobster!', 'lobster!')
    node = nodes.reference('', '', node, anchorname='', internal=True, refuri='index')
    node = addnodes.only('', node, expr='lobster')
    node = addnodes.compact_paragraph('', '', node, skip_section_number=True)
    node = nodes.list_item('', node)
    node = addnodes.only('', node, expr='not spam')
    node = addnodes.only('', node, expr='lobster')
    node = addnodes.only('', node, expr='not ham')
    node = nodes.bullet_list('', node)
    # this is a tree of the shape:
    # <bullet_list>
    #   <only expr="not ham">
    #     <only expr="lobster">
    #       <only expr="not spam">
    #         <list_item>
    #           <compact_paragraph skip_section_number="True">
    #             <only expr="lobster">
    #               <reference anchorname="" internal="True" refuri="index">
    #                 <literal>
    #                   lobster!

    tags = Tags({'lobster'})
    toc = _toctree_copy(node, 2, 0, False, tags)
    # the filtered ToC should look like:
    # <bullet_list>
    #   <list_item>
    #     <compact_paragraph skip_section_number="True">
    #       <reference anchorname="" internal="True" refuri="index">
    #         <literal>
    #           lobster!

    # no only nodes should remain
    assert list(toc.findall(addnodes.only)) == []

    # the tree is preserved
    assert isinstance(toc, nodes.bullet_list)
    assert isinstance(toc[0], nodes.list_item)
    assert isinstance(extract_node(toc, 0, 0), addnodes.compact_paragraph)
    assert isinstance(extract_node(toc, 0, 0, 0), nodes.reference)
    assert isinstance(extract_node(toc, 0, 0, 0, 0), nodes.literal)
    assert extract_node(toc, 0, 0, 0, 0, 0) == nodes.Text('lobster!')
