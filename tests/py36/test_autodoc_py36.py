# -*- coding: utf-8 -*-
"""
    test_autodoc
    ~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.testing.util import SphinxTestApp, Struct
import pytest

from docutils.statemachine import ViewList

from sphinx.ext.autodoc import AutoDirective

app = None


@pytest.fixture(scope='module', autouse=True)
def setup_module(rootdir, sphinx_test_tempdir):
    global app
    srcdir = sphinx_test_tempdir / 'autodoc-root'
    if not srcdir.exists():
        (rootdir/'test-root').copytree(srcdir)
    app = SphinxTestApp(srcdir=srcdir)
    app.builder.env.app = app
    app.builder.env.temp_data['docname'] = 'dummy'
    yield
    app.cleanup()


directive = options = None


@pytest.fixture
def setup_test():
    global options, directive
    global processed_docstrings, processed_signatures, _warnings

    options = Struct(
        inherited_members = False,
        undoc_members = False,
        private_members = False,
        special_members = False,
        imported_members = False,
        show_inheritance = False,
        noindex = False,
        annotation = None,
        synopsis = '',
        platform = '',
        deprecated = False,
        members = [],
        member_order = 'alphabetic',
        exclude_members = set(),
    )

    directive = Struct(
        env = app.builder.env,
        genopt = options,
        result = ViewList(),
        warn = warnfunc,
        filename_set = set(),
    )

    processed_docstrings = []
    processed_signatures = []
    _warnings = []


_warnings = []


def warnfunc(msg):
    _warnings.append(msg)


@pytest.mark.usefixtures('setup_test')
def test_generate():
    inst = AutoDirective._registry['module'](directive, 'test_autodoc_py36')
    inst.generate(all_members=True)
    assert directive.result
    assert '.. py:data:: integer' in '\n'.join(directive.result)
    assert len(_warnings) == 0, _warnings
    del directive.result[:]


# --- generate fodder ------------
__all__ = ['integer']

#: documentation for the integer
integer: int = 1
