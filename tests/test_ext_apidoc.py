"""
    test_apidoc
    ~~~~~~~~~~~

    Test the sphinx.apidoc module.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import namedtuple

import pytest

from sphinx.ext.apidoc import main as apidoc_main
from sphinx.testing.path import path


@pytest.fixture()
def apidoc(rootdir, tempdir, apidoc_params):
    _, kwargs = apidoc_params
    coderoot = rootdir / kwargs.get('coderoot', 'test-root')
    outdir = tempdir / 'out'
    excludes = [coderoot / e for e in kwargs.get('excludes', [])]
    args = ['-o', outdir, '-F', coderoot] + excludes + kwargs.get('options', [])
    apidoc_main(args)
    return namedtuple('apidoc', 'coderoot,outdir')(coderoot, outdir)


@pytest.fixture
def apidoc_params(request):
    if hasattr(request.node, 'iter_markers'):  # pytest-3.6.0 or newer
        markers = request.node.iter_markers("apidoc")
    else:
        markers = request.node.get_marker("apidoc")
    pargs = {}
    kwargs = {}

    if markers is not None:
        for info in reversed(list(markers)):
            for i, a in enumerate(info.args):
                pargs[i] = a
            kwargs.update(info.kwargs)

    args = [pargs[i] for i in sorted(pargs.keys())]
    return args, kwargs


@pytest.mark.apidoc(coderoot='test-root')
def test_simple(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'index.rst').isfile()

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())


@pytest.mark.apidoc(
    coderoot='test-apidoc-pep420/a',
    options=["--implicit-namespaces"],
)
def test_pep_0420_enabled(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'a.b.c.rst').isfile()
    assert (outdir / 'a.b.e.rst').isfile()
    assert (outdir / 'a.b.x.rst').isfile()

    with open(outdir / 'a.b.c.rst') as f:
        rst = f.read()
        assert "automodule:: a.b.c.d\n" in rst
        assert "automodule:: a.b.c\n" in rst

    with open(outdir / 'a.b.e.rst') as f:
        rst = f.read()
        assert "automodule:: a.b.e.f\n" in rst

    with open(outdir / 'a.b.x.rst') as f:
        rst = f.read()
        assert "automodule:: a.b.x.y\n" in rst
        assert "automodule:: a.b.x\n" not in rst

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())

    builddir = outdir / '_build' / 'text'
    assert (builddir / 'a.b.c.txt').isfile()
    assert (builddir / 'a.b.e.txt').isfile()
    assert (builddir / 'a.b.x.txt').isfile()

    with open(builddir / 'a.b.c.txt') as f:
        txt = f.read()
        assert "a.b.c package\n" in txt

    with open(builddir / 'a.b.e.txt') as f:
        txt = f.read()
        assert "a.b.e.f module\n" in txt

    with open(builddir / 'a.b.x.txt') as f:
        txt = f.read()
        assert "a.b.x namespace\n" in txt


@pytest.mark.apidoc(
    coderoot='test-apidoc-pep420/a',
    options=["--implicit-namespaces", "--separate"],
)
def test_pep_0420_enabled_separate(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'a.b.c.rst').isfile()
    assert (outdir / 'a.b.e.rst').isfile()
    assert (outdir / 'a.b.e.f.rst').isfile()
    assert (outdir / 'a.b.x.rst').isfile()
    assert (outdir / 'a.b.x.y.rst').isfile()

    with open(outdir / 'a.b.c.rst') as f:
        rst = f.read()
        assert ".. toctree::\n   :maxdepth: 4\n\n   a.b.c.d\n" in rst

    with open(outdir / 'a.b.e.rst') as f:
        rst = f.read()
        assert ".. toctree::\n   :maxdepth: 4\n\n   a.b.e.f\n" in rst

    with open(outdir / 'a.b.x.rst') as f:
        rst = f.read()
        assert ".. toctree::\n   :maxdepth: 4\n\n   a.b.x.y\n" in rst

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())

    builddir = outdir / '_build' / 'text'
    assert (builddir / 'a.b.c.txt').isfile()
    assert (builddir / 'a.b.e.txt').isfile()
    assert (builddir / 'a.b.e.f.txt').isfile()
    assert (builddir / 'a.b.x.txt').isfile()
    assert (builddir / 'a.b.x.y.txt').isfile()

    with open(builddir / 'a.b.c.txt') as f:
        txt = f.read()
        assert "a.b.c package\n" in txt

    with open(builddir / 'a.b.e.f.txt') as f:
        txt = f.read()
        assert "a.b.e.f module\n" in txt

    with open(builddir / 'a.b.x.txt') as f:
        txt = f.read()
        assert "a.b.x namespace\n" in txt


@pytest.mark.apidoc(coderoot='test-apidoc-pep420/a')
def test_pep_0420_disabled(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert not (outdir / 'a.b.c.rst').exists()
    assert not (outdir / 'a.b.x.rst').exists()

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())


@pytest.mark.apidoc(
    coderoot='test-apidoc-pep420/a/b')
def test_pep_0420_disabled_top_level_verify(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'c.rst').isfile()
    assert not (outdir / 'x.rst').exists()

    with open(outdir / 'c.rst') as f:
        rst = f.read()
        assert "c package\n" in rst
        assert "automodule:: c.d\n" in rst
        assert "automodule:: c\n" in rst

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())


@pytest.mark.apidoc(
    coderoot='test-apidoc-trailing-underscore')
def test_trailing_underscore(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'package_.rst').isfile()

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())

    builddir = outdir / '_build' / 'text'
    with open(builddir / 'package_.txt') as f:
        rst = f.read()
        assert "package_ package\n" in rst
        assert "package_.module_ module\n" in rst


@pytest.mark.apidoc(
    coderoot='test-apidoc-pep420/a',
    excludes=["b/c/d.py", "b/e/f.py", "b/e/__init__.py"],
    options=["--implicit-namespaces", "--separate"],
)
def test_excludes(apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'a.rst').isfile()
    assert (outdir / 'a.b.rst').isfile()
    assert (outdir / 'a.b.c.rst').isfile()  # generated because not empty
    assert not (outdir / 'a.b.e.rst').isfile()  # skipped because of empty after excludes
    assert (outdir / 'a.b.x.rst').isfile()
    assert (outdir / 'a.b.x.y.rst').isfile()


@pytest.mark.apidoc(
    coderoot='test-apidoc-pep420/a',
    excludes=["b/e"],
    options=["--implicit-namespaces", "--separate"],
)
def test_excludes_subpackage_should_be_skipped(apidoc):
    """Subpackage exclusion should work."""
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'a.rst').isfile()
    assert (outdir / 'a.b.rst').isfile()
    assert (outdir / 'a.b.c.rst').isfile()  # generated because not empty
    assert not (outdir / 'a.b.e.f.rst').isfile()  # skipped because 'b/e' subpackage is skipped


@pytest.mark.apidoc(
    coderoot='test-apidoc-pep420/a',
    excludes=["b/e/f.py"],
    options=["--implicit-namespaces", "--separate"],
)
def test_excludes_module_should_be_skipped(apidoc):
    """Module exclusion should work."""
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'a.rst').isfile()
    assert (outdir / 'a.b.rst').isfile()
    assert (outdir / 'a.b.c.rst').isfile()  # generated because not empty
    assert not (outdir / 'a.b.e.f.rst').isfile()  # skipped because of empty after excludes


@pytest.mark.apidoc(
    coderoot='test-apidoc-pep420/a',
    excludes=[],
    options=["--implicit-namespaces", "--separate"],
)
def test_excludes_module_should_not_be_skipped(apidoc):
    """Module should be included if no excludes are used."""
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'a.rst').isfile()
    assert (outdir / 'a.b.rst').isfile()
    assert (outdir / 'a.b.c.rst').isfile()  # generated because not empty
    assert (outdir / 'a.b.e.f.rst').isfile()  # skipped because of empty after excludes


@pytest.mark.apidoc(
    coderoot='test-root',
    options=[
        '--doc-project', 'プロジェクト名',
        '--doc-author', '著者名',
        '--doc-version', 'バージョン',
        '--doc-release', 'リリース',
    ],
)
def test_multibyte_parameters(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'index.rst').isfile()

    conf_py = (outdir / 'conf.py').read_text()
    assert "project = 'プロジェクト名'" in conf_py
    assert "author = '著者名'" in conf_py
    assert "version = 'バージョン'" in conf_py
    assert "release = 'リリース'" in conf_py

    app = make_app('text', srcdir=outdir)
    app.build()
    print(app._status.getvalue())
    print(app._warning.getvalue())


@pytest.mark.apidoc(
    coderoot='test-root',
    options=['--ext-mathjax'],
)
def test_extension_parsed(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()

    with open(outdir / 'conf.py') as f:
        rst = f.read()
        assert "sphinx.ext.mathjax" in rst


@pytest.mark.apidoc(
    coderoot='test-apidoc-toc/mypackage',
    options=["--implicit-namespaces"],
)
def test_toc_all_references_should_exist_pep420_enabled(make_app, apidoc):
    """All references in toc should exist. This test doesn't say if
       directories with empty __init__.py and and nothing else should be
       skipped, just ensures consistency between what's referenced in the toc
       and what is created. This is the variant with pep420 enabled.
    """
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()

    toc = extract_toc(outdir / 'mypackage.rst')

    refs = [l.strip() for l in toc.splitlines() if l.strip()]
    found_refs = []
    missing_files = []
    for ref in refs:
        if ref and ref[0] in (':', '#'):
            continue
        found_refs.append(ref)
        filename = "{}.rst".format(ref)
        if not (outdir / filename).isfile():
            missing_files.append(filename)

    assert len(missing_files) == 0, \
        'File(s) referenced in TOC not found: {}\n' \
        'TOC:\n{}'.format(", ".join(missing_files), toc)


@pytest.mark.apidoc(
    coderoot='test-apidoc-toc/mypackage',
)
def test_toc_all_references_should_exist_pep420_disabled(make_app, apidoc):
    """All references in toc should exist. This test doesn't say if
       directories with empty __init__.py and and nothing else should be
       skipped, just ensures consistency between what's referenced in the toc
       and what is created. This is the variant with pep420 disabled.
    """
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()

    toc = extract_toc(outdir / 'mypackage.rst')

    refs = [l.strip() for l in toc.splitlines() if l.strip()]
    found_refs = []
    missing_files = []
    for ref in refs:
        if ref and ref[0] in (':', '#'):
            continue
        filename = "{}.rst".format(ref)
        found_refs.append(ref)
        if not (outdir / filename).isfile():
            missing_files.append(filename)

    assert len(missing_files) == 0, \
        'File(s) referenced in TOC not found: {}\n' \
        'TOC:\n{}'.format(", ".join(missing_files), toc)


def extract_toc(path):
    """Helper: Extract toc section from package rst file"""
    with open(path) as f:
        rst = f.read()

    # Read out the part containing the toctree
    toctree_start = "\n.. toctree::\n"
    toctree_end = "\nSubmodules"

    start_idx = rst.index(toctree_start)
    end_idx = rst.index(toctree_end, start_idx)
    toctree = rst[start_idx + len(toctree_start):end_idx]

    return toctree


@pytest.mark.apidoc(
    coderoot='test-apidoc-subpackage-in-toc',
    options=['--separate']
)
def test_subpackage_in_toc(make_app, apidoc):
    """Make sure that empty subpackages with non-empty subpackages in them
       are not skipped (issue #4520)
    """
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()

    assert (outdir / 'parent.rst').isfile()
    with open(outdir / 'parent.rst') as f:
        parent = f.read()
    assert 'parent.child' in parent

    assert (outdir / 'parent.child.rst').isfile()
    with open(outdir / 'parent.child.rst') as f:
        parent_child = f.read()
    assert 'parent.child.foo' in parent_child

    assert (outdir / 'parent.child.foo.rst').isfile()


def test_private(tempdir):
    (tempdir / 'hello.py').write_text('')
    (tempdir / '_world.py').write_text('')

    # without --private option
    apidoc_main(['-o', tempdir, tempdir])
    assert (tempdir / 'hello.rst').exists()
    assert ':private-members:' not in (tempdir / 'hello.rst').read_text()
    assert not (tempdir / '_world.rst').exists()

    # with --private option
    apidoc_main(['--private', '-f', '-o', tempdir, tempdir])
    assert (tempdir / 'hello.rst').exists()
    assert ':private-members:' in (tempdir / 'hello.rst').read_text()
    assert (tempdir / '_world.rst').exists()


def test_toc_file(tempdir):
    outdir = path(tempdir)
    (outdir / 'module').makedirs()
    (outdir / 'example.py').write_text('')
    (outdir / 'module' / 'example.py').write_text('')
    apidoc_main(['-o', tempdir, tempdir])
    assert (outdir / 'modules.rst').exists()

    content = (outdir / 'modules.rst').read_text()
    assert content == ("test_toc_file0\n"
                       "==============\n"
                       "\n"
                       ".. toctree::\n"
                       "   :maxdepth: 4\n"
                       "\n"
                       "   example\n")


def test_module_file(tempdir):
    outdir = path(tempdir)
    (outdir / 'example.py').write_text('')
    apidoc_main(['-o', tempdir, tempdir])
    assert (outdir / 'example.rst').exists()

    content = (outdir / 'example.rst').read_text()
    assert content == ("example module\n"
                       "==============\n"
                       "\n"
                       ".. automodule:: example\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n")


def test_module_file_noheadings(tempdir):
    outdir = path(tempdir)
    (outdir / 'example.py').write_text('')
    apidoc_main(['--no-headings', '-o', tempdir, tempdir])
    assert (outdir / 'example.rst').exists()

    content = (outdir / 'example.rst').read_text()
    assert content == (".. automodule:: example\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n")


def test_package_file(tempdir):
    outdir = path(tempdir)
    (outdir / 'testpkg').makedirs()
    (outdir / 'testpkg' / '__init__.py').write_text('')
    (outdir / 'testpkg' / 'hello.py').write_text('')
    (outdir / 'testpkg' / 'world.py').write_text('')
    (outdir / 'testpkg' / 'subpkg').makedirs()
    (outdir / 'testpkg' / 'subpkg' / '__init__.py').write_text('')
    apidoc_main(['-o', tempdir, tempdir / 'testpkg'])
    assert (outdir / 'testpkg.rst').exists()
    assert (outdir / 'testpkg.subpkg.rst').exists()

    content = (outdir / 'testpkg.rst').read_text()
    assert content == ("testpkg package\n"
                       "===============\n"
                       "\n"
                       "Subpackages\n"
                       "-----------\n"
                       "\n"
                       ".. toctree::\n"
                       "   :maxdepth: 4\n"
                       "\n"
                       "   testpkg.subpkg\n"
                       "\n"
                       "Submodules\n"
                       "----------\n"
                       "\n"
                       "testpkg.hello module\n"
                       "--------------------\n"
                       "\n"
                       ".. automodule:: testpkg.hello\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n"
                       "\n"
                       "testpkg.world module\n"
                       "--------------------\n"
                       "\n"
                       ".. automodule:: testpkg.world\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n"
                       "\n"
                       "Module contents\n"
                       "---------------\n"
                       "\n"
                       ".. automodule:: testpkg\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n")

    content = (outdir / 'testpkg.subpkg.rst').read_text()
    assert content == ("testpkg.subpkg package\n"
                       "======================\n"
                       "\n"
                       "Module contents\n"
                       "---------------\n"
                       "\n"
                       ".. automodule:: testpkg.subpkg\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n")


def test_package_file_separate(tempdir):
    outdir = path(tempdir)
    (outdir / 'testpkg').makedirs()
    (outdir / 'testpkg' / '__init__.py').write_text('')
    (outdir / 'testpkg' / 'example.py').write_text('')
    apidoc_main(['--separate', '-o', tempdir, tempdir / 'testpkg'])
    assert (outdir / 'testpkg.rst').exists()
    assert (outdir / 'testpkg.example.rst').exists()

    content = (outdir / 'testpkg.rst').read_text()
    assert content == ("testpkg package\n"
                       "===============\n"
                       "\n"
                       "Submodules\n"
                       "----------\n"
                       "\n"
                       ".. toctree::\n"
                       "   :maxdepth: 4\n"
                       "\n"
                       "   testpkg.example\n"
                       "\n"
                       "Module contents\n"
                       "---------------\n"
                       "\n"
                       ".. automodule:: testpkg\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n")

    content = (outdir / 'testpkg.example.rst').read_text()
    assert content == ("testpkg.example module\n"
                       "======================\n"
                       "\n"
                       ".. automodule:: testpkg.example\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n")


def test_package_file_module_first(tempdir):
    outdir = path(tempdir)
    (outdir / 'testpkg').makedirs()
    (outdir / 'testpkg' / '__init__.py').write_text('')
    (outdir / 'testpkg' / 'example.py').write_text('')
    apidoc_main(['--module-first', '-o', tempdir, tempdir])

    content = (outdir / 'testpkg.rst').read_text()
    assert content == ("testpkg package\n"
                       "===============\n"
                       "\n"
                       ".. automodule:: testpkg\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n"
                       "\n"
                       "Submodules\n"
                       "----------\n"
                       "\n"
                       "testpkg.example module\n"
                       "----------------------\n"
                       "\n"
                       ".. automodule:: testpkg.example\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n")


def test_package_file_without_submodules(tempdir):
    outdir = path(tempdir)
    (outdir / 'testpkg').makedirs()
    (outdir / 'testpkg' / '__init__.py').write_text('')
    apidoc_main(['-o', tempdir, tempdir / 'testpkg'])
    assert (outdir / 'testpkg.rst').exists()

    content = (outdir / 'testpkg.rst').read_text()
    assert content == ("testpkg package\n"
                       "===============\n"
                       "\n"
                       "Module contents\n"
                       "---------------\n"
                       "\n"
                       ".. automodule:: testpkg\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n")


def test_namespace_package_file(tempdir):
    outdir = path(tempdir)
    (outdir / 'testpkg').makedirs()
    (outdir / 'testpkg' / 'example.py').write_text('')
    apidoc_main(['--implicit-namespace', '-o', tempdir, tempdir / 'testpkg'])
    assert (outdir / 'testpkg.rst').exists()

    content = (outdir / 'testpkg.rst').read_text()
    assert content == ("testpkg namespace\n"
                       "=================\n"
                       "\n"
                       ".. py:module:: testpkg\n"
                       "\n"
                       "Submodules\n"
                       "----------\n"
                       "\n"
                       "testpkg.example module\n"
                       "----------------------\n"
                       "\n"
                       ".. automodule:: testpkg.example\n"
                       "   :members:\n"
                       "   :undoc-members:\n"
                       "   :show-inheritance:\n")
