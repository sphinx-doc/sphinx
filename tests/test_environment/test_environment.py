"""Test the BuildEnvironment class."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder
from sphinx.config import Config
from sphinx.environment import (
    CONFIG_CHANGED,
    CONFIG_EXTENSIONS_CHANGED,
    CONFIG_NEW,
    CONFIG_OK,
    _differing_config_keys,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sphinx.testing.fixtures import _app_params
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('dummy', testroot='basic', copy_test_root=True)
def test_config_status(
    make_app: Callable[..., SphinxTestApp], app_params: _app_params
) -> None:
    args, kwargs = app_params

    # clean build
    app1 = make_app(*args, freshenv=True, **kwargs)
    assert app1.env.config_status == CONFIG_NEW
    app1.build()
    output = strip_escape_sequences(app1.status.getvalue())
    # assert 'The configuration has changed' not in output
    assert '[new config] 1 added' in output

    # incremental build (no config changed)
    app2 = make_app(*args, **kwargs)
    assert app2.env.config_status == CONFIG_OK
    app2.build()
    output = strip_escape_sequences(app2.status.getvalue())
    assert 'The configuration has changed' not in output
    assert '0 added, 0 changed, 0 removed' in output

    # incremental build (config entry changed)
    app3 = make_app(*args, confoverrides={'root_doc': 'indexx'}, **kwargs)
    fname = app3.srcdir / 'index.rst'
    other_fname = app3.srcdir / 'indexx.rst'
    assert fname.is_file()
    shutil.move(fname, other_fname)
    assert app3.env.config_status == CONFIG_CHANGED
    app3.build()
    shutil.move(other_fname, fname)
    output = strip_escape_sequences(app3.status.getvalue())
    assert 'The configuration has changed' in output
    assert "[config changed ('master_doc')] 1 added," in output

    # incremental build (extension changed)
    app4 = make_app(
        *args, confoverrides={'extensions': ['sphinx.ext.autodoc']}, **kwargs
    )
    assert app4.env.config_status == CONFIG_EXTENSIONS_CHANGED
    app4.build()
    want_str = "[extensions changed ('sphinx.ext.autodoc')] 1 added"
    output = strip_escape_sequences(app4.status.getvalue())
    assert 'The configuration has changed' not in output
    assert want_str in output


@pytest.mark.sphinx('dummy', testroot='root')
def test_images(app: SphinxTestApp) -> None:
    app.build()

    tree = app.env.get_doctree('images')
    htmlbuilder = StandaloneHTMLBuilder(app, app.env)
    htmlbuilder.init()
    htmlbuilder.imgpath = 'dummy'
    htmlbuilder.post_process_images(tree)
    assert set(htmlbuilder.images.keys()) == {
        'subdir/img.png',
        'img.png',
        'subdir/simg.png',
        'svgimg.svg',
        'img.foo.png',
    }
    assert set(htmlbuilder.images.values()) == {
        'img.png',
        'img1.png',
        'simg.png',
        'svgimg.svg',
        'img.foo.png',
    }

    latexbuilder = LaTeXBuilder(app, app.env)
    latexbuilder.init()
    latexbuilder.post_process_images(tree)
    assert set(latexbuilder.images.keys()) == {
        'subdir/img.png',
        'subdir/simg.png',
        'img.png',
        'img.pdf',
        'svgimg.pdf',
        'img.foo.png',
    }
    assert set(latexbuilder.images.values()) == {
        'img.pdf',
        'img.png',
        'img1.png',
        'simg.png',
        'svgimg.pdf',
        'img.foo.png',
    }


@pytest.mark.sphinx('dummy', testroot='root')
def test_object_inventory(app: SphinxTestApp) -> None:
    app.build()
    refs = app.env.domaindata['py']['objects']

    assert 'func_without_module' in refs
    assert refs['func_without_module'] == (
        'objects',
        'func_without_module',
        'function',
        False,
    )
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

    assert app.env.domaindata['py']['modules']['mod'] == (
        'objects',
        'module-mod',
        'Module synopsis.',
        'UNIX',
        False,
    )

    assert app.env.domains.python_domain.data is app.env.domaindata['py']
    assert app.env.domains.c_domain.data is app.env.domaindata['c']


@pytest.mark.sphinx('dummy', testroot='basic')
def test_env_relfn2path(app: SphinxTestApp) -> None:
    # relative filename and root document
    relfn, absfn = app.env.relfn2path('logo.jpg', 'index')
    assert relfn == 'logo.jpg'
    assert absfn == str(app.srcdir / 'logo.jpg')

    # absolute filename and root document
    relfn, absfn = app.env.relfn2path('/logo.jpg', 'index')
    assert relfn == 'logo.jpg'
    assert absfn == str(app.srcdir / 'logo.jpg')

    # relative filename and a document in subdir
    relfn, absfn = app.env.relfn2path('logo.jpg', 'subdir/index')
    assert Path(relfn) == Path('subdir/logo.jpg')
    assert absfn == str(app.srcdir / 'subdir' / 'logo.jpg')

    # absolute filename and a document in subdir
    relfn, absfn = app.env.relfn2path('/logo.jpg', 'subdir/index')
    assert relfn == 'logo.jpg'
    assert absfn == str(app.srcdir / 'logo.jpg')

    # relative filename having subdir
    relfn, absfn = app.env.relfn2path('images/logo.jpg', 'index')
    assert relfn == 'images/logo.jpg'
    assert absfn == str(app.srcdir / 'images' / 'logo.jpg')

    # relative path traversal
    relfn, absfn = app.env.relfn2path('../logo.jpg', 'index')
    assert relfn == '../logo.jpg'
    assert absfn == str(app.srcdir.parent / 'logo.jpg')

    # relative path traversal
    relfn, absfn = app.env.relfn2path('subdir/../logo.jpg', 'index')
    assert relfn == 'logo.jpg'
    assert absfn == str(app.srcdir / 'logo.jpg')

    # omit docname (w/ current docname)
    app.env.current_document.docname = 'subdir/document'
    relfn, absfn = app.env.relfn2path('images/logo.jpg')
    assert Path(relfn) == Path('subdir/images/logo.jpg')
    assert absfn == str(app.srcdir / 'subdir' / 'images' / 'logo.jpg')

    # omit docname (w/o current docname)
    app.env.current_document.clear()
    with pytest.raises(KeyError, match=r"^'docname'$"):
        app.env.relfn2path('images/logo.jpg')


def test_differing_config_keys() -> None:
    diff = _differing_config_keys

    old = Config({'project': 'old'})
    new = Config({'project': 'new'})
    assert diff(old, new) == frozenset({'project'})

    old = Config({'project': 'project', 'release': 'release'})
    new = Config({'project': 'project', 'version': 'version'})
    assert diff(old, new) == frozenset({'release', 'version'})

    old = Config({'project': 'project', 'release': 'release'})
    new = Config({'project': 'project'})
    assert diff(old, new) == frozenset({'release'})

    old = Config({'project': 'project'})
    new = Config({'project': 'project', 'version': 'version'})
    assert diff(old, new) == frozenset({'version'})

    old = Config({'project': 'project', 'release': 'release', 'version': 'version'})
    new = Config({'project': 'project', 'release': 'release', 'version': 'version'})
    assert diff(old, new) == frozenset()

    old = Config({'project': 'old', 'release': 'release'})
    new = Config({'project': 'new', 'version': 'version'})
    assert diff(old, new) == frozenset({'project', 'release', 'version'})
