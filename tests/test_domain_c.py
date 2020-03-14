"""
    test_domain_c
    ~~~~~~~~~~~~~

    Tests the C Domain

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (
    desc, desc_addname, desc_annotation, desc_content, desc_name, desc_optional,
    desc_parameter, desc_parameterlist, desc_returns, desc_signature, desc_type,
    pending_xref
)
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


def test_cfunction(app):
    text = (".. c:function:: PyObject* "
            "PyType_GenericAlloc(PyTypeObject *type, Py_ssize_t nitems)")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree,
                (addnodes.index,
                 [desc, ([desc_signature, ([desc_type, ([pending_xref, "PyObject"],
                                                        "* ")],
                                           [desc_name, "PyType_GenericAlloc"],
                                           [desc_parameterlist, (desc_parameter,
                                                                 desc_parameter)])],
                         desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="function",
                domain="c", objtype="function", noindex=False)
    assert_node(doctree[1][0][2][0],
                [desc_parameter, ([pending_xref, "PyTypeObject"],
                                  [nodes.emphasis, "\xa0*type"])])
    assert_node(doctree[1][0][2][1],
                [desc_parameter, ([pending_xref, "Py_ssize_t"],
                                  [nodes.emphasis, "\xa0nitems"])])

    domain = app.env.get_domain('c')
    entry = domain.objects.get('PyType_GenericAlloc')
    assert entry == ('index', 'c-pytype-genericalloc', 'function')


def test_cmember(app):
    text = ".. c:member:: PyObject* PyTypeObject.tp_bases"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree,
                (addnodes.index,
                 [desc, ([desc_signature, ([desc_type, ([pending_xref, "PyObject"],
                                                        "* ")],
                                           [desc_name, "PyTypeObject.tp_bases"])],
                         desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="member",
                domain="c", objtype="member", noindex=False)

    domain = app.env.get_domain('c')
    entry = domain.objects.get('PyTypeObject.tp_bases')
    assert entry == ('index', 'c-pytypeobject-tp-bases', 'member')


def test_cvar(app):
    text = ".. c:var:: PyObject* PyClass_Type"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree,
                (addnodes.index,
                 [desc, ([desc_signature, ([desc_type, ([pending_xref, "PyObject"],
                                                        "* ")],
                                           [desc_name, "PyClass_Type"])],
                         desc_content)]))
    assert_node(doctree[1], addnodes.desc, desctype="var",
                domain="c", objtype="var", noindex=False)

    domain = app.env.get_domain('c')
    entry = domain.objects.get('PyClass_Type')
    assert entry == ('index', 'c-pyclass-type', 'var')
