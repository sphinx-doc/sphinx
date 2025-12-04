from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.testing.util import SphinxTestApp
from sphinx.transforms import MoveModuleTargets

if TYPE_CHECKING:
    from pathlib import Path

CONTENT_PY = """\
move-module-targets
===================

.. py:module:: fish_licence.halibut
"""
CONTENT_JS = """\
move-module-targets
===================

.. js:module:: fish_licence.halibut
"""


@pytest.mark.parametrize(
    'content',
    [
        CONTENT_PY,  # Python
        CONTENT_JS,  # JavaScript
    ],
)
@pytest.mark.usefixtures('rollback_sysmodules')
def test_move_module_targets(tmp_path: Path, content: str) -> None:
    # Test for the MoveModuleTargets transform
    tmp_path.joinpath('conf.py').touch()
    tmp_path.joinpath('index.rst').write_text(content, encoding='utf-8')

    app = SphinxTestApp('dummy', srcdir=tmp_path)
    app.build(force_all=True)
    document = app.env.get_doctree('index')
    section: nodes.section = document[0]  # type: ignore[assignment]

    # target ID has been lifted into the section node
    assert section['ids'] == ['module-fish_licence.halibut', 'move-module-targets']
    # nodes.target has been removed from 'section'
    assert isinstance(section[0], nodes.title)
    assert isinstance(section[1], addnodes.index)
    assert len(section) == 2


@pytest.mark.usefixtures('rollback_sysmodules')
def test_move_module_targets_no_section(tmp_path: Path) -> None:
    # Test for the MoveModuleTargets transform
    tmp_path.joinpath('conf.py').touch()
    tmp_path.joinpath('index.rst').write_text(
        '.. py:module:: fish_licence.halibut\n', encoding='utf-8'
    )

    app = SphinxTestApp('dummy', srcdir=tmp_path)
    app.build(force_all=True)
    document = app.env.get_doctree('index')

    assert document['ids'] == []


@pytest.mark.usefixtures('rollback_sysmodules')
def test_move_module_targets_disabled(tmp_path: Path) -> None:
    # Test for the MoveModuleTargets transform
    tmp_path.joinpath('conf.py').touch()
    tmp_path.joinpath('index.rst').write_text(CONTENT_PY, encoding='utf-8')

    app = SphinxTestApp('dummy', srcdir=tmp_path)
    app.registry.transforms.remove(MoveModuleTargets)  # disable the transform
    app.build(force_all=True)
    document = app.env.get_doctree('index')
    section: nodes.section = document[0]  # type: ignore[assignment]

    # target ID is not lifted into the section node
    assert section['ids'] == ['move-module-targets']
    assert section[2]['ids'] == ['module-fish_licence.halibut']  # type: ignore[index]
    # nodes.target remains in 'section'
    assert isinstance(section[0], nodes.title)
    assert isinstance(section[1], addnodes.index)
    assert isinstance(section[2], nodes.target)
    assert len(section) == 3
