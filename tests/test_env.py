# -*- coding: utf-8 -*-
"""
    test_env
    ~~~~~~~~

    Test the BuildEnvironment class.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys

from util import *

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder

app = env = None
warnings = []

def setup_module():
    global app, env
    app = TestApp(srcdir='(temp)', freshenv=True)
    env = app.env
    env.set_warnfunc(lambda *args: warnings.append(args))

def teardown_module():
    app.cleanup()

def warning_emitted(file, text):
    for warning in warnings:
        if len(warning) == 2 and file in warning[1] and text in warning[0]:
            return True
    return False

# Tests are run in the order they appear in the file, therefore we can
# afford to not run update() in the setup but in its own test

def test_first_update():
    msg, num, it = env.update(app.config, app.srcdir, app.doctreedir, app)
    assert msg.endswith('%d added, 0 changed, 0 removed' % len(env.found_docs))
    docnames = set()
    for docname in it:  # the generator does all the work
        docnames.add(docname)
    assert docnames == env.found_docs == set(env.all_docs)
    # test if exclude_patterns works ok
    assert 'subdir/excluded' not in env.found_docs

def test_images():
    assert warning_emitted('images', 'image file not readable: foo.png')
    assert warning_emitted('images', 'nonlocal image URI found: '
                           'http://www.python.org/logo.png')

    tree = env.get_doctree('images')
    app._warning.reset()
    htmlbuilder = StandaloneHTMLBuilder(app)
    htmlbuilder.post_process_images(tree)
    image_uri_message = "no matching candidate for image URI u'foo.*'"
    if sys.version_info >= (3, 0):
        image_uri_message = remove_unicode_literals(image_uri_message)
    assert image_uri_message in app._warning.content[-1]
    assert set(htmlbuilder.images.keys()) == \
        set(['subdir/img.png', 'img.png', 'subdir/simg.png', 'svgimg.svg'])
    assert set(htmlbuilder.images.values()) == \
        set(['img.png', 'img1.png', 'simg.png', 'svgimg.svg'])

    app._warning.reset()
    latexbuilder = LaTeXBuilder(app)
    latexbuilder.post_process_images(tree)
    assert image_uri_message in app._warning.content[-1]
    assert set(latexbuilder.images.keys()) == \
        set(['subdir/img.png', 'subdir/simg.png', 'img.png', 'img.pdf',
             'svgimg.pdf'])
    assert set(latexbuilder.images.values()) == \
        set(['img.pdf', 'img.png', 'img1.png', 'simg.png', 'svgimg.pdf'])

def test_second_update():
    # delete, add and "edit" (change saved mtime) some files and update again
    env.all_docs['contents'] = 0
    root = path(app.srcdir)
    # important: using "autodoc" because it is the last one to be included in
    # the contents.txt toctree; otherwise section numbers would shift
    (root / 'autodoc.txt').unlink()
    (root / 'new.txt').write_text('New file\n========\n')
    msg, num, it = env.update(app.config, app.srcdir, app.doctreedir, app)
    assert '1 added, 3 changed, 1 removed' in msg
    docnames = set()
    for docname in it:
        docnames.add(docname)
    # "includes" and "images" are in there because they contain references
    # to nonexisting downloadable or image files, which are given another
    # chance to exist
    assert docnames == set(['contents', 'new', 'includes', 'images'])
    assert 'autodoc' not in env.all_docs
    assert 'autodoc' not in env.found_docs

def test_object_inventory():
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
