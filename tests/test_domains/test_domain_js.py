"""Tests the JavaScript Domain"""

from unittest.mock import Mock

import docutils.utils
import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (
    desc,
    desc_annotation,
    desc_content,
    desc_name,
    desc_parameter,
    desc_parameterlist,
    desc_sig_keyword,
    desc_sig_name,
    desc_sig_space,
    desc_signature,
)
from sphinx.domains.javascript import JavaScriptDomain
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node
from sphinx.writers.text import STDINDENT


@pytest.mark.sphinx('dummy', testroot='domain-js')
def test_domain_js_xrefs(app, status, warning):
    """Domain objects have correct prefixes when looking up xrefs"""
    app.build(force_all=True)

    def assert_refnode(node, mod_name, prefix, target, reftype=None,
                       domain='js'):
        attributes = {
            'refdomain': domain,
            'reftarget': target,
        }
        if reftype is not None:
            attributes['reftype'] = reftype
        if mod_name is not False:
            attributes['js:module'] = mod_name
        if prefix is not False:
            attributes['js:object'] = prefix
        assert_node(node, **attributes)

    doctree = app.env.get_doctree('roles')
    refnodes = list(doctree.findall(addnodes.pending_xref))
    assert_refnode(refnodes[0], None, None, 'TopLevel', 'class')
    assert_refnode(refnodes[1], None, None, 'top_level', 'func')
    assert_refnode(refnodes[2], None, 'NestedParentA', 'child_1', 'func')
    assert_refnode(refnodes[3], None, 'NestedParentA', 'NestedChildA.subchild_2', 'func')
    assert_refnode(refnodes[4], None, 'NestedParentA', 'child_2', 'func')
    assert_refnode(refnodes[5], False, 'NestedParentA', 'any_child', domain='')
    assert_refnode(refnodes[6], None, 'NestedParentA', 'NestedChildA', 'class')
    assert_refnode(refnodes[7], None, 'NestedParentA.NestedChildA', 'subchild_2', 'func')
    assert_refnode(refnodes[8], None, 'NestedParentA.NestedChildA',
                   'NestedParentA.child_1', 'func')
    assert_refnode(refnodes[9], None, 'NestedParentA', 'NestedChildA.subchild_1', 'func')
    assert_refnode(refnodes[10], None, 'NestedParentB', 'child_1', 'func')
    assert_refnode(refnodes[11], None, 'NestedParentB', 'NestedParentB', 'class')
    assert_refnode(refnodes[12], None, None, 'NestedParentA.NestedChildA', 'class')
    assert len(refnodes) == 13

    doctree = app.env.get_doctree('module')
    refnodes = list(doctree.findall(addnodes.pending_xref))
    assert_refnode(refnodes[0], 'module_a.submodule', None, 'ModTopLevel',
                   'class')
    assert_refnode(refnodes[1], 'module_a.submodule', 'ModTopLevel',
                   'mod_child_1', 'meth')
    assert_refnode(refnodes[2], 'module_a.submodule', 'ModTopLevel',
                   'ModTopLevel.mod_child_1', 'meth')
    assert_refnode(refnodes[3], 'module_a.submodule', 'ModTopLevel',
                   'mod_child_2', 'meth')
    assert_refnode(refnodes[4], 'module_a.submodule', 'ModTopLevel',
                   'module_a.submodule.ModTopLevel.mod_child_1', 'meth')
    assert_refnode(refnodes[5], 'module_b.submodule', None, 'ModTopLevel',
                   'class')
    assert_refnode(refnodes[6], 'module_b.submodule', 'ModTopLevel',
                   'module_a.submodule', 'mod')
    assert len(refnodes) == 7


@pytest.mark.sphinx('dummy', testroot='domain-js')
def test_domain_js_objects(app, status, warning):
    app.build(force_all=True)

    modules = app.env.domains['js'].data['modules']
    objects = app.env.domains['js'].data['objects']

    assert 'module_a.submodule' in modules
    assert 'module_a.submodule' in objects
    assert 'module_b.submodule' in modules
    assert 'module_b.submodule' in objects

    assert objects['module_a.submodule.ModTopLevel'][2] == 'class'
    assert objects['module_a.submodule.ModTopLevel.mod_child_1'][2] == 'method'
    assert objects['module_a.submodule.ModTopLevel.mod_child_2'][2] == 'method'
    assert objects['module_b.submodule.ModTopLevel'][2] == 'class'

    assert objects['TopLevel'][2] == 'class'
    assert objects['top_level'][2] == 'function'
    assert objects['NestedParentA'][2] == 'class'
    assert objects['NestedParentA.child_1'][2] == 'function'
    assert objects['NestedParentA.any_child'][2] == 'function'
    assert objects['NestedParentA.NestedChildA'][2] == 'class'
    assert objects['NestedParentA.NestedChildA.subchild_1'][2] == 'function'
    assert objects['NestedParentA.NestedChildA.subchild_2'][2] == 'function'
    assert objects['NestedParentA.child_2'][2] == 'function'
    assert objects['NestedParentB'][2] == 'class'
    assert objects['NestedParentB.child_1'][2] == 'function'


@pytest.mark.sphinx('dummy', testroot='domain-js')
def test_domain_js_find_obj(app, status, warning):

    def find_obj(mod_name, prefix, obj_name, obj_type, searchmode=0):
        return app.env.domains['js'].find_obj(
            app.env, mod_name, prefix, obj_name, obj_type, searchmode)

    app.build(force_all=True)

    assert (find_obj(None, None, 'NONEXISTANT', 'class') == (None, None))
    assert (find_obj(None, None, 'NestedParentA', 'class') ==
            ('NestedParentA', ('roles', 'NestedParentA', 'class')))
    assert (find_obj(None, None, 'NestedParentA.NestedChildA', 'class') ==
            ('NestedParentA.NestedChildA',
             ('roles', 'NestedParentA.NestedChildA', 'class')))
    assert (find_obj(None, 'NestedParentA', 'NestedChildA', 'class') ==
            ('NestedParentA.NestedChildA',
             ('roles', 'NestedParentA.NestedChildA', 'class')))
    assert (find_obj(None, None, 'NestedParentA.NestedChildA.subchild_1', 'func') ==
            ('NestedParentA.NestedChildA.subchild_1',
             ('roles', 'NestedParentA.NestedChildA.subchild_1', 'function')))
    assert (find_obj(None, 'NestedParentA', 'NestedChildA.subchild_1', 'func') ==
            ('NestedParentA.NestedChildA.subchild_1',
             ('roles', 'NestedParentA.NestedChildA.subchild_1', 'function')))
    assert (find_obj(None, 'NestedParentA.NestedChildA', 'subchild_1', 'func') ==
            ('NestedParentA.NestedChildA.subchild_1',
             ('roles', 'NestedParentA.NestedChildA.subchild_1', 'function')))
    assert (find_obj('module_a.submodule', 'ModTopLevel', 'mod_child_2', 'meth') ==
            ('module_a.submodule.ModTopLevel.mod_child_2',
             ('module', 'module_a.submodule.ModTopLevel.mod_child_2', 'method')))
    assert (find_obj('module_b.submodule', 'ModTopLevel', 'module_a.submodule', 'mod') ==
            ('module_a.submodule',
             ('module', 'module-module_a.submodule', 'module')))


def test_get_full_qualified_name():
    env = Mock(domaindata={})
    domain = JavaScriptDomain(env)

    # non-js references
    node = nodes.reference()
    assert domain.get_full_qualified_name(node) is None

    # simple reference
    node = nodes.reference(reftarget='func')
    assert domain.get_full_qualified_name(node) == 'func'

    # with js:module context
    kwargs = {'js:module': 'module1'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'module1.func'

    # with js:object context
    kwargs = {'js:object': 'Class'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'Class.func'

    # with both js:module and js:object context
    kwargs = {'js:module': 'module1', 'js:object': 'Class'}
    node = nodes.reference(reftarget='func', **kwargs)
    assert domain.get_full_qualified_name(node) == 'module1.Class.func'


def test_js_module(app):
    text = ".. js:module:: sphinx"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          nodes.target))
    assert_node(doctree[0], addnodes.index,
                entries=[("single", "sphinx (module)", "module-sphinx", "", None)])
    assert_node(doctree[1], nodes.target, ids=["module-sphinx"])


def test_js_function(app):
    text = ".. js:function:: sum(a, b)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, ([desc_sig_name, "sum"])],
                                                    desc_parameterlist)],
                                  [desc_content, ()])]))
    assert_node(doctree[1][0][1], [desc_parameterlist, ([desc_parameter, ([desc_sig_name, "a"])],
                                                        [desc_parameter, ([desc_sig_name, "b"])])])
    assert_node(doctree[0], addnodes.index,
                entries=[("single", "sum() (built-in function)", "sum", "", None)])
    assert_node(doctree[1], addnodes.desc, domain="js", objtype="function", no_index=False)


def test_js_class(app):
    text = ".. js:class:: Application"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, ([desc_sig_keyword, 'class'],
                                                                       desc_sig_space)],
                                                    [desc_name, ([desc_sig_name, "Application"])],
                                                    [desc_parameterlist, ()])],
                                  [desc_content, ()])]))
    assert_node(doctree[0], addnodes.index,
                entries=[("single", "Application() (class)", "Application", "", None)])
    assert_node(doctree[1], addnodes.desc, domain="js", objtype="class", no_index=False)


def test_js_data(app):
    text = ".. js:data:: name"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, ([desc_sig_name, "name"])])],
                                  [desc_content, ()])]))
    assert_node(doctree[0], addnodes.index,
                entries=[("single", "name (global variable or constant)", "name", "", None)])
    assert_node(doctree[1], addnodes.desc, domain="js", objtype="data", no_index=False)


def test_no_index_entry(app):
    text = (".. js:function:: f()\n"
            ".. js:function:: g()\n"
            "   :no-index-entry:\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index, desc, addnodes.index, desc))
    assert_node(doctree[0], addnodes.index, entries=[('single', 'f() (built-in function)', 'f', '', None)])
    assert_node(doctree[2], addnodes.index, entries=[])


def test_module_content_line_number(app):
    text = (".. js:module:: foo\n" +
            "\n" +
            "   Some link here: :ref:`abc`\n")
    doc = restructuredtext.parse(app, text)
    xrefs = list(doc.findall(condition=addnodes.pending_xref))
    assert len(xrefs) == 1
    source, line = docutils.utils.get_source_line(xrefs[0])
    assert 'index.rst' in source
    assert line == 3


@pytest.mark.sphinx('html', confoverrides={
    'javascript_maximum_signature_line_length': len("hello(name)"),
})
def test_jsfunction_signature_with_javascript_maximum_signature_line_length_equal(app):
    text = ".. js:function:: hello(name)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        addnodes.index,
        [desc, (
            [desc_signature, (
                [desc_name, ([desc_sig_name, "hello"])],
                desc_parameterlist,
            )],
            desc_content,
        )],
    ))
    assert_node(doctree[1], desc, desctype="function",
                domain="js", objtype="function", no_index=False)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, desc_parameter, ([desc_sig_name, "name"])])
    assert_node(doctree[1][0][1], desc_parameterlist, multi_line_parameter_list=False)


@pytest.mark.sphinx('html', confoverrides={
    'javascript_maximum_signature_line_length': len("hello(name)"),
})
def test_jsfunction_signature_with_javascript_maximum_signature_line_length_force_single(app):
    text = (".. js:function:: hello(names)\n"
            "   :single-line-parameter-list:")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        addnodes.index,
        [desc, (
            [desc_signature, (
                [desc_name, ([desc_sig_name, "hello"])],
                desc_parameterlist,
            )],
            desc_content,
        )],
    ))
    assert_node(doctree[1], desc, desctype="function",
                domain="js", objtype="function", no_index=False)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, desc_parameter, ([desc_sig_name, "names"])])
    assert_node(doctree[1][0][1], desc_parameterlist, multi_line_parameter_list=False)


@pytest.mark.sphinx('html', confoverrides={
    'javascript_maximum_signature_line_length': len("hello(name)"),
})
def test_jsfunction_signature_with_javascript_maximum_signature_line_length_break(app):
    text = ".. js:function:: hello(names)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        addnodes.index,
        [desc, (
            [desc_signature, (
                [desc_name, ([desc_sig_name, "hello"])],
                desc_parameterlist,
            )],
            desc_content,
        )],
    ))
    assert_node(doctree[1], desc, desctype="function",
                domain="js", objtype="function", no_index=False)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, desc_parameter, ([desc_sig_name, "names"])])
    assert_node(doctree[1][0][1], desc_parameterlist, multi_line_parameter_list=True)


@pytest.mark.sphinx('html', confoverrides={
    'maximum_signature_line_length': len("hello(name)"),
})
def test_jsfunction_signature_with_maximum_signature_line_length_equal(app):
    text = ".. js:function:: hello(name)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        addnodes.index,
        [desc, (
            [desc_signature, (
                [desc_name, ([desc_sig_name, "hello"])],
                desc_parameterlist,
            )],
            desc_content,
        )],
    ))
    assert_node(doctree[1], desc, desctype="function",
                domain="js", objtype="function", no_index=False)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, desc_parameter, ([desc_sig_name, "name"])])
    assert_node(doctree[1][0][1], desc_parameterlist, multi_line_parameter_list=False)


@pytest.mark.sphinx('html', confoverrides={
    'maximum_signature_line_length': len("hello(name)"),
})
def test_jsfunction_signature_with_maximum_signature_line_length_force_single(app):
    text = (".. js:function:: hello(names)\n"
            "   :single-line-parameter-list:")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        addnodes.index,
        [desc, (
            [desc_signature, (
                [desc_name, ([desc_sig_name, "hello"])],
                desc_parameterlist,
            )],
            desc_content,
        )],
    ))
    assert_node(doctree[1], desc, desctype="function",
                domain="js", objtype="function", no_index=False)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, desc_parameter, ([desc_sig_name, "names"])])
    assert_node(doctree[1][0][1], desc_parameterlist, multi_line_parameter_list=False)


@pytest.mark.sphinx('html', confoverrides={
    'maximum_signature_line_length': len("hello(name)"),
})
def test_jsfunction_signature_with_maximum_signature_line_length_break(app):
    text = ".. js:function:: hello(names)"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (
        addnodes.index,
        [desc, (
            [desc_signature, (
                [desc_name, ([desc_sig_name, "hello"])],
                desc_parameterlist,
            )],
            desc_content,
        )],
    ))
    assert_node(doctree[1], desc, desctype="function",
                domain="js", objtype="function", no_index=False)
    assert_node(doctree[1][0][1],
                [desc_parameterlist, desc_parameter, ([desc_sig_name, "names"])])
    assert_node(doctree[1][0][1], desc_parameterlist, multi_line_parameter_list=True)


@pytest.mark.sphinx(
    'html',
    confoverrides={
        'javascript_maximum_signature_line_length': len("hello(name)"),
        'maximum_signature_line_length': 1,
    },
)
def test_javascript_maximum_signature_line_length_overrides_global(app):
    text = ".. js:function:: hello(name)"
    doctree = restructuredtext.parse(app, text)
    expected_doctree = (addnodes.index,
                        [desc, ([desc_signature, ([desc_name, ([desc_sig_name, "hello"])],
                                                  desc_parameterlist)],
                                desc_content)])
    assert_node(doctree, expected_doctree)
    assert_node(doctree[1], desc, desctype="function",
                domain="js", objtype="function", no_index=False)
    expected_sig = [desc_parameterlist, desc_parameter, [desc_sig_name, "name"]]
    assert_node(doctree[1][0][1], expected_sig)
    assert_node(doctree[1][0][1], desc_parameterlist, multi_line_parameter_list=False)


@pytest.mark.sphinx(
    'html', testroot='domain-js-javascript_maximum_signature_line_length',
)
def test_domain_js_javascript_maximum_signature_line_length_in_html(app, status, warning):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    expected_parameter_list_hello = """\

<dl>
<dd>\
<em class="sig-param">\
<span class="n"><span class="pre">name</span></span>\
</em>,\
</dd>
</dl>

<span class="sig-paren">)</span>\
<a class="headerlink" href="#hello" title="Link to this definition">¶</a>\
</dt>\
"""
    assert expected_parameter_list_hello in content

    param_line_fmt = '<dd>{}</dd>\n'
    param_name_fmt = (
        '<em class="sig-param"><span class="n"><span class="pre">{}</span></span></em>'
    )
    optional_fmt = '<span class="optional">{}</span>'

    expected_a = param_line_fmt.format(
        optional_fmt.format("[") + param_name_fmt.format("a") + "," + optional_fmt.format("["),
    )
    assert expected_a in content

    expected_b = param_line_fmt.format(
        param_name_fmt.format("b") + "," + optional_fmt.format("]") + optional_fmt.format("]"),
    )
    assert expected_b in content

    expected_c = param_line_fmt.format(param_name_fmt.format("c") + ",")
    assert expected_c in content

    expected_d = param_line_fmt.format(param_name_fmt.format("d") + optional_fmt.format("[") + ",")
    assert expected_d in content

    expected_e = param_line_fmt.format(param_name_fmt.format("e") + ",")
    assert expected_e in content

    expected_f = param_line_fmt.format(param_name_fmt.format("f") + "," + optional_fmt.format("]"))
    assert expected_f in content

    expected_parameter_list_foo = """\

<dl>
{}{}{}{}{}{}</dl>

<span class="sig-paren">)</span>\
<a class="headerlink" href="#foo" title="Link to this definition">¶</a>\
</dt>\
""".format(expected_a, expected_b, expected_c, expected_d, expected_e, expected_f)
    assert expected_parameter_list_foo in content


@pytest.mark.sphinx(
    'text', testroot='domain-js-javascript_maximum_signature_line_length',
)
def test_domain_js_javascript_maximum_signature_line_length_in_text(app, status, warning):
    app.build()
    content = (app.outdir / 'index.txt').read_text(encoding='utf8')
    param_line_fmt = STDINDENT * " " + "{}\n"

    expected_parameter_list_hello = "(\n{})".format(param_line_fmt.format("name,"))

    assert expected_parameter_list_hello in content

    expected_a = param_line_fmt.format("[a,[")
    assert expected_a in content

    expected_b = param_line_fmt.format("b,]]")
    assert expected_b in content

    expected_c = param_line_fmt.format("c,")
    assert expected_c in content

    expected_d = param_line_fmt.format("d[,")
    assert expected_d in content

    expected_e = param_line_fmt.format("e,")
    assert expected_e in content

    expected_f = param_line_fmt.format("f,]")
    assert expected_f in content

    expected_parameter_list_foo = "(\n{}{}{}{}{}{})".format(
        expected_a, expected_b, expected_c, expected_d, expected_e, expected_f,
    )
    assert expected_parameter_list_foo in content
