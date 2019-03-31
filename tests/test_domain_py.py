"""
    test_domain_py
    ~~~~~~~~~~~~~~

    Tests the Python Domain

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest.mock import Mock, patch

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (
    desc, desc_addname, desc_annotation, desc_content, desc_name, desc_optional,
    desc_parameter, desc_parameterlist, desc_returns, desc_signature
)
from sphinx.domains.python import py_sig_re, _pseudo_parse_arglist, PythonDomain
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


if False:
    from typing import List, Dict, Optional


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
    assert rv == 'a=1'

    rv = parse('func(a=1, [b=None])')
    assert rv == 'a=1, [b=None]'

    rv = parse('func(a=1[, b=None])')
    assert rv == 'a=1, [b=None]'

    rv = parse("compile(source : string, filename, symbol='file')")
    assert rv == "source : string, filename, symbol='file'"

    rv = parse('func(a=[], [b=None])')
    assert rv == 'a=[], [b=None]'

    rv = parse('func(a=[][, b=None])')
    assert rv == 'a=[], [b=None]'


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
    assert_refnode(refnodes[0], None, None, 'TopLevel', 'class')
    assert_refnode(refnodes[1], None, None, 'top_level', 'meth')
    assert_refnode(refnodes[2], None, 'NestedParentA', 'child_1', 'meth')
    assert_refnode(refnodes[3], None, 'NestedParentA', 'NestedChildA.subchild_2', 'meth')
    assert_refnode(refnodes[4], None, 'NestedParentA', 'child_2', 'meth')
    assert_refnode(refnodes[5], False, 'NestedParentA', 'any_child', domain='')
    assert_refnode(refnodes[6], None, 'NestedParentA', 'NestedChildA', 'class')
    assert_refnode(refnodes[7], None, 'NestedParentA.NestedChildA', 'subchild_2', 'meth')
    assert_refnode(refnodes[8], None, 'NestedParentA.NestedChildA',
                   'NestedParentA.child_1', 'meth')
    assert_refnode(refnodes[9], None, 'NestedParentA', 'NestedChildA.subchild_1', 'meth')
    assert_refnode(refnodes[10], None, 'NestedParentB', 'child_1', 'meth')
    assert_refnode(refnodes[11], None, 'NestedParentB', 'NestedParentB', 'class')
    assert_refnode(refnodes[12], None, None, 'NestedParentA.NestedChildA', 'class')
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

    assert (find_obj(None, None, 'NONEXISTANT', 'class') == [])
    assert (find_obj(None, None, 'NestedParentA', 'class') ==
            [('NestedParentA', ('roles', 'class'))])
    assert (find_obj(None, None, 'NestedParentA.NestedChildA', 'class') ==
            [('NestedParentA.NestedChildA', ('roles', 'class'))])
    assert (find_obj(None, 'NestedParentA', 'NestedChildA', 'class') ==
            [('NestedParentA.NestedChildA', ('roles', 'class'))])
    assert (find_obj(None, None, 'NestedParentA.NestedChildA.subchild_1', 'meth') ==
            [('NestedParentA.NestedChildA.subchild_1', ('roles', 'method'))])
    assert (find_obj(None, 'NestedParentA', 'NestedChildA.subchild_1', 'meth') ==
            [('NestedParentA.NestedChildA.subchild_1', ('roles', 'method'))])
    assert (find_obj(None, 'NestedParentA.NestedChildA', 'subchild_1', 'meth') ==
            [('NestedParentA.NestedChildA.subchild_1', ('roles', 'method'))])


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


def test_pyfunction_signature(app):
    text = ".. py:function:: hello(name: str) -> str"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "hello"],
                                                    desc_parameterlist,
                                                    [desc_returns, "str"])],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="function",
                domain="py", objtype="function", noindex=False)
    assert_node(doctree[1][0][1], [desc_parameterlist, desc_parameter, "name: str"])


def test_optional_pyfunction_signature(app):
    text = ".. py:function:: compile(source [, filename [, symbol]]) -> ast object"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "compile"],
                                                    desc_parameterlist,
                                                    [desc_returns, "ast object"])],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="function",
                domain="py", objtype="function", noindex=False)
    assert_node(doctree[1][0][1],
                ([desc_parameter, "source"],
                 [desc_optional, ([desc_parameter, "filename"],
                                  [desc_optional, desc_parameter, "symbol"])]))


def test_pyexception_signature(app):
    text = ".. py:exception:: exceptions.IOError"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "exception "],
                                                    [desc_addname, "exceptions."],
                                                    [desc_name, "IOError"])],
                                  desc_content)]))
    assert_node(doctree[1], desc, desctype="exception",
                domain="py", objtype="exception", noindex=False)


def test_exceptions_module_is_ignored(app):
    text = (".. py:exception:: IOError\n"
            "   :module: exceptions\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "exception "],
                                                    [desc_name, "IOError"])],
                                  desc_content)]))
    assert_node(doctree[1], desc, desctype="exception",
                domain="py", objtype="exception", noindex=False)


def test_pydata_signature(app):
    text = (".. py:data:: version\n"
            "   :annotation: = 1\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "version"],
                                                    [desc_annotation, " = 1"])],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="data",
                domain="py", objtype="data", noindex=False)


def test_pyobject_prefix(app):
    text = (".. py:class:: Foo\n"
            "\n"
            "   .. py:method:: Foo.say\n"
            "   .. py:method:: FooBar.say")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Foo"])],
                                  [desc_content, (addnodes.index,
                                                  desc,
                                                  addnodes.index,
                                                  desc)])]))
    assert doctree[1][1][1].astext().strip() == 'say'           # prefix is stripped
    assert doctree[1][1][3].astext().strip() == 'FooBar.say'    # not stripped


def assert_classmember_list(node, num_methods):
    # type: (desc_content, int) -> None
    assert isinstance(node, desc_content)
    num_nodes = len(node)
    assert num_nodes == num_methods * 2, \
        f"Expected two nodes for %d methods each, got %d total" % (num_methods, num_nodes)

    def iter_a_b(a, b, length):
        """Iterate over (a, b, a, b, …) to yield 2*length items."""
        for i in range(length):
            yield a
            yield b

    inner_node_spec = tuple(iter_a_b(a=addnodes.index,
                                     b=[desc, (desc_signature, desc_content)],
                                     length=num_methods))
    assert_node(node, inner_node_spec)


def assert_classmember_sig(node, name, prefix=None, has_params=True):
    # type: (desc_signature, Optional[str], Optional[str], bool) -> None
    """Assert that the structure of a `desc_signature` node of a classmember is sound.

    The pseudo-xml representation of a fully-fleshed node looks something like this:

        <desc_signature class="Foo" […]>
            <desc_annotation xml:space="preserve">
                abstract static
            <desc_name xml:space="preserve">
                baz
            <desc_parameterlist xml:space="preserve">

    The `annotation` part only appears when there is a prefix (like ``static ``),
    the `parameterlist` only appears for methods.
    """
    assert isinstance(node, desc_signature)
    inner_node_spec = []
    if prefix is not None:
        inner_node_spec.append([desc_annotation, prefix])

    inner_node_spec.append([desc_name, name])

    if has_params:
        inner_node_spec.append(desc_parameterlist)

    assert_node(node, [desc_signature, tuple(inner_node_spec)])


def assert_index(node, text, target):
    # type: (addnodes.index, str, str) -> None
    assert isinstance(node, addnodes.index)
    assert len(node.get('entries', [])) == 1
    entrytype, entryname, entrytarget, ignored, key = node['entries'][0]
    assert entrytype == 'single', "Unexpected entrytype %s" % entrytype
    assert entryname == text
    assert entrytarget == target


def test_method_prefix_included(app):
    text = (".. py:class:: Foo\n"
            "\n"
            "   .. py:method:: Foo.say\n"
            "      :classmethod:\n"
            "\n"
            "   .. py:method:: Foo.listen")
    doctree = restructuredtext.parse(app, text)

    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Foo"])],
                                  desc_content)]))

    foo_content = doctree[1][1]  # type: desc_content
    assert_classmember_list(foo_content, 2)
    assert_classmember_sig(foo_content[1][0], name="say", prefix="classmethod ")
    assert_classmember_sig(foo_content[3][0], name="listen", prefix=None)


def test_method_objtype_aliases(app):
    text = (".. py:class:: Foo\n"
            "\n"
            "   .. py:classmethod:: Foo.cm_by_objtype\n"
            "\n"
            "   .. py:method:: Foo.cm_by_option\n"
            "      :classmethod:\n"
            "\n"
            "   .. py:staticmethod:: Foo.sm_by_objtype\n"
            "\n"
            "   .. py:method:: Foo.sm_by_option\n"
            "      :static:\n"
            "\n"
            "   .. py:method:: Foo.ordinary_method\n"
            "\n")
    doctree = restructuredtext.parse(app, text)

    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Foo"])],
                                  desc_content)]))

    foo_content = doctree[1][1]  # type: desc_content
    assert_classmember_list(foo_content, 5)
    assert_classmember_sig(foo_content[1][0], name="cm_by_objtype", prefix="classmethod ")
    assert_classmember_sig(foo_content[3][0], name="cm_by_option", prefix="classmethod ")
    assert_classmember_sig(foo_content[5][0], name="sm_by_objtype", prefix="static ")
    assert_classmember_sig(foo_content[7][0], name="sm_by_option", prefix="static ")
    assert_classmember_sig(foo_content[9][0], name="ordinary_method", prefix=None)


def test_classmember_abstract_prefixes(app):
    text = (".. py:class:: Foo\n"
            "\n"
            "   .. py:method:: Foo.foo\n"
            "      :abstract:"
            "\n"
            "   .. py:method:: Foo.bar\n"
            "      :abstract:\n"
            "      :classmethod:\n"
            "\n"
            "   .. py:method:: Foo.baz\n"
            "      :abstract:\n"
            "      :static:\n"
            "\n"
            "   .. py:attribute:: Foo.attr\n"
            "      :abstract:\n"
            "\n"
            )
    doctree = restructuredtext.parse(app, text)

    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Foo"])],
                                  desc_content)]))

    foo_content = doctree[1][1]  # type: desc_content
    assert_classmember_list(foo_content, 4)
    assert_index(foo_content[0], text="foo() (abstract Foo method)", target="Foo.foo")
    assert_classmember_sig(foo_content[1][0], name="foo", prefix="abstract ")
    assert_index(foo_content[0], text="bar() (abstract Foo classmethod)", target="Foo.bar")
    assert_classmember_sig(foo_content[3][0], name="bar", prefix="abstract classmethod ")
    assert_index(foo_content[0], text="foo() (abstract static Foo method)", target="Foo.baz")
    assert_classmember_sig(foo_content[5][0], name="baz", prefix="abstract static ")
    assert_index(foo_content[0], text="foo() (abstract Foo attribute)", target="Foo.attr")
    assert_classmember_sig(foo_content[7][0], name="attr", prefix="abstract ", has_params=False)
