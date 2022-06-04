"""Tests the directives"""

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

DOMAINS = [
    # directive, noindex, noindexentry, signature of f, signature of g, index entry of g
    ('c:function', False, True, 'void f()', 'void g()', ('single', 'g (C function)', 'c.g', '', None)),
    ('cpp:function', False, True, 'void f()', 'void g()', ('single', 'g (C++ function)', '_CPPv41gv', '', None)),
    ('js:function', True, True, 'f()', 'g()', ('single', 'g() (built-in function)', 'g', '', None)),
    ('py:function', True, True, 'f()', 'g()', ('pair', 'built-in function; g()', 'g', '', None)),
    ('rst:directive', True, False, 'f', 'g', ('single', 'g (directive)', 'directive-g', '', None)),
    ('cmdoption', True, False, 'f', 'g', ('pair', 'command line option; g', 'cmdoption-arg-g', '', None)),
    ('envvar', True, False, 'f', 'g', ('single', 'environment variable; g', 'envvar-g', '', None)),
]


@pytest.mark.parametrize("directive,noindex,noindexentry,sig_f,sig_g,index_g", DOMAINS)
def test_object_description_notypesetting(app, directive, noindex, noindexentry, sig_f, sig_g, index_g):
    text = (f".. {directive}:: {sig_f}\n"
            f"   :notypesetting:\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, nodes.target))


@pytest.mark.parametrize("directive,noindex,noindexentry,sig_f,sig_g,index_g", DOMAINS)
def test_object_description_notypesetting_twice(app, directive, noindex, noindexentry, sig_f, sig_g, index_g):
    text = (f".. {directive}:: {sig_f}\n"
            f"   :notypesetting:\n"
            f".. {directive}:: {sig_g}\n"
            f"   :notypesetting:\n")
    doctree = restructuredtext.parse(app, text)
    # Note that all index come before the targets
    assert_node(doctree, (addnodes.index, addnodes.index, nodes.target, nodes.target))


@pytest.mark.parametrize("directive,noindex,noindexentry,sig_f,sig_g,index_g", DOMAINS)
def test_object_description_notypesetting_noindex_orig(app, directive, noindex, noindexentry, sig_f, sig_g, index_g):
    if not noindex:
        pytest.skip(f"{directive} does not support :noindex: option")
    text = (f".. {directive}:: {sig_f}\n"
            f"   :noindex:\n"
            f".. {directive}:: {sig_g}\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, addnodes.desc, addnodes.index, addnodes.desc))
    assert_node(doctree[2], addnodes.index, entries=[index_g])


@pytest.mark.parametrize("directive,noindex,noindexentry,sig_f,sig_g,index_g", DOMAINS)
def test_object_description_notypesetting_noindex(app, directive, noindex, noindexentry, sig_f, sig_g, index_g):
    if not noindex:
        pytest.skip(f"{directive} does not support :noindex: option")
    text = (f".. {directive}:: {sig_f}\n"
            f"   :noindex:\n"
            f"   :notypesetting:\n"
            f".. {directive}:: {sig_g}\n"
            f"   :notypesetting:\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, addnodes.index, nodes.target))
    assert_node(doctree[0], addnodes.index, entries=[])
    assert_node(doctree[1], addnodes.index, entries=[index_g])


@pytest.mark.parametrize("directive,noindex,noindexentry,sig_f,sig_g,index_g", DOMAINS)
def test_object_description_notypesetting_noindexentry(app, directive, noindex, noindexentry, sig_f, sig_g, index_g):
    if not noindexentry:
        pytest.skip(f"{directive} does not support :noindexentry: option")
    text = (f".. {directive}:: {sig_f}\n"
            f"   :noindexentry:\n"
            f"   :notypesetting:\n"
            f".. {directive}:: {sig_g}\n"
            f"   :notypesetting:\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, addnodes.index, nodes.target, nodes.target))
    assert_node(doctree[0], addnodes.index, entries=[])
    assert_node(doctree[1], addnodes.index, entries=[index_g])


@pytest.mark.parametrize("directive,noindex,noindexentry,sig_f,sig_g,index_g", DOMAINS)
def test_object_description_notypesetting_code(app, directive, noindex, noindexentry, sig_f, sig_g, index_g):
    text = (f".. {directive}:: {sig_f}\n"
            f"   :notypesetting:\n"
            f".. {directive}:: {sig_g}\n"
            f"   :notypesetting:\n"
            f".. code::\n"
            f"\n"
            f"   code\n")
    doctree = restructuredtext.parse(app, text)
    # Note that all index come before the targets
    assert_node(doctree, (addnodes.index, addnodes.index, nodes.target, nodes.target, nodes.literal_block))


@pytest.mark.parametrize("directive,noindex,noindexentry,sig_f,sig_g,index_g", DOMAINS)
def test_object_description_notypesetting_heading(app, directive, noindex, noindexentry, sig_f, sig_g, index_g):
    text = (f".. {directive}:: {sig_f}\n"
            f"   :notypesetting:\n"
            f".. {directive}:: {sig_g}\n"
            f"   :notypesetting:\n"
            f"\n"
            f"Heading\n"
            f"=======\n")
    doctree = restructuredtext.parse(app, text)
    # Note that all index come before the targets and the heading is floated before those.
    assert_node(doctree, (nodes.title, addnodes.index, addnodes.index, nodes.target, nodes.target))
