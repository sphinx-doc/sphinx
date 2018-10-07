# -*- coding: utf-8 -*-
"""
    test_domain_py
    ~~~~~~~~~~~~~~

    Tests the Python Domain

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
from docutils import nodes
from mock import Mock
from six import text_type

from sphinx import addnodes
from sphinx.domains.python import py_sig_re, _pseudo_parse_arglist, PythonDomain
from sphinx.testing.util import assert_node


def parse(sig):
    m = py_sig_re.match(sig)
    if m is None:
        raise ValueError
    name_prefix, name, arglist, retann = m.groups()
    signode = addnodes.desc_signature(sig, '')
    _pseudo_parse_arglist(signode, arglist)
    return signode.astext()


def test_function_signatures():
    rv = parse('func(a=1) -> int object')
    assert text_type(rv) == u'a=1'

    rv = parse('func(a=1, [b=None])')
    assert text_type(rv) == u'a=1, [b=None]'

    rv = parse('func(a=1[, b=None])')
    assert text_type(rv) == u'a=1, [b=None]'

    rv = parse("compile(source : string, filename, symbol='file')")
    assert text_type(rv) == u"source : string, filename, symbol='file'"

    rv = parse('func(a=[], [b=None])')
    assert text_type(rv) == u'a=[], [b=None]'

    rv = parse('func(a=[][, b=None])')
    assert text_type(rv) == u'a=[], [b=None]'


@pytest.mark.sphinx('dummy', testroot='domain-py')
def test_domain_py_xrefs(app, status, warning):
    """Domain objects have correct prefixes when looking up xrefs"""
    app.builder.build_all()

    def assert_refnode(node, module_name, class_name, target, reftype=None,
                       domain='py'):
        attributes = {
            'refdomain': domain,
            'reftarget': target,
        }
        if reftype is not None:
            attributes['reftype'] = reftype
        if module_name is not False:
            attributes['py:module'] = module_name
        if class_name is not False:
            attributes['py:class'] = class_name
        assert_node(node, **attributes)

    doctree = app.env.get_doctree('roles')
    refnodes = list(doctree.traverse(addnodes.pending_xref))
    assert_refnode(refnodes[0], None, None, u'TopLevel', u'class')
    assert_refnode(refnodes[1], None, None, u'top_level', u'meth')
    assert_refnode(refnodes[2], None, u'NestedParentA', u'child_1', u'meth')
    assert_refnode(refnodes[3], None, u'NestedParentA',
                   u'NestedChildA.subchild_2', u'meth')
    assert_refnode(refnodes[4], None, u'NestedParentA', u'child_2', u'meth')
    assert_refnode(refnodes[5], False, u'NestedParentA', u'any_child', domain='')
    assert_refnode(refnodes[6], None, u'NestedParentA', u'NestedChildA',
                   u'class')
    assert_refnode(refnodes[7], None, u'NestedParentA.NestedChildA',
                   u'subchild_2', u'meth')
    assert_refnode(refnodes[8], None, u'NestedParentA.NestedChildA',
                   u'NestedParentA.child_1', u'meth')
    assert_refnode(refnodes[9], None, u'NestedParentA',
                   u'NestedChildA.subchild_1', u'meth')
    assert_refnode(refnodes[10], None, u'NestedParentB', u'child_1', u'meth')
    assert_refnode(refnodes[11], None, u'NestedParentB', u'NestedParentB',
                   u'class')
    assert_refnode(refnodes[12], None, None, u'NestedParentA.NestedChildA',
                   u'class')
    assert len(refnodes) == 13

    doctree = app.env.get_doctree('module')
    refnodes = list(doctree.traverse(addnodes.pending_xref))
    assert_refnode(refnodes[0], 'module_a.submodule', None,
                   'ModTopLevel', 'class')
    assert_refnode(refnodes[1], 'module_a.submodule', 'ModTopLevel',
                   'mod_child_1', 'meth')
    assert_refnode(refnodes[2], 'module_a.submodule', 'ModTopLevel',
                   'ModTopLevel.mod_child_1', 'meth')
    assert_refnode(refnodes[3], 'module_a.submodule', 'ModTopLevel',
                   'mod_child_2', 'meth')
    assert_refnode(refnodes[4], 'module_a.submodule', 'ModTopLevel',
                   'module_a.submodule.ModTopLevel.mod_child_1', 'meth')
    assert_refnode(refnodes[5], 'module_b.submodule', None,
                   'ModTopLevel', 'class')
    assert_refnode(refnodes[6], 'module_b.submodule', 'ModTopLevel',
                   'ModNoModule', 'class')
    assert_refnode(refnodes[7], False, False, 'int', 'class')
    assert_refnode(refnodes[8], False, False, 'tuple', 'class')
    assert_refnode(refnodes[9], False, False, 'str', 'class')
    assert_refnode(refnodes[10], False, False, 'float', 'class')
    assert_refnode(refnodes[11], False, False, 'list', 'class')
    assert_refnode(refnodes[11], False, False, 'list', 'class')
    assert_refnode(refnodes[12], False, False, 'ModTopLevel', 'class')
    assert_refnode(refnodes[13], False, False, 'index', 'doc', domain='std')
    assert len(refnodes) == 14

    doctree = app.env.get_doctree('module_option')
    refnodes = list(doctree.traverse(addnodes.pending_xref))
    print(refnodes)
    print(refnodes[0])
    print(refnodes[1])
    assert_refnode(refnodes[0], 'test.extra', 'B', 'foo', 'meth')
    assert_refnode(refnodes[1], 'test.extra', 'B', 'foo', 'meth')
    assert len(refnodes) == 2


@pytest.mark.sphinx('dummy', testroot='domain-py')
def test_domain_py_objects(app, status, warning):
    app.builder.build_all()

    modules = app.env.domains['py'].data['modules']
    objects = app.env.domains['py'].data['objects']

    assert 'module_a.submodule' in modules
    assert 'module_a.submodule' in objects
    assert 'module_b.submodule' in modules
    assert 'module_b.submodule' in objects

    assert objects['module_a.submodule.ModTopLevel'] == ('module', 'class')
    assert objects['module_a.submodule.ModTopLevel.mod_child_1'] == ('module', 'method')
    assert objects['module_a.submodule.ModTopLevel.mod_child_2'] == ('module', 'method')
    assert 'ModTopLevel.ModNoModule' not in objects
    assert objects['ModNoModule'] == ('module', 'class')
    assert objects['module_b.submodule.ModTopLevel'] == ('module', 'class')

    assert objects['TopLevel'] == ('roles', 'class')
    assert objects['top_level'] == ('roles', 'method')
    assert objects['NestedParentA'] == ('roles', 'class')
    assert objects['NestedParentA.child_1'] == ('roles', 'method')
    assert objects['NestedParentA.any_child'] == ('roles', 'method')
    assert objects['NestedParentA.NestedChildA'] == ('roles', 'class')
    assert objects['NestedParentA.NestedChildA.subchild_1'] == ('roles', 'method')
    assert objects['NestedParentA.NestedChildA.subchild_2'] == ('roles', 'method')
    assert objects['NestedParentA.child_2'] == ('roles', 'method')
    assert objects['NestedParentB'] == ('roles', 'class')
    assert objects['NestedParentB.child_1'] == ('roles', 'method')


@pytest.mark.sphinx('dummy', testroot='domain-py')
def test_domain_py_find_obj(app, status, warning):

    def find_obj(modname, prefix, obj_name, obj_type, searchmode=0):
        return app.env.domains['py'].find_obj(
            app.env, modname, prefix, obj_name, obj_type, searchmode)

    app.builder.build_all()

    assert (find_obj(None, None, u'NONEXISTANT', u'class') ==
            [])
    assert (find_obj(None, None, u'NestedParentA', u'class') ==
            [(u'NestedParentA', (u'roles', u'class'))])
    assert (find_obj(None, None, u'NestedParentA.NestedChildA', u'class') ==
            [(u'NestedParentA.NestedChildA', (u'roles', u'class'))])
    assert (find_obj(None, 'NestedParentA', u'NestedChildA', u'class') ==
            [(u'NestedParentA.NestedChildA', (u'roles', u'class'))])
    assert (find_obj(None, None, u'NestedParentA.NestedChildA.subchild_1', u'meth') ==
            [(u'NestedParentA.NestedChildA.subchild_1', (u'roles', u'method'))])
    assert (find_obj(None, u'NestedParentA', u'NestedChildA.subchild_1', u'meth') ==
            [(u'NestedParentA.NestedChildA.subchild_1', (u'roles', u'method'))])
    assert (find_obj(None, u'NestedParentA.NestedChildA', u'subchild_1', u'meth') ==
            [(u'NestedParentA.NestedChildA.subchild_1', (u'roles', u'method'))])


def test_get_full_qualified_name():
    env = Mock(domaindata={})
    domain = PythonDomain(env)

    # non-python references
    node = nodes.reference()
    assert domain.get_full_qualified_name(node) is None

    # simple reference
    node = nodes.reference(reftarget='func')
    assert domain.get_full_qualified_name(node) == 'func'

    # with py:module context
    kwargs = {'py:module': 'module1'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'module1.func'

    # with py:class context
    kwargs = {'py:class': 'Class'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'Class.func'

    # with both py:module and py:class context
    kwargs = {'py:module': 'module1', 'py:class': 'Class'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'module1.Class.func'
