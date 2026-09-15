"""Test toctree ``:level-up:`` hierarchy handling."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.environment.adapters.toctree import global_toctree_for_doc
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


def _toc_children(item: nodes.list_item) -> list[tuple[str, object]]:
    if len(item) < 2 or not isinstance(item[1], nodes.bullet_list):
        return []
    result: list[tuple[str, object]] = []
    for child in item[1]:
        if isinstance(child, addnodes.toctree):
            result.append(('toctree', list(child['includefiles'])))
        elif isinstance(child, nodes.list_item):
            result.append(('section', child[0].astext()))
        elif isinstance(child, addnodes.only):
            for nested in child:
                if isinstance(nested, addnodes.toctree):
                    result.extend([('only-toctree', list(nested['includefiles']))])
    return result


@pytest.mark.sphinx('html', testroot='toctree-level-up')
def test_toctree_level_up_option(app: SphinxTestApp) -> None:
    text = '.. toctree::\n   :level-up: 2\n\n   page1\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert isinstance(doctree[0], nodes.compound)
    assert_node(doctree[0][0], addnodes.toctree, level_up=2)


@pytest.mark.sphinx('html', testroot='toctree-level-up')
def test_toc_level_up_directive_sets_default(app: SphinxTestApp) -> None:
    text = '.. toc-level-up:: 1\n\n.. toctree::\n\n   page1\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert isinstance(doctree[0], nodes.compound)
    assert_node(doctree[0][0], addnodes.toctree, level_up=1)


@pytest.mark.sphinx('html', testroot='toctree-level-up')
def test_explicit_zero_overrides_default(app: SphinxTestApp) -> None:
    text = '.. toc-level-up:: 1\n\n.. toctree::\n   :level-up: 0\n\n   page1\n'

    app.env.find_files(app.config, app.builder)
    doctree = restructuredtext.parse(app, text, 'index')
    assert isinstance(doctree[0], nodes.compound)
    assert_node(doctree[0][0], addnodes.toctree, level_up=0)


@pytest.mark.sphinx('xml', testroot='toctree-level-up')
def test_level_up_env_tocs(app: SphinxTestApp) -> None:
    app.build()

    title_item = app.env.tocs['index'][0]
    assert isinstance(title_item, nodes.list_item)
    assert _toc_children(title_item) == [
        ('toctree', ['defaults', 'over']),
        ('section', 'Intro header'),
        ('toctree', ['page1']),
        ('section', 'Later sibling'),
        ('section', 'Level two'),
        ('toctree', ['page2']),
        ('section', 'Hidden section'),
        ('toctree', ['hidden']),
        ('section', 'Numbered section'),
        ('toctree', ['numbered']),
    ]

    assert isinstance(title_item[1], nodes.bullet_list)
    level_two = title_item[1][4]
    assert isinstance(level_two, nodes.list_item)
    assert _toc_children(level_two) == [('section', 'Nested')]


@pytest.mark.sphinx('xml', testroot='toctree-level-up')
def test_toc_level_up_directive_and_override(app: SphinxTestApp) -> None:
    app.build()

    title_item = app.env.tocs['defaults'][0]
    assert isinstance(title_item, nodes.list_item)
    assert _toc_children(title_item) == [
        ('section', 'Section A'),
        ('toctree', ['default']),
        ('section', 'Section B'),
    ]

    assert isinstance(title_item[1], nodes.bullet_list)
    section_b = title_item[1][2]
    assert isinstance(section_b, nodes.list_item)
    assert isinstance(section_b[1], nodes.bullet_list)
    subsection = section_b[1][0]
    assert isinstance(subsection, nodes.list_item)
    assert _toc_children(subsection) == [('toctree', ['override'])]


@pytest.mark.sphinx('xml', testroot='toctree-level-up', freshenv=True)
def test_level_up_over_promotion_warns(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    toc = app.env.tocs['over']
    assert isinstance(toc[0], nodes.list_item)
    assert toc[0][0].astext() == 'Over'
    assert _toc_children(toc[0]) == [('section', 'Deep')]
    assert_node(toc[1], addnodes.toctree, includefiles=['over-child'])
    assert 'toctree :level-up: 5 exceeds the number of containing sections' in (
        app.warning.getvalue()
    )


@pytest.mark.sphinx('html', testroot='toctree-level-up')
def test_level_up_html_global_toc(app: SphinxTestApp) -> None:
    app.build()
    toctree = global_toctree_for_doc(
        app.env,
        'index',
        app.builder,
        collapse=False,
        includehidden=True,
        tags=app.tags,
    )
    assert toctree is not None
    titles = [
        entry[0].astext()
        for entry in toctree.findall(nodes.list_item)
        if entry[0].astext()
        in {'Defaults', 'Over', 'Page 1', 'Page 2', 'Hidden page', 'Numbered page'}
    ]
    assert titles == [
        'Defaults',
        'Over',
        'Page 1',
        'Page 2',
        'Hidden page',
        'Numbered page',
    ]


@pytest.mark.sphinx('html', testroot='toctree-level-up')
def test_level_up_html_in_page_order(app: SphinxTestApp) -> None:
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    before = content.index('Paragraph before toctree')
    after = content.index('Paragraph after toctree')
    page1 = content.index('main-toctree')
    later = content.index('Later sibling content')
    assert before < page1 < after < later


@pytest.mark.sphinx('latex', testroot='toctree-level-up')
def test_toctree_level_up_latex_section_nesting(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    tex_files = list(app.outdir.glob('*.tex'))
    assert tex_files
    result = tex_files[0].read_text(encoding='utf8')
    intro = result.index('\\chapter{Intro header}')
    page1 = result.index('\\chapter{Page 1}')
    later = result.index('\\chapter{Later sibling}')
    page2 = result.index('\\chapter{Page 2}')
    assert intro < page1 < later < page2
    assert '\\section{Page 1}' not in result
    assert '\\section{Page 2}' not in result
    assert '\\section{Hidden page}' not in result
    assert '\\chapter{Hidden page}' in result
    assert result.index('Paragraph after toctree') < page1
    assert '\\section{Default page}' in result
    assert '\\subsubsection{Override page}' in result


@pytest.mark.sphinx('singlehtml', testroot='toctree-level-up')
def test_toctree_level_up_singlehtml_section_nesting(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    intro = result.index('<h2>Intro header')
    page1 = result.index('<h2>Page 1')
    later = result.index('<h2>Later sibling')
    page2 = result.index('<h2>Page 2')
    assert intro < page1 < later < page2
    assert '<h3>Page 1' not in result
    assert '<h3>Page 2' not in result


@pytest.mark.sphinx('latex', testroot='only-level-up')
def test_level_up_only_wrapper_excludes_latex(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    tex_files = list(app.outdir.glob('*.tex'))
    assert tex_files
    result = tex_files[0].read_text(encoding='utf8')
    assert 'Child body.' not in result


@pytest.mark.sphinx('singlehtml', testroot='only-level-up')
def test_level_up_only_wrapper_includes_singlehtml(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert 'Child body.' in result


@pytest.mark.sphinx('xml', testroot='only-level-up')
def test_level_up_preserves_only_wrapper(app: SphinxTestApp) -> None:
    app.build()
    title_item = app.env.tocs['index'][0]
    assert isinstance(title_item, nodes.list_item)
    assert _toc_children(title_item) == [
        ('section', 'Section'),
        ('only-toctree', ['child']),
    ]
