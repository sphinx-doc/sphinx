"""Test the sphinx.environment.adapters.toctree."""

from __future__ import annotations

from typing import TYPE_CHECKING

import docutils
import pytest
from docutils import nodes
from docutils.nodes import Element, bullet_list, list_item, literal, reference, title

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

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_process_doc(app: SphinxTestApp) -> None:
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

    toctree_0 = toctree[0]
    assert isinstance(toctree_0, Element)
    toctree_0_0 = toctree_0[0]
    assert isinstance(toctree_0_0, Element)
    assert_node(
        toctree_0_0,
        [compact_paragraph, reference, "Welcome to Sphinx Tests's documentation!"],
    )
    assert_node(toctree_0_0[0], reference, anchorname='')

    toctree_0_1 = toctree_0[1]
    assert isinstance(toctree_0_1, Element)
    assert_node(
        toctree_0_1[0],
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
    toctree_0_1_1 = toctree_0_1[1]
    assert isinstance(toctree_0_1_1, Element)
    assert_node(toctree_0_1_1, addnodes.only, expr='html')
    assert_node(
        toctree_0_1_1,
        [
            only,
            list_item,
            (
                [compact_paragraph, reference, 'Section for HTML'],
                [bullet_list, addnodes.toctree],
            ),
        ],
    )
    toctree_0_1_1_0 = toctree_0_1_1[0]
    assert isinstance(toctree_0_1_1_0, Element)
    toctree_0_1_1_0_0 = toctree_0_1_1_0[0]
    assert isinstance(toctree_0_1_1_0_0, Element)
    assert_node(toctree_0_1_1_0_0[0], reference, anchorname='#section-for-html')
    toctree_0_1_1_0_1 = toctree_0_1_1_0[1]
    assert isinstance(toctree_0_1_1_0_1, Element)
    assert_node(
        toctree_0_1_1_0_1[0],
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
        toctree_0_1[2],
        (
            [compact_paragraph, reference, 'subsection'],
            [bullet_list, list_item, compact_paragraph, reference, 'subsubsection'],
        ),
    )

    toctree_1 = toctree[1]
    assert isinstance(toctree_1, Element)
    toctree_1_0 = toctree_1[0]
    assert isinstance(toctree_1_0, Element)
    assert_node(
        toctree_1_0,
        [
            compact_paragraph,
            reference,
            "Test for combination of 'globaltoc.html' and hidden toctree",
        ],
    )
    assert_node(
        toctree_1_0[0],
        reference,
        anchorname='#test-for-combination-of-globaltoc-html-and-hidden-toctree',
    )
    toctree_1_1 = toctree_1[1]
    assert isinstance(toctree_1_1, Element)
    assert_node(
        toctree_1_1[0],
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
        toctree_1_1[1],
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

    toctree_2 = toctree[2]
    assert isinstance(toctree_2, Element)
    assert_node(toctree_2[0], [compact_paragraph, reference, 'Indices and tables'])

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
def test_glob(app: SphinxTestApp) -> None:
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

    toctree_0 = toctree[0]
    assert isinstance(toctree_0, Element)
    assert_node(toctree_0[0], [compact_paragraph, reference, 'test-toctree-glob'])

    toctree_0_1 = toctree_0[1]
    assert isinstance(toctree_0_1, Element)
    toctree_0_1_0 = toctree_0_1[0]
    assert isinstance(toctree_0_1_0, Element)
    assert_node(
        toctree_0_1_0,
        [
            list_item,
            (
                [compact_paragraph, reference, 'normal order'],
                [bullet_list, addnodes.toctree],  # [0][1][0][1][0]
            ),
        ],
    )
    toctree_0_1_0_1 = toctree_0_1_0[1]
    assert isinstance(toctree_0_1_0_1, Element)
    assert_node(
        toctree_0_1_0_1[0],
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
            ('hyperref', 'https://sphinx-doc.org/?q= sphinx'),
        ],
    )
    toctree_0_1_1 = toctree_0_1[1]
    assert isinstance(toctree_0_1_1, Element)
    assert_node(
        toctree_0_1_1,
        [
            list_item,
            (
                [compact_paragraph, reference, 'reversed order'],
                [bullet_list, addnodes.toctree],  # [0][1][1][1][0]
            ),
        ],
    )
    toctree_0_1_1_1 = toctree_0_1_1[1]
    assert isinstance(toctree_0_1_1_1, Element)
    assert_node(
        toctree_0_1_1_1[0],
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
def test_domain_objects(app: SphinxTestApp) -> None:
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

    toctree_0 = toctree[0]
    assert isinstance(toctree_0, Element)
    assert_node(toctree_0[0], [compact_paragraph, reference, 'test-domain-objects'])

    toctree_0_1 = toctree_0[1]
    assert isinstance(toctree_0_1, Element)
    assert_node(
        toctree_0_1[0],
        [list_item, ([compact_paragraph, reference, literal, 'world()'])],
    )

    toctree_0_1_1 = toctree_0_1[1]
    assert isinstance(toctree_0_1_1, Element)
    toctree_0_1_1_1 = toctree_0_1_1[1]
    assert isinstance(toctree_0_1_1_1, Element)
    assert_node(
        toctree_0_1_1_1[3],
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
def test_document_toc(app: SphinxTestApp) -> None:
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
    item0 = toctree[0]
    assert isinstance(item0, Element)
    assert_node(
        item0[0],
        [compact_paragraph, reference, "Welcome to Sphinx Tests's documentation!"],
    )
    item01 = item0[1]
    assert isinstance(item01, Element)
    assert_node(
        item01[1],
        (
            [compact_paragraph, reference, 'subsection'],
            [bullet_list, list_item, compact_paragraph, reference, 'subsubsection'],
        ),
    )
    item1 = toctree[1]
    assert isinstance(item1, Element)
    assert_node(
        item1[0],
        [
            compact_paragraph,
            reference,
            "Test for combination of 'globaltoc.html' and hidden toctree",
        ],
    )
    item2 = toctree[2]
    assert isinstance(item2, Element)
    assert_node(item2[0], [compact_paragraph, reference, 'Indices and tables'])


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_document_toc_only(app: SphinxTestApp) -> None:
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
    item0_only = toctree[0]
    assert isinstance(item0_only, Element)
    assert_node(
        item0_only[0],
        [compact_paragraph, reference, "Welcome to Sphinx Tests's documentation!"],
    )
    item01_only = item0_only[1]
    assert isinstance(item01_only, Element)
    assert_node(
        item01_only[1],
        (
            [compact_paragraph, reference, 'Section for HTML'],
            [bullet_list, addnodes.toctree],
        ),
    )
    assert_node(
        item01_only[2],
        (
            [compact_paragraph, reference, 'subsection'],
            [bullet_list, list_item, compact_paragraph, reference, 'subsubsection'],
        ),
    )
    item1_only = toctree[1]
    assert isinstance(item1_only, Element)
    assert_node(
        item1_only[0],
        [
            compact_paragraph,
            reference,
            "Test for combination of 'globaltoc.html' and hidden toctree",
        ],
    )
    item2_only = toctree[2]
    assert isinstance(item2_only, Element)
    assert_node(item2_only[0], [compact_paragraph, reference, 'Indices and tables'])


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_document_toc_tocdepth(app: SphinxTestApp) -> None:
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
    item0_tocdepth = toctree[0]
    assert isinstance(item0_tocdepth, Element)
    assert_node(item0_tocdepth[0], [compact_paragraph, reference, 'level 1'])
    assert_node(
        item0_tocdepth[1],
        [bullet_list, list_item, compact_paragraph, reference, 'level 2'],
    )


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_global_toctree_for_doc(app: SphinxTestApp) -> None:
    app.build()
    toctree = global_toctree_for_doc(
        app.env, 'index', app.builder, tags=app.tags, collapse=False
    )
    assert toctree is not None
    assert_node(
        toctree,
        [
            compact_paragraph,
            ([title, 'Table of Contents'], bullet_list, bullet_list, bullet_list),
        ],
    )

    item1 = toctree[1]
    assert isinstance(item1, Element)
    assert_node(
        item1,
        (
            [list_item, ([compact_paragraph, reference, 'foo'], bullet_list)],
            [list_item, compact_paragraph, reference, 'bar'],
            [list_item, compact_paragraph, reference, 'https://sphinx-doc.org/'],
            [
                list_item,
                compact_paragraph,
                reference,
                "Welcome to Sphinx Tests's documentation!",
            ],
        ),
    )
    item10 = item1[0]
    assert isinstance(item10, Element)
    item101 = item10[1]
    assert isinstance(item101, Element)
    assert_node(
        item101,
        (
            [list_item, compact_paragraph, reference, 'quux'],
            [list_item, compact_paragraph, reference, 'foo.1'],
            [list_item, compact_paragraph, reference, 'foo.2'],
        ),
    )

    item100 = item10[0]
    assert isinstance(item100, Element)
    assert_node(item100[0], reference, refuri='foo', secnumber=[1])
    item1010 = item101[0]
    assert isinstance(item1010, Element)
    item1010_0 = item1010[0]
    assert isinstance(item1010_0, Element)
    item1010_00 = item1010_0[0]
    assert isinstance(item1010_00, Element)
    assert_node(item1010_00[0], reference, refuri='quux', secnumber=[1, 1])
    item1011 = item101[1]
    assert isinstance(item1011, Element)
    item1011_0 = item1011[0]
    assert isinstance(item1011_0, Element)
    assert_node(item1011_0[0], reference, refuri='foo#foo-1', secnumber=[1, 2])
    item1012 = item101[2]
    assert isinstance(item1012, Element)
    item1012_0 = item1012[0]
    assert isinstance(item1012_0, Element)
    assert_node(item1012_0[0], reference, refuri='foo#foo-2', secnumber=[1, 3])
    item11 = item1[1]
    assert isinstance(item11, Element)
    item11_0 = item11[0]
    assert isinstance(item11_0, Element)
    assert_node(item11_0[0], reference, refuri='bar', secnumber=[2])
    item12 = item1[2]
    assert isinstance(item12, Element)
    item12_0 = item12[0]
    assert isinstance(item12_0, Element)
    assert_node(item12_0[0], reference, refuri='https://sphinx-doc.org/')
    item13 = item1[3]
    assert isinstance(item13, Element)
    item13_0 = item13[0]
    assert isinstance(item13_0, Element)
    assert_node(item13_0[0], reference, refuri='')

    item2 = toctree[2]
    assert isinstance(item2, Element)
    assert_node(item2, [bullet_list, list_item, compact_paragraph, reference, 'baz'])
    item3 = toctree[3]
    assert isinstance(item3, Element)
    assert_node(
        item3,
        (
            [list_item, compact_paragraph, reference, 'Latest reference'],
            [list_item, compact_paragraph, reference, 'Python'],
        ),
    )
    item30 = item3[0]
    assert isinstance(item30, Element)
    item30_0 = item30[0]
    assert isinstance(item30_0, Element)
    assert_node(item30_0[0], reference, refuri='https://sphinx-doc.org/latest/')
    item31 = item3[1]
    assert isinstance(item31, Element)
    item31_0 = item31[0]
    assert isinstance(item31_0, Element)
    assert_node(item31_0[0], reference, refuri='https://python.org/')


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_global_toctree_for_doc_collapse(app: SphinxTestApp) -> None:
    app.build()
    toctree = global_toctree_for_doc(
        app.env, 'index', app.builder, tags=app.tags, collapse=True
    )
    assert toctree is not None
    assert_node(
        toctree,
        [
            compact_paragraph,
            ([title, 'Table of Contents'], bullet_list, bullet_list, bullet_list),
        ],
    )

    item1_collapse = toctree[1]
    assert isinstance(item1_collapse, Element)
    assert_node(
        item1_collapse,
        (
            [list_item, compact_paragraph, reference, 'foo'],
            [list_item, compact_paragraph, reference, 'bar'],
            [list_item, compact_paragraph, reference, 'https://sphinx-doc.org/'],
            [
                list_item,
                compact_paragraph,
                reference,
                "Welcome to Sphinx Tests's documentation!",
            ],
        ),
    )
    item10_collapse = item1_collapse[0]
    assert isinstance(item10_collapse, Element)
    item10_collapse_0 = item10_collapse[0]
    assert isinstance(item10_collapse_0, Element)
    assert_node(item10_collapse_0[0], reference, refuri='foo', secnumber=[1])
    item11_collapse = item1_collapse[1]
    assert isinstance(item11_collapse, Element)
    item11_collapse_0 = item11_collapse[0]
    assert isinstance(item11_collapse_0, Element)
    assert_node(item11_collapse_0[0], reference, refuri='bar', secnumber=[2])
    item12_collapse = item1_collapse[2]
    assert isinstance(item12_collapse, Element)
    item12_collapse_0 = item12_collapse[0]
    assert isinstance(item12_collapse_0, Element)
    assert_node(item12_collapse_0[0], reference, refuri='https://sphinx-doc.org/')
    item13_collapse = item1_collapse[3]
    assert isinstance(item13_collapse, Element)
    item13_collapse_0 = item13_collapse[0]
    assert isinstance(item13_collapse_0, Element)
    assert_node(item13_collapse_0[0], reference, refuri='')

    item2_collapse = toctree[2]
    assert isinstance(item2_collapse, Element)
    assert_node(
        item2_collapse, [bullet_list, list_item, compact_paragraph, reference, 'baz']
    )
    item3_collapse = toctree[3]
    assert isinstance(item3_collapse, Element)
    assert_node(
        item3_collapse,
        (
            [list_item, compact_paragraph, reference, 'Latest reference'],
            [list_item, compact_paragraph, reference, 'Python'],
        ),
    )
    item30_collapse = item3_collapse[0]
    assert isinstance(item30_collapse, Element)
    item30_collapse_0 = item30_collapse[0]
    assert isinstance(item30_collapse_0, Element)
    assert_node(
        item30_collapse_0[0], reference, refuri='https://sphinx-doc.org/latest/'
    )
    item31_collapse = item3_collapse[1]
    assert isinstance(item31_collapse, Element)
    item31_collapse_0 = item31_collapse[0]
    assert isinstance(item31_collapse_0, Element)
    assert_node(item31_collapse_0[0], reference, refuri='https://python.org/')


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_global_toctree_for_doc_maxdepth(app: SphinxTestApp) -> None:
    app.build()
    toctree = global_toctree_for_doc(
        app.env, 'index', app.builder, tags=app.tags, collapse=False, maxdepth=3
    )
    assert toctree is not None
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

    item1_maxdepth = toctree[1]
    assert isinstance(item1_maxdepth, Element)
    assert_node(
        item1_maxdepth,
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
                "Welcome to Sphinx Tests's documentation!",
            ],
        ),
    )
    item10_maxdepth = item1_maxdepth[0]
    assert isinstance(item10_maxdepth, Element)
    item101_maxdepth = item10_maxdepth[1]
    assert isinstance(item101_maxdepth, Element)
    assert_node(
        item101_maxdepth,
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
    item1011_maxdepth = item101_maxdepth[1]
    assert isinstance(item1011_maxdepth, Element)
    item10111_maxdepth = item1011_maxdepth[1]
    assert isinstance(item10111_maxdepth, Element)
    assert_node(
        item10111_maxdepth,
        [bullet_list, list_item, compact_paragraph, reference, 'foo.1-1'],
    )

    item100_maxdepth = item10_maxdepth[0]
    assert isinstance(item100_maxdepth, Element)
    assert_node(item100_maxdepth[0], reference, refuri='foo', secnumber=[1])
    item1010_maxdepth = item101_maxdepth[0]
    assert isinstance(item1010_maxdepth, Element)
    item1010_maxdepth_0 = item1010_maxdepth[0]
    assert isinstance(item1010_maxdepth_0, Element)
    item1010_maxdepth_00 = item1010_maxdepth_0[0]
    assert isinstance(item1010_maxdepth_00, Element)
    assert_node(item1010_maxdepth_00[0], reference, refuri='quux', secnumber=[1, 1])
    item10110_maxdepth = item1011_maxdepth[0]
    assert isinstance(item10110_maxdepth, Element)
    assert_node(item10110_maxdepth[0], reference, refuri='foo#foo-1', secnumber=[1, 2])
    item101110_maxdepth = item10111_maxdepth[0]
    assert isinstance(item101110_maxdepth, Element)
    item101110_maxdepth_0 = item101110_maxdepth[0]
    assert isinstance(item101110_maxdepth_0, Element)
    item101110_maxdepth_00 = item101110_maxdepth_0[0]
    assert isinstance(item101110_maxdepth_00, Element)
    assert_node(
        item101110_maxdepth_00[0],
        reference,
        refuri='foo#foo-1-1',
        secnumber=[1, 2, 1],
    )
    item1012_maxdepth = item101_maxdepth[2]
    assert isinstance(item1012_maxdepth, Element)
    item1012_maxdepth_0 = item1012_maxdepth[0]
    assert isinstance(item1012_maxdepth_0, Element)
    assert_node(item1012_maxdepth_0[0], reference, refuri='foo#foo-2', secnumber=[1, 3])
    item11_maxdepth = item1_maxdepth[1]
    assert isinstance(item11_maxdepth, Element)
    item11_maxdepth_0 = item11_maxdepth[0]
    assert isinstance(item11_maxdepth_0, Element)
    assert_node(item11_maxdepth_0[0], reference, refuri='bar', secnumber=[2])
    item12_maxdepth = item1_maxdepth[2]
    assert isinstance(item12_maxdepth, Element)
    item12_maxdepth_0 = item12_maxdepth[0]
    assert isinstance(item12_maxdepth_0, Element)
    assert_node(item12_maxdepth_0[0], reference, refuri='https://sphinx-doc.org/')
    item13_maxdepth = item1_maxdepth[3]
    assert isinstance(item13_maxdepth, Element)
    item13_maxdepth_0 = item13_maxdepth[0]
    assert isinstance(item13_maxdepth_0, Element)
    assert_node(item13_maxdepth_0[0], reference, refuri='')

    item2_maxdepth = toctree[2]
    assert isinstance(item2_maxdepth, Element)
    assert_node(
        item2_maxdepth, [bullet_list, list_item, compact_paragraph, reference, 'baz']
    )
    item3_maxdepth = toctree[3]
    assert isinstance(item3_maxdepth, Element)
    assert_node(
        item3_maxdepth,
        (
            [list_item, compact_paragraph, reference, 'Latest reference'],
            [list_item, compact_paragraph, reference, 'Python'],
        ),
    )
    item30_maxdepth = item3_maxdepth[0]
    assert isinstance(item30_maxdepth, Element)
    item30_maxdepth_0 = item30_maxdepth[0]
    assert isinstance(item30_maxdepth_0, Element)
    assert_node(
        item30_maxdepth_0[0], reference, refuri='https://sphinx-doc.org/latest/'
    )
    item31_maxdepth = item3_maxdepth[1]
    assert isinstance(item31_maxdepth, Element)
    item31_maxdepth_0 = item31_maxdepth[0]
    assert isinstance(item31_maxdepth_0, Element)
    assert_node(item31_maxdepth_0[0], reference, refuri='https://python.org/')


@pytest.mark.sphinx('xml', testroot='toctree')
@pytest.mark.test_params(shared_result='test_environment_toctree_basic')
def test_global_toctree_for_doc_includehidden(app: SphinxTestApp) -> None:
    app.build()
    toctree = global_toctree_for_doc(
        app.env,
        'index',
        app.builder,
        tags=app.tags,
        collapse=False,
        includehidden=False,
    )
    assert toctree is not None
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

    item1_includehidden = toctree[1]
    assert isinstance(item1_includehidden, Element)
    assert_node(
        item1_includehidden,
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
                "Welcome to Sphinx Tests's documentation!",
            ],
        ),
    )
    item10_includehidden = item1_includehidden[0]
    assert isinstance(item10_includehidden, Element)
    item101_includehidden = item10_includehidden[1]
    assert isinstance(item101_includehidden, Element)
    assert_node(
        item101_includehidden,
        (
            [list_item, compact_paragraph, reference, 'quux'],
            [list_item, compact_paragraph, reference, 'foo.1'],
            [list_item, compact_paragraph, reference, 'foo.2'],
        ),
    )

    item100_includehidden = item10_includehidden[0]
    assert isinstance(item100_includehidden, Element)
    assert_node(item100_includehidden[0], reference, refuri='foo', secnumber=[1])
    item1010_includehidden = item101_includehidden[0]
    assert isinstance(item1010_includehidden, Element)
    item1010_includehidden_0 = item1010_includehidden[0]
    assert isinstance(item1010_includehidden_0, Element)
    item1010_includehidden_00 = item1010_includehidden_0[0]
    assert isinstance(item1010_includehidden_00, Element)
    assert_node(
        item1010_includehidden_00[0], reference, refuri='quux', secnumber=[1, 1]
    )
    item1011_includehidden = item101_includehidden[1]
    assert isinstance(item1011_includehidden, Element)
    item1011_includehidden_0 = item1011_includehidden[0]
    assert isinstance(item1011_includehidden_0, Element)
    assert_node(
        item1011_includehidden_0[0], reference, refuri='foo#foo-1', secnumber=[1, 2]
    )
    item1012_includehidden = item101_includehidden[2]
    assert isinstance(item1012_includehidden, Element)
    item1012_includehidden_0 = item1012_includehidden[0]
    assert isinstance(item1012_includehidden_0, Element)
    assert_node(
        item1012_includehidden_0[0], reference, refuri='foo#foo-2', secnumber=[1, 3]
    )
    item11_includehidden = item1_includehidden[1]
    assert isinstance(item11_includehidden, Element)
    item11_includehidden_0 = item11_includehidden[0]
    assert isinstance(item11_includehidden_0, Element)
    assert_node(item11_includehidden_0[0], reference, refuri='bar', secnumber=[2])
    item12_includehidden = item1_includehidden[2]
    assert isinstance(item12_includehidden, Element)
    item12_includehidden_0 = item12_includehidden[0]
    assert isinstance(item12_includehidden_0, Element)
    assert_node(item12_includehidden_0[0], reference, refuri='https://sphinx-doc.org/')

    item2_includehidden = toctree[2]
    assert isinstance(item2_includehidden, Element)
    assert_node(
        item2_includehidden,
        [bullet_list, list_item, compact_paragraph, reference, 'baz'],
    )


@pytest.mark.sphinx('xml', testroot='toctree-index')
def test_toctree_index(app: SphinxTestApp) -> None:
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
    toctree_0 = toctree[0]
    assert isinstance(toctree_0, Element)
    toctree_0_1 = toctree_0[1]
    assert isinstance(toctree_0_1, Element)
    assert_node(
        toctree_0_1[1],
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
def test_toctree_only(app: SphinxTestApp) -> None:
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


def test_toctree_copy_only() -> None:
    # regression test for https://github.com/sphinx-doc/sphinx/issues/13022
    # ensure ``_toctree_copy()`` properly filters out ``only`` nodes,
    # including nested nodes.
    node: Element = nodes.literal('lobster!', 'lobster!')
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
    assert isinstance(toc[0][0], addnodes.compact_paragraph)
    assert isinstance(toc[0][0][0], nodes.reference)
    assert isinstance(toc[0][0][0][0], nodes.literal)
    assert toc[0][0][0][0][0] == nodes.Text('lobster!')
