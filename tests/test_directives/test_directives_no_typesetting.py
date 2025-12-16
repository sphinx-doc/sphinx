"""Tests the directives"""

from __future__ import annotations

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

TYPE_CHECKING = False
if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp

    type _IndexEntry = tuple[str, str, str, str, str | None]

DOMAINS = [
    # directive, no-index, no-index-entry, signature of f, signature of g, index entry of g
    (
        'c:function',
        False,
        True,
        'void f()',
        'void g()',
        ('single', 'g (C function)', 'c.g', '', None),
    ),
    (
        'cpp:function',
        False,
        True,
        'void f()',
        'void g()',
        ('single', 'g (C++ function)', '_CPPv41gv', '', None),
    ),
    (
        'js:function',
        True,
        True,
        'f()',
        'g()',
        ('single', 'g() (built-in function)', 'g', '', None),
    ),
    (
        'py:function',
        True,
        True,
        'f()',
        'g()',
        ('pair', 'built-in function; g()', 'g', '', None),
    ),
    (
        'rst:directive',
        True,
        False,
        'f',
        'g',
        ('single', 'g (directive)', 'directive-g', '', None),
    ),
    (
        'cmdoption',
        True,
        False,
        'f',
        'g',
        ('pair', 'command line option; g', 'cmdoption-arg-g', '', None),
    ),
    (
        'envvar',
        True,
        False,
        'f',
        'g',
        ('single', 'environment variable; g', 'envvar-g', '', None),
    ),
]


@pytest.mark.parametrize(
    ('directive', 'no_index', 'no_index_entry', 'sig_f', 'sig_g', 'index_g'),
    DOMAINS,
)
@pytest.mark.sphinx('html', testroot='root')
def test_object_description_no_typesetting(
    app: SphinxTestApp,
    directive: str,
    no_index: bool,
    no_index_entry: bool,
    sig_f: str,
    sig_g: str,
    index_g: _IndexEntry,
) -> None:
    text = f'.. {directive}:: {sig_f}\n   :no-typesetting:\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, nodes.target))


@pytest.mark.parametrize(
    ('directive', 'no_index', 'no_index_entry', 'sig_f', 'sig_g', 'index_g'),
    DOMAINS,
)
@pytest.mark.sphinx('html', testroot='root')
def test_object_description_no_typesetting_twice(
    app: SphinxTestApp,
    directive: str,
    no_index: bool,
    no_index_entry: bool,
    sig_f: str,
    sig_g: str,
    index_g: _IndexEntry,
) -> None:
    text = (
        f'.. {directive}:: {sig_f}\n'
        f'   :no-typesetting:\n'
        f'.. {directive}:: {sig_g}\n'
        f'   :no-typesetting:\n'
    )
    doctree = restructuredtext.parse(app, text)
    # Note that all index nodes come before the target nodes
    assert_node(doctree, (addnodes.index, addnodes.index, nodes.target, nodes.target))


@pytest.mark.parametrize(
    ('directive', 'no_index', 'no_index_entry', 'sig_f', 'sig_g', 'index_g'),
    DOMAINS,
)
@pytest.mark.sphinx('html', testroot='root')
def test_object_description_no_typesetting_noindex_orig(
    app: SphinxTestApp,
    directive: str,
    no_index: bool,
    no_index_entry: bool,
    sig_f: str,
    sig_g: str,
    index_g: _IndexEntry,
) -> None:
    if not no_index:
        pytest.skip(f'{directive} does not support :no-index: option')
    text = f'.. {directive}:: {sig_f}\n   :no-index:\n.. {directive}:: {sig_g}\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, addnodes.desc, addnodes.index, addnodes.desc))
    assert_node(doctree[2], addnodes.index, entries=[index_g])


@pytest.mark.parametrize(
    ('directive', 'no_index', 'no_index_entry', 'sig_f', 'sig_g', 'index_g'),
    DOMAINS,
)
@pytest.mark.sphinx('html', testroot='root')
def test_object_description_no_typesetting_noindex(
    app: SphinxTestApp,
    directive: str,
    no_index: bool,
    no_index_entry: bool,
    sig_f: str,
    sig_g: str,
    index_g: _IndexEntry,
) -> None:
    if not no_index:
        pytest.skip(f'{directive} does not support :no-index: option')
    text = (
        f'.. {directive}:: {sig_f}\n'
        f'   :no-index:\n'
        f'   :no-typesetting:\n'
        f'.. {directive}:: {sig_g}\n'
        f'   :no-typesetting:\n'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, addnodes.index, nodes.target))
    assert_node(doctree[0], addnodes.index, entries=[])
    assert_node(doctree[1], addnodes.index, entries=[index_g])


@pytest.mark.parametrize(
    ('directive', 'no_index', 'no_index_entry', 'sig_f', 'sig_g', 'index_g'),
    DOMAINS,
)
@pytest.mark.sphinx('html', testroot='root')
def test_object_description_no_typesetting_no_index_entry(
    app: SphinxTestApp,
    directive: str,
    no_index: bool,
    no_index_entry: bool,
    sig_f: str,
    sig_g: str,
    index_g: _IndexEntry,
) -> None:
    if not no_index_entry:
        pytest.skip(f'{directive} does not support :no-index-entry: option')
    text = (
        f'.. {directive}:: {sig_f}\n'
        f'   :no-index-entry:\n'
        f'   :no-typesetting:\n'
        f'.. {directive}:: {sig_g}\n'
        f'   :no-typesetting:\n'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, addnodes.index, nodes.target, nodes.target))
    assert_node(doctree[0], addnodes.index, entries=[])
    assert_node(doctree[1], addnodes.index, entries=[index_g])


@pytest.mark.parametrize(
    ('directive', 'no_index', 'no_index_entry', 'sig_f', 'sig_g', 'index_g'),
    DOMAINS,
)
@pytest.mark.sphinx('html', testroot='root')
def test_object_description_no_typesetting_code(
    app: SphinxTestApp,
    directive: str,
    no_index: bool,
    no_index_entry: bool,
    sig_f: str,
    sig_g: str,
    index_g: _IndexEntry,
) -> None:
    text = (
        f'.. {directive}:: {sig_f}\n'
        f'   :no-typesetting:\n'
        f'.. {directive}:: {sig_g}\n'
        f'   :no-typesetting:\n'
        f'.. code::\n'
        f'\n'
        f'   code\n'
    )
    doctree = restructuredtext.parse(app, text)
    # Note that all index nodes come before the targets
    assert_node(
        doctree,
        (
            addnodes.index,
            addnodes.index,
            nodes.target,
            nodes.target,
            nodes.literal_block,
        ),
    )


@pytest.mark.parametrize(
    ('directive', 'no_index', 'no_index_entry', 'sig_f', 'sig_g', 'index_g'),
    DOMAINS,
)
@pytest.mark.sphinx('html', testroot='root')
def test_object_description_no_typesetting_heading(
    app: SphinxTestApp,
    directive: str,
    no_index: bool,
    no_index_entry: bool,
    sig_f: str,
    sig_g: str,
    index_g: _IndexEntry,
) -> None:
    text = (
        f'.. {directive}:: {sig_f}\n'
        f'   :no-typesetting:\n'
        f'.. {directive}:: {sig_g}\n'
        f'   :no-typesetting:\n'
        f'\n'
        f'Heading\n'
        f'=======\n'
    )
    doctree = restructuredtext.parse(app, text)
    # Note that all index nodes come before the targets and the heading is floated before those.
    assert_node(
        doctree,
        (nodes.title, addnodes.index, addnodes.index, nodes.target, nodes.target),
    )
