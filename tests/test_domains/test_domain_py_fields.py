"""Tests the Python Domain"""

from __future__ import annotations

from docutils import nodes

from sphinx import addnodes
from sphinx.addnodes import (
    desc,
    desc_addname,
    desc_annotation,
    desc_content,
    desc_name,
    desc_sig_punctuation,
    desc_sig_space,
    desc_signature,
    pending_xref,
)
from sphinx.testing import restructuredtext
from sphinx.testing.util import assert_node


def test_info_field_list(app):
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :meta blah: this meta-field must not show up in the toc-tree\n"
            "   :param str name: blah blah\n"
            "   :meta another meta field:\n"
            "   :param age: blah blah\n"
            "   :type age: int\n"
            "   :param items: blah blah\n"
            "   :type items: Tuple[str, ...]\n"
            "   :param Dict[str, str] params: blah blah\n")
    doctree = restructuredtext.parse(app, text)
    print(doctree)

    assert_node(doctree, (addnodes.index,
                          addnodes.index,
                          nodes.target,
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
                (addnodes.index,
                 addnodes.index,
                 nodes.target,
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
                (addnodes.index,
                 addnodes.index,
                 nodes.target,
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


def test_info_field_list_napoleon_deliminator_of(app):
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :param list_str_var: example description.\n"
            "   :type list_str_var: list of str\n"
            "   :param tuple_int_var: example description.\n"
            "   :type tuple_int_var: tuple of tuple of int\n"
            )
    doctree = restructuredtext.parse(app, text)

    # :param list of str list_str_var:
    assert_node(doctree[3][1][0][0][1][0][0][0],
                ([addnodes.literal_strong, "list_str_var"],
                 " (",
                 [pending_xref, addnodes.literal_emphasis, "list"],
                 [addnodes.literal_emphasis, " of "],
                 [pending_xref, addnodes.literal_emphasis, "str"],
                 ")",
                 " -- ",
                 "example description."))

    # :param tuple of tuple of int tuple_int_var:
    assert_node(doctree[3][1][0][0][1][0][1][0],
                ([addnodes.literal_strong, "tuple_int_var"],
                 " (",
                 [pending_xref, addnodes.literal_emphasis, "tuple"],
                 [addnodes.literal_emphasis, " of "],
                 [pending_xref, addnodes.literal_emphasis, "tuple"],
                 [addnodes.literal_emphasis, " of "],
                 [pending_xref, addnodes.literal_emphasis, "int"],
                 ")",
                 " -- ",
                 "example description."))


def test_info_field_list_napoleon_deliminator_or(app):
    text = (".. py:module:: example\n"
            ".. py:class:: Class\n"
            "\n"
            "   :param bool_str_var: example description.\n"
            "   :type bool_str_var: bool or str\n"
            "   :param str_float_int_var: example description.\n"
            "   :type str_float_int_var: str or float or int\n"
            )
    doctree = restructuredtext.parse(app, text)

    # :param bool or str bool_str_var:
    assert_node(doctree[3][1][0][0][1][0][0][0],
                ([addnodes.literal_strong, "bool_str_var"],
                 " (",
                 [pending_xref, addnodes.literal_emphasis, "bool"],
                 [addnodes.literal_emphasis, " or "],
                 [pending_xref, addnodes.literal_emphasis, "str"],
                 ")",
                 " -- ",
                 "example description."))

    # :param str or float or int str_float_int_var:
    assert_node(doctree[3][1][0][0][1][0][1][0],
                ([addnodes.literal_strong, "str_float_int_var"],
                 " (",
                 [pending_xref, addnodes.literal_emphasis, "str"],
                 [addnodes.literal_emphasis, " or "],
                 [pending_xref, addnodes.literal_emphasis, "float"],
                 [addnodes.literal_emphasis, " or "],
                 [pending_xref, addnodes.literal_emphasis, "int"],
                 ")",
                 " -- ",
                 "example description."))


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
