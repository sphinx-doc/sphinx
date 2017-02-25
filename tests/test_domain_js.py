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
def test_build_domain_py_xrefs_resolve_correctly(app, status, warning):
    from sphinx.domains.javascript import JavaScriptDomain

    calls = {}

    def wrapped_find_obj(fn):
        def wrapped(*args):
            ret = fn(*args)
            # args = [domain, env, env object, role text, role type, order]
            calls[args[2:-1]] = ret
            return ret
        return wrapped

    JavaScriptDomain.find_obj = wrapped_find_obj(JavaScriptDomain.find_obj)

    app.builder.build_all()

    calls_expected = {
        (None, u'TopLevel', u'class'): (u'TopLevel', (u'roles', u'class')),
        (None, u'top_level', u'func'): (u'top_level', (u'roles', u'function')),
        (None, u'NestedParentA.NestedChildA', u'class'): (None, None),
        (None, u'NestedChildA.subchild_1', u'func'): (None, None),
        (None, u'subchild_2', u'func'): (u'subchild_2', (u'roles', u'function')),
        (None, u'NestedParentA.child_1', u'func'): (None, None),
        (None, u'NestedChildA.subchild_2', u'func'): (None, None),
        (None, u'NestedChildA', u'class'): (u'NestedChildA', (u'roles', u'class')),
        (None, u'NestedParentB', u'class'): (u'NestedParentB', (u'roles', u'class')),
        (None, u'any_child', None): (u'any_child', (u'roles', u'function')),
        (None, u'child_1', u'func'): (u'child_1', (u'roles', u'function')),
        (None, u'child_2', u'func'): (u'child_2', (u'roles', u'function'))
    }

    assert calls_expected == calls

    with pytest.raises(KeyError):
        assert (calls[('NestedParentA.NestedChildA', 'subchild_2',
                       'func')] \
                == ('NestedParentA.NestedChildA.subchild_2',
                    ('roles', 'function')))
    with pytest.raises(KeyError):
        assert (calls[('NestedParentA.NestedChildA',
                       'NestedParentA.child_1', 'func')] \
                == ('NestedParentA.child_1', ('roles', 'function')))
    with pytest.raises(KeyError):
        assert (calls[('NestedParentA', 'NestedChildA.subchild_2',
                       'func')] \
                == ('NestedParentA.NestedChildA.subchild_2',
                    ('roles', 'function')))
