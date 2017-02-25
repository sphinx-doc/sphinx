# -*- coding: utf-8 -*-
"""
    test_domain_js
    ~~~~~~~~~~~~~~

    Tests the JavaScript Domain

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
from sphinx import addnodes

from util import assert_node


@pytest.mark.sphinx('dummy', testroot='domain-js')
def test_domain_js_xrefs(app, status, warning):
    """Domain objects have correct prefixes when looking up xrefs"""
    app.builder.build_all()

    def assert_refnode(node, class_name, target, reftype=None,
                       domain='js'):
        attributes = {
            'refdomain': domain,
            'reftarget': target,
        }
        if reftype is not None:
            attributes['reftype'] = reftype
        if class_name is not False:
            attributes['js:class'] = class_name
        assert_node(node, **attributes)

    doctree = app.env.get_doctree('roles')
    refnodes = list(doctree.traverse(addnodes.pending_xref))
    assert_refnode(refnodes[0], False, u'TopLevel', u'class')
    assert_refnode(refnodes[1], False, u'top_level', u'func')
    assert_refnode(refnodes[2], False, u'child_1', u'func')
    assert_refnode(refnodes[3], False, u'NestedChildA.subchild_2', u'func')
    assert_refnode(refnodes[4], False, u'child_2', u'func')
    assert_refnode(refnodes[5], False, u'any_child', domain='')
    assert_refnode(refnodes[6], False, u'NestedChildA', u'class')
    assert_refnode(refnodes[7], False, u'subchild_2', u'func')
    assert_refnode(refnodes[8], False, u'NestedParentA.child_1', u'func')
    assert_refnode(refnodes[9], False, u'NestedChildA.subchild_1', u'func')
    assert_refnode(refnodes[10], False, u'child_1', u'func')
    assert_refnode(refnodes[11], False, u'NestedParentB', u'class')
    assert_refnode(refnodes[12], False, u'NestedParentA.NestedChildA', u'class')
    assert len(refnodes) == 13


@pytest.mark.sphinx('dummy', testroot='domain-js')
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


@pytest.mark.sphinx('dummy', testroot='domain-js')
def test_domain_js_find_obj(app, status, warning):

    def find_obj(prefix, obj_name, obj_type, searchmode=0):
        return app.env.domains['js'].find_obj(
            app.env, prefix, obj_name, obj_type, searchmode)

    app.builder.build_all()

    assert (find_obj(None, u'NONEXISTANT', u'class') ==
            (None, None))
    assert (find_obj(None, u'TopLevel', u'class') ==
            (u'TopLevel', (u'roles', u'class')))
    assert (find_obj(None, u'NestedParentA.NestedChildA', u'class') ==
            (None, None))
    assert (find_obj(None, u'subchild_2', u'func') ==
            (u'subchild_2', (u'roles', u'function')))
