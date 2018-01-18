# -*- coding: utf-8 -*-
"""
    test_project
    ~~~~~~~~~~~~

    Tests project module.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from sphinx.project import Project


def test_project_discovery(rootdir):
    project = Project(rootdir / 'test-root', {})

    docnames = {'autodoc', 'bom', 'extapi', 'extensions', 'footnote', 'images',
                'includes', 'index', 'lists', 'markup', 'math', 'objects',
                'subdir/excluded', 'subdir/images', 'subdir/includes'}
    subdir_docnames = {'subdir/excluded', 'subdir/images', 'subdir/includes'}

    # basic case
    project.source_suffix = ['.txt']
    assert project.discovery() == docnames

    # exclude_paths option
    assert project.discovery(['subdir/*']) == docnames - subdir_docnames

    # exclude_patterns
    assert project.discovery(['.txt', 'subdir/*']) == docnames - subdir_docnames

    # multiple source_suffixes
    project.source_suffix = ['.txt', '.foo']
    assert project.discovery() == docnames | {'otherext'}

    # complicated source_suffix
    project.source_suffix = ['.foo.png']
    assert project.discovery() == {'img'}

    # templates_path
    project.source_suffix = ['.html']
    assert project.discovery() == {'_templates/layout',
                                   '_templates/customsb',
                                   '_templates/contentssb'}

    assert project.discovery(['_templates']) == set()
