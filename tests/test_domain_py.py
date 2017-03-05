# -*- coding: utf-8 -*-
"""
    test_domain_py
    ~~~~~~~~~~~~~~

    Tests the Python Domain

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import text_type
import pytest
import mock

from sphinx import addnodes
from sphinx.domains.python import py_sig_re, _pseudo_parse_arglist


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


@pytest.mark.sphinx(testroot='domain-py')
def test_domain_py_xrefs(app, status, warning):
    """Domain objects have correct prefixes when looking up xrefs"""
    find_obj = app.env.domains['py'].find_obj
    app.env.domains['py'].find_obj = mock.Mock(wraps=find_obj)
    app.builder.build_all()

    def assert_called(mod_name, prefix, obj_name, obj_type, searchmode=0):
        app.env.domains['py'].find_obj.assert_any_call(
            app.env, mod_name, prefix, obj_name, obj_type, searchmode)

    assert_called(None, None, u'TopLevel', u'class')
    assert_called(None, None, u'top_level', u'meth')
    assert_called(None, u'NestedParentA', u'child_1', u'meth')
    assert_called(None, u'NestedParentA', u'NestedChildA.subchild_2', u'meth')
    assert_called(None, u'NestedParentA', u'child_2', u'meth')
    assert_called(None, u'NestedParentA', u'any_child', None, 1)
    assert_called(None, u'NestedParentA', u'NestedChildA', u'class')
    assert_called(None, u'NestedParentA.NestedChildA', u'subchild_2', u'meth')
    assert_called(None, u'NestedParentA.NestedChildA', u'NestedParentA.child_1',
                  u'meth')
    assert_called(None, None, u'NestedChildA.subchild_1', u'meth')
    assert_called(None, u'NestedParentB', u'child_1', u'meth')
    assert_called(None, u'NestedParentB', u'NestedParentB', u'class')
    assert_called(None, None, u'NestedParentA.NestedChildA', u'class')

    assert_called('module_a.submodule', 'ModTopLevel', 'mod_child_1', 'meth')
    assert_called('module_a.submodule', 'ModTopLevel',
                  'ModTopLevel.mod_child_1', 'meth')
    assert_called('module_a.submodule', 'ModTopLevel', 'mod_child_2', 'meth')
    assert_called('module_a.submodule', 'ModTopLevel',
                  'module_a.submodule.ModTopLevel.mod_child_1', 'meth')

    with pytest.raises(AssertionError):
        assert_called('module_a.submodule', None, 'ModTopLevel', 'class')
    with pytest.raises(AssertionError):
        assert_called('module_b.submodule', None, 'ModTopLevel', 'class')
    with pytest.raises(AssertionError):
        assert_called('module_b.submodule', 'ModTopLevel', 'ModNoModule', 'class')


@pytest.mark.sphinx(testroot='domain-py')
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
    assert objects['child_2'] == ('roles', 'method')
    assert objects['NestedParentB'] == ('roles', 'class')
    assert objects['NestedParentB.child_1'] == ('roles', 'method')


@pytest.mark.sphinx(testroot='domain-py')
def test_domain_py_find_obj(app, status, warning):

    def find_obj(modname, prefix, obj_name, obj_type, searchmode=0):
        return app.env.domains['py'].find_obj(
            app.env, modname, prefix, obj_name, obj_type, searchmode)

    app.builder.build_all()

    assert find_obj(None, None, u'NONEXISTANT', u'class') == []
    assert find_obj(None, None, u'NestedParentA', u'class') == [(
        u'NestedParentA', (u'roles', u'class'))]
    assert find_obj(None, None, u'NestedParentA.NestedChildA', u'class') == [(
        u'NestedParentA.NestedChildA', (u'roles', u'class'))]
    assert find_obj(None, 'NestedParentA', u'NestedChildA', u'class') == [(
        u'NestedParentA.NestedChildA', (u'roles', u'class'))]
    assert find_obj(None, None, u'NestedParentA.NestedChildA.subchild_1', u'meth') == [(
        u'NestedParentA.NestedChildA.subchild_1', (u'roles', u'method'))]
    assert find_obj(None, u'NestedParentA', u'NestedChildA.subchild_1', u'meth') == [(
        u'NestedParentA.NestedChildA.subchild_1', (u'roles', u'method'))]
    assert find_obj(None, u'NestedParentA.NestedChildA', u'subchild_1', u'meth') == [(
        u'NestedParentA.NestedChildA.subchild_1', (u'roles', u'method'))]
