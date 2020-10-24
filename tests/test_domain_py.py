"""
    test_domain_py
    ~~~~~~~~~~~~~~

    Tests the Python Domain

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from unittest.mock import Mock

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (
    desc, desc_addname, desc_annotation, desc_content, desc_name, desc_optional,
    desc_parameter, desc_parameterlist, desc_returns, desc_signature,
    desc_sig_name, desc_sig_operator, desc_sig_punctuation, pending_xref,
)
from sphinx.domains import IndexEntry
from sphinx.domains.python import (
    py_sig_re, _parse_annotation, _pseudo_parse_arglist, PythonDomain, PythonModuleIndex
)
from sphinx.testing import restructuredtext
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
    assert rv == '(a=1)'

    rv = parse('func(a=1, [b=None])')
    assert rv == '(a=1, [b=None])'

    rv = parse('func(a=1[, b=None])')
    assert rv == '(a=1, [b=None])'

    rv = parse("compile(source : string, filename, symbol='file')")
    assert rv == "(source : string, filename, symbol='file')"

    rv = parse('func(a=[], [b=None])')
    assert rv == '(a=[], [b=None])'

    rv = parse('func(a=[][, b=None])')
    assert rv == '(a=[], [b=None])'


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
    refnodes = list(doctree.traverse(pending_xref))
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
    refnodes = list(doctree.traverse(pending_xref))
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
    assert_refnode(refnodes[5], 'module_a.submodule', 'ModTopLevel',
                   'prop', 'attr')
    assert_refnode(refnodes[6], 'module_a.submodule', 'ModTopLevel',
                   'prop', 'meth')
    assert_refnode(refnodes[7], 'module_b.submodule', None,
                   'ModTopLevel', 'class')
    assert_refnode(refnodes[8], 'module_b.submodule', 'ModTopLevel',
                   'ModNoModule', 'class')
    assert_refnode(refnodes[9], False, False, 'int', 'class')
    assert_refnode(refnodes[10], False, False, 'tuple', 'class')
    assert_refnode(refnodes[11], False, False, 'str', 'class')
    assert_refnode(refnodes[12], False, False, 'float', 'class')
    assert_refnode(refnodes[13], False, False, 'list', 'class')
    assert_refnode(refnodes[14], False, False, 'ModTopLevel', 'class')
    assert_refnode(refnodes[15], False, False, 'index', 'doc', domain='std')
    assert len(refnodes) == 16

    doctree = app.env.get_doctree('module_option')
    refnodes = list(doctree.traverse(pending_xref))
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

    assert objects['module_a.submodule.ModTopLevel'][2] == 'class'
    assert objects['module_a.submodule.ModTopLevel.mod_child_1'][2] == 'method'
    assert objects['module_a.submodule.ModTopLevel.mod_child_2'][2] == 'method'
    assert 'ModTopLevel.ModNoModule' not in objects
    assert objects['ModNoModule'][2] == 'class'
    assert objects['module_b.submodule.ModTopLevel'][2] == 'class'

    assert objects['TopLevel'][2] == 'class'
    assert objects['top_level'][2] == 'method'
    assert objects['NestedParentA'][2] == 'class'
    assert objects['NestedParentA.child_1'][2] == 'method'
    assert objects['NestedParentA.any_child'][2] == 'method'
    assert objects['NestedParentA.NestedChildA'][2] == 'class'
    assert objects['NestedParentA.NestedChildA.subchild_1'][2] == 'method'
    assert objects['NestedParentA.NestedChildA.subchild_2'][2] == 'method'
    assert objects['NestedParentA.child_2'][2] == 'method'
    assert objects['NestedParentB'][2] == 'class'
    assert objects['NestedParentB.child_1'][2] == 'method'


@pytest.mark.sphinx('html', testroot='domain-py')
def test_resolve_xref_for_properties(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'module.html').read_text()
    assert ('Link to <a class="reference internal" href="#module_a.submodule.ModTopLevel.prop"'
            ' title="module_a.submodule.ModTopLevel.prop">'
            '<code class="xref py py-attr docutils literal notranslate"><span class="pre">'
            'prop</span> <span class="pre">attribute</span></code></a>' in content)
    assert ('Link to <a class="reference internal" href="#module_a.submodule.ModTopLevel.prop"'
            ' title="module_a.submodule.ModTopLevel.prop">'
            '<code class="xref py py-meth docutils literal notranslate"><span class="pre">'
            'prop</span> <span class="pre">method</span></code></a>' in content)


@pytest.mark.sphinx('dummy', testroot='domain-py')
def test_domain_py_find_obj(app, status, warning):

    def find_obj(modname, prefix, obj_name, obj_type, searchmode=0):
        return app.env.domains['py'].find_obj(
            app.env, modname, prefix, obj_name, obj_type, searchmode)

    app.builder.build_all()

    assert (find_obj(None, None, 'NONEXISTANT', 'class') == [])
    assert (find_obj(None, None, 'NestedParentA', 'class') ==
            [('NestedParentA', ('roles', 'NestedParentA', 'class'))])
    assert (find_obj(None, None, 'NestedParentA.NestedChildA', 'class') ==
            [('NestedParentA.NestedChildA', ('roles', 'NestedParentA.NestedChildA', 'class'))])
    assert (find_obj(None, 'NestedParentA', 'NestedChildA', 'class') ==
            [('NestedParentA.NestedChildA', ('roles', 'NestedParentA.NestedChildA', 'class'))])
    assert (find_obj(None, None, 'NestedParentA.NestedChildA.subchild_1', 'meth') ==
            [('NestedParentA.NestedChildA.subchild_1',
              ('roles', 'NestedParentA.NestedChildA.subchild_1', 'method'))])
    assert (find_obj(None, 'NestedParentA', 'NestedChildA.subchild_1', 'meth') ==
            [('NestedParentA.NestedChildA.subchild_1',
              ('roles', 'NestedParentA.NestedChildA.subchild_1', 'method'))])
    assert (find_obj(None, 'NestedParentA.NestedChildA', 'subchild_1', 'meth') ==
            [('NestedParentA.NestedChildA.subchild_1',
              ('roles', 'NestedParentA.NestedChildA.subchild_1', 'method'))])


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


def test_parse_annotation(app):
    doctree = _parse_annotation("int", app.env)
    assert_node(doctree, ([pending_xref, "int"],))
    assert_node(doctree[0], pending_xref, refdomain="py", reftype="class", reftarget="int")

    doctree = _parse_annotation("List[int]", app.env)
    assert_node(doctree, ([pending_xref, "List"],
                          [desc_sig_punctuation, "["],
                          [pending_xref, "int"],
                          [desc_sig_punctuation, "]"]))

    doctree = _parse_annotation("Tuple[int, int]", app.env)
    assert_node(doctree, ([pending_xref, "Tuple"],
                          [desc_sig_punctuation, "["],
                          [pending_xref, "int"],
                          [desc_sig_punctuation, ", "],
                          [pending_xref, "int"],
                          [desc_sig_punctuation, "]"]))

    doctree = _parse_annotation("Tuple[()]", app.env)
    assert_node(doctree, ([pending_xref, "Tuple"],
                          [desc_sig_punctuation, "["],
                          [desc_sig_punctuation, "("],
                          [desc_sig_punctuation, ")"],
                          [desc_sig_punctuation, "]"]))

    doctree = _parse_annotation("Tuple[int, ...]", app.env)
    assert_node(doctree, ([pending_xref, "Tuple"],
                          [desc_sig_punctuation, "["],
                          [pending_xref, "int"],
                          [desc_sig_punctuation, ", "],
                          [desc_sig_punctuation, "..."],
                          [desc_sig_punctuation, "]"]))

    doctree = _parse_annotation("Callable[[int, int], int]", app.env)
    assert_node(doctree, ([pending_xref, "Callable"],
                          [desc_sig_punctuation, "["],
                          [desc_sig_punctuation, "["],
                          [pending_xref, "int"],
                          [desc_sig_punctuation, ", "],
                          [pending_xref, "int"],
                          [desc_sig_punctuation, "]"],
                          [desc_sig_punctuation, ", "],
                          [pending_xref, "int"],
                          [desc_sig_punctuation, "]"]))

    doctree = _parse_annotation("List[None]", app.env)
    assert_node(doctree, ([pending_xref, "List"],
                          [desc_sig_punctuation, "["],
                          [pending_xref, "None"],
                          [desc_sig_punctuation, "]"]))

    # None type makes an object-reference (not a class reference)
    doctree = _parse_annotation("None", app.env)
    assert_node(doctree, ([pending_xref, "None"],))
    assert_node(doctree[0], pending_xref, refdomain="py", reftype="obj", reftarget="None")


def test_pyfunction_signature(app):
    text = ".. py:function:: hello(name: str) -> str"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "hello"],
                                                    desc_parameterlist,
                                                    [desc_returns, pending_xref, "str"])],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="function",
                domain="py", objtype="function", noindex=False)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, desc_parameter, ([desc_sig_name, "name"],
                                                      [desc_sig_punctuation, ":"],
                                                      " ",
                                                      [nodes.inline, pending_xref, "str"])])


def test_pyfunction_signature_full(app):
    text = (".. py:function:: hello(a: str, b = 1, *args: str, "
            "c: bool = True, d: tuple = (1, 2), **kwargs: str) -> str")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "hello"],
                                                    desc_parameterlist,
                                                    [desc_returns, pending_xref, "str"])],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="function",
                domain="py", objtype="function", noindex=False)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, ([desc_parameter, ([desc_sig_name, "a"],
                                                        [desc_sig_punctuation, ":"],
                                                        " ",
                                                        [desc_sig_name, pending_xref, "str"])],
                                      [desc_parameter, ([desc_sig_name, "b"],
                                                        [desc_sig_operator, "="],
                                                        [nodes.inline, "1"])],
                                      [desc_parameter, ([desc_sig_operator, "*"],
                                                        [desc_sig_name, "args"],
                                                        [desc_sig_punctuation, ":"],
                                                        " ",
                                                        [desc_sig_name, pending_xref, "str"])],
                                      [desc_parameter, ([desc_sig_name, "c"],
                                                        [desc_sig_punctuation, ":"],
                                                        " ",
                                                        [desc_sig_name, pending_xref, "bool"],
                                                        " ",
                                                        [desc_sig_operator, "="],
                                                        " ",
                                                        [nodes.inline, "True"])],
                                      [desc_parameter, ([desc_sig_name, "d"],
                                                        [desc_sig_punctuation, ":"],
                                                        " ",
                                                        [desc_sig_name, pending_xref, "tuple"],
                                                        " ",
                                                        [desc_sig_operator, "="],
                                                        " ",
                                                        [nodes.inline, "(1, 2)"])],
                                      [desc_parameter, ([desc_sig_operator, "**"],
                                                        [desc_sig_name, "kwargs"],
                                                        [desc_sig_punctuation, ":"],
                                                        " ",
                                                        [desc_sig_name, pending_xref, "str"])])])


@pytest.mark.skipif(sys.version_info < (3, 8), reason='python 3.8+ is required.')
def test_pyfunction_signature_full_py38(app):
    # case: separator at head
    text = ".. py:function:: hello(*, a)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, ([desc_parameter, nodes.inline, "*"],
                                      [desc_parameter, desc_sig_name, "a"])])

    # case: separator in the middle
    text = ".. py:function:: hello(a, /, b, *, c)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, ([desc_parameter, desc_sig_name, "a"],
                                      [desc_parameter, desc_sig_operator, "/"],
                                      [desc_parameter, desc_sig_name, "b"],
                                      [desc_parameter, desc_sig_operator, "*"],
                                      [desc_parameter, desc_sig_name, "c"])])

    # case: separator in the middle (2)
    text = ".. py:function:: hello(a, /, *, b)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, ([desc_parameter, desc_sig_name, "a"],
                                      [desc_parameter, desc_sig_operator, "/"],
                                      [desc_parameter, desc_sig_operator, "*"],
                                      [desc_parameter, desc_sig_name, "b"])])

    # case: separator at tail
    text = ".. py:function:: hello(a, /)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, ([desc_parameter, desc_sig_name, "a"],
                                      [desc_parameter, desc_sig_operator, "/"])])


@pytest.mark.skipif(sys.version_info < (3, 8), reason='python 3.8+ is required.')
def test_pyfunction_with_number_literals(app):
    text = ".. py:function:: hello(age=0x10, height=1_6_0)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, ([desc_parameter, ([desc_sig_name, "age"],
                                                        [desc_sig_operator, "="],
                                                        [nodes.inline, "0x10"])],
                                      [desc_parameter, ([desc_sig_name, "height"],
                                                        [desc_sig_operator, "="],
                                                        [nodes.inline, "1_6_0"])])])


def test_optional_pyfunction_signature(app):
    text = ".. py:function:: compile(source [, filename [, symbol]]) -> ast object"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "compile"],
                                                    desc_parameterlist,
                                                    [desc_returns, pending_xref, "ast object"])],
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
            "   :type: int\n"
            "   :value: 1\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "version"],
                                                    [desc_annotation, (": ",
                                                                       [pending_xref, "int"])],
                                                    [desc_annotation, " = 1"])],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="data",
                domain="py", objtype="data", noindex=False)


def test_pydata_signature_old(app):
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
    assert doctree[1][1][1].astext().strip() == 'say()'           # prefix is stripped
    assert doctree[1][1][3].astext().strip() == 'FooBar.say()'    # not stripped


def test_pydata(app):
    text = (".. py:module:: example\n"
            ".. py:data:: var\n"
            "   :type: int\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (nodes.target,
                          addnodes.index,
                          addnodes.index,
                          [desc, ([desc_signature, ([desc_addname, "example."],
                                                    [desc_name, "var"],
                                                    [desc_annotation, (": ",
                                                                       [pending_xref, "int"])])],
                                  [desc_content, ()])]))
    assert_node(doctree[3][0][2][1], pending_xref, **{"py:module": "example"})
    assert 'example.var' in domain.objects
    assert domain.objects['example.var'] == ('index', 'example.var', 'data')


def test_pyfunction(app):
    text = (".. py:function:: func1\n"
            ".. py:module:: example\n"
            ".. py:function:: func2\n"
            "   :async:\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "func1"],
                                                    [desc_parameterlist, ()])],
                                  [desc_content, ()])],
                          nodes.target,
                          addnodes.index,
                          addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "async "],
                                                    [desc_addname, "example."],
                                                    [desc_name, "func2"],
                                                    [desc_parameterlist, ()])],
                                  [desc_content, ()])]))
    assert_node(doctree[0], addnodes.index,
                entries=[('pair', 'built-in function; func1()', 'func1', '', None)])
    assert_node(doctree[3], addnodes.index,
                entries=[('pair', 'module; example', 'module-example', '', None)])
    assert_node(doctree[4], addnodes.index,
                entries=[('single', 'func2() (in module example)', 'example.func2', '', None)])

    assert 'func1' in domain.objects
    assert domain.objects['func1'] == ('index', 'func1', 'function')
    assert 'example.func2' in domain.objects
    assert domain.objects['example.func2'] == ('index', 'example.func2', 'function')


def test_pyclass_options(app):
    text = (".. py:class:: Class1\n"
            ".. py:class:: Class2\n"
            "   :final:\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Class1"])],
                                  [desc_content, ()])],
                          addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "final class "],
                                                    [desc_name, "Class2"])],
                                  [desc_content, ()])]))

    # class
    assert_node(doctree[0], addnodes.index,
                entries=[('single', 'Class1 (built-in class)', 'Class1', '', None)])
    assert 'Class1' in domain.objects
    assert domain.objects['Class1'] == ('index', 'Class1', 'class')

    # :final:
    assert_node(doctree[2], addnodes.index,
                entries=[('single', 'Class2 (built-in class)', 'Class2', '', None)])
    assert 'Class2' in domain.objects
    assert domain.objects['Class2'] == ('index', 'Class2', 'class')


def test_pymethod_options(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:method:: meth1\n"
            "   .. py:method:: meth2\n"
            "      :classmethod:\n"
            "   .. py:method:: meth3\n"
            "      :staticmethod:\n"
            "   .. py:method:: meth4\n"
            "      :async:\n"
            "   .. py:method:: meth5\n"
            "      :property:\n"
            "   .. py:method:: meth6\n"
            "      :abstractmethod:\n"
            "   .. py:method:: meth7\n"
            "      :final:\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Class"])],
                                  [desc_content, (addnodes.index,
                                                  desc,
                                                  addnodes.index,
                                                  desc,
                                                  addnodes.index,
                                                  desc,
                                                  addnodes.index,
                                                  desc,
                                                  addnodes.index,
                                                  desc,
                                                  addnodes.index,
                                                  desc,
                                                  addnodes.index,
                                                  desc)])]))

    # method
    assert_node(doctree[1][1][0], addnodes.index,
                entries=[('single', 'meth1() (Class method)', 'Class.meth1', '', None)])
    assert_node(doctree[1][1][1], ([desc_signature, ([desc_name, "meth1"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth1' in domain.objects
    assert domain.objects['Class.meth1'] == ('index', 'Class.meth1', 'method')

    # :classmethod:
    assert_node(doctree[1][1][2], addnodes.index,
                entries=[('single', 'meth2() (Class class method)', 'Class.meth2', '', None)])
    assert_node(doctree[1][1][3], ([desc_signature, ([desc_annotation, "classmethod "],
                                                     [desc_name, "meth2"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth2' in domain.objects
    assert domain.objects['Class.meth2'] == ('index', 'Class.meth2', 'method')

    # :staticmethod:
    assert_node(doctree[1][1][4], addnodes.index,
                entries=[('single', 'meth3() (Class static method)', 'Class.meth3', '', None)])
    assert_node(doctree[1][1][5], ([desc_signature, ([desc_annotation, "static "],
                                                     [desc_name, "meth3"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth3' in domain.objects
    assert domain.objects['Class.meth3'] == ('index', 'Class.meth3', 'method')

    # :async:
    assert_node(doctree[1][1][6], addnodes.index,
                entries=[('single', 'meth4() (Class method)', 'Class.meth4', '', None)])
    assert_node(doctree[1][1][7], ([desc_signature, ([desc_annotation, "async "],
                                                     [desc_name, "meth4"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth4' in domain.objects
    assert domain.objects['Class.meth4'] == ('index', 'Class.meth4', 'method')

    # :property:
    assert_node(doctree[1][1][8], addnodes.index,
                entries=[('single', 'meth5() (Class property)', 'Class.meth5', '', None)])
    assert_node(doctree[1][1][9], ([desc_signature, ([desc_annotation, "property "],
                                                     [desc_name, "meth5"])],
                                   [desc_content, ()]))
    assert 'Class.meth5' in domain.objects
    assert domain.objects['Class.meth5'] == ('index', 'Class.meth5', 'method')

    # :abstractmethod:
    assert_node(doctree[1][1][10], addnodes.index,
                entries=[('single', 'meth6() (Class method)', 'Class.meth6', '', None)])
    assert_node(doctree[1][1][11], ([desc_signature, ([desc_annotation, "abstract "],
                                                      [desc_name, "meth6"],
                                                      [desc_parameterlist, ()])],
                                    [desc_content, ()]))
    assert 'Class.meth6' in domain.objects
    assert domain.objects['Class.meth6'] == ('index', 'Class.meth6', 'method')

    # :final:
    assert_node(doctree[1][1][12], addnodes.index,
                entries=[('single', 'meth7() (Class method)', 'Class.meth7', '', None)])
    assert_node(doctree[1][1][13], ([desc_signature, ([desc_annotation, "final "],
                                                      [desc_name, "meth7"],
                                                      [desc_parameterlist, ()])],
                                    [desc_content, ()]))
    assert 'Class.meth7' in domain.objects
    assert domain.objects['Class.meth7'] == ('index', 'Class.meth7', 'method')


def test_pyclassmethod(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:classmethod:: meth\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Class"])],
                                  [desc_content, (addnodes.index,
                                                  desc)])]))
    assert_node(doctree[1][1][0], addnodes.index,
                entries=[('single', 'meth() (Class class method)', 'Class.meth', '', None)])
    assert_node(doctree[1][1][1], ([desc_signature, ([desc_annotation, "classmethod "],
                                                     [desc_name, "meth"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth' in domain.objects
    assert domain.objects['Class.meth'] == ('index', 'Class.meth', 'method')


def test_pystaticmethod(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:staticmethod:: meth\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Class"])],
                                  [desc_content, (addnodes.index,
                                                  desc)])]))
    assert_node(doctree[1][1][0], addnodes.index,
                entries=[('single', 'meth() (Class static method)', 'Class.meth', '', None)])
    assert_node(doctree[1][1][1], ([desc_signature, ([desc_annotation, "static "],
                                                     [desc_name, "meth"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth' in domain.objects
    assert domain.objects['Class.meth'] == ('index', 'Class.meth', 'method')


def test_pyattribute(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:attribute:: attr\n"
            "      :type: Optional[str]\n"
            "      :value: ''\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "class "],
                                                    [desc_name, "Class"])],
                                  [desc_content, (addnodes.index,
                                                  desc)])]))
    assert_node(doctree[1][1][0], addnodes.index,
                entries=[('single', 'attr (Class attribute)', 'Class.attr', '', None)])
    assert_node(doctree[1][1][1], ([desc_signature, ([desc_name, "attr"],
                                                     [desc_annotation, (": ",
                                                                        [pending_xref, "Optional"],
                                                                        [desc_sig_punctuation, "["],
                                                                        [pending_xref, "str"],
                                                                        [desc_sig_punctuation, "]"])],
                                                     [desc_annotation, " = ''"])],
                                   [desc_content, ()]))
    assert_node(doctree[1][1][1][0][1][1], pending_xref, **{"py:class": "Class"})
    assert_node(doctree[1][1][1][0][1][3], pending_xref, **{"py:class": "Class"})
    assert 'Class.attr' in domain.objects
    assert domain.objects['Class.attr'] == ('index', 'Class.attr', 'attribute')


def test_pydecorator_signature(app):
    text = ".. py:decorator:: deco"
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_addname, "@"],
                                                    [desc_name, "deco"])],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="function",
                domain="py", objtype="function", noindex=False)

    assert 'deco' in domain.objects
    assert domain.objects['deco'] == ('index', 'deco', 'function')


def test_pydecoratormethod_signature(app):
    text = ".. py:decoratormethod:: deco"
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_addname, "@"],
                                                    [desc_name, "deco"])],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="method",
                domain="py", objtype="method", noindex=False)

    assert 'deco' in domain.objects
    assert domain.objects['deco'] == ('index', 'deco', 'method')


@pytest.mark.sphinx(freshenv=True)
def test_module_index(app):
    text = (".. py:module:: docutils\n"
            ".. py:module:: sphinx\n"
            ".. py:module:: sphinx.config\n"
            ".. py:module:: sphinx.builders\n"
            ".. py:module:: sphinx.builders.html\n"
            ".. py:module:: sphinx_intl\n")
    restructuredtext.parse(app, text)
    index = PythonModuleIndex(app.env.get_domain('py'))
    assert index.generate() == (
        [('d', [IndexEntry('docutils', 0, 'index', 'module-docutils', '', '', '')]),
         ('s', [IndexEntry('sphinx', 1, 'index', 'module-sphinx', '', '', ''),
                IndexEntry('sphinx.builders', 2, 'index', 'module-sphinx.builders', '', '', ''),  # NOQA
                IndexEntry('sphinx.builders.html', 2, 'index', 'module-sphinx.builders.html', '', '', ''),  # NOQA
                IndexEntry('sphinx.config', 2, 'index', 'module-sphinx.config', '', '', ''),
                IndexEntry('sphinx_intl', 0, 'index', 'module-sphinx_intl', '', '', '')])],
        False
    )


@pytest.mark.sphinx(freshenv=True)
def test_module_index_submodule(app):
    text = ".. py:module:: sphinx.config\n"
    restructuredtext.parse(app, text)
    index = PythonModuleIndex(app.env.get_domain('py'))
    assert index.generate() == (
        [('s', [IndexEntry('sphinx', 1, '', '', '', '', ''),
                IndexEntry('sphinx.config', 2, 'index', 'module-sphinx.config', '', '', '')])],
        False
    )


@pytest.mark.sphinx(freshenv=True)
def test_module_index_not_collapsed(app):
    text = (".. py:module:: docutils\n"
            ".. py:module:: sphinx\n")
    restructuredtext.parse(app, text)
    index = PythonModuleIndex(app.env.get_domain('py'))
    assert index.generate() == (
        [('d', [IndexEntry('docutils', 0, 'index', 'module-docutils', '', '', '')]),
         ('s', [IndexEntry('sphinx', 0, 'index', 'module-sphinx', '', '', '')])],
        True
    )


@pytest.mark.sphinx(freshenv=True, confoverrides={'modindex_common_prefix': ['sphinx.']})
def test_modindex_common_prefix(app):
    text = (".. py:module:: docutils\n"
            ".. py:module:: sphinx\n"
            ".. py:module:: sphinx.config\n"
            ".. py:module:: sphinx.builders\n"
            ".. py:module:: sphinx.builders.html\n"
            ".. py:module:: sphinx_intl\n")
    restructuredtext.parse(app, text)
    index = PythonModuleIndex(app.env.get_domain('py'))
    assert index.generate() == (
        [('b', [IndexEntry('sphinx.builders', 1, 'index', 'module-sphinx.builders', '', '', ''),  # NOQA
                IndexEntry('sphinx.builders.html', 2, 'index', 'module-sphinx.builders.html', '', '', '')]),  # NOQA
         ('c', [IndexEntry('sphinx.config', 0, 'index', 'module-sphinx.config', '', '', '')]),
         ('d', [IndexEntry('docutils', 0, 'index', 'module-docutils', '', '', '')]),
         ('s', [IndexEntry('sphinx', 0, 'index', 'module-sphinx', '', '', ''),
                IndexEntry('sphinx_intl', 0, 'index', 'module-sphinx_intl', '', '', '')])],
        True
    )


def test_noindexentry(app):
    text = (".. py:function:: f()\n"
            ".. py:function:: g()\n"
            "   :noindexentry:\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, desc, addnodes.index, desc))
    assert_node(doctree[0], addnodes.index, entries=[('pair', 'built-in function; f()', 'f', '', None)])
    assert_node(doctree[2], addnodes.index, entries=[])

    text = (".. py:class:: f\n"
            ".. py:class:: g\n"
            "   :noindexentry:\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, desc, addnodes.index, desc))
    assert_node(doctree[0], addnodes.index, entries=[('single', 'f (built-in class)', 'f', '', None)])
    assert_node(doctree[2], addnodes.index, entries=[])
