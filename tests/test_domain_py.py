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

    def find_obj(prefix, obj_name, obj_type, modname=None, searchmode=0):
        return app.env.domains['py'].find_obj(
            app.env, modname, prefix, obj_name, obj_type, searchmode)

    app.builder.build_all()

    xrefs = {
        (None, u'TopLevel', u'class'): [
            (u'TopLevel', (u'roles', u'class'))],
        (None, u'top_level', u'meth'): [
            (u'top_level', (u'roles', u'method'))],
        (u'NestedParentA', u'child_1', u'meth'): [
            (u'NestedParentA.child_1', (u'roles', u'method'))],
        (u'NestedParentA', u'NestedChildA.subchild_2', u'meth'): [
            (u'NestedParentA.NestedChildA.subchild_2', (u'roles', u'method'))],
        (u'NestedParentA', u'child_2', u'meth'): [
            (u'child_2', (u'roles', u'method'))],
        (u'NestedParentA', u'any_child', None): [
            (u'NestedParentA.any_child', (u'roles', u'method'))],
        (u'NestedParentA', u'NestedChildA', u'class'): [
            (u'NestedParentA.NestedChildA', (u'roles', u'class'))],
        (u'NestedParentA.NestedChildA', u'subchild_2', u'meth'): [
            (u'NestedParentA.NestedChildA.subchild_2', (u'roles', u'method'))],
        (u'NestedParentA.NestedChildA', u'NestedParentA.child_1', u'meth'): [
            (u'NestedParentA.child_1', (u'roles', u'method'))],
        (None, u'NestedChildA.subchild_1', u'meth'): [],
        (u'NestedParentB', u'child_1', u'meth'): [
            (u'NestedParentB.child_1', (u'roles', u'method'))],
        (u'NestedParentB', u'NestedParentB', u'class'): [
            (u'NestedParentB', (u'roles', u'class'))],
        (None, u'NestedParentA.NestedChildA', u'class'): [
            (u'NestedParentA.NestedChildA', (u'roles', u'class'))],
    }

    for (search, found) in xrefs.items():
        assert find_obj(*search) == found
