# -*- coding: utf-8 -*-
"""
    test_env
    ~~~~~~~~

    Test the BuildEnvironment class.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder


@pytest.fixture
def env(app):
    env = app.env
    env.test_warnings = []
    env.set_warnfunc(lambda *args, **kwargs: env.test_warnings.append(args))
    yield env


def warning_emitted(env, file, text):
    for warning in env.test_warnings:
        if len(warning) == 2 and file in warning[1] and text in warning[0]:
            return True
    return False


@pytest.mark.sphinx(srcdir='root-envtest')
def test_first_update(app, env):
    updated = env.update(app.config, app.srcdir, app.doctreedir, app)
    assert set(updated) == env.found_docs == set(env.all_docs)
    # test if exclude_patterns works ok
    assert 'subdir/excluded' not in env.found_docs


@pytest.mark.sphinx(srcdir='root-envtest')
def test_images(app, env):
    env.update(app.config, app.srcdir, app.doctreedir, app)
    assert warning_emitted(
        env, 'images', 'image file not readable: foo.png')
    assert warning_emitted(
        env, 'images',
        'nonlocal image URI found: http://www.python.org/logo.png')

    tree = env.get_doctree('images')
    htmlbuilder = StandaloneHTMLBuilder(app)
    htmlbuilder.imgpath = 'dummy'
    htmlbuilder.post_process_images(tree)
    assert set(htmlbuilder.images.keys()) == \
           {'subdir/img.png', 'img.png', 'subdir/simg.png', 'svgimg.svg',
            'img.foo.png'}
    assert set(htmlbuilder.images.values()) == \
           {'img.png', 'img1.png', 'simg.png', 'svgimg.svg', 'img.foo.png'}

    latexbuilder = LaTeXBuilder(app)
    latexbuilder.post_process_images(tree)
    assert set(latexbuilder.images.keys()) == \
           {'subdir/img.png', 'subdir/simg.png', 'img.png', 'img.pdf',
            'svgimg.pdf', 'img.foo.png'}
    assert set(latexbuilder.images.values()) == \
           {'img.pdf', 'img.png', 'img1.png', 'simg.png',
            'svgimg.pdf', 'img.foo.png'}


@pytest.mark.sphinx(srcdir='root-envtest')
def test_second_update(app, env):
    env.update(app.config, app.srcdir, app.doctreedir, app)
    # delete, add and "edit" (change saved mtime) some files and update again
    env.all_docs['contents'] = 0
    root = app.srcdir
    # important: using "autodoc" because it is the last one to be included in
    # the contents.txt toctree; otherwise section numbers would shift
    (root / 'autodoc.txt').unlink()
    (root / 'new.txt').write_text('New file\n========\n')
    updated = env.update(app.config, app.srcdir, app.doctreedir, app)
    # "includes" and "images" are in there because they contain references
    # to nonexisting downloadable or image files, which are given another
    # chance to exist
    assert set(updated) == {'contents', 'new', 'includes', 'images'}
    assert 'autodoc' not in env.all_docs
    assert 'autodoc' not in env.found_docs


@pytest.mark.sphinx(srcdir='root-envtest')
def test_env_read_docs(app, env):
    """By default, docnames are read in alphanumeric order"""
    def on_env_read_docs_1(app, env, docnames):
        pass

    app.connect('env-before-read-docs', on_env_read_docs_1)

    read_docnames = env.update(app.config, app.srcdir, app.doctreedir, app)
    assert len(read_docnames) > 2 and read_docnames == sorted(read_docnames)

    def on_env_read_docs_2(app, env, docnames):
        docnames.remove('images')

    app.connect('env-before-read-docs', on_env_read_docs_2)

    read_docnames = env.update(app.config, app.srcdir, app.doctreedir, app)
    assert len(read_docnames) == 2


@pytest.mark.sphinx(srcdir='root-envtest')
def test_object_inventory(app, env):
    env.update(app.config, app.srcdir, app.doctreedir, app)
    refs = env.domaindata['py']['objects']

    assert 'func_without_module' in refs
    assert refs['func_without_module'] == ('objects', 'function')
    assert 'func_without_module2' in refs
    assert 'mod.func_in_module' in refs
    assert 'mod.Cls' in refs
    assert 'mod.Cls.meth1' in refs
    assert 'mod.Cls.meth2' in refs
    assert 'mod.Cls.meths' in refs

    assert 'mod.Error' not in refs
    assert 'errmod.Error' in refs

    assert 'func_in_module' not in refs
    assert 'func_noindex' not in refs

    assert env.domaindata['py']['modules']['mod'] == \
        ('objects', 'Module synopsis.', 'UNIX', False)

    assert env.domains['py'].data is env.domaindata['py']
    assert env.domains['c'].data is env.domaindata['c']
