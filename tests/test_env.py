# -*- coding: utf-8 -*-
"""
    test_env
    ~~~~~~~~

    Test the BuildEnvironment class.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import *

from sphinx.environment import BuildEnvironment
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder

app = env = None
warnings = []

def setup_module():
    global app, env
    app = TestApp(srcdir='(temp)')
    env = BuildEnvironment(app.srcdir, app.doctreedir, app.config)
    env.set_warnfunc(warnings.append)

def teardown_module():
    app.cleanup()

def warning_emitted(file, text):
    for warning in warnings:
        if file+':' in warning and text in warning:
            return True
    return False

# Tests are run in the order they appear in the file, therefore we can
# afford to not run update() in the setup but in its own test

def test_first_update():
    it = env.update(app.config, app.srcdir, app.doctreedir, app)
    msg = it.next()
    assert msg.endswith('%d added, 0 changed, 0 removed' % len(env.found_docs))
    docnames = set()
    for docname in it:  # the generator does all the work
        docnames.add(docname)
    assert docnames == env.found_docs == set(env.all_docs)

def test_images():
    assert warning_emitted('images.txt', 'Image file not readable: foo.png')
    assert warning_emitted('images.txt', 'Nonlocal image URI found: '
                           'http://www.python.org/logo.png')

    tree = env.get_doctree('images')
    app._warning.reset()
    htmlbuilder = StandaloneHTMLBuilder(app, env)
    htmlbuilder.post_process_images(tree)
    assert "no matching candidate for image URI u'foo.*'" in app._warning.content[-1]
    assert set(htmlbuilder.images.keys()) == set(['subdir/img.png', 'img.png',
                                                  'subdir/simg.png'])
    assert set(htmlbuilder.images.values()) == set(['img.png', 'img1.png',
                                                    'simg.png'])

    app._warning.reset()
    latexbuilder = LaTeXBuilder(app, env)
    latexbuilder.post_process_images(tree)
    assert "no matching candidate for image URI u'foo.*'" in app._warning.content[-1]
    assert set(latexbuilder.images.keys()) == set(['subdir/img.png', 'subdir/simg.png',
                                                   'img.png', 'img.pdf'])
    assert set(latexbuilder.images.values()) == set(['img.pdf', 'img.png',
                                                     'img1.png', 'simg.png'])

def test_second_update():
    # delete, add and "edit" (change saved mtime) some files and update again
    env.all_docs['contents'] = 0
    root = path(app.srcdir)
    (root / 'images.txt').unlink()
    (root / 'new.txt').write_text('New file\n========\n')
    it = env.update(app.config, app.srcdir, app.doctreedir, app)
    msg = it.next()
    assert '1 added, 2 changed, 1 removed' in msg
    docnames = set()
    for docname in it:
        docnames.add(docname)
    # "includes" is in there because it contains a reference to a nonexisting
    # downloadable file, which is given another chance to exist
    assert docnames == set(['contents', 'new', 'includes'])
    assert 'images' not in env.all_docs
    assert 'images' not in env.found_docs

def test_object_inventory():
    refs = env.descrefs

    assert 'func_without_module' in refs
    assert refs['func_without_module'] == ('desc', 'function')
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

    assert 'mod' in env.modules
    assert env.modules['mod'] == ('desc', 'Module synopsis.', 'UNIX', False)
