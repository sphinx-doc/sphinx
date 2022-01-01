"""
    test_project
    ~~~~~~~~~~~~

    Tests project module.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import OrderedDict

import pytest

from sphinx.project import Project


def test_project_discover(rootdir):
    project = Project(rootdir / 'test-root', {})

    docnames = {'autodoc', 'bom', 'extapi', 'extensions', 'footnote', 'images',
                'includes', 'index', 'lists', 'markup', 'math', 'objects',
                'subdir/excluded', 'subdir/images', 'subdir/includes'}
    subdir_docnames = {'subdir/excluded', 'subdir/images', 'subdir/includes'}

    # basic case
    project.source_suffix = ['.txt']
    assert project.discover() == docnames

    # exclude_paths option
    assert project.discover(['subdir/*']) == docnames - subdir_docnames

    # exclude_patterns
    assert project.discover(['.txt', 'subdir/*']) == docnames - subdir_docnames

    # multiple source_suffixes
    project.source_suffix = ['.txt', '.foo']
    assert project.discover() == docnames | {'otherext'}

    # complicated source_suffix
    project.source_suffix = ['.foo.png']
    assert project.discover() == {'img'}

    # templates_path
    project.source_suffix = ['.html']
    assert project.discover() == {'_templates/layout',
                                  '_templates/customsb',
                                  '_templates/contentssb'}

    assert project.discover(['_templates']) == set()


@pytest.mark.sphinx(testroot='basic')
def test_project_path2doc(app):
    project = Project(app.srcdir, app.config.source_suffix)
    assert project.path2doc('index.rst') == 'index'
    assert project.path2doc('index.foo') is None  # unknown extension
    assert project.path2doc('index.foo.rst') == 'index.foo'
    assert project.path2doc('index') is None
    assert project.path2doc('path/to/index.rst') == 'path/to/index'
    assert project.path2doc(app.srcdir / 'to/index.rst') == 'to/index'


@pytest.mark.sphinx(srcdir='project_doc2path', testroot='basic')
def test_project_doc2path(app):
    source_suffix = OrderedDict([('.rst', 'restructuredtext'),
                                 ('.txt', 'restructuredtext')])

    project = Project(app.srcdir, source_suffix)
    assert project.doc2path('index') == (app.srcdir / 'index.rst')

    # first source_suffix is used for missing file
    assert project.doc2path('foo') == (app.srcdir / 'foo.rst')

    # matched source_suffix is used if exists
    (app.srcdir / 'foo.txt').write_text('')
    assert project.doc2path('foo') == (app.srcdir / 'foo.txt')

    # absolute path
    assert project.doc2path('index', basedir=True) == (app.srcdir / 'index.rst')

    # relative path
    assert project.doc2path('index', basedir=False) == 'index.rst'
