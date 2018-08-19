# -*- coding: utf-8 -*-
"""
    test_apidoc
    ~~~~~~~~~~~

    Test the sphinx.apidoc module.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from __future__ import print_function

from collections import namedtuple

import pytest

from sphinx.ext.apidoc import main as apidoc_main
from sphinx.testing.util import remove_unicode_literals


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
    assert (outdir / 'autodoc_fodder.rst').isfile()
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
        assert ".. toctree::\n\n   a.b.c.d\n" in rst

    with open(outdir / 'a.b.e.rst') as f:
        rst = f.read()
        assert ".. toctree::\n\n   a.b.e.f\n" in rst

    with open(outdir / 'a.b.x.rst') as f:
        rst = f.read()
        assert ".. toctree::\n\n   a.b.x.y\n" in rst

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
    assert (outdir / 'a.b.c.rst').isfile()  # generated because not empty
    assert (outdir / 'a.b.e.f.rst').isfile()  # skipped because of empty after excludes


@pytest.mark.apidoc(
    coderoot='test-root',
    options=[
        '--doc-project', u'プロジェクト名',
        '--doc-author', u'著者名',
        '--doc-version', u'バージョン',
        '--doc-release', u'リリース',
    ],
)
def test_multibyte_parameters(make_app, apidoc):
    outdir = apidoc.outdir
    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'autodoc_fodder.rst').isfile()
    assert (outdir / 'index.rst').isfile()

    conf_py = (outdir / 'conf.py').text()
    conf_py_ = remove_unicode_literals(conf_py)
    assert u"project = 'プロジェクト名'" in conf_py_
    assert u"author = '著者名'" in conf_py_
    assert u"version = 'バージョン'" in conf_py_
    assert u"release = 'リリース'" in conf_py_

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
