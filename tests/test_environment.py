"""
    test_env
    ~~~~~~~~

    Test the BuildEnvironment class.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import pytest

from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder
from sphinx.testing.comparer import PathComparer


@pytest.mark.sphinx('dummy')
def test_images(app):
    app.build()

    tree = app.env.get_doctree('images')
    htmlbuilder = StandaloneHTMLBuilder(app)
    htmlbuilder.set_environment(app.env)
    htmlbuilder.init()
    htmlbuilder.imgpath = 'dummy'
    htmlbuilder.post_process_images(tree)
    assert set(htmlbuilder.images.keys()) == \
        {'subdir/img.png', 'img.png', 'subdir/simg.png', 'svgimg.svg', 'img.foo.png'}
    assert set(htmlbuilder.images.values()) == \
        {'img.png', 'img1.png', 'simg.png', 'svgimg.svg', 'img.foo.png'}

    latexbuilder = LaTeXBuilder(app)
    latexbuilder.set_environment(app.env)
    latexbuilder.init()
    latexbuilder.post_process_images(tree)
    assert set(latexbuilder.images.keys()) == \
        {'subdir/img.png', 'subdir/simg.png', 'img.png', 'img.pdf',
         'svgimg.pdf', 'img.foo.png'}
    assert set(latexbuilder.images.values()) == \
        {'img.pdf', 'img.png', 'img1.png', 'simg.png',
         'svgimg.pdf', 'img.foo.png'}


@pytest.mark.sphinx('dummy')
def test_object_inventory(app):
    app.build()
    refs = app.env.domaindata['py']['objects']

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

    assert app.env.domaindata['py']['modules']['mod'] == \
        ('objects', 'Module synopsis.', 'UNIX', False)

    assert app.env.domains['py'].data is app.env.domaindata['py']
    assert app.env.domains['c'].data is app.env.domaindata['c']


@pytest.mark.sphinx('dummy', testroot='basic')
def test_env_relfn2path(app):
    # relative filename and root document
    relfn, absfn = app.env.relfn2path('logo.jpg', 'index')
    assert relfn == 'logo.jpg'
    assert absfn == app.srcdir / 'logo.jpg'

    # absolute filename and root document
    relfn, absfn = app.env.relfn2path('/logo.jpg', 'index')
    assert relfn == 'logo.jpg'
    assert absfn == app.srcdir / 'logo.jpg'

    # relative filename and a document in subdir
    relfn, absfn = app.env.relfn2path('logo.jpg', 'subdir/index')
    assert relfn == PathComparer('subdir/logo.jpg')
    assert absfn == app.srcdir / 'subdir' / 'logo.jpg'

    # absolute filename and a document in subdir
    relfn, absfn = app.env.relfn2path('/logo.jpg', 'subdir/index')
    assert relfn == 'logo.jpg'
    assert absfn == app.srcdir / 'logo.jpg'

    # relative filename having subdir
    relfn, absfn = app.env.relfn2path('images/logo.jpg', 'index')
    assert relfn == 'images/logo.jpg'
    assert absfn == app.srcdir / 'images' / 'logo.jpg'

    # relative path traversal
    relfn, absfn = app.env.relfn2path('../logo.jpg', 'index')
    assert relfn == '../logo.jpg'
    assert absfn == app.srcdir.parent / 'logo.jpg'

    # omit docname (w/ current docname)
    app.env.temp_data['docname'] = 'subdir/document'
    relfn, absfn = app.env.relfn2path('images/logo.jpg')
    assert relfn == PathComparer('subdir/images/logo.jpg')
    assert absfn == app.srcdir / 'subdir' / 'images' / 'logo.jpg'

    # omit docname (w/o current docname)
    app.env.temp_data.clear()
    with pytest.raises(KeyError):
        app.env.relfn2path('images/logo.jpg')
