"""Test the only directive with the test root."""

from __future__ import annotations

import pickle
import re
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('text', testroot='directive-only')
def test_sectioning(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'only.rst'])
    doctree = app.env.get_doctree('only')
    app.env.apply_post_transforms(doctree, 'only')

    parts = [_get_sections(n) for n in doctree.children if isinstance(n, nodes.section)]
    for i, section in enumerate(parts):
        _test_sections(f'{i + 1}.', section, 4)
    actual_headings = '\n'.join(p[0] for p in parts)  # type: ignore[misc]
    assert len(parts) == 4, (
        f'Expected 4 document level headings, got:\n{actual_headings}'
    )


@pytest.mark.sphinx('pseudoxml', testroot='directive-only')
def test_section_hierarchy_after_only(app: SphinxTestApp) -> None:
    source = app.srcdir / 'section-mixup.rst'
    source.write_text(
        """\
Element mix-up
==============

.. only:: html or pseudoxml

   Section in "only"
   =================
   Paragraph in "only"

Paragraph after "only".

Subsection after "only"
-----------------------

Section after "only"
====================
""",
        encoding='utf-8',
    )
    app.build(filenames=[source])
    doctree = app.env.get_doctree('section-mixup')
    app.env.apply_post_transforms(doctree, 'section-mixup')

    sections = list(doctree.findall(nodes.section))
    top_section, conditional_section, subsection, following_section = sections
    assert [section[0].astext() for section in sections] == [
        'Element mix-up',
        'Section in “only”',
        'Subsection after “only”',
        'Section after “only”',
    ]
    assert conditional_section.parent is doctree
    assert subsection.parent is conditional_section
    assert following_section.parent is doctree
    assert conditional_section['ids'] == ['section-in-only']
    assert [
        paragraph.astext() for paragraph in conditional_section.findall(nodes.paragraph)
    ] == ['Paragraph in “only”', 'Paragraph after “only”.']
    assert top_section.parent is doctree
    output = (app.outdir / 'section-mixup.pseudoxml').read_text(encoding='utf-8')
    assert 'Paragraph in “only”' in output
    assert 'Paragraph after “only”.' in output


@pytest.mark.sphinx('pseudoxml', testroot='directive-only')
def test_only_section_hierarchy_and_transitions(app: SphinxTestApp) -> None:
    source = app.srcdir / 'section-transitions.rst'
    source.write_text(
        """\
Parent
======

.. only:: pseudoxml

   Conditional A
   -------------

   Conditional B
   ==============

   Conditional C
   --------------

Unconditional subsection
------------------------

Another parent
==============

.. only:: pseudoxml

   First subsection
   ----------------

.. only:: pseudoxml

   Second subsection
   -----------------

Nested outer
============

.. only:: pseudoxml

   .. only:: pseudoxml

      Nested section
      --------------

After nested only
-----------------
""",
        encoding='utf-8',
    )
    app.build(filenames=[source])
    doctree = app.env.get_doctree('section-transitions')

    sections = list(doctree.findall(nodes.section))
    by_title = {section[0].astext(): section for section in sections}
    assert by_title['Parent'].parent is doctree
    assert by_title['Conditional A'].parent is by_title['Parent']
    assert by_title['Conditional B'].parent is doctree
    assert by_title['Conditional C'].parent is by_title['Conditional B']
    assert by_title['Unconditional subsection'].parent is by_title['Conditional B']
    assert by_title['First subsection'].parent is by_title['Another parent']
    assert by_title['Second subsection'].parent is by_title['Another parent']
    assert by_title['Nested section'].parent is by_title['Nested outer']
    assert by_title['After nested only'].parent is by_title['Nested outer']


@pytest.mark.parametrize(
    ('source_text', 'expected_titles', 'hidden_ids', 'visible_section_parent'),
    [
        (
            """\
Outer
=====

.. only:: false_tag

   Hidden section
   --------------

Visible paragraph.

Visible subsection
------------------
""",
            ['Outer', 'Visible subsection'],
            ['hidden-section'],
            'outer',
        ),
        (
            """\
Outer
=====

.. only:: false_tag

   Hidden section
   --------------

Visible paragraph.

Visible section
===============
""",
            ['Outer', 'Visible section'],
            ['hidden-section'],
            'document',
        ),
        (
            """\
Outer
=====

.. only:: false_tag

   Hidden A
   --------

   Hidden B
   ========

Visible paragraph.
""",
            ['Outer'],
            ['hidden-a', 'hidden-b'],
            None,
        ),
    ],
)
@pytest.mark.sphinx('text', testroot='directive-only')
def test_false_only_section_does_not_change_section_state(
    app: SphinxTestApp,
    source_text: str,
    expected_titles: list[str],
    hidden_ids: list[str],
    visible_section_parent: str | None,
) -> None:
    source = app.srcdir / 'false-only-section.rst'
    source.write_text(source_text, encoding='utf-8')
    app.build(filenames=[source])
    doctree = app.env.get_doctree('false-only-section')

    sections = list(doctree.findall(nodes.section))
    assert [section[0].astext() for section in sections] == expected_titles
    outer_section = doctree[0]
    assert isinstance(outer_section, nodes.section)
    visible_paragraph = next(
        paragraph
        for paragraph in doctree.findall(nodes.paragraph)
        if paragraph.astext() == 'Visible paragraph.'
    )
    assert visible_paragraph.parent is outer_section
    assert not set(hidden_ids) & doctree.ids.keys()
    if visible_section_parent == 'outer':
        assert sections[-1].parent is outer_section
    elif visible_section_parent == 'document':
        assert sections[-1].parent is doctree


@pytest.mark.sphinx('pseudoxml', testroot='directive-only')
def test_enabled_only_preserves_section_and_active_paragraph_parent(
    app: SphinxTestApp,
) -> None:
    source = app.srcdir / 'enabled-only-section.rst'
    source.write_text(
        """\
Outer
=====

.. only:: pseudoxml

   Conditional subsection
   ----------------------

   Conditional content.

After only.

Following subsection
--------------------
""",
        encoding='utf-8',
    )
    app.build(filenames=[source])
    doctree = app.env.get_doctree('enabled-only-section')
    outer_section = next(
        section
        for section in doctree.findall(nodes.section)
        if section[0].astext() == 'Outer'
    )
    conditional_section = next(
        section
        for section in doctree.findall(nodes.section)
        if section[0].astext() == 'Conditional subsection'
    )
    following_section = next(
        section
        for section in doctree.findall(nodes.section)
        if section[0].astext() == 'Following subsection'
    )
    paragraphs = {
        paragraph.astext(): paragraph for paragraph in doctree.findall(nodes.paragraph)
    }

    assert conditional_section.parent is outer_section
    assert following_section.parent is outer_section
    assert paragraphs['Conditional content.'].parent is conditional_section
    assert paragraphs['After only.'].parent is conditional_section


@pytest.mark.sphinx('pseudoxml', testroot='directive-only')
def test_only_inside_included_content_updates_active_section(
    app: SphinxTestApp,
) -> None:
    source = app.srcdir / 'included-only.rst'
    source.write_text(
        """\
Outer
=====

.. include:: only-fragment.rst

After include.

Following subsection
--------------------
""",
        encoding='utf-8',
    )
    (app.srcdir / 'only-fragment.rst').write_text(
        """\
.. only:: pseudoxml

   Included subsection
   -------------------

   Included content.
""",
        encoding='utf-8',
    )
    app.build(filenames=[source])
    doctree = app.env.get_doctree('included-only')
    outer_section = next(
        section
        for section in doctree.findall(nodes.section)
        if section[0].astext() == 'Outer'
    )
    included_section = next(
        section
        for section in doctree.findall(nodes.section)
        if section[0].astext() == 'Included subsection'
    )
    following_section = next(
        section
        for section in doctree.findall(nodes.section)
        if section[0].astext() == 'Following subsection'
    )
    after_include = next(
        paragraph
        for paragraph in doctree.findall(nodes.paragraph)
        if paragraph.astext() == 'After include.'
    )

    assert included_section.parent is outer_section
    assert following_section.parent is outer_section
    assert after_include.parent is included_section


@pytest.mark.sphinx('pseudoxml', testroot='directive-only')
def test_include_inside_only_preserves_source_location(app: SphinxTestApp) -> None:
    source = app.srcdir / 'only-includes.rst'
    source.write_text(
        """\
Parent
======

.. only:: pseudoxml

   .. include:: included-fragment.rst

After only.
""",
        encoding='utf-8',
    )
    (app.srcdir / 'included-fragment.rst').write_text(
        """\
Included subsection
-------------------

.. unknown-only-directive::

   Included content.
""",
        encoding='utf-8',
    )
    app.build(filenames=[source])
    doctree = app.env.get_doctree('only-includes')
    included_section = next(
        section
        for section in doctree.findall(nodes.section)
        if section[0].astext() == 'Included subsection'
    )
    after_only = next(
        paragraph
        for paragraph in doctree.findall(nodes.paragraph)
        if paragraph.astext() == 'After only.'
    )

    assert included_section.parent is doctree[0]
    assert after_only.parent is included_section
    assert f'{app.srcdir / "included-fragment.rst"}:4:' in app.warning.getvalue()


@pytest.mark.sphinx('text', testroot='directive-only')
def test_only_rewrite_preserves_source_line_after_trailing_blank_lines(
    app: SphinxTestApp,
) -> None:
    source = app.srcdir / 'only-source-line.rst'
    source.write_text(
        """\
Title
=====

.. only:: text

   .. unknown-only-directive::

      Included content.


""",
        encoding='utf-8',
    )
    app.build(filenames=[source])

    assert f'{source}:6:' in app.warning.getvalue()


@pytest.mark.sphinx('text', testroot='directive-only')
def test_invalid_only_expression_warns_and_keeps_content(app: SphinxTestApp) -> None:
    source = app.srcdir / 'invalid-only-expression.rst'
    source.write_text(
        """\
Visible content
===============

.. only:: invalid(

   Kept despite invalid expression.
""",
        encoding='utf-8',
    )
    app.build(filenames=[source])
    doctree = app.env.get_doctree('invalid-only-expression')

    assert 'Kept despite invalid expression.' in doctree.astext()
    assert 'exception while evaluating only directive expression' in (
        app.warning.getvalue()
    )


@pytest.mark.sphinx('pseudoxml', testroot='directive-only')
def test_only_section_label(app: SphinxTestApp) -> None:
    source = app.srcdir / 'section-label.rst'
    source.write_text(
        """\
Outer
=====

.. only:: pseudoxml

   .. _explicit-heading-label:

   Conditional heading
   -------------------

After only, see :ref:`explicit-heading-label`.
""",
        encoding='utf-8',
    )
    app.build(filenames=[source])
    doctree = app.env.get_doctree('section-label')
    app.env.apply_post_transforms(doctree, 'section-label')

    conditional_section = next(
        section
        for section in doctree.findall(nodes.section)
        if section[0].astext() == 'Conditional heading'
    )
    assert conditional_section['ids'] == [
        'conditional-heading',
        'explicit-heading-label',
    ]
    reference = next(doctree.findall(nodes.reference))
    assert reference['refid'] == 'explicit-heading-label'


@pytest.mark.sphinx('pseudoxml', testroot='directive-only')
def test_only_reparses_doctree_when_tags_change(app: SphinxTestApp) -> None:
    source = app.srcdir / 'section-tags.rst'
    source.write_text(
        """\
Parent
======

.. only:: conditional

   Conditional section
   -------------------
""",
        encoding='utf-8',
    )
    app.build(filenames=[source])
    assert 'conditional-section' not in app.env.get_doctree('section-tags').ids

    app.tags.add('conditional')
    app.build(filenames=[source])
    assert 'conditional-section' in app.env.get_doctree('section-tags').ids

    app.tags.remove('conditional')
    app.build(filenames=[source])
    assert 'conditional-section' not in app.env.get_doctree('section-tags').ids


def test_only_reparses_doctree_when_builder_tags_change(
    make_app: Any, tmp_path: Path
) -> None:
    srcdir = tmp_path / 'src'
    srcdir.mkdir()
    (srcdir / 'conf.py').write_text("project = 'test'\n", encoding='utf-8')
    (srcdir / 'index.rst').write_text(
        """\
Parent
======

.. only:: html

   Conditional section
   -------------------
""",
        encoding='utf-8',
    )
    builddir = tmp_path / 'build'

    app = make_app('pseudoxml', srcdir=srcdir, builddir=builddir)
    app.build()
    assert 'conditional-section' not in app.env.get_doctree('index').ids

    app_with_tag = make_app('html', srcdir=srcdir, builddir=builddir)
    app_with_tag.build()
    assert 'conditional-section' in app_with_tag.env.get_doctree('index').ids

    app_without_tag = make_app('pseudoxml', srcdir=srcdir, builddir=builddir)
    app_without_tag.build()
    assert 'conditional-section' not in app_without_tag.env.get_doctree('index').ids


def test_only_doc_tracking_survives_merge_and_removal(
    make_app: Any, tmp_path: Path
) -> None:
    srcdir = tmp_path / 'src'
    srcdir.mkdir()
    (srcdir / 'conf.py').write_text("project = 'test'\n", encoding='utf-8')
    (srcdir / 'index.rst').write_text(
        """\
.. toctree::

   conditional
""",
        encoding='utf-8',
    )
    conditional_doc = srcdir / 'conditional.rst'
    conditional_doc.write_text(
        """\
Parent
======

.. only:: conditional

   Conditional section
   -------------------
""",
        encoding='utf-8',
    )
    builddir = tmp_path / 'build'
    app = make_app('pseudoxml', srcdir=srcdir, builddir=builddir, parallel=2)
    app.build()

    assert app.env._only_docs == {'conditional'}
    assert app.env._parsed_tags == frozenset(app.tags)

    worker = make_app('pseudoxml', srcdir=srcdir, builddir=tmp_path / 'worker')
    worker.build()
    app.env._only_docs.clear()
    app.env.merge_info_from(['conditional'], worker.env, app)
    assert app.env._only_docs == {'conditional'}

    worker.env._only_docs.discard('conditional')
    app.env.merge_info_from(['conditional'], worker.env, app)
    assert not app.env._only_docs
    worker.env._only_docs.add('conditional')
    app.env.merge_info_from(['conditional'], worker.env, app)

    app.tags.add('conditional')
    app.build()
    assert 'conditional-section' in app.env.get_doctree('conditional').ids

    conditional_doc.unlink()
    app.build()
    assert 'conditional' not in app.env._only_docs


def test_old_environment_version_is_discarded_for_only_doctrees(
    make_app: Any, tmp_path: Path
) -> None:
    srcdir = tmp_path / 'src'
    srcdir.mkdir()
    (srcdir / 'conf.py').write_text("project = 'test'\n", encoding='utf-8')
    (srcdir / 'index.rst').write_text(
        """\
.. only:: html

   Conditional section
   -------------------
""",
        encoding='utf-8',
    )
    builddir = tmp_path / 'build'

    app = make_app('pseudoxml', srcdir=srcdir, builddir=builddir)
    app.build()
    app.env.version = {'sphinx': app.env.version['sphinx'] - 1}
    with (app.doctreedir / 'environment.pickle').open('wb') as stream:
        pickle.dump(app.env, stream)

    app_with_tag = make_app('html', srcdir=srcdir, builddir=builddir)
    app_with_tag.build()

    assert app_with_tag.fresh_env_used
    assert 'conditional-section' in app_with_tag.env.get_doctree('index').ids


def test_only_sections_are_numbered(make_app: Any, tmp_path: Path) -> None:
    srcdir = tmp_path / 'src'
    srcdir.mkdir()
    (srcdir / 'conf.py').write_text("project = 'test'\n", encoding='utf-8')
    (srcdir / 'index.rst').write_text(
        """\
Contents
========

.. toctree::
   :numbered:

   child
""",
        encoding='utf-8',
    )
    (srcdir / 'child.rst').write_text(
        """\
Parent
======

.. only:: html

   Conditional section
   -------------------

Following section
-----------------
""",
        encoding='utf-8',
    )
    app = make_app('html', srcdir=srcdir, builddir=tmp_path / 'build')
    app.build()

    assert app.env.toc_secnumbers['child'] == {
        '': (1,),
        '#conditional-section': (1, 1),
        '#following-section': (1, 2),
    }


def _get_sections(section: nodes.Node) -> list[str | list[Any]]:
    if not isinstance(section, nodes.section):
        return list(map(_get_sections, section.children))
    next_title_node = section.next_node(nodes.title)
    assert next_title_node is not None
    title = next_title_node.astext().strip()
    subsections = []
    children = section.children.copy()
    while children:
        node = children.pop(0)
        if isinstance(node, nodes.section):
            subsections.append(node)
            continue
        children = list(node.children) + children
    return [title, list(map(_get_sections, subsections))]


def _test_sections(
    prefix: str, sections: list[str | list[Any]], indent: int = 0
) -> None:
    title = sections[0]
    assert isinstance(title, str)
    parent_num = title.partition(' ')[0]
    assert prefix == parent_num, f'Section out of place: {title!r}'
    for i, subsection in enumerate(sections[1]):
        subsection_title = subsection[0]
        assert isinstance(subsection_title, str)
        num = subsection_title.partition(' ')[0]
        assert re.match('[0-9]+[.0-9]*[.]', num), (
            f'Unnumbered section: {subsection[0]!r}'
        )
        _test_sections(f'{prefix}{i + 1}.', subsection, indent + 4)
