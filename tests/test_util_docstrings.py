"""
    test_util_docstrings
    ~~~~~~~~~~~~~~~~~~~~

    Test sphinx.util.docstrings.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.util.docstrings import prepare_commentdoc, prepare_docstring, separate_metadata


def test_separate_metadata():
    # metadata only
    text = (":meta foo: bar\n"
            ":meta baz:\n")
    docstring, metadata = separate_metadata(text)
    assert docstring == ''
    assert metadata == {'foo': 'bar', 'baz': ''}

    # non metadata field list item
    text = (":meta foo: bar\n"
            ":param baz:\n")
    docstring, metadata = separate_metadata(text)
    assert docstring == ':param baz:\n'
    assert metadata == {'foo': 'bar'}

    # field_list like text following just after paragaph is not a field_list
    text = ("blah blah blah\n"
            ":meta foo: bar\n"
            ":meta baz:\n")
    docstring, metadata = separate_metadata(text)
    assert docstring == text
    assert metadata == {}

    # field_list like text following after blank line is a field_list
    text = ("blah blah blah\n"
            "\n"
            ":meta foo: bar\n"
            ":meta baz:\n")
    docstring, metadata = separate_metadata(text)
    assert docstring == "blah blah blah\n\n"
    assert metadata == {'foo': 'bar', 'baz': ''}

    # non field_list item breaks field_list
    text = (":meta foo: bar\n"
            "blah blah blah\n"
            ":meta baz:\n")
    docstring, metadata = separate_metadata(text)
    assert docstring == ("blah blah blah\n"
                         ":meta baz:\n")
    assert metadata == {'foo': 'bar'}


def test_prepare_docstring():
    docstring = """multiline docstring

                Lorem ipsum dolor sit amet, consectetur adipiscing elit,
                sed do eiusmod tempor incididunt ut labore et dolore magna
                aliqua::

                  Ut enim ad minim veniam, quis nostrud exercitation
                    ullamco laboris nisi ut aliquip ex ea commodo consequat.
                """

    assert (prepare_docstring(docstring) ==
            ["multiline docstring",
             "",
             "Lorem ipsum dolor sit amet, consectetur adipiscing elit,",
             "sed do eiusmod tempor incididunt ut labore et dolore magna",
             "aliqua::",
             "",
             "  Ut enim ad minim veniam, quis nostrud exercitation",
             "    ullamco laboris nisi ut aliquip ex ea commodo consequat.",
             ""])

    docstring = """

                multiline docstring with leading empty lines
                """
    assert (prepare_docstring(docstring) ==
            ["multiline docstring with leading empty lines",
             ""])

    docstring = "single line docstring"
    assert (prepare_docstring(docstring) ==
            ["single line docstring",
             ""])


def test_prepare_commentdoc():
    assert prepare_commentdoc("hello world") == []
    assert prepare_commentdoc("#: hello world") == ["hello world", ""]
    assert prepare_commentdoc("#:  hello world") == [" hello world", ""]
    assert prepare_commentdoc("#: hello\n#: world\n") == ["hello", "world", ""]
