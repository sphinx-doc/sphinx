"""
    test_domain_py
    ~~~~~~~~~~~~~~

    Tests the Python Domain

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest.mock import Mock

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (
    desc, desc_addname, desc_annotation, desc_content, desc_name, desc_optional,
    desc_parameter, desc_parameterlist, desc_returns, desc_signature
)
from sphinx.domains import IndexEntry
from sphinx.domains.python import (
    py_sig_re, _pseudo_parse_arglist, PythonDomain, PythonModuleIndex
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


@pytest.mark.sphinx('html', testroot='domain-py')
def test_resolve_xref_for_properties(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'module.html').text()
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
            "   :type: int\n"
            "   :value: 1\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "version"],
                                                    [desc_annotation, ": int"],
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
    assert doctree[1][1][1].astext().strip() == 'say'           # prefix is stripped
    assert doctree[1][1][3].astext().strip() == 'FooBar.say'    # not stripped


def test_pydata(app):
    text = ".. py:data:: var\n"
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, desc_name, "var"],
                                  [desc_content, ()])]))
    assert 'var' in domain.objects
    assert domain.objects['var'] == ('index', 'data')


def test_pyfunction(app):
    text = (".. py:function:: func1\n"
            ".. py:function:: func2\n"
            "   :async:\n")
    domain = app.env.get_domain('py')
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, "func1"],
                                                    [desc_parameterlist, ()])],
                                  [desc_content, ()])],
                          addnodes.index,
                          [desc, ([desc_signature, ([desc_annotation, "async "],
                                                    [desc_name, "func2"],
                                                    [desc_parameterlist, ()])],
                                  [desc_content, ()])]))
    assert 'func1' in domain.objects
    assert domain.objects['func1'] == ('index', 'function')
    assert 'func2' in domain.objects
    assert domain.objects['func2'] == ('index', 'function')


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
            "      :abstractmethod:\n")
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
                                                  desc)])]))

    # method
    assert_node(doctree[1][1][0], addnodes.index,
                entries=[('single', 'meth1() (Class method)', 'Class.meth1', '', None)])
    assert_node(doctree[1][1][1], ([desc_signature, ([desc_name, "meth1"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth1' in domain.objects
    assert domain.objects['Class.meth1'] == ('index', 'method')

    # :classmethod:
    assert_node(doctree[1][1][2], addnodes.index,
                entries=[('single', 'meth2() (Class class method)', 'Class.meth2', '', None)])
    assert_node(doctree[1][1][3], ([desc_signature, ([desc_annotation, "classmethod "],
                                                     [desc_name, "meth2"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth2' in domain.objects
    assert domain.objects['Class.meth2'] == ('index', 'method')

    # :staticmethod:
    assert_node(doctree[1][1][4], addnodes.index,
                entries=[('single', 'meth3() (Class static method)', 'Class.meth3', '', None)])
    assert_node(doctree[1][1][5], ([desc_signature, ([desc_annotation, "static "],
                                                     [desc_name, "meth3"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth3' in domain.objects
    assert domain.objects['Class.meth3'] == ('index', 'method')

    # :async:
    assert_node(doctree[1][1][6], addnodes.index,
                entries=[('single', 'meth4() (Class method)', 'Class.meth4', '', None)])
    assert_node(doctree[1][1][7], ([desc_signature, ([desc_annotation, "async "],
                                                     [desc_name, "meth4"],
                                                     [desc_parameterlist, ()])],
                                   [desc_content, ()]))
    assert 'Class.meth4' in domain.objects
    assert domain.objects['Class.meth4'] == ('index', 'method')

    # :property:
    assert_node(doctree[1][1][8], addnodes.index,
                entries=[('single', 'meth5() (Class property)', 'Class.meth5', '', None)])
    assert_node(doctree[1][1][9], ([desc_signature, ([desc_annotation, "property "],
                                                     [desc_name, "meth5"])],
                                   [desc_content, ()]))
    assert 'Class.meth5' in domain.objects
    assert domain.objects['Class.meth5'] == ('index', 'method')

    # :abstractmethod:
    assert_node(doctree[1][1][10], addnodes.index,
                entries=[('single', 'meth6() (Class method)', 'Class.meth6', '', None)])
    assert_node(doctree[1][1][11], ([desc_signature, ([desc_annotation, "abstract "],
                                                      [desc_name, "meth6"],
                                                      [desc_parameterlist, ()])],
                                    [desc_content, ()]))
    assert 'Class.meth6' in domain.objects
    assert domain.objects['Class.meth6'] == ('index', 'method')


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
    assert domain.objects['Class.meth'] == ('index', 'method')


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
    assert domain.objects['Class.meth'] == ('index', 'method')


def test_pyattribute(app):
    text = (".. py:class:: Class\n"
            "\n"
            "   .. py:attribute:: attr\n"
            "      :type: str\n"
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
                                                     [desc_annotation, ": str"],
                                                     [desc_annotation, " = ''"])],
                                   [desc_content, ()]))
    assert 'Class.attr' in domain.objects
    assert domain.objects['Class.attr'] == ('index', 'attribute')


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
