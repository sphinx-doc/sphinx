# -*- coding: utf-8 -*-
"""
    test_domain_js
    ~~~~~~~~~~~~~~

    Tests the JavaScript Domain

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
import mock


@pytest.mark.sphinx(testroot='domain-js')
def test_domain_js_xrefs(app, status, warning):
    """Domain objects have correct prefixes when looking up xrefs"""
    find_obj = app.env.domains['js'].find_obj
    app.env.domains['js'].find_obj = mock.Mock(wraps=find_obj)
    app.builder.build_all()

    def assert_called(prefix, obj_name, obj_type, searchmode=0):
        app.env.domains['js'].find_obj.assert_any_call(
            app.env, prefix, obj_name, obj_type, searchmode)

    assert_called(None, u'TopLevel', u'class')
    assert_called(None, u'top_level', u'func')
    assert_called(None, u'child_1', u'func')
    assert_called(None, u'NestedChildA.subchild_2', u'func')
    assert_called(None, u'child_2', u'func')
    assert_called(None, u'any_child', None, 1)
    assert_called(None, u'NestedChildA', u'class')
    assert_called(None, u'subchild_2', u'func')
    assert_called(None, u'NestedParentA.child_1', u'func')
    assert_called(None, u'NestedChildA.subchild_1', u'func')
    assert_called(None, u'NestedParentB', u'class')
    assert_called(None, u'NestedParentA.NestedChildA', u'class')


@pytest.mark.sphinx(testroot='domain-js')
def test_domain_js_objects(app, status, warning):
    app.builder.build_all()

    objects = app.env.domains['js'].data['objects']

    assert objects['TopLevel'] == ('roles', 'class')
    assert objects['top_level'] == ('roles', 'function')
    assert objects['NestedParentA'] == ('roles', 'class')
    assert objects['child_1'] == ('roles', 'function')
    assert objects['any_child'] == ('roles', 'function')
    assert objects['NestedChildA'] == ('roles', 'class')
    assert objects['subchild_1'] == ('roles', 'function')
    assert objects['subchild_2'] == ('roles', 'function')
    assert objects['child_2'] == ('roles', 'function')
    assert objects['NestedParentB'] == ('roles', 'class')


@pytest.mark.sphinx(testroot='domain-js')
def test_domain_js_find_obj(app, status, warning):

    def find_obj(prefix, obj_name, obj_type, searchmode=0):
        return app.env.domains['js'].find_obj(
            app.env, prefix, obj_name, obj_type, searchmode)

    app.builder.build_all()

    assert find_obj(None, u'NONEXISTANT', u'class') == (None, None)
    assert find_obj(None, u'TopLevel', u'class') == (
        u'TopLevel', (u'roles', u'class'))
    assert find_obj(None, u'NestedParentA.NestedChildA', u'class') == (
        None, None)
    assert find_obj(None, u'subchild_2', u'func') == (
        u'subchild_2', (u'roles', u'function'))
