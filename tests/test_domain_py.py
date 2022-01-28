"""
    test_domain_py
    ~~~~~~~~~~~~~~

    Tests the Python Domain

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
from unittest.mock import Mock

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (desc, desc_addname, desc_annotation, desc_content, desc_name,
                             desc_optional, desc_parameter, desc_parameterlist, desc_returns,
                             desc_sig_keyword, desc_sig_literal_number,
                             desc_sig_literal_string, desc_sig_name, desc_sig_operator,
                             desc_sig_punctuation, desc_sig_space, desc_signature,
                             pending_xref)
from sphinx.domains import IndexEntry
from sphinx.domains.python import (PythonDomain, PythonModuleIndex, _parse_annotation,
                                   _pseudo_parse_arglist, py_sig_re)
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
    refnodes = list(doctree.findall(pending_xref))
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
    refnodes = list(doctree.findall(pending_xref))
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
    refnodes = list(doctree.findall(pending_xref))
    print(refnodes)
    print(refnodes[0])
    print(refnodes[1])
    assert_refnode(refnodes[0], 'test.extra', 'B', 'foo', 'meth')
    assert_refnode(refnodes[1], 'test.extra', 'B', 'foo', 'meth')
    assert len(refnodes) == 2


@pytest.mark.sphinx('html', testroot='domain-py')
def test_domain_py_xrefs_abbreviations(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'abbr.html').read_text()
    assert re.search(r'normal: <a .* href="module.html#module_a.submodule.ModTopLevel.'
                     r'mod_child_1" .*><.*>module_a.submodule.ModTopLevel.mod_child_1\(\)'
                     r'<.*></a>',
                     content)
    assert re.search(r'relative: <a .* href="module.html#module_a.submodule.ModTopLevel.'
                     r'mod_child_1" .*><.*>ModTopLevel.mod_child_1\(\)<.*></a>',
                     content)
    assert re.search(r'short name: <a .* href="module.html#module_a.submodule.ModTopLevel.'
                     r'mod_child_1" .*><.*>mod_child_1\(\)<.*></a>',
                     content)
    assert re.search(r'relative \+ short name: <a .* href="module.html#module_a.submodule.'
                     r'ModTopLevel.mod_child_1" .*><.*>mod_child_1\(\)<.*></a>',
                     content)
    assert re.search(r'short name \+ relative: <a .* href="module.html#module_a.submodule.'
                     r'ModTopLevel.mod_child_1" .*><.*>mod_child_1\(\)<.*></a>',
                     content)


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
    assert ('Link to <a class="reference internal" href="#module_a.submodule.ModTopLevel.prop"'
            ' title="module_a.submodule.ModTopLevel.prop">'
            '<code class="xref py py-attr docutils literal notranslate"><span class="pre">'
            'prop</span> <span class="pre">attribute</span></code></a>' in content)


@pytest.mark.sphinx('dummy', testroot='domain-py')
def test_domain_py_find_obj(app, status, warning):

    def find_obj(modname, prefix, obj_name, obj_type, searchmode=0):
        return app.env.domains['py'].find_obj(
            app.env, modname, prefix, obj_name, obj_type, searchmode)

    app.builder.build_all()

    assert (find_obj(None, None, 'NONEXISTANT', 'class') == [])
    assert (find_obj(None, None, 'NestedParentA', 'class') ==
            [('NestedParentA', ('roles', 'NestedParentA', 'class', False))])
    assert (find_obj(None, None, 'NestedParentA.NestedChildA', 'class') ==
            [('NestedParentA.NestedChildA',
              ('roles', 'NestedParentA.NestedChildA', 'class', False))])
    assert (find_obj(None, 'NestedParentA', 'NestedChildA', 'class') ==
            [('NestedParentA.NestedChildA',
              ('roles', 'NestedParentA.NestedChildA', 'class', False))])
    assert (find_obj(None, None, 'NestedParentA.NestedChildA.subchild_1', 'meth') ==
            [('NestedParentA.NestedChildA.subchild_1',
              ('roles', 'NestedParentA.NestedChildA.subchild_1', 'method', False))])
    assert (find_obj(None, 'NestedParentA', 'NestedChildA.subchild_1', 'meth') ==
            [('NestedParentA.NestedChildA.subchild_1',
              ('roles', 'NestedParentA.NestedChildA.subchild_1', 'method', False))])
    assert (find_obj(None, 'NestedParentA.NestedChildA', 'subchild_1', 'meth') ==
            [('NestedParentA.NestedChildA.subchild_1',
              ('roles', 'NestedParentA.NestedChildA.subchild_1', 'method', False))])


@pytest.mark.sphinx('html', testroot='domain-py', freshenv=True)
def test_domain_py_canonical(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'canonical.html').read_text()
    assert ('<a class="reference internal" href="#canonical.Foo" title="canonical.Foo">'
            '<code class="xref py py-class docutils literal notranslate">'
            '<span class="pre">Foo</span></code></a>' in content)
    assert warning.getvalue() == ''


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
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
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
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
                          [desc_sig_punctuation, "..."],
                          [desc_sig_punctuation, "]"]))

    doctree = _parse_annotation("Callable[[int, int], int]", app.env)
    assert_node(doctree, ([pending_xref, "Callable"],
                          [desc_sig_punctuation, "["],
                          [desc_sig_punctuation, "["],
                          [pending_xref, "int"],
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
                          [pending_xref, "int"],
                          [desc_sig_punctuation, "]"],
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
                          [pending_xref, "int"],
                          [desc_sig_punctuation, "]"]))

    doctree = _parse_annotation("Callable[[], int]", app.env)
    assert_node(doctree, ([pending_xref, "Callable"],
                          [desc_sig_punctuation, "["],
                          [desc_sig_punctuation, "["],
                          [desc_sig_punctuation, "]"],
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
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

    # Literal type makes an object-reference (not a class reference)
    doctree = _parse_annotation("typing.Literal['a', 'b']", app.env)
    assert_node(doctree, ([pending_xref, "Literal"],
                          [desc_sig_punctuation, "["],
                          [desc_sig_literal_string, "'a'"],
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
                          [desc_sig_literal_string, "'b'"],
                          [desc_sig_punctuation, "]"]))
    assert_node(doctree[0], pending_xref, refdomain="py", reftype="obj", reftarget="typing.Literal")


def test_parse_annotation_suppress(app):
    doctree = _parse_annotation("~typing.Dict[str, str]", app.env)
    assert_node(doctree, ([pending_xref, "Dict"],
                          [desc_sig_punctuation, "["],
                          [pending_xref, "str"],
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
                          [pending_xref, "str"],
                          [desc_sig_punctuation, "]"]))
    assert_node(doctree[0], pending_xref, refdomain="py", reftype="obj", reftarget="typing.Dict")


@pytest.mark.skipif(sys.version_info < (3, 8), reason='python 3.8+ is required.')
def test_parse_annotation_Literal(app):
    doctree = _parse_annotation("Literal[True, False]", app.env)
    assert_node(doctree, ([pending_xref, "Literal"],
                          [desc_sig_punctuation, "["],
                          [desc_sig_keyword, "True"],
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
                          [desc_sig_keyword, "False"],
                          [desc_sig_punctuation, "]"]))

    doctree = _parse_annotation("typing.Literal[0, 1, 'abc']", app.env)
    assert_node(doctree, ([pending_xref, "Literal"],
                          [desc_sig_punctuation, "["],
                          [desc_sig_literal_number, "0"],
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
                          [desc_sig_literal_number, "1"],
                          [desc_sig_punctuation, ","],
                          desc_sig_space,
                          [desc_sig_literal_string, "'abc'"],
                          [desc_sig_punctuation, "]"]))


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
                                                      desc_sig_space,
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
                                                        desc_sig_space,
                                                        [desc_sig_name, pending_xref, "str"])],
                                      [desc_parameter, ([desc_sig_name, "b"],
                                                        [desc_sig_operator, "="],
                                                        [nodes.inline, "1"])],
                                      [desc_parameter, ([desc_sig_operator, "*"],
                                                        [desc_sig_name, "args"],
                                                        [desc_sig_punctuation, ":"],
                                                        desc_sig_space,
                                                        [desc_sig_name, pending_xref, "str"])],
                                      [desc_parameter, ([desc_sig_name, "c"],
                                                        [desc_sig_punctuation, ":"],
                                                        desc_sig_space,
                                                        [desc_sig_name, pending_xref, "bool"],
                                                        desc_sig_space,
                                                        [desc_sig_operator, "="],
                                                        desc_sig_space,
                                                        [nodes.inline, "True"])],
                                      [desc_parameter, ([desc_sig_name, "d"],
                                                        [desc_sig_punctuation, ":"],
                                                        desc_sig_space,
                                                        [desc_sig_name, pending_xref, "tuple"],
                                                        desc_sig_space,
                                                        [desc_sig_operator, "="],
                                                        desc_sig_space,
                                                        [nodes.inline, "(1, 2)"])],
                                      [desc_parameter, ([desc_sig_operator, "**"],
                                                        [desc_sig_name, "kwargs"],
                                                        [desc_sig_punctuation, ":"],
                                                        desc_sig_space,
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


def test_pyfunction_with_union_type_operator(app):
    text = ".. py:function:: hello(age: int | None)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, ([desc_parameter, ([desc_sig_name, "age"],
                                                        [desc_sig_punctuation, ":"],
                                                        desc_sig_space,
                                                        [desc_sig_name, ([pending_xref, "int"],
                                                                         desc_sig_space,
                                                                         [desc_sig_punctuation, "|"],
                                                                         desc_sig_space,
                                                                         [pending_xref, "None"])])])])


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
                ([desc_parameter, ([desc_sig_name, "source"])],
                 [desc_optional, ([desc_parameter, ([desc_sig_name, "filename"])],
                                  [desc_optional, desc_parameter, ([desc_sig_name, "symbol"])])]))


def test_pyexception_signature(app):
    text = ".. py:exception:: builtins.IOError"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ('exception', desc_sig_space)],
                                                    [desc_addname, "builtins."],
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
                                                    [desc_annotation, ([desc_sig_punctuation, ':'],
                                                                       desc_sig_space,
                                                                       [pending_xref, "int"])],
                                                    [desc_annotation, (
                                                        desc_sig_space,
                                                        [desc_sig_punctuation, '='],
                                                        desc_sig_space,
                                                        "1")]
                                                    )],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="data",
                domain="py", objtype="data", noindex=False)


def test_pydata_signature_old(app):
    text = (".. py:data:: version\n"
            "   :annotation: = 1\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "version"],
                                                    [desc_annotation, (desc_sig_space,
                                                                       "= 1")])],
                                  desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="data",
                domain="py", objtype="data", noindex=False)


def test_pydata_with_union_type_operator(app):
    text = (".. py:data:: version\n"
            "   :type: int | str")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree[1][0],
                ([desc_name, "version"],
                 [desc_annotation, ([desc_sig_punctuation, ':'],
                                    desc_sig_space,
                                    [pending_xref, "int"],
                                    desc_sig_space,
                                    [desc_sig_punctuation, "|"],
                                    desc_sig_space,
                                    [pending_xref, "str"])]))


def test_pyobject_prefix(app):
    text = (".. py:class:: Foo\n"
            "\n"
            "   .. py:method:: Foo.say\n"
            "   .. py:method:: FooBar.say")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ('class', desc_sig_space)],
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
                                                    [desc_annotation, ([desc_sig_punctuation, ':'],
                                                                       desc_sig_space,
                                                                       [pending_xref, "int"])])],
                                  [desc_content, ()])]))
    assert_node(doctree[3][0][2][2], pending_xref, **{"py:module": "example"})
    assert 'example.var' in domain.objects
    assert domain.objects['example.var'] == ('index', 'example.var', 'data', False)


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
                          [desc, ([desc_signature, ([desc_annotation, ([desc_sig_keyword, 'async'],
                                                                       desc_sig_space)],
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
    assert domain.objects['func1'] == ('index', 'func1', 'function', False)
    assert 'example.func2' in domain.objects
    assert domain.objects['example.func2'] == ('index', 'example.func2', 'function', False)


def test_pyclass_options(app):
    text = (".. py:class:: Class1\n"
            ".. py:class:: Class2\n"
            "   :final:\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
                                                    [desc_name, "Class1"])],
                                  [desc_content, ()])],
                          addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ("final",
                                                                       desc_sig_space,
                                                                       "class",
                                                                       desc_sig_space)],
                                                    [desc_name, "Class2"])],
                                  [desc_content, ()])]))

    # class
    assert_node(doctree[0], addnodes.index,
                entries=[('single', 'Class1 (built-in class)', 'Class1', '', None)])
    assert 'Class1' in domain.objects
    assert domain.objects['Class1'] == ('index', 'Class1', 'class', False)

    # :final:
    assert_node(doctree[2], addnodes.index,
                entries=[('single', 'Class2 (built-in class)', 'Class2', '', None)])
    assert 'Class2' in domain.objects
    assert domain.objects['Class2'] == ('index', 'Class2', 'class', False)


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
                          [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
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
    assert domain.objects['Class.meth1'] == ('index', 'Class.meth1', 'method', False)

    # :classmethod:
    assert_node(doctree[1][1][2], addnodes.index,
                entries=[('single', 'meth2() (Class class method)', 'Class.meth2', '', None)])
    assert_node(doctree[1][1][3], ([desc_signature, ([desc_annotation, ("classmethod", desc_sig_space)],
                                                     [desc_name, "meth2"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth2' in domain.objects
    assert domain.objects['Class.meth2'] == ('index', 'Class.meth2', 'method', False)

    # :staticmethod:
    assert_node(doctree[1][1][4], addnodes.index,
                entries=[('single', 'meth3() (Class static method)', 'Class.meth3', '', None)])
    assert_node(doctree[1][1][5], ([desc_signature, ([desc_annotation, ("static", desc_sig_space)],
                                                     [desc_name, "meth3"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth3' in domain.objects
    assert domain.objects['Class.meth3'] == ('index', 'Class.meth3', 'method', False)

    # :async:
    assert_node(doctree[1][1][6], addnodes.index,
                entries=[('single', 'meth4() (Class method)', 'Class.meth4', '', None)])
    assert_node(doctree[1][1][7], ([desc_signature, ([desc_annotation, ("async", desc_sig_space)],
                                                     [desc_name, "meth4"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth4' in domain.objects
    assert domain.objects['Class.meth4'] == ('index', 'Class.meth4', 'method', False)

    # :property:
    assert_node(doctree[1][1][8], addnodes.index,
                entries=[('single', 'meth5 (Class property)', 'Class.meth5', '', None)])
    assert_node(doctree[1][1][9], ([desc_signature, ([desc_annotation, ("property", desc_sig_space)],
                                                     [desc_name, "meth5"])],
                                   [desc_content, ()]))
    assert 'Class.meth5' in domain.objects
    assert domain.objects['Class.meth5'] == ('index', 'Class.meth5', 'method', False)

    # :abstractmethod:
    assert_node(doctree[1][1][10], addnodes.index,
                entries=[('single', 'meth6() (Class method)', 'Class.meth6', '', None)])
    assert_node(doctree[1][1][11], ([desc_signature, ([desc_annotation, ("abstract", desc_sig_space)],
                                                      [desc_name, "meth6"],
                                                      [desc_parameterlist, ()])],
                                    [desc_content, ()]))
    assert 'Class.meth6' in domain.objects
    assert domain.objects['Class.meth6'] == ('index', 'Class.meth6', 'method', False)

    # :final:
    assert_node(doctree[1][1][12], addnodes.index,
                entries=[('single', 'meth7() (Class method)', 'Class.meth7', '', None)])
    assert_node(doctree[1][1][13], ([desc_signature, ([desc_annotation, ("final", desc_sig_space)],
                                                      [desc_name, "meth7"],
                                                      [desc_parameterlist, ()])],
                                    [desc_content, ()]))
    assert 'Class.meth7' in domain.objects
    assert domain.objects['Class.meth7'] == ('index', 'Class.meth7', 'method', False)


def test_pyclassmethod(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:classmethod:: meth\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
                                                    [desc_name, "Class"])],
                                  [desc_content, (addnodes.index,
                                                  desc)])]))
    assert_node(doctree[1][1][0], addnodes.index,
                entries=[('single', 'meth() (Class class method)', 'Class.meth', '', None)])
    assert_node(doctree[1][1][1], ([desc_signature, ([desc_annotation, ("classmethod", desc_sig_space)],
                                                     [desc_name, "meth"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth' in domain.objects
    assert domain.objects['Class.meth'] == ('index', 'Class.meth', 'method', False)


def test_pystaticmethod(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:staticmethod:: meth\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
                                                    [desc_name, "Class"])],
                                  [desc_content, (addnodes.index,
                                                  desc)])]))
    assert_node(doctree[1][1][0], addnodes.index,
                entries=[('single', 'meth() (Class static method)', 'Class.meth', '', None)])
    assert_node(doctree[1][1][1], ([desc_signature, ([desc_annotation, ("static", desc_sig_space)],
                                                     [desc_name, "meth"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth' in domain.objects
    assert domain.objects['Class.meth'] == ('index', 'Class.meth', 'method', False)


def test_pyattribute(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:attribute:: attr\n"
            "      :type: Optional[str]\n"
            "      :value: ''\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
                                                    [desc_name, "Class"])],
                                  [desc_content, (addnodes.index,
                                                  desc)])]))
    assert_node(doctree[1][1][0], addnodes.index,
                entries=[('single', 'attr (Class attribute)', 'Class.attr', '', None)])
    assert_node(doctree[1][1][1], ([desc_signature, ([desc_name, "attr"],
                                                     [desc_annotation, ([desc_sig_punctuation, ':'],
                                                                        desc_sig_space,
                                                                        [pending_xref, "Optional"],
                                                                        [desc_sig_punctuation, "["],
                                                                        [pending_xref, "str"],
                                                                        [desc_sig_punctuation, "]"])],
                                                     [desc_annotation, (desc_sig_space,
                                                                        [desc_sig_punctuation, '='],
                                                                        desc_sig_space,
                                                                        "''")]
                                                     )],
                                   [desc_content, ()]))
    assert_node(doctree[1][1][1][0][1][2], pending_xref, **{"py:class": "Class"})
    assert_node(doctree[1][1][1][0][1][4], pending_xref, **{"py:class": "Class"})
    assert 'Class.attr' in domain.objects
    assert domain.objects['Class.attr'] == ('index', 'Class.attr', 'attribute', False)


def test_pyproperty(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:property:: prop1\n"
            "      :abstractmethod:\n"
            "      :type: str\n"
            "\n"
            "   .. py:property:: prop2\n"
            "      :classmethod:\n"
            "      :type: str\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
                                                    [desc_name, "Class"])],
                                  [desc_content, (addnodes.index,
                                                  desc,
                                                  addnodes.index,
                                                  desc)])]))
    assert_node(doctree[1][1][0], addnodes.index,
                entries=[('single', 'prop1 (Class property)', 'Class.prop1', '', None)])
    assert_node(doctree[1][1][1], ([desc_signature, ([desc_annotation, ("abstract", desc_sig_space,
                                                                        "property", desc_sig_space)],
                                                     [desc_name, "prop1"],
                                                     [desc_annotation, ([desc_sig_punctuation, ':'],
                                                                        desc_sig_space,
                                                                        [pending_xref, "str"])])],
                                   [desc_content, ()]))
    assert_node(doctree[1][1][2], addnodes.index,
                entries=[('single', 'prop2 (Class property)', 'Class.prop2', '', None)])
    assert_node(doctree[1][1][3], ([desc_signature, ([desc_annotation, ("class", desc_sig_space,
                                                                        "property", desc_sig_space)],
                                                     [desc_name, "prop2"],
                                                     [desc_annotation, ([desc_sig_punctuation, ':'],
                                                                        desc_sig_space,
                                                                        [pending_xref, "str"])])],
                                   [desc_content, ()]))
    assert 'Class.prop1' in domain.objects
    assert domain.objects['Class.prop1'] == ('index', 'Class.prop1', 'property', False)
    assert 'Class.prop2' in domain.objects
    assert domain.objects['Class.prop2'] == ('index', 'Class.prop2', 'property', False)


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
    assert domain.objects['deco'] == ('index', 'deco', 'function', False)


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
    assert domain.objects['deco'] == ('index', 'deco', 'method', False)


def test_canonical(app):
    text = (".. py:class:: io.StringIO\n"
            "   :canonical: _io.StringIO")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
                                                    [desc_addname, "io."],
                                                    [desc_name, "StringIO"])],
                                  desc_content)]))
    assert 'io.StringIO' in domain.objects
    assert domain.objects['io.StringIO'] == ('index', 'io.StringIO', 'class', False)
    assert domain.objects['_io.StringIO'] == ('index', 'io.StringIO', 'class', True)


def test_canonical_definition_overrides(app, warning):
    text = (".. py:class:: io.StringIO\n"
            "   :canonical: _io.StringIO\n"
            ".. py:class:: _io.StringIO\n")
    restructuredtext.parse(app, text)
    assert warning.getvalue() == ""

    domain = app.env.get_domain('py')
    assert domain.objects['_io.StringIO'] == ('index', 'id0', 'class', False)


def test_canonical_definition_skip(app, warning):
    text = (".. py:class:: _io.StringIO\n"
            ".. py:class:: io.StringIO\n"
            "   :canonical: _io.StringIO\n")

    restructuredtext.parse(app, text)
    assert warning.getvalue() == ""

    domain = app.env.get_domain('py')
    assert domain.objects['_io.StringIO'] == ('index', 'io.StringIO', 'class', False)


def test_canonical_duplicated(app, warning):
    text = (".. py:class:: mypackage.StringIO\n"
            "   :canonical: _io.StringIO\n"
            ".. py:class:: io.StringIO\n"
            "   :canonical: _io.StringIO\n")

    restructuredtext.parse(app, text)
    assert warning.getvalue() != ""


def test_info_field_list(app):
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :param str name: blah blah\n"
            "   :param age: blah blah\n"
            "   :type age: int\n"
            "   :param items: blah blah\n"
            "   :type items: Tuple[str, ...]\n"
            "   :param Dict[str, str] params: blah blah\n")
    doctree = restructuredtext.parse(app, text)
    print(doctree)

    assert_node(doctree, (nodes.target,
                          addnodes.index,
                          addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
                                                    [desc_addname, "example."],
                                                    [desc_name, "Class"])],
                                  [desc_content, nodes.field_list, nodes.field])]))
    assert_node(doctree[3][1][0][0],
                ([nodes.field_name, "Parameters"],
                 [nodes.field_body, nodes.bullet_list, ([nodes.list_item, nodes.paragraph],
                                                        [nodes.list_item, nodes.paragraph],
                                                        [nodes.list_item, nodes.paragraph],
                                                        [nodes.list_item, nodes.paragraph])]))

    # :param str name:
    assert_node(doctree[3][1][0][0][1][0][0][0],
                ([addnodes.literal_strong, "name"],
                 " (",
                 [pending_xref, addnodes.literal_emphasis, "str"],
                 ")",
                 " -- ",
                 "blah blah"))
    assert_node(doctree[3][1][0][0][1][0][0][0][2], pending_xref,
                refdomain="py", reftype="class", reftarget="str",
                **{"py:module": "example", "py:class": "Class"})

    # :param age: + :type age:
    assert_node(doctree[3][1][0][0][1][0][1][0],
                ([addnodes.literal_strong, "age"],
                 " (",
                 [pending_xref, addnodes.literal_emphasis, "int"],
                 ")",
                 " -- ",
                 "blah blah"))
    assert_node(doctree[3][1][0][0][1][0][1][0][2], pending_xref,
                refdomain="py", reftype="class", reftarget="int",
                **{"py:module": "example", "py:class": "Class"})

    # :param items: + :type items:
    assert_node(doctree[3][1][0][0][1][0][2][0],
                ([addnodes.literal_strong, "items"],
                 " (",
                 [pending_xref, addnodes.literal_emphasis, "Tuple"],
                 [addnodes.literal_emphasis, "["],
                 [pending_xref, addnodes.literal_emphasis, "str"],
                 [addnodes.literal_emphasis, ", "],
                 [addnodes.literal_emphasis, "..."],
                 [addnodes.literal_emphasis, "]"],
                 ")",
                 " -- ",
                 "blah blah"))
    assert_node(doctree[3][1][0][0][1][0][2][0][2], pending_xref,
                refdomain="py", reftype="class", reftarget="Tuple",
                **{"py:module": "example", "py:class": "Class"})
    assert_node(doctree[3][1][0][0][1][0][2][0][4], pending_xref,
                refdomain="py", reftype="class", reftarget="str",
                **{"py:module": "example", "py:class": "Class"})

    # :param Dict[str, str] params:
    assert_node(doctree[3][1][0][0][1][0][3][0],
                ([addnodes.literal_strong, "params"],
                 " (",
                 [pending_xref, addnodes.literal_emphasis, "Dict"],
                 [addnodes.literal_emphasis, "["],
                 [pending_xref, addnodes.literal_emphasis, "str"],
                 [addnodes.literal_emphasis, ", "],
                 [pending_xref, addnodes.literal_emphasis, "str"],
                 [addnodes.literal_emphasis, "]"],
                 ")",
                 " -- ",
                 "blah blah"))
    assert_node(doctree[3][1][0][0][1][0][3][0][2], pending_xref,
                refdomain="py", reftype="class", reftarget="Dict",
                **{"py:module": "example", "py:class": "Class"})
    assert_node(doctree[3][1][0][0][1][0][3][0][4], pending_xref,
                refdomain="py", reftype="class", reftarget="str",
                **{"py:module": "example", "py:class": "Class"})
    assert_node(doctree[3][1][0][0][1][0][3][0][6], pending_xref,
                refdomain="py", reftype="class", reftarget="str",
                **{"py:module": "example", "py:class": "Class"})


def test_info_field_list_piped_type(app):
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :param age: blah blah\n"
            "   :type age: int | str\n")
    doctree = restructuredtext.parse(app, text)

    assert_node(doctree,
                (nodes.target,
                 addnodes.index,
                 addnodes.index,
                 [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
                                           [desc_addname, "example."],
                                           [desc_name, "Class"])],
                         [desc_content, nodes.field_list, nodes.field, (nodes.field_name,
                                                                        nodes.field_body)])]))
    assert_node(doctree[3][1][0][0][1],
                ([nodes.paragraph, ([addnodes.literal_strong, "age"],
                                    " (",
                                    [pending_xref, addnodes.literal_emphasis, "int"],
                                    [addnodes.literal_emphasis, " | "],
                                    [pending_xref, addnodes.literal_emphasis, "str"],
                                    ")",
                                    " -- ",
                                    "blah blah")],))
    assert_node(doctree[3][1][0][0][1][0][2], pending_xref,
                refdomain="py", reftype="class", reftarget="int",
                **{"py:module": "example", "py:class": "Class"})
    assert_node(doctree[3][1][0][0][1][0][4], pending_xref,
                refdomain="py", reftype="class", reftarget="str",
                **{"py:module": "example", "py:class": "Class"})


def test_info_field_list_Literal(app):
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :param age: blah blah\n"
            "   :type age: Literal['foo', 'bar', 'baz']\n")
    doctree = restructuredtext.parse(app, text)

    assert_node(doctree,
                (nodes.target,
                 addnodes.index,
                 addnodes.index,
                 [desc, ([desc_signature, ([desc_annotation, ("class", desc_sig_space)],
                                           [desc_addname, "example."],
                                           [desc_name, "Class"])],
                         [desc_content, nodes.field_list, nodes.field, (nodes.field_name,
                                                                        nodes.field_body)])]))
    assert_node(doctree[3][1][0][0][1],
                ([nodes.paragraph, ([addnodes.literal_strong, "age"],
                                    " (",
                                    [pending_xref, addnodes.literal_emphasis, "Literal"],
                                    [addnodes.literal_emphasis, "["],
                                    [addnodes.literal_emphasis, "'foo'"],
                                    [addnodes.literal_emphasis, ", "],
                                    [addnodes.literal_emphasis, "'bar'"],
                                    [addnodes.literal_emphasis, ", "],
                                    [addnodes.literal_emphasis, "'baz'"],
                                    [addnodes.literal_emphasis, "]"],
                                    ")",
                                    " -- ",
                                    "blah blah")],))
    assert_node(doctree[3][1][0][0][1][0][2], pending_xref,
                refdomain="py", reftype="class", reftarget="Literal",
                **{"py:module": "example", "py:class": "Class"})


def test_info_field_list_var(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   :var int attr: blah blah\n")
    doctree = restructuredtext.parse(app, text)

    assert_node(doctree, (addnodes.index,
                          [desc, (desc_signature,
                                  [desc_content, nodes.field_list, nodes.field])]))
    assert_node(doctree[1][1][0][0], ([nodes.field_name, "Variables"],
                                      [nodes.field_body, nodes.paragraph]))

    # :var int attr:
    assert_node(doctree[1][1][0][0][1][0],
                ([addnodes.literal_strong, "attr"],
                 " (",
                 [pending_xref, addnodes.literal_emphasis, "int"],
                 ")",
                 " -- ",
                 "blah blah"))
    assert_node(doctree[1][1][0][0][1][0][2], pending_xref,
                refdomain="py", reftype="class", reftarget="int", **{"py:class": "Class"})


def test_type_field(app):
    text = (".. py:data:: var1\n"
            "   :type: .int\n"
            ".. py:data:: var2\n"
            "   :type: ~builtins.int\n"
            ".. py:data:: var3\n"
            "   :type: typing.Optional[typing.Tuple[int, typing.Any]]\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "var1"],
                                                    [desc_annotation, ([desc_sig_punctuation, ':'],
                                                                       desc_sig_space,
                                                                       [pending_xref, "int"])])],
                                  [desc_content, ()])],
                          addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "var2"],
                                                    [desc_annotation, ([desc_sig_punctuation, ':'],
                                                                       desc_sig_space,
                                                                       [pending_xref, "int"])])],
                                  [desc_content, ()])],
                          addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "var3"],
                                                    [desc_annotation, ([desc_sig_punctuation, ":"],
                                                                       desc_sig_space,
                                                                       [pending_xref, "Optional"],
                                                                       [desc_sig_punctuation, "["],
                                                                       [pending_xref, "Tuple"],
                                                                       [desc_sig_punctuation, "["],
                                                                       [pending_xref, "int"],
                                                                       [desc_sig_punctuation, ","],
                                                                       desc_sig_space,
                                                                       [pending_xref, "Any"],
                                                                       [desc_sig_punctuation, "]"],
                                                                       [desc_sig_punctuation, "]"])])],
                                  [desc_content, ()])]))
    assert_node(doctree[1][0][1][2], pending_xref, reftarget='int', refspecific=True)
    assert_node(doctree[3][0][1][2], pending_xref, reftarget='builtins.int', refspecific=False)
    assert_node(doctree[5][0][1][2], pending_xref, reftarget='typing.Optional', refspecific=False)
    assert_node(doctree[5][0][1][4], pending_xref, reftarget='typing.Tuple', refspecific=False)
    assert_node(doctree[5][0][1][6], pending_xref, reftarget='int', refspecific=False)
    assert_node(doctree[5][0][1][9], pending_xref, reftarget='typing.Any', refspecific=False)


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


@pytest.mark.sphinx('html', testroot='domain-py-python_use_unqualified_type_names')
def test_python_python_use_unqualified_type_names(app, status, warning):
    app.build()
    content = (app.outdir / 'index.html').read_text()
    assert ('<span class="n"><a class="reference internal" href="#foo.Name" title="foo.Name">'
            '<span class="pre">Name</span></a></span>' in content)
    assert '<span class="n"><span class="pre">foo.Age</span></span>' in content
    assert ('<p><strong>name</strong> (<a class="reference internal" href="#foo.Name" '
            'title="foo.Name"><em>Name</em></a>) – blah blah</p>' in content)
    assert '<p><strong>age</strong> (<em>foo.Age</em>) – blah blah</p>' in content


@pytest.mark.sphinx('html', testroot='domain-py-python_use_unqualified_type_names',
                    confoverrides={'python_use_unqualified_type_names': False})
def test_python_python_use_unqualified_type_names_disabled(app, status, warning):
    app.build()
    content = (app.outdir / 'index.html').read_text()
    assert ('<span class="n"><a class="reference internal" href="#foo.Name" title="foo.Name">'
            '<span class="pre">foo.Name</span></a></span>' in content)
    assert '<span class="n"><span class="pre">foo.Age</span></span>' in content
    assert ('<p><strong>name</strong> (<a class="reference internal" href="#foo.Name" '
            'title="foo.Name"><em>foo.Name</em></a>) – blah blah</p>' in content)
    assert '<p><strong>age</strong> (<em>foo.Age</em>) – blah blah</p>' in content


@pytest.mark.sphinx('dummy', testroot='domain-py-xref-warning')
def test_warn_missing_reference(app, status, warning):
    app.build()
    assert 'index.rst:6: WARNING: undefined label: no-label' in warning.getvalue()
    assert ('index.rst:6: WARNING: Failed to create a cross reference. A title or caption not found: existing-label'
            in warning.getvalue())
