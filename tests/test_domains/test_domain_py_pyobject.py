"""Tests the Python Domain"""

from __future__ import annotations

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (
    desc,
    desc_addname,
    desc_annotation,
    desc_content,
    desc_name,
    desc_parameterlist,
    desc_sig_keyword,
    desc_sig_punctuation,
    desc_sig_space,
    desc_signature,
    pending_xref,
)
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node

from tests.utils import extract_node


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyexception_signature(app):
    text = '.. py:exception:: builtins.IOError'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'exception'], desc_sig_space),
                            ],
                            [desc_addname, 'builtins.'],
                            [desc_name, 'IOError'],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        desc,
        desctype='exception',
        domain='py',
        objtype='exception',
        no_index=False,
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pydata_signature(app):
    text = '.. py:data:: version\n   :type: int\n   :value: 1\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [desc_name, 'version'],
                            [
                                desc_annotation,
                                (
                                    [desc_sig_punctuation, ':'],
                                    desc_sig_space,
                                    [pending_xref, 'int'],
                                ),
                            ],
                            [
                                desc_annotation,
                                (
                                    desc_sig_space,
                                    [desc_sig_punctuation, '='],
                                    desc_sig_space,
                                    '1',
                                ),
                            ],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='data',
        domain='py',
        objtype='data',
        no_index=False,
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pydata_signature_old(app):
    text = '.. py:data:: version\n   :annotation: = 1\n'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [desc_name, 'version'],
                            [desc_annotation, (desc_sig_space, '= 1')],
                        ),
                    ],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='data',
        domain='py',
        objtype='data',
        no_index=False,
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pydata_with_union_type_operator(app):
    text = '.. py:data:: version\n   :type: int | str'
    doctree = restructuredtext.parse(app, text)
    assert_node(
        extract_node(doctree, 1, 0),
        (
            [desc_name, 'version'],
            [
                desc_annotation,
                (
                    [desc_sig_punctuation, ':'],
                    desc_sig_space,
                    [pending_xref, 'int'],
                    desc_sig_space,
                    [desc_sig_punctuation, '|'],
                    desc_sig_space,
                    [pending_xref, 'str'],
                ),
            ],
        ),
    )


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyobject_prefix(app):
    text = (
        '.. py:class:: Foo\n\n   .. py:method:: Foo.say\n   .. py:method:: FooBar.say'
    )
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_name, 'Foo'],
                        ),
                    ],
                    [desc_content, (addnodes.index, desc, addnodes.index, desc)],
                ),
            ],
        ),
    )
    # prefix is stripped
    assert extract_node(doctree, 1, 1, 1).astext().strip() == 'say()'
    # not stripped
    assert extract_node(doctree, 1, 1, 3).astext().strip() == 'FooBar.say()'


@pytest.mark.sphinx('html', testroot='_blank')
def test_pydata(app):
    text = '.. py:module:: example\n.. py:data:: var\n   :type: int\n'
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            addnodes.index,
            nodes.target,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [desc_addname, 'example.'],
                            [desc_name, 'var'],
                            [
                                desc_annotation,
                                (
                                    [desc_sig_punctuation, ':'],
                                    desc_sig_space,
                                    [pending_xref, 'int'],
                                ),
                            ],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 3, 0, 2, 2), pending_xref, **{'py:module': 'example'}
    )
    assert 'example.var' in domain.objects
    assert domain.objects['example.var'] == ('index', 'example.var', 'data', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyclass_options(app):
    text = '.. py:class:: Class1\n.. py:class:: Class2\n   :final:\n'
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_name, 'Class1'],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                (
                                    [desc_sig_keyword, 'final'],
                                    desc_sig_space,
                                    [desc_sig_keyword, 'class'],
                                    desc_sig_space,
                                ),
                            ],
                            [desc_name, 'Class2'],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
        ),
    )

    # class
    assert_node(
        doctree[0],
        addnodes.index,
        entries=[('single', 'Class1 (built-in class)', 'Class1', '', None)],
    )
    assert 'Class1' in domain.objects
    assert domain.objects['Class1'] == ('index', 'Class1', 'class', False)

    # :final:
    assert_node(
        doctree[2],
        addnodes.index,
        entries=[('single', 'Class2 (built-in class)', 'Class2', '', None)],
    )
    assert 'Class2' in domain.objects
    assert domain.objects['Class2'] == ('index', 'Class2', 'class', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_pymethod_options(app):
    text = (
        '.. py:class:: Class\n'
        '\n'
        '   .. py:method:: meth1\n'
        '   .. py:method:: meth2\n'
        '      :classmethod:\n'
        '   .. py:method:: meth3\n'
        '      :staticmethod:\n'
        '   .. py:method:: meth4\n'
        '      :async:\n'
        '   .. py:method:: meth5\n'
        '      :abstractmethod:\n'
        '   .. py:method:: meth6\n'
        '      :final:\n'
    )
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_name, 'Class'],
                        ),
                    ],
                    [
                        desc_content,
                        (
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
                            desc,
                        ),
                    ],
                ),
            ],
        ),
    )

    # method
    assert_node(
        extract_node(doctree, 1, 1, 0),
        addnodes.index,
        entries=[('single', 'meth1() (Class method)', 'Class.meth1', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 1),
        (
            [desc_signature, ([desc_name, 'meth1'], [desc_parameterlist, ()])],
            [desc_content, ()],
        ),
    )
    assert 'Class.meth1' in domain.objects
    assert domain.objects['Class.meth1'] == ('index', 'Class.meth1', 'method', False)

    # :classmethod:
    assert_node(
        extract_node(doctree, 1, 1, 2),
        addnodes.index,
        entries=[('single', 'meth2() (Class class method)', 'Class.meth2', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 3),
        (
            [
                desc_signature,
                (
                    [
                        desc_annotation,
                        ([desc_sig_keyword, 'classmethod'], desc_sig_space),
                    ],
                    [desc_name, 'meth2'],
                    [desc_parameterlist, ()],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert 'Class.meth2' in domain.objects
    assert domain.objects['Class.meth2'] == ('index', 'Class.meth2', 'method', False)

    # :staticmethod:
    assert_node(
        extract_node(doctree, 1, 1, 4),
        addnodes.index,
        entries=[('single', 'meth3() (Class static method)', 'Class.meth3', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 5),
        (
            [
                desc_signature,
                (
                    [desc_annotation, ([desc_sig_keyword, 'static'], desc_sig_space)],
                    [desc_name, 'meth3'],
                    [desc_parameterlist, ()],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert 'Class.meth3' in domain.objects
    assert domain.objects['Class.meth3'] == ('index', 'Class.meth3', 'method', False)

    # :async:
    assert_node(
        extract_node(doctree, 1, 1, 6),
        addnodes.index,
        entries=[('single', 'meth4() (Class method)', 'Class.meth4', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 7),
        (
            [
                desc_signature,
                (
                    [desc_annotation, ([desc_sig_keyword, 'async'], desc_sig_space)],
                    [desc_name, 'meth4'],
                    [desc_parameterlist, ()],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert 'Class.meth4' in domain.objects
    assert domain.objects['Class.meth4'] == ('index', 'Class.meth4', 'method', False)

    # :abstractmethod:
    assert_node(
        extract_node(doctree, 1, 1, 8),
        addnodes.index,
        entries=[('single', 'meth5() (Class method)', 'Class.meth5', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 9),
        (
            [
                desc_signature,
                (
                    [
                        desc_annotation,
                        ([desc_sig_keyword, 'abstractmethod'], desc_sig_space),
                    ],
                    [desc_name, 'meth5'],
                    [desc_parameterlist, ()],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert 'Class.meth5' in domain.objects
    assert domain.objects['Class.meth5'] == ('index', 'Class.meth5', 'method', False)

    # :final:
    assert_node(
        extract_node(doctree, 1, 1, 10),
        addnodes.index,
        entries=[('single', 'meth6() (Class method)', 'Class.meth6', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 11),
        (
            [
                desc_signature,
                (
                    [desc_annotation, ([desc_sig_keyword, 'final'], desc_sig_space)],
                    [desc_name, 'meth6'],
                    [desc_parameterlist, ()],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert 'Class.meth6' in domain.objects
    assert domain.objects['Class.meth6'] == ('index', 'Class.meth6', 'method', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyclassmethod(app):
    text = '.. py:class:: Class\n\n   .. py:classmethod:: meth\n'
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_name, 'Class'],
                        ),
                    ],
                    [desc_content, (addnodes.index, desc)],
                ),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 1, 1, 0),
        addnodes.index,
        entries=[('single', 'meth() (Class class method)', 'Class.meth', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 1),
        (
            [
                desc_signature,
                (
                    [
                        desc_annotation,
                        ([desc_sig_keyword, 'classmethod'], desc_sig_space),
                    ],
                    [desc_name, 'meth'],
                    [desc_parameterlist, ()],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert 'Class.meth' in domain.objects
    assert domain.objects['Class.meth'] == ('index', 'Class.meth', 'method', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_pystaticmethod(app):
    text = '.. py:class:: Class\n\n   .. py:staticmethod:: meth\n'
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_name, 'Class'],
                        ),
                    ],
                    [desc_content, (addnodes.index, desc)],
                ),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 1, 1, 0),
        addnodes.index,
        entries=[('single', 'meth() (Class static method)', 'Class.meth', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 1),
        (
            [
                desc_signature,
                (
                    [desc_annotation, ([desc_sig_keyword, 'static'], desc_sig_space)],
                    [desc_name, 'meth'],
                    [desc_parameterlist, ()],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert 'Class.meth' in domain.objects
    assert domain.objects['Class.meth'] == ('index', 'Class.meth', 'method', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyattribute(app):
    text = (
        '.. py:class:: Class\n'
        '\n'
        '   .. py:attribute:: attr\n'
        '      :type: Optional[str]\n'
        "      :value: ''\n"
    )
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_name, 'Class'],
                        ),
                    ],
                    [desc_content, (addnodes.index, desc)],
                ),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 1, 1, 0),
        addnodes.index,
        entries=[('single', 'attr (Class attribute)', 'Class.attr', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 1),
        (
            [
                desc_signature,
                (
                    [desc_name, 'attr'],
                    [
                        desc_annotation,
                        (
                            [desc_sig_punctuation, ':'],
                            desc_sig_space,
                            [pending_xref, 'str'],
                            desc_sig_space,
                            [desc_sig_punctuation, '|'],
                            desc_sig_space,
                            [pending_xref, 'None'],
                        ),
                    ],
                    [
                        desc_annotation,
                        (
                            desc_sig_space,
                            [desc_sig_punctuation, '='],
                            desc_sig_space,
                            "''",
                        ),
                    ],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert_node(
        extract_node(doctree, 1, 1, 1, 0, 1, 2), pending_xref, **{'py:class': 'Class'}
    )
    assert_node(
        extract_node(doctree, 1, 1, 1, 0, 1, 6), pending_xref, **{'py:class': 'Class'}
    )
    assert 'Class.attr' in domain.objects
    assert domain.objects['Class.attr'] == ('index', 'Class.attr', 'attribute', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_pyproperty(app):
    text = (
        '.. py:class:: Class\n'
        '\n'
        '   .. py:property:: prop1\n'
        '      :abstractmethod:\n'
        '      :type: str\n'
        '\n'
        '   .. py:property:: prop2\n'
        '      :classmethod:\n'
        '      :type: str\n'
    )
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_name, 'Class'],
                        ),
                    ],
                    [desc_content, (addnodes.index, desc, addnodes.index, desc)],
                ),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 1, 1, 0),
        addnodes.index,
        entries=[('single', 'prop1 (Class property)', 'Class.prop1', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 1),
        (
            [
                desc_signature,
                (
                    [
                        desc_annotation,
                        (
                            [desc_sig_keyword, 'abstract'],
                            desc_sig_space,
                            [desc_sig_keyword, 'property'],
                            desc_sig_space,
                        ),
                    ],
                    [desc_name, 'prop1'],
                    [
                        desc_annotation,
                        (
                            [desc_sig_punctuation, ':'],
                            desc_sig_space,
                            [pending_xref, 'str'],
                        ),
                    ],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert_node(
        extract_node(doctree, 1, 1, 2),
        addnodes.index,
        entries=[('single', 'prop2 (Class property)', 'Class.prop2', '', None)],
    )
    assert_node(
        extract_node(doctree, 1, 1, 3),
        (
            [
                desc_signature,
                (
                    [
                        desc_annotation,
                        (
                            [desc_sig_keyword, 'class'],
                            desc_sig_space,
                            [desc_sig_keyword, 'property'],
                            desc_sig_space,
                        ),
                    ],
                    [desc_name, 'prop2'],
                    [
                        desc_annotation,
                        (
                            [desc_sig_punctuation, ':'],
                            desc_sig_space,
                            [pending_xref, 'str'],
                        ),
                    ],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert 'Class.prop1' in domain.objects
    assert domain.objects['Class.prop1'] == ('index', 'Class.prop1', 'property', False)
    assert 'Class.prop2' in domain.objects
    assert domain.objects['Class.prop2'] == ('index', 'Class.prop2', 'property', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_py_type_alias(app):
    text = (
        '.. py:module:: example\n'
        '.. py:type:: Alias1\n'
        '   :canonical: list[str | int]\n'
        '\n'
        '.. py:class:: Class\n'
        '\n'
        '   .. py:type:: Alias2\n'
        '      :canonical: int\n'
    )
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            addnodes.index,
            nodes.target,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'type'], desc_sig_space),
                            ],
                            [desc_addname, 'example.'],
                            [desc_name, 'Alias1'],
                            [
                                desc_annotation,
                                (
                                    desc_sig_space,
                                    [desc_sig_punctuation, '='],
                                    desc_sig_space,
                                    [pending_xref, 'list'],
                                    [desc_sig_punctuation, '['],
                                    [pending_xref, 'str'],
                                    desc_sig_space,
                                    [desc_sig_punctuation, '|'],
                                    desc_sig_space,
                                    [pending_xref, 'int'],
                                    [desc_sig_punctuation, ']'],
                                ),
                            ],
                        ),
                    ],
                    [desc_content, ()],
                ),
            ],
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_addname, 'example.'],
                            [desc_name, 'Class'],
                        ),
                    ],
                    [desc_content, (addnodes.index, desc)],
                ),
            ],
        ),
    )
    assert_node(
        extract_node(doctree, 5, 1, 0),
        addnodes.index,
        entries=[
            (
                'single',
                'Alias2 (type alias in example.Class)',
                'example.Class.Alias2',
                '',
                None,
            )
        ],
    )
    assert_node(
        extract_node(doctree, 5, 1, 1),
        (
            [
                desc_signature,
                (
                    [desc_annotation, ([desc_sig_keyword, 'type'], desc_sig_space)],
                    [desc_name, 'Alias2'],
                    [
                        desc_annotation,
                        (
                            desc_sig_space,
                            [desc_sig_punctuation, '='],
                            desc_sig_space,
                            [pending_xref, 'int'],
                        ),
                    ],
                ),
            ],
            [desc_content, ()],
        ),
    )
    assert 'example.Alias1' in domain.objects
    assert domain.objects['example.Alias1'] == (
        'index',
        'example.Alias1',
        'type',
        False,
    )
    assert 'example.Class.Alias2' in domain.objects
    assert domain.objects['example.Class.Alias2'] == (
        'index',
        'example.Class.Alias2',
        'type',
        False,
    )


@pytest.mark.sphinx('html', testroot='domain-py', freshenv=True)
def test_domain_py_type_alias(app):
    app.build(force_all=True)

    content = (app.outdir / 'type_alias.html').read_text(encoding='utf8')
    assert (
        '<span class="property"><span class="k"><span class="pre">type</span></span><span class="w"> </span></span>'
        '<span class="sig-prename descclassname"><span class="pre">module_one.</span></span>'
        '<span class="sig-name descname"><span class="pre">MyAlias</span></span>'
        '<span class="property"><span class="w"> </span><span class="p"><span class="pre">=</span></span>'
        '<span class="w"> </span><span class="pre">list</span>'
        '<span class="p"><span class="pre">[</span></span>'
        '<span class="pre">int</span><span class="w"> </span>'
        '<span class="p"><span class="pre">|</span></span><span class="w"> </span>'
        '<a class="reference internal" href="#module_two.SomeClass" title="module_two.SomeClass">'
        '<span class="pre">module_two.SomeClass</span></a>'
        '<span class="p"><span class="pre">]</span></span></span>'
    ) in content
    assert app.warning.getvalue() == ''


@pytest.mark.sphinx('html', testroot='_blank')
def test_pydecorator_signature(app):
    text = '.. py:decorator:: deco'
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [desc_signature, ([desc_addname, '@'], [desc_name, 'deco'])],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='function',
        domain='py',
        objtype='function',
        no_index=False,
    )

    assert 'deco' in domain.objects
    assert domain.objects['deco'] == ('index', 'deco', 'function', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_pydecoratormethod_signature(app):
    text = '.. py:decoratormethod:: deco'
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    assert_node(
        doctree,
        (
            addnodes.index,
            [
                desc,
                (
                    [desc_signature, ([desc_addname, '@'], [desc_name, 'deco'])],
                    desc_content,
                ),
            ],
        ),
    )
    assert_node(
        doctree[1],
        addnodes.desc,
        desctype='method',
        domain='py',
        objtype='method',
        no_index=False,
    )

    assert 'deco' in domain.objects
    assert domain.objects['deco'] == ('index', 'deco', 'method', False)


@pytest.mark.sphinx('html', testroot='_blank')
def test_pycurrentmodule(app):
    text = (
        '.. py:module:: Other\n'
        '\n'
        '.. py:module:: Module\n'
        '.. py:class:: A\n'
        '\n'
        '   .. py:method:: m1\n'
        '   .. py:method:: m2\n'
        '\n'
        '.. py:currentmodule:: Other\n'
        '\n'
        '.. py:class:: B\n'
        '\n'
        '   .. py:method:: m3\n'
        '   .. py:method:: m4\n'
    )
    domain = app.env.domains.python_domain
    doctree = restructuredtext.parse(app, text)
    print(doctree)
    assert_node(
        doctree,
        (
            addnodes.index,
            addnodes.index,
            addnodes.index,
            nodes.target,
            nodes.target,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_addname, 'Module.'],
                            [desc_name, 'A'],
                        ),
                    ],
                    [
                        desc_content,
                        (
                            addnodes.index,
                            [
                                desc,
                                (
                                    [
                                        desc_signature,
                                        (
                                            [desc_name, 'm1'],
                                            [desc_parameterlist, ()],
                                        ),
                                    ],
                                    [desc_content, ()],
                                ),
                            ],
                            addnodes.index,
                            [
                                desc,
                                (
                                    [
                                        desc_signature,
                                        (
                                            [desc_name, 'm2'],
                                            [desc_parameterlist, ()],
                                        ),
                                    ],
                                    [desc_content, ()],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
            addnodes.index,
            [
                desc,
                (
                    [
                        desc_signature,
                        (
                            [
                                desc_annotation,
                                ([desc_sig_keyword, 'class'], desc_sig_space),
                            ],
                            [desc_addname, 'Other.'],
                            [desc_name, 'B'],
                        ),
                    ],
                    [
                        desc_content,
                        (
                            addnodes.index,
                            [
                                desc,
                                (
                                    [
                                        desc_signature,
                                        (
                                            [desc_name, 'm3'],
                                            [desc_parameterlist, ()],
                                        ),
                                    ],
                                    [desc_content, ()],
                                ),
                            ],
                            addnodes.index,
                            [
                                desc,
                                (
                                    [
                                        desc_signature,
                                        (
                                            [desc_name, 'm4'],
                                            [desc_parameterlist, ()],
                                        ),
                                    ],
                                    [desc_content, ()],
                                ),
                            ],
                        ),
                    ],
                ),
            ],
        ),
    )
    assert 'Module' in domain.objects
    assert domain.objects['Module'] == ('index', 'module-Module', 'module', False)
    assert 'Other' in domain.objects
    assert domain.objects['Other'] == ('index', 'module-Other', 'module', False)
    assert 'Module.A' in domain.objects
    assert domain.objects['Module.A'] == ('index', 'Module.A', 'class', False)
    assert 'Other.B' in domain.objects
    assert domain.objects['Other.B'] == ('index', 'Other.B', 'class', False)
    assert 'Module.A.m1' in domain.objects
    assert domain.objects['Module.A.m1'] == ('index', 'Module.A.m1', 'method', False)
    assert 'Module.A.m2' in domain.objects
    assert domain.objects['Module.A.m2'] == ('index', 'Module.A.m2', 'method', False)
    assert 'Other.B.m3' in domain.objects
    assert domain.objects['Other.B.m3'] == ('index', 'Other.B.m3', 'method', False)
    assert 'Other.B.m4' in domain.objects
    assert domain.objects['Other.B.m4'] == ('index', 'Other.B.m4', 'method', False)
