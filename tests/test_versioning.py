"""
    test_versioning
    ~~~~~~~~~~~~~~~

    Test the versioning implementation.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pickle

import pytest

from sphinx import addnodes
from sphinx.testing.util import SphinxTestApp
from sphinx.versioning import add_uids, get_ratio, merge_doctrees

try:
    from docutils.nodes import meta
except ImportError:
    # docutils-0.18.0 or older
    from docutils.parsers.rst.directives.html import MetaBody
    meta = MetaBody.meta

app = original = original_uids = None


@pytest.fixture(scope='module', autouse=True)
def setup_module(rootdir, sphinx_test_tempdir):
    global app, original, original_uids
    srcdir = sphinx_test_tempdir / 'test-versioning'
    if not srcdir.exists():
        (rootdir / 'test-versioning').copytree(srcdir)
    app = SphinxTestApp(srcdir=srcdir)
    app.builder.env.app = app
    app.connect('doctree-resolved', on_doctree_resolved)
    app.build()
    original = doctrees['original']
    original_uids = [n.uid for n in add_uids(original, is_paragraph)]
    yield
    app.cleanup()


doctrees = {}


def on_doctree_resolved(app, doctree, docname):
    doctrees[docname] = doctree


def is_paragraph(node):
    return node.__class__.__name__ == 'paragraph'


def test_get_ratio():
    assert get_ratio('', 'a')
    assert get_ratio('a', '')


def test_add_uids():
    assert len(original_uids) == 3


def test_picklablility():
    # we have to modify the doctree so we can pickle it
    copy = original.copy()
    copy.reporter = None
    copy.transformer = None
    copy.settings.warning_stream = None
    copy.settings.env = None
    copy.settings.record_dependencies = None
    for metanode in copy.findall(meta):
        metanode.__class__ = addnodes.meta
    loaded = pickle.loads(pickle.dumps(copy, pickle.HIGHEST_PROTOCOL))
    assert all(getattr(n, 'uid', False) for n in loaded.findall(is_paragraph))


def test_modified():
    modified = doctrees['modified']
    new_nodes = list(merge_doctrees(original, modified, is_paragraph))
    uids = [n.uid for n in modified.findall(is_paragraph)]
    assert not new_nodes
    assert original_uids == uids


def test_added():
    added = doctrees['added']
    new_nodes = list(merge_doctrees(original, added, is_paragraph))
    uids = [n.uid for n in added.findall(is_paragraph)]
    assert len(new_nodes) == 1
    assert original_uids == uids[:-1]


def test_deleted():
    deleted = doctrees['deleted']
    new_nodes = list(merge_doctrees(original, deleted, is_paragraph))
    uids = [n.uid for n in deleted.findall(is_paragraph)]
    assert not new_nodes
    assert original_uids[::2] == uids


def test_deleted_end():
    deleted_end = doctrees['deleted_end']
    new_nodes = list(merge_doctrees(original, deleted_end, is_paragraph))
    uids = [n.uid for n in deleted_end.findall(is_paragraph)]
    assert not new_nodes
    assert original_uids[:-1] == uids


def test_insert():
    insert = doctrees['insert']
    new_nodes = list(merge_doctrees(original, insert, is_paragraph))
    uids = [n.uid for n in insert.findall(is_paragraph)]
    assert len(new_nodes) == 1
    assert original_uids[0] == uids[0]
    assert original_uids[1:] == uids[2:]


def test_insert_beginning():
    insert_beginning = doctrees['insert_beginning']
    new_nodes = list(merge_doctrees(original, insert_beginning, is_paragraph))
    uids = [n.uid for n in insert_beginning.findall(is_paragraph)]
    assert len(new_nodes) == 1
    assert len(uids) == 4
    assert original_uids == uids[1:]
    assert original_uids[0] != uids[0]


def test_insert_similar():
    insert_similar = doctrees['insert_similar']
    new_nodes = list(merge_doctrees(original, insert_similar, is_paragraph))
    uids = [n.uid for n in insert_similar.findall(is_paragraph)]
    assert len(new_nodes) == 1
    assert new_nodes[0].rawsource == 'Anyway I need more'
    assert original_uids[0] == uids[0]
    assert original_uids[1:] == uids[2:]
