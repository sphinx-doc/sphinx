"""
    test_domain_js
    ~~~~~~~~~~~~~~

    Tests the JavaScript Domain

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest.mock import Mock

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (desc, desc_annotation, desc_content, desc_name, desc_parameter,
                             desc_parameterlist, desc_signature)
from sphinx.domains.javascript import JavaScriptDomain
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


@pytest.mark.sphinx('dummy', testroot='domain-js')
def test_domain_js_xrefs(app, status, warning):
    """Domain objects have correct prefixes when looking up xrefs"""
    app.builder.build_all()

    def assert_refnode(node, mod_name, prefix, target, reftype=None,
                       domain='js'):
        attributes = {
            'refdomain': domain,
            'reftarget': target,
        }
        if reftype is not None:
            attributes['reftype'] = reftype
        if mod_name is not False:
            attributes['js:module'] = mod_name
        if prefix is not False:
            attributes['js:object'] = prefix
        assert_node(node, **attributes)

    doctree = app.env.get_doctree('roles')
    refnodes = list(doctree.traverse(addnodes.pending_xref))
    assert_refnode(refnodes[0], None, None, 'TopLevel', 'class')
    assert_refnode(refnodes[1], None, None, 'top_level', 'func')
    assert_refnode(refnodes[2], None, 'NestedParentA', 'child_1', 'func')
    assert_refnode(refnodes[3], None, 'NestedParentA', 'NestedChildA.subchild_2', 'func')
    assert_refnode(refnodes[4], None, 'NestedParentA', 'child_2', 'func')
    assert_refnode(refnodes[5], False, 'NestedParentA', 'any_child', domain='')
    assert_refnode(refnodes[6], None, 'NestedParentA', 'NestedChildA', 'class')
    assert_refnode(refnodes[7], None, 'NestedParentA.NestedChildA', 'subchild_2', 'func')
    assert_refnode(refnodes[8], None, 'NestedParentA.NestedChildA',
                   'NestedParentA.child_1', 'func')
    assert_refnode(refnodes[9], None, 'NestedParentA', 'NestedChildA.subchild_1', 'func')
    assert_refnode(refnodes[10], None, 'NestedParentB', 'child_1', 'func')
    assert_refnode(refnodes[11], None, 'NestedParentB', 'NestedParentB', 'class')
    assert_refnode(refnodes[12], None, None, 'NestedParentA.NestedChildA', 'class')
    assert len(refnodes) == 13

    doctree = app.env.get_doctree('module')
    refnodes = list(doctree.traverse(addnodes.pending_xref))
    assert_refnode(refnodes[0], 'module_a.submodule', None, 'ModTopLevel',
                   'class')
    assert_refnode(refnodes[1], 'module_a.submodule', 'ModTopLevel',
                   'mod_child_1', 'meth')
    assert_refnode(refnodes[2], 'module_a.submodule', 'ModTopLevel',
                   'ModTopLevel.mod_child_1', 'meth')
    assert_refnode(refnodes[3], 'module_a.submodule', 'ModTopLevel',
                   'mod_child_2', 'meth')
    assert_refnode(refnodes[4], 'module_a.submodule', 'ModTopLevel',
                   'module_a.submodule.ModTopLevel.mod_child_1', 'meth')
    assert_refnode(refnodes[5], 'module_b.submodule', None, 'ModTopLevel',
                   'class')
    assert_refnode(refnodes[6], 'module_b.submodule', 'ModTopLevel',
                   'module_a.submodule', 'mod')
    assert len(refnodes) == 7


@pytest.mark.sphinx('dummy', testroot='domain-js')
def test_domain_js_objects(app, status, warning):
    app.builder.build_all()

    modules = app.env.domains['js'].data['modules']
    objects = app.env.domains['js'].data['objects']

    assert 'module_a.submodule' in modules
    assert 'module_a.submodule' in objects
    assert 'module_b.submodule' in modules
    assert 'module_b.submodule' in objects

    assert objects['module_a.submodule.ModTopLevel'][2] == 'class'
    assert objects['module_a.submodule.ModTopLevel.mod_child_1'][2] == 'method'
    assert objects['module_a.submodule.ModTopLevel.mod_child_2'][2] == 'method'
    assert objects['module_b.submodule.ModTopLevel'][2] == 'class'

    assert objects['TopLevel'][2] == 'class'
    assert objects['top_level'][2] == 'function'
    assert objects['NestedParentA'][2] == 'class'
    assert objects['NestedParentA.child_1'][2] == 'function'
    assert objects['NestedParentA.any_child'][2] == 'function'
    assert objects['NestedParentA.NestedChildA'][2] == 'class'
    assert objects['NestedParentA.NestedChildA.subchild_1'][2] == 'function'
    assert objects['NestedParentA.NestedChildA.subchild_2'][2] == 'function'
    assert objects['NestedParentA.child_2'][2] == 'function'
    assert objects['NestedParentB'][2] == 'class'
    assert objects['NestedParentB.child_1'][2] == 'function'


@pytest.mark.sphinx('dummy', testroot='domain-js')
def test_domain_js_find_obj(app, status, warning):

    def find_obj(mod_name, prefix, obj_name, obj_type, searchmode=0):
        return app.env.domains['js'].find_obj(
            app.env, mod_name, prefix, obj_name, obj_type, searchmode)

    app.builder.build_all()

    assert (find_obj(None, None, 'NONEXISTANT', 'class') == (None, None))
    assert (find_obj(None, None, 'NestedParentA', 'class') ==
            ('NestedParentA', ('roles', 'NestedParentA', 'class')))
    assert (find_obj(None, None, 'NestedParentA.NestedChildA', 'class') ==
            ('NestedParentA.NestedChildA',
             ('roles', 'NestedParentA.NestedChildA', 'class')))
    assert (find_obj(None, 'NestedParentA', 'NestedChildA', 'class') ==
            ('NestedParentA.NestedChildA',
             ('roles', 'NestedParentA.NestedChildA', 'class')))
    assert (find_obj(None, None, 'NestedParentA.NestedChildA.subchild_1', 'func') ==
            ('NestedParentA.NestedChildA.subchild_1',
             ('roles', 'NestedParentA.NestedChildA.subchild_1', 'function')))
    assert (find_obj(None, 'NestedParentA', 'NestedChildA.subchild_1', 'func') ==
            ('NestedParentA.NestedChildA.subchild_1',
             ('roles', 'NestedParentA.NestedChildA.subchild_1', 'function')))
    assert (find_obj(None, 'NestedParentA.NestedChildA', 'subchild_1', 'func') ==
            ('NestedParentA.NestedChildA.subchild_1',
             ('roles', 'NestedParentA.NestedChildA.subchild_1', 'function')))
    assert (find_obj('module_a.submodule', 'ModTopLevel', 'mod_child_2', 'meth') ==
            ('module_a.submodule.ModTopLevel.mod_child_2',
             ('module', 'module_a.submodule.ModTopLevel.mod_child_2', 'method')))
    assert (find_obj('module_b.submodule', 'ModTopLevel', 'module_a.submodule', 'mod') ==
            ('module_a.submodule',
             ('module', 'module-module_a.submodule', 'module')))


def test_get_full_qualified_name():
    env = Mock(domaindata={})
    domain = JavaScriptDomain(env)

    # non-js references
    node = nodes.reference()
    assert domain.get_full_qualified_name(node) is None

    # simple reference
    node = nodes.reference(reftarget='func')
    assert domain.get_full_qualified_name(node) == 'func'

    # with js:module context
    kwargs = {'js:module': 'module1'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'module1.func'

    # with js:object context
    kwargs = {'js:object': 'Class'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'Class.func'

    # with both js:module and js:object context
    kwargs = {'js:module': 'module1', 'js:object': 'Class'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'module1.Class.func'


def test_js_module(app):
    text = ".. js:module:: sphinx"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (nodes.target,
                          addnodes.index))
    assert_node(doctree[0], nodes.target, ids=["module-sphinx"])
    assert_node(doctree[1], addnodes.index,
                entries=[("single", "sphinx (module)", "module-sphinx", "", None)])


def test_js_function(app):
    text = ".. js:function:: sum(a, b)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "sum"],
                                                    desc_parameterlist)],
                                  [desc_content, ()])]))
    assert_node(doctree[1][0][1], [desc_parameterlist, ([desc_parameter, "a"],
                                                        [desc_parameter, "b"])])
    assert_node(doctree[0], addnodes.index,
                entries=[("single", "sum() (built-in function)", "sum", "", None)])
    assert_node(doctree[1], addnodes.desc, domain="js", objtype="function", noindex=False)


def test_js_class(app):
    text = ".. js:class:: Application"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Application"],
                                                    [desc_parameterlist, ()])],
                                  [desc_content, ()])]))
    assert_node(doctree[0], addnodes.index,
                entries=[("single", "Application() (class)", "Application", "", None)])
    assert_node(doctree[1], addnodes.desc, domain="js", objtype="class", noindex=False)


def test_js_data(app):
    text = ".. js:data:: name"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, desc_name, "name"],
                                  [desc_content, ()])]))
    assert_node(doctree[0], addnodes.index,
                entries=[("single", "name (global variable or constant)", "name", "", None)])
    assert_node(doctree[1], addnodes.desc, domain="js", objtype="data", noindex=False)


def test_noindexentry(app):
    text = (".. js:function:: f()\n"
            ".. js:function:: g()\n"
            "   :noindexentry:\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, desc, addnodes.index, desc))
    assert_node(doctree[0], addnodes.index, entries=[('single', 'f() (built-in function)', 'f', '', None)])
    assert_node(doctree[2], addnodes.index, entries=[])
