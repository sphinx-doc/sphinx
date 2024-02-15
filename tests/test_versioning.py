"""Test the versioning implementation."""
from __future__ import annotations

import pickle
import shutil
import uuid
from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest

import docutils.nodes as nodes
from sphinx.util.docutils import new_document
from sphinx.versioning import VERSIONING_RATIO, add_uids, get_ratio, merge_doctrees
from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from _pytest.fixtures import FixtureRequest
    from _pytest.python import Module

_DOCTREES = pytest.StashKey[dict[str, nodes.Node]]()  # docname -> doctree


def _set_node_uids(node: nodes.Node) -> list[nodes.Node]:
    return list(add_uids(node, nodes.paragraph))


def _get_node_uids(node: nodes.Node) -> list[str]:
    return [n.uid for n in node.findall(nodes.paragraph)]


@pytest.fixture(scope='module')
def test_module(request: FixtureRequest) -> Module:
    module = request.node.getparent(pytest.Module)
    assert module is not None
    module.stash.setdefault(_DOCTREES, {})
    return module


@pytest.fixture(scope='module', autouse=True)
def _setup_module(
    request: FixtureRequest,
    test_module: Module,
    sphinx_test_tempdir: Path,
    rootdir: Path,
) -> None:
    def on_doctree_resolved(_: SphinxTestApp, doctree: nodes.Node, docname: str) -> None:
        if docname == 'original':
            _set_node_uids(doctree)  # add UUIDs to the paragraph nodes
        assert docname not in test_module.stash[_DOCTREES]
        test_module.stash[_DOCTREES][docname] = doctree

    testroot = 'test-versioning'
    srcdir = sphinx_test_tempdir / testroot / uuid.uuid4().hex
    assert not srcdir.exists()
    shutil.copytree(rootdir / testroot, srcdir)

    app = SphinxTestApp('dummy', srcdir=srcdir)
    app.connect('doctree-resolved', on_doctree_resolved)
    app.build()
    yield
    app.cleanup()


@pytest.fixture()
def doctrees(test_module: Module) -> Mapping[str, nodes.Node]:
    return MappingProxyType(test_module.stash[_DOCTREES])


@pytest.fixture()
def original(doctrees: Mapping[str, nodes.Node]) -> nodes.Node:
    return doctrees['original']


@pytest.fixture()
def original_uids(original: nodes.Node) -> list[str]:
    return _get_node_uids(original)


def test_get_ratio():
    assert get_ratio('', 'a') == VERSIONING_RATIO
    assert get_ratio('a', '') == VERSIONING_RATIO


def test_add_uids():
    doc = new_document('')
    doc += nodes.paragraph(text='a')
    doc += nodes.paragraph(text='b')
    for node in add_uids(doc, nodes.paragraph):  # type: nodes.document
        assert hasattr(node, 'uid')


def test_picklablility():
    paragraph = nodes.paragraph(text='a')
    assert _set_node_uids(paragraph) == [paragraph]

    loaded = pickle.loads(pickle.dumps(paragraph, pickle.HIGHEST_PROTOCOL))
    assert isinstance(loaded, nodes.paragraph)
    assert loaded.uid == paragraph.uid


def test_original(original_uids):
    assert len(original_uids) == 3


def test_modified(doctrees, original, original_uids):
    modified = doctrees['modified']
    new_nodes = list(merge_doctrees(original, modified, nodes.paragraph))
    assert not new_nodes
    assert _get_node_uids(modified) == original_uids


def test_added(doctrees, original, original_uids):
    added = doctrees['added']
    new_nodes = list(merge_doctrees(original, added, nodes.paragraph))
    uids = _get_node_uids(added)
    assert len(new_nodes) == 1
    assert original_uids == uids[:-1]


def test_deleted(doctrees, original, original_uids):
    deleted = doctrees['deleted']
    new_nodes = list(merge_doctrees(original, deleted, nodes.paragraph))
    uids = _get_node_uids(deleted)
    assert not new_nodes
    assert original_uids[::2] == uids


def test_deleted_end(doctrees, original, original_uids):
    deleted_end = doctrees['deleted_end']
    new_nodes = list(merge_doctrees(original, deleted_end, nodes.paragraph))
    uids = _get_node_uids(deleted_end)
    assert not new_nodes
    assert original_uids[:-1] == uids


def test_insert(doctrees, original, original_uids):
    insert = doctrees['insert']
    new_nodes = list(merge_doctrees(original, insert, nodes.paragraph))
    uids = _get_node_uids(insert)
    assert len(new_nodes) == 1
    assert original_uids[0] == uids[0]
    assert original_uids[1:] == uids[2:]


def test_insert_beginning(doctrees, original, original_uids):
    insert_beginning = doctrees['insert_beginning']
    new_nodes = list(merge_doctrees(original, insert_beginning, nodes.paragraph))
    uids = _get_node_uids(insert_beginning)
    assert len(new_nodes) == 1
    assert len(uids) == 4
    assert original_uids == uids[1:]
    assert original_uids[0] != uids[0]


def test_insert_similar(doctrees, original, original_uids):
    insert_similar = doctrees['insert_similar']
    new_nodes = list(merge_doctrees(original, insert_similar, nodes.paragraph))
    uids = _get_node_uids(insert_similar)
    assert len(new_nodes) == 1
    assert new_nodes[0].rawsource == 'Anyway I need more'
    assert original_uids[0] == uids[0]
    assert original_uids[1:] == uids[2:]
