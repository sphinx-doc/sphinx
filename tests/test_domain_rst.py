"""
    test_rst_domain
    ~~~~~~~~~~~~~~~

    Tests the reStructuredText domain.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx import addnodes
from sphinx.addnodes import (
    desc, desc_addname, desc_content, desc_name, desc_optional, desc_parameter,
    desc_parameterlist, desc_returns, desc_signature
)
from sphinx.domains.rst import parse_directive
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


def test_parse_directive():
    s = parse_directive(' foö  ')
    assert s == ('foö', '')

    s = parse_directive(' ..    foö ::  ')
    assert s == ('foö', ' ')

    s = parse_directive('.. foö:: args1 args2')
    assert s == ('foö', ' args1 args2')

    s = parse_directive('.. :: bar')
    assert s == ('.. :: bar', '')


def test_rst_directive(app):
    # bare
    text = ".. rst:directive:: toctree"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, desc_name, ".. toctree::"],
                                  [desc_content, ()])]))
    assert_node(doctree[0],
                entries=[("single", "toctree (directive)", "directive-toctree", "", None)])
    assert_node(doctree[1], addnodes.desc, desctype="directive",
                domain="rst", objtype="directive", noindex=False)

    # decorated
    text = ".. rst:directive:: .. toctree::"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, ".. toctree::"],
                                                    [desc_addname, " "])],
                                  [desc_content, ()])]))
    assert_node(doctree[0],
                entries=[("single", "toctree (directive)", "directive-toctree", "", None)])
    assert_node(doctree[1], addnodes.desc, desctype="directive",
                domain="rst", objtype="directive", noindex=False)


def test_rst_directive_with_argument(app):
    text = ".. rst:directive:: .. toctree:: foo bar baz"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, ".. toctree::"],
                                                    [desc_addname, " foo bar baz"])],
                                  [desc_content, ()])]))
    assert_node(doctree[0],
                entries=[("single", "toctree (directive)", "directive-toctree", "", None)])
    assert_node(doctree[1], addnodes.desc, desctype="directive",
                domain="rst", objtype="directive", noindex=False)


def test_rst_role(app):
    text = ".. rst:role:: ref"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, desc_name, ":ref:"],
                                  [desc_content, ()])]))
    assert_node(doctree[0],
                entries=[("single", "ref (role)", "role-ref", "", None)])
    assert_node(doctree[1], addnodes.desc, desctype="role",
                domain="rst", objtype="role", noindex=False)
