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
def test_build_domain_py_xrefs_resolve_correctly(app, status, warning):
    from sphinx.domains.python import PythonDomain

    calls = {}

    def wrapped_find_obj(fn):
        def wrapped(*args):
            ret = fn(*args)
            # args = [domain, env, ??, env object, role text, role type, order]
            calls[args[3:-1]] = ret
            return ret
        return wrapped

    PythonDomain.find_obj = wrapped_find_obj(PythonDomain.find_obj)

    app.builder.build_all()

    calls_expected = {
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

    assert calls_expected == calls
