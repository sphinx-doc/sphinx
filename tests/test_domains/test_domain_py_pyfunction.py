"""Tests the Python Domain"""

from __future__ import annotations

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (
    desc,
    desc_addname,
    desc_annotation,
    desc_content,
    desc_name,
    desc_optional,
    desc_parameter,
    desc_parameterlist,
    desc_returns,
    desc_sig_keyword,
    desc_sig_name,
    desc_sig_operator,
    desc_sig_punctuation,
    desc_sig_space,
    desc_signature,
    pending_xref,
)
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

from tests.utils import extract_node

TYPE_CHECKING = False
if TYPE_CHECKING:
    from sphinx.application import Sphinx


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyfunction(app):
    text = (
        '.. py:function:: func1\n'
        '.. py:module:: example\n'
        '.. py:function:: func2\n'
        '   :async:\n'
    )
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [desc_signature, ([desc_name, 'func1'], [desc_parameterlist, ()])],
                    [desc_content, ()],
                ),
            ],
            addnodes.index,
            addnodes.index,
            nodes.target,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'async'], desc_sig_space),
                            ],
                            [desc_addname, 'example.'],
                            [desc_name, 'func2'],
                            [desc_parameterlist, ()],
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
        entries=[('pair', 'built-in function; func1()', 'func1', '', None)],
    )
    assert_node(
        doctree[2],
        addnodes.index,
        entries=[('pair', 'module; example', 'module-example', '', None)],
    )
    assert_node(
        doctree[3],
        addnodes.index,
        entries=[('single', 'func2() (in module example)', 'example.func2', '', None)],
    )

    assert 'func1' in domain.objects
    assert domain.objects['func1'] == ('index', 'func1', 'function', False)
    assert 'example.func2' in domain.objects
    assert domain.objects['example.func2'] == (
        'index',
        'example.func2',
        'function',
        False,
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyfunction_signature(app):
    text = '.. py:function:: hello(name: str) -> str'
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
                            [desc_name, 'hello'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'str'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [desc_sig_name, 'name'],
                [desc_sig_punctuation, ':'],
                desc_sig_space,
                [nodes.inline, pending_xref, 'str'],
            ),
        ],
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyfunction_signature_full(app):
    text = (
        '.. py:function:: hello(a: str, b = 1, *args: str, '
        'c: bool = True, d: tuple = (1, 2), **kwargs: str) -> str'
    )
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
                            [desc_name, 'hello'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'str'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            (
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'a'],
                        [desc_sig_punctuation, ':'],
                        desc_sig_space,
                        [desc_sig_name, pending_xref, 'str'],
                    ),
                ],
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'b'],
                        [desc_sig_operator, '='],
                        [nodes.inline, '1'],
                    ),
                ],
                [
                    desc_parameter,
                    (
                        [desc_sig_operator, '*'],
                        [desc_sig_name, 'args'],
                        [desc_sig_punctuation, ':'],
                        desc_sig_space,
                        [desc_sig_name, pending_xref, 'str'],
                    ),
                ],
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'c'],
                        [desc_sig_punctuation, ':'],
                        desc_sig_space,
                        [desc_sig_name, pending_xref, 'bool'],
                        desc_sig_space,
                        [desc_sig_operator, '='],
                        desc_sig_space,
                        [nodes.inline, 'True'],
                    ),
                ],
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'd'],
                        [desc_sig_punctuation, ':'],
                        desc_sig_space,
                        [desc_sig_name, pending_xref, 'tuple'],
                        desc_sig_space,
                        [desc_sig_operator, '='],
                        desc_sig_space,
                        [nodes.inline, '(1, 2)'],
                    ),
                ],
                [
                    desc_parameter,
                    (
                        [desc_sig_operator, '**'],
                        [desc_sig_name, 'kwargs'],
                        [desc_sig_punctuation, ':'],
                        desc_sig_space,
                        [desc_sig_name, pending_xref, 'str'],
                    ),
                ],
            ),
        ],
    )
    # case: separator at head
    text = '.. py:function:: hello(*, a)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            (
                [desc_parameter, desc_sig_operator, nodes.abbreviation, '*'],
                [desc_parameter, desc_sig_name, 'a'],
            ),
        ],
    )

    # case: separator in the middle
    text = '.. py:function:: hello(a, /, b, *, c)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            (
                [desc_parameter, desc_sig_name, 'a'],
                [desc_parameter, desc_sig_operator, nodes.abbreviation, '/'],
                [desc_parameter, desc_sig_name, 'b'],
                [desc_parameter, desc_sig_operator, nodes.abbreviation, '*'],
                [desc_parameter, desc_sig_name, 'c'],
            ),
        ],
    )

    # case: separator in the middle (2)
    text = '.. py:function:: hello(a, /, *, b)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            (
                [desc_parameter, desc_sig_name, 'a'],
                [desc_parameter, desc_sig_operator, nodes.abbreviation, '/'],
                [desc_parameter, desc_sig_operator, nodes.abbreviation, '*'],
                [desc_parameter, desc_sig_name, 'b'],
            ),
        ],
    )

    # case: separator at tail
    text = '.. py:function:: hello(a, /)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            (
                [desc_parameter, desc_sig_name, 'a'],
                [desc_parameter, desc_sig_operator, nodes.abbreviation, '/'],
            ),
        ],
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyfunction_with_unary_operators(app):
    text = '.. py:function:: menu(egg=+1, bacon=-1, sausage=~1, spam=not spam)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            (
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'egg'],
                        [desc_sig_operator, '='],
                        [nodes.inline, '+1'],
                    ),
                ],
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'bacon'],
                        [desc_sig_operator, '='],
                        [nodes.inline, '-1'],
                    ),
                ],
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'sausage'],
                        [desc_sig_operator, '='],
                        [nodes.inline, '~1'],
                    ),
                ],
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'spam'],
                        [desc_sig_operator, '='],
                        [nodes.inline, 'not spam'],
                    ),
                ],
            ),
        ],
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyfunction_with_binary_operators(app):
    text = '.. py:function:: menu(spam=2**64)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            ([
                desc_parameter,
                (
                    [desc_sig_name, 'spam'],
                    [desc_sig_operator, '='],
                    [nodes.inline, '2**64'],
                ),
            ]),
        ],
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyfunction_with_number_literals(app):
    text = '.. py:function:: hello(age=0x10, height=1_6_0)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            (
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'age'],
                        [desc_sig_operator, '='],
                        [nodes.inline, '0x10'],
                    ),
                ],
                [
                    desc_parameter,
                    (
                        [desc_sig_name, 'height'],
                        [desc_sig_operator, '='],
                        [nodes.inline, '1_6_0'],
                    ),
                ],
            ),
        ],
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyfunction_with_union_type_operator(app):
    text = '.. py:function:: hello(age: int | None)'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            ([
                desc_parameter,
                (
                    [desc_sig_name, 'age'],
                    [desc_sig_punctuation, ':'],
                    desc_sig_space,
                    [
                        desc_sig_name,
                        (
                            [pending_xref, 'int'],
                            desc_sig_space,
                            [desc_sig_punctuation, '|'],
                            desc_sig_space,
                            [pending_xref, 'None'],
                        ),
                    ],
                ),
            ]),
        ],
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_optional_pyfunction_signature(app):
    text = '.. py:function:: compile(source [, filename [, symbol]]) -> ast object'
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
                            [desc_name, 'compile'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'ast object'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        (
            [desc_parameter, ([desc_sig_name, 'source'])],
            [
                desc_optional,
                (
                    [desc_parameter, ([desc_sig_name, 'filename'])],
                    [desc_optional, desc_parameter, ([desc_sig_name, 'symbol'])],
                ),
            ],
        ),
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyfunction_signature_with_bracket(app: Sphinx) -> None:
    text = '.. py:function:: hello(a : ~typing.Any = <b>) -> None'
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
                            [desc_name, 'hello'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'None'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        (
            [
                desc_parameter,
                (
                    [desc_sig_name, 'a'],
                    [desc_sig_punctuation, ':'],
                    desc_sig_space,
                    [desc_sig_name, pending_xref, 'Any'],
                    desc_sig_space,
                    [desc_sig_operator, '='],
                    desc_sig_space,
                    [nodes.inline, '<b>'],
                ),
            ],
        ),
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'python_maximum_signature_line_length': len('hello(name: str) -> str'),
    },
)
def test_pyfunction_signature_with_python_maximum_signature_line_length_equal(app):
    text = '.. py:function:: hello(name: str) -> str'
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
                            [desc_name, 'hello'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'str'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [desc_sig_name, 'name'],
                [desc_sig_punctuation, ':'],
                desc_sig_space,
                [nodes.inline, pending_xref, 'str'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        desc_parameterlist,
        multi_line_parameter_list=False,
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'python_maximum_signature_line_length': len('hello(name: str) -> str'),
    },
)
def test_pyfunction_signature_with_python_maximum_signature_line_length_force_single(
    app,
):
    text = '.. py:function:: hello(names: str) -> str\n   :single-line-parameter-list:'
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
                            [desc_name, 'hello'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'str'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [desc_sig_name, 'names'],
                [desc_sig_punctuation, ':'],
                desc_sig_space,
                [nodes.inline, pending_xref, 'str'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        desc_parameterlist,
        multi_line_parameter_list=False,
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'python_maximum_signature_line_length': len('hello(name: str) -> str'),
    },
)
def test_pyfunction_signature_with_python_maximum_signature_line_length_break(app):
    text = '.. py:function:: hello(names: str) -> str'
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
                            [desc_name, 'hello'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'str'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [desc_sig_name, 'names'],
                [desc_sig_punctuation, ':'],
                desc_sig_space,
                [nodes.inline, pending_xref, 'str'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        desc_parameterlist,
        multi_line_parameter_list=True,
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'maximum_signature_line_length': len('hello(name: str) -> str'),
    },
)
def test_pyfunction_signature_with_maximum_signature_line_length_equal(app):
    text = '.. py:function:: hello(name: str) -> str'
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
                            [desc_name, 'hello'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'str'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [desc_sig_name, 'name'],
                [desc_sig_punctuation, ':'],
                desc_sig_space,
                [nodes.inline, pending_xref, 'str'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        desc_parameterlist,
        multi_line_parameter_list=False,
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'maximum_signature_line_length': len('hello(name: str) -> str'),
    },
)
def test_pyfunction_signature_with_maximum_signature_line_length_force_single(app):
    text = '.. py:function:: hello(names: str) -> str\n   :single-line-parameter-list:'
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
                            [desc_name, 'hello'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'str'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [desc_sig_name, 'names'],
                [desc_sig_punctuation, ':'],
                desc_sig_space,
                [nodes.inline, pending_xref, 'str'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        desc_parameterlist,
        multi_line_parameter_list=False,
    )


@pytest.mark.sphinx(
    'html',
    testroot='root',
    confoverrides={
        'maximum_signature_line_length': len('hello(name: str) -> str'),
    },
)
def test_pyfunction_signature_with_maximum_signature_line_length_break(app):
    text = '.. py:function:: hello(names: str) -> str'
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
                            [desc_name, 'hello'],
                            desc_parameterlist,
                            [desc_returns, pending_xref, 'str'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        [
            desc_parameterlist,
            desc_parameter,
            (
                [desc_sig_name, 'names'],
                [desc_sig_punctuation, ':'],
                desc_sig_space,
                [nodes.inline, pending_xref, 'str'],
            ),
        ],
    )
    assert_node(
        extract_node(doctree, 1, 0, 1),
        desc_parameterlist,
        multi_line_parameter_list=True,
    )
