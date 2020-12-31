"""
    test_rst_domain
    ~~~~~~~~~~~~~~~

    Tests the reStructuredText domain.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx import addnodes
from sphinx.addnodes import (desc, desc_addname, desc_annotation, desc_content, desc_name,
                             desc_signature)
from sphinx.domains.rst import parse_directive
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


def test_parse_directive():
    s = parse_directive(' foö  ')
    assert s == ('foö', '')

    s = parse_directive(' ..    foö ::  ')
    assert s == ('foö', '')

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
                          [desc, ([desc_signature, desc_name, ".. toctree::"],
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


def test_rst_directive_option(app):
    text = ".. rst:directive:option:: foo"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, desc_name, ":foo:"],
                                  [desc_content, ()])]))
    assert_node(doctree[0],
                entries=[("single", ":foo: (directive option)",
                          "directive-option-foo", "", "F")])
    assert_node(doctree[1], addnodes.desc, desctype="directive:option",
                domain="rst", objtype="directive:option", noindex=False)


def test_rst_directive_option_with_argument(app):
    text = ".. rst:directive:option:: foo: bar baz"
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, ":foo:"],
                                                    [desc_annotation, " bar baz"])],
                                  [desc_content, ()])]))
    assert_node(doctree[0],
                entries=[("single", ":foo: (directive option)",
                          "directive-option-foo", "", "F")])
    assert_node(doctree[1], addnodes.desc, desctype="directive:option",
                domain="rst", objtype="directive:option", noindex=False)


def test_rst_directive_option_type(app):
    text = (".. rst:directive:option:: foo\n"
            "   :type: directives.flags\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, ([desc_name, ":foo:"],
                                                    [desc_annotation, " (directives.flags)"])],
                                  [desc_content, ()])]))
    assert_node(doctree[0],
                entries=[("single", ":foo: (directive option)",
                          "directive-option-foo", "", "F")])
    assert_node(doctree[1], addnodes.desc, desctype="directive:option",
                domain="rst", objtype="directive:option", noindex=False)


def test_rst_directive_and_directive_option(app):
    text = (".. rst:directive:: foo\n"
            "\n"
            "   .. rst:directive:option:: bar\n")
    doctree = restructuredtext.parse(app, text)
    assert_node(doctree, (addnodes.index,
                          [desc, ([desc_signature, desc_name, ".. foo::"],
                                  [desc_content, (addnodes.index,
                                                  desc)])]))
    assert_node(doctree[1][1][0],
                entries=[("pair", "foo (directive); :bar: (directive option)",
                          "directive-option-foo-bar", "", "B")])
    assert_node(doctree[1][1][1], ([desc_signature, desc_name, ":bar:"],
                                   [desc_content, ()]))
    assert_node(doctree[1][1][1], addnodes.desc, desctype="directive:option",
                domain="rst", objtype="directive:option", noindex=False)


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
