# -*- coding: utf-8 -*-
"""
    test_autodoc
    ~~~~~~~~~~~~

    Test the autodoc extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pickle

import pytest

from sphinx import addnodes


@pytest.mark.sphinx('dummy', testroot='ext-autodoc')
def test_autodoc(app, status, warning):
    app.builder.build_all()

    content = pickle.loads((app.doctreedir / 'contents.doctree').bytes())
    assert isinstance(content[3], addnodes.desc)
    assert content[3][0].astext() == 'autodoc_dummy_module.test'
    assert content[3][1].astext() == 'Dummy function using dummy.*'

    # issue sphinx-doc/sphinx#2437
    assert content[11][-1].astext() == """Dummy class Bar with alias.



my_name

alias of bug2437.autodoc_dummy_foo.Foo"""
    assert warning.getvalue() == ''
