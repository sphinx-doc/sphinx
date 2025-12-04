"""Tests project module."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from sphinx.project import Project

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp

DOCNAMES = {
    'autodoc',
    'bom',
    'extapi',
    'extensions',
    'footnote',
    'images',
    'includes',
    'index',
    'lists',
    'markup',
    'math',
    'objects',
    'subdir/excluded',
    'subdir/images',
    'subdir/includes',
}
SUBDIR_DOCNAMES = {'subdir/excluded', 'subdir/images', 'subdir/includes'}


def test_project_discover_basic(rootdir: Path) -> None:
    # basic case
    project = Project(rootdir / 'test-root', ['.txt'])
    assert project.discover() == DOCNAMES


def test_project_discover_exclude_patterns(rootdir: Path) -> None:
    project = Project(rootdir / 'test-root', ['.txt'])

    # exclude_paths option
    assert project.discover(['subdir/*']) == DOCNAMES - SUBDIR_DOCNAMES
    assert project.discover(['.txt', 'subdir/*']) == DOCNAMES - SUBDIR_DOCNAMES


def test_project_discover_multiple_suffixes(rootdir: Path) -> None:
    # multiple source_suffixes
    project = Project(rootdir / 'test-root', ['.txt', '.foo'])
    assert project.discover() == DOCNAMES | {'otherext'}


def test_project_discover_complicated_suffix(rootdir: Path) -> None:
    # complicated source_suffix
    project = Project(rootdir / 'test-root', ['.foo.png'])
    assert project.discover() == {'img'}


def test_project_discover_templates_path(rootdir: Path) -> None:
    # templates_path
    project = Project(rootdir / 'test-root', ['.html'])
    assert project.discover() == {
        '_templates/layout',
        '_templates/customsb',
        '_templates/contentssb',
    }

    assert project.discover(['_templates']) == set()


def test_project_path2doc(rootdir: Path) -> None:
    project = Project(rootdir / 'test-basic', {'.rst': 'restructuredtext'})
    assert project.path2doc('index.rst') == 'index'
    assert project.path2doc('index.foo') is None  # unknown extension
    assert project.path2doc('index.foo.rst') == 'index.foo'
    assert project.path2doc('index') is None
    assert project.path2doc('path/to/index.rst') == 'path/to/index'
    assert project.path2doc(rootdir / 'test-basic' / 'to/index.rst') == 'to/index'


@pytest.mark.sphinx(
    'html',
    testroot='basic',
    srcdir='project_doc2path',
)
def test_project_doc2path(app: SphinxTestApp) -> None:
    source_suffix = {'.rst': 'restructuredtext', '.txt': 'restructuredtext'}

    project = Project(app.srcdir, source_suffix)
    project.discover()

    # absolute path
    assert project.doc2path('index', absolute=True) == app.srcdir / 'index.rst'

    # relative path
    assert project.doc2path('index', absolute=False) == Path('index.rst')

    # first source_suffix is used for missing file
    assert project.doc2path('foo', absolute=False) == Path('foo.rst')

    # matched source_suffix is used if exists
    (app.srcdir / 'bar.txt').touch()
    project.discover()
    assert project.doc2path('bar', absolute=False) == Path('bar.txt')
