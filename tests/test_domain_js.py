# -*- coding: utf-8 -*-
"""
    test_domain_js
    ~~~~~~~~~~~~~~

    Tests the JavaScript Domain

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


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

    xrefs = {
        (None, u'NONEXISTANT', u'class'): (None, None),
        (None, u'TopLevel', u'class'): (u'TopLevel', (u'roles', u'class')),
        (None, u'top_level', u'func'): (u'top_level', (u'roles', u'function')),
        (None, u'child_1', u'func'): (u'child_1', (u'roles', u'function')),
        (None, u'NestedChildA.subchild_2', u'func'): (None, None),
        (None, u'child_2', u'func'): (u'child_2', (u'roles', u'function')),
        (None, u'any_child', None): (u'any_child', (u'roles', u'function')),
        (None, u'NestedChildA', u'class'): (u'NestedChildA', (u'roles', u'class')),
        (None, u'subchild_2', u'func'): (u'subchild_2', (u'roles', u'function')),
        (None, u'NestedParentA.child_1', u'func'): (None, None),
        (None, u'NestedChildA.subchild_1', u'func'): (None, None),
        (None, u'NestedParentB', u'class'): (u'NestedParentB', (u'roles', u'class')),
        (None, u'NestedParentA.NestedChildA', u'class'): (None, None),
    }

    for (search, found) in xrefs.items():
        assert find_obj(*search) == found
