"""Test the versioning implementation."""

from __future__ import annotations

import pickle
import shutil

import pytest
from docutils.utils import DependencyList

from sphinx.testing.util import SphinxTestApp
from sphinx.versioning import add_uids, get_ratio, merge_doctrees

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from docutils import nodes

    from sphinx.application import Sphinx

original: nodes.document
original_uids: list[str]


@pytest.fixture(scope='module', autouse=True)
def _setup_module(rootdir: Path, sphinx_test_tempdir: Path) -> Iterator[None]:
    global original, original_uids  # NoQA: PLW0603
    srcdir = sphinx_test_tempdir / 'test-versioning'
    if not srcdir.exists():
        shutil.copytree(rootdir / 'test-versioning', srcdir)
    app = SphinxTestApp(srcdir=srcdir)
    app.builder.env._app = app
    app.connect('doctree-resolved', on_doctree_resolved)
    app.build()
    original = doctrees['original']
    original_uids = [n.uid for n in add_uids(original, is_paragraph)]  # type: ignore[attr-defined]
    yield
    app.cleanup()


doctrees = {}


def on_doctree_resolved(app: Sphinx, doctree: nodes.document, docname: str) -> None:
    doctrees[docname] = doctree


def is_paragraph(node: nodes.Node) -> bool:
    return node.__class__.__name__ == 'paragraph'


def test_get_ratio() -> None:
    assert get_ratio('', 'a')
    assert get_ratio('a', '')


def test_add_uids() -> None:
    assert len(original_uids) == 3


def test_pickleablility() -> None:
    # we have to modify the doctree so we can pickle it
    copy = original.copy()
    copy.reporter = None  # type: ignore[assignment]
    copy.transformer = None  # type: ignore[assignment]
    copy.settings.warning_stream = None
    copy.settings.env = None
    copy.settings.record_dependencies = DependencyList()
    loaded = pickle.loads(pickle.dumps(copy, pickle.HIGHEST_PROTOCOL))
    assert all(getattr(n, 'uid', False) for n in loaded.findall(is_paragraph))


def test_modified() -> None:
    modified = doctrees['modified']
    new_nodes = list(merge_doctrees(original, modified, is_paragraph))
    uids = [n.uid for n in modified.findall(is_paragraph)]  # type: ignore[attr-defined]
    assert not new_nodes
    assert original_uids == uids


def test_added() -> None:
    added = doctrees['added']
    new_nodes = list(merge_doctrees(original, added, is_paragraph))
    uids = [n.uid for n in added.findall(is_paragraph)]  # type: ignore[attr-defined]
    assert len(new_nodes) == 1
    assert original_uids == uids[:-1]


def test_deleted() -> None:
    deleted = doctrees['deleted']
    new_nodes = list(merge_doctrees(original, deleted, is_paragraph))
    uids = [n.uid for n in deleted.findall(is_paragraph)]  # type: ignore[attr-defined]
    assert not new_nodes
    assert original_uids[::2] == uids


def test_deleted_end() -> None:
    deleted_end = doctrees['deleted_end']
    new_nodes = list(merge_doctrees(original, deleted_end, is_paragraph))
    uids = [n.uid for n in deleted_end.findall(is_paragraph)]  # type: ignore[attr-defined]
    assert not new_nodes
    assert original_uids[:-1] == uids


def test_insert() -> None:
    insert = doctrees['insert']
    new_nodes = list(merge_doctrees(original, insert, is_paragraph))
    uids = [n.uid for n in insert.findall(is_paragraph)]  # type: ignore[attr-defined]
    assert len(new_nodes) == 1
    assert original_uids[0] == uids[0]
    assert original_uids[1:] == uids[2:]


def test_insert_beginning() -> None:
    insert_beginning = doctrees['insert_beginning']
    new_nodes = list(merge_doctrees(original, insert_beginning, is_paragraph))
    uids = [n.uid for n in insert_beginning.findall(is_paragraph)]  # type: ignore[attr-defined]
    assert len(new_nodes) == 1
    assert len(uids) == 4
    assert original_uids == uids[1:]
    assert original_uids[0] != uids[0]


def test_insert_similar() -> None:
    insert_similar = doctrees['insert_similar']
    new_nodes = list(merge_doctrees(original, insert_similar, is_paragraph))
    uids = [n.uid for n in insert_similar.findall(is_paragraph)]  # type: ignore[attr-defined]
    assert len(new_nodes) == 1
    assert new_nodes[0].rawsource == 'Anyway I need more'  # type: ignore[attr-defined]
    assert original_uids[0] == uids[0]
    assert original_uids[1:] == uids[2:]
