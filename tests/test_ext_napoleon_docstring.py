"""
    test_napoleon_docstring
    ~~~~~~~~~~~~~~~~~~~~~~~

    Tests for :mod:`sphinx.ext.napoleon.docstring` module.


    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
from collections import namedtuple
from contextlib import contextmanager
from inspect import cleandoc
from textwrap import dedent
from unittest import TestCase, mock

import pytest

from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import (GoogleDocstring, NumpyDocstring,
                                           _convert_numpy_type_spec, _recombine_set_tokens,
                                           _token_type, _tokenize_type_spec)

if sys.version_info >= (3, 6):
    from .ext_napoleon_pep526_data_google import PEP526GoogleClass
    from .ext_napoleon_pep526_data_numpy import PEP526NumpyClass


class NamedtupleSubclass(namedtuple('NamedtupleSubclass', ('attr1', 'attr2'))):
    """Sample namedtuple subclass

    Attributes
    ----------
    attr1 : Arbitrary type
        Quick description of attr1
    attr2 : Another arbitrary type
        Quick description of attr2
    attr3 : Type

        Adds a newline after the type

    """
    # To avoid creating a dict, as a namedtuple doesn't have it:
    __slots__ = ()

    def __new__(cls, attr1, attr2=None):
        return super().__new__(cls, attr1, attr2)


class BaseDocstringTest(TestCase):
    pass


class NamedtupleSubclassTest(BaseDocstringTest):
    def test_attributes_docstring(self):
        config = Config()
        actual = str(NumpyDocstring(cleandoc(NamedtupleSubclass.__doc__),
                     config=config, app=None, what='class',
                     name='NamedtupleSubclass', obj=NamedtupleSubclass))
        expected = """\
Sample namedtuple subclass

.. attribute:: attr1

   Quick description of attr1

   :type: Arbitrary type

.. attribute:: attr2

   Quick description of attr2

   :type: Another arbitrary type

.. attribute:: attr3

   Adds a newline after the type

   :type: Type
"""

        self.assertEqual(expected, actual)


class InlineAttributeTest(BaseDocstringTest):

    def test_class_data_member(self):
        config = Config()
        docstring = dedent("""\
        data member description:

        - a: b
        """)
        actual = str(GoogleDocstring(docstring, config=config, app=None,
                     what='attribute', name='some_data', obj=0))
        expected = dedent("""\
        data member description:

        - a: b""")

        self.assertEqual(expected, actual)

    def test_class_data_member_inline(self):
        config = Config()
        docstring = """b: data member description with :ref:`reference`"""
        actual = str(GoogleDocstring(docstring, config=config, app=None,
                     what='attribute', name='some_data', obj=0))
        expected = dedent("""\
        data member description with :ref:`reference`

        :type: b""")
        self.assertEqual(expected, actual)

    def test_class_data_member_inline_no_type(self):
        config = Config()
        docstring = """data with ``a : in code`` and :ref:`reference` and no type"""
        actual = str(GoogleDocstring(docstring, config=config, app=None,
                     what='attribute', name='some_data', obj=0))
        expected = """data with ``a : in code`` and :ref:`reference` and no type"""

        self.assertEqual(expected, actual)

    def test_class_data_member_inline_ref_in_type(self):
        config = Config()
        docstring = """:class:`int`: data member description"""
        actual = str(GoogleDocstring(docstring, config=config, app=None,
                     what='attribute', name='some_data', obj=0))
        expected = dedent("""\
        data member description

        :type: :class:`int`""")
        self.assertEqual(expected, actual)


class GoogleDocstringTest(BaseDocstringTest):
    docstrings = [(
        """Single line summary""",
        """Single line summary"""
    ), (
        """
        Single line summary

        Extended description

        """,
        """
        Single line summary

        Extended description
        """
    ), (
        """
        Single line summary

        Args:
          arg1(str):Extended
            description of arg1
        """,
        """
        Single line summary

        :Parameters: **arg1** (*str*) -- Extended
                     description of arg1
        """
    ), (
        """
        Single line summary

        Args:
          arg1(str):Extended
            description of arg1
          arg2 ( int ) : Extended
            description of arg2

        Keyword Args:
          kwarg1(str):Extended
            description of kwarg1
          kwarg2 ( int ) : Extended
            description of kwarg2""",
        """
        Single line summary

        :Parameters: * **arg1** (*str*) -- Extended
                       description of arg1
                     * **arg2** (*int*) -- Extended
                       description of arg2

        :Keyword Arguments: * **kwarg1** (*str*) -- Extended
                              description of kwarg1
                            * **kwarg2** (*int*) -- Extended
                              description of kwarg2
        """
    ), (
        """
        Single line summary

        Arguments:
          arg1(str):Extended
            description of arg1
          arg2 ( int ) : Extended
            description of arg2

        Keyword Arguments:
          kwarg1(str):Extended
            description of kwarg1
          kwarg2 ( int ) : Extended
            description of kwarg2""",
        """
        Single line summary

        :Parameters: * **arg1** (*str*) -- Extended
                       description of arg1
                     * **arg2** (*int*) -- Extended
                       description of arg2

        :Keyword Arguments: * **kwarg1** (*str*) -- Extended
                              description of kwarg1
                            * **kwarg2** (*int*) -- Extended
                              description of kwarg2
        """
    ), (
        """
        Single line summary

        Return:
          str:Extended
          description of return value
        """,
        """
        Single line summary

        :returns: *str* -- Extended
                  description of return value
        """
    ), (
        """
        Single line summary

        Returns:
          str:Extended
          description of return value
        """,
        """
        Single line summary

        :returns: *str* -- Extended
                  description of return value
        """
    ), (
        """
        Single line summary

        Returns:
          Extended
          description of return value
        """,
        """
        Single line summary

        :returns: Extended
                  description of return value
        """
    ), (
        """
        Single line summary

        Args:
          arg1(str):Extended
            description of arg1
          *args: Variable length argument list.
          **kwargs: Arbitrary keyword arguments.
        """,
        """
        Single line summary

        :Parameters: * **arg1** (*str*) -- Extended
                       description of arg1
                     * **\\*args** -- Variable length argument list.
                     * **\\*\\*kwargs** -- Arbitrary keyword arguments.
        """
    ), (
        """
        Single line summary

        Args:
          arg1 (list(int)): Description
          arg2 (list[int]): Description
          arg3 (dict(str, int)): Description
          arg4 (dict[str, int]): Description
        """,
        """
        Single line summary

        :Parameters: * **arg1** (*list(int)*) -- Description
                     * **arg2** (*list[int]*) -- Description
                     * **arg3** (*dict(str, int)*) -- Description
                     * **arg4** (*dict[str, int]*) -- Description
        """
    ), (
        """
        Single line summary

        Receive:
          arg1 (list(int)): Description
          arg2 (list[int]): Description
        """,
        """
        Single line summary

        :Receives: * **arg1** (*list(int)*) -- Description
                   * **arg2** (*list[int]*) -- Description
        """
    ), (
        """
        Single line summary

        Receives:
          arg1 (list(int)): Description
          arg2 (list[int]): Description
        """,
        """
        Single line summary

        :Receives: * **arg1** (*list(int)*) -- Description
                   * **arg2** (*list[int]*) -- Description
        """
    ), (
        """
        Single line summary

        Yield:
          str:Extended
          description of yielded value
        """,
        """
        Single line summary

        :Yields: *str* -- Extended
                 description of yielded value
        """
    ), (
        """
        Single line summary

        Yields:
          Extended
          description of yielded value
        """,
        """
        Single line summary

        :Yields: Extended
                 description of yielded value
        """
    )]

    def test_sphinx_admonitions(self):
        admonition_map = {
            'Attention': 'attention',
            'Caution': 'caution',
            'Danger': 'danger',
            'Error': 'error',
            'Hint': 'hint',
            'Important': 'important',
            'Note': 'note',
            'Tip': 'tip',
            'Todo': 'todo',
            'Warning': 'warning',
            'Warnings': 'warning',
        }
        config = Config()
        for section, admonition in admonition_map.items():
            # Multiline
            actual = str(GoogleDocstring(("{}:\n"
                                          "    this is the first line\n"
                                          "\n"
                                          "    and this is the second line\n"
                                          ).format(section), config))
            expect = (".. {}::\n"
                      "\n"
                      "   this is the first line\n"
                      "   \n"
                      "   and this is the second line\n"
                      ).format(admonition)
            self.assertEqual(expect, actual)

            # Single line
            actual = str(GoogleDocstring(("{}:\n"
                                          "    this is a single line\n"
                                          ).format(section), config))
            expect = (".. {}:: this is a single line\n"
                      ).format(admonition)
            self.assertEqual(expect, actual)

    def test_docstrings(self):
        config = Config(
            napoleon_use_param=False,
            napoleon_use_rtype=False,
            napoleon_use_keyword=False
        )
        for docstring, expected in self.docstrings:
            actual = str(GoogleDocstring(dedent(docstring), config))
            expected = dedent(expected)
            self.assertEqual(expected, actual)

    def test_parameters_with_class_reference(self):
        docstring = """\
Construct a new XBlock.

This class should only be used by runtimes.

Arguments:
    runtime (:class:`~typing.Dict`\\[:class:`int`,:class:`str`\\]): Use it to
        access the environment. It is available in XBlock code
        as ``self.runtime``.

    field_data (:class:`FieldData`): Interface used by the XBlock
        fields to access their data from wherever it is persisted.

    scope_ids (:class:`ScopeIds`): Identifiers needed to resolve scopes.

"""

        actual = str(GoogleDocstring(docstring))
        expected = """\
Construct a new XBlock.

This class should only be used by runtimes.

:param runtime: Use it to
                access the environment. It is available in XBlock code
                as ``self.runtime``.
:type runtime: :class:`~typing.Dict`\\[:class:`int`,:class:`str`\\]
:param field_data: Interface used by the XBlock
                   fields to access their data from wherever it is persisted.
:type field_data: :class:`FieldData`
:param scope_ids: Identifiers needed to resolve scopes.
:type scope_ids: :class:`ScopeIds`
"""
        self.assertEqual(expected, actual)

    def test_attributes_with_class_reference(self):
        docstring = """\
Attributes:
    in_attr(:class:`numpy.ndarray`): super-dooper attribute
"""

        actual = str(GoogleDocstring(docstring))
        expected = """\
.. attribute:: in_attr

   super-dooper attribute

   :type: :class:`numpy.ndarray`
"""
        self.assertEqual(expected, actual)

        docstring = """\
Attributes:
    in_attr(numpy.ndarray): super-dooper attribute
"""

        actual = str(GoogleDocstring(docstring))
        expected = """\
.. attribute:: in_attr

   super-dooper attribute

   :type: numpy.ndarray
"""
        self.assertEqual(expected, actual)

    def test_code_block_in_returns_section(self):
        docstring = """
Returns:
    foobar: foo::

        codecode
        codecode
"""
        expected = """
:returns:

          foo::

              codecode
              codecode
:rtype: foobar
"""
        actual = str(GoogleDocstring(docstring))
        self.assertEqual(expected, actual)

    def test_colon_in_return_type(self):
        docstring = """Example property.

Returns:
    :py:class:`~.module.submodule.SomeClass`: an example instance
    if available, None if not available.
"""
        expected = """Example property.

:returns: an example instance
          if available, None if not available.
:rtype: :py:class:`~.module.submodule.SomeClass`
"""
        actual = str(GoogleDocstring(docstring))
        self.assertEqual(expected, actual)

    def test_xrefs_in_return_type(self):
        docstring = """Example Function

Returns:
    :class:`numpy.ndarray`: A :math:`n \\times 2` array containing
    a bunch of math items
"""
        expected = """Example Function

:returns: A :math:`n \\times 2` array containing
          a bunch of math items
:rtype: :class:`numpy.ndarray`
"""
        actual = str(GoogleDocstring(docstring))
        self.assertEqual(expected, actual)

    def test_raises_types(self):
        docstrings = [("""
Example Function

Raises:
    RuntimeError:
        A setting wasn't specified, or was invalid.
    ValueError:
        Something something value error.
    :py:class:`AttributeError`
        errors for missing attributes.
    ~InvalidDimensionsError
        If the dimensions couldn't be parsed.
    `InvalidArgumentsError`
        If the arguments are invalid.
    :exc:`~ValueError`
        If the arguments are wrong.

""", """
Example Function

:raises RuntimeError: A setting wasn't specified, or was invalid.
:raises ValueError: Something something value error.
:raises AttributeError: errors for missing attributes.
:raises ~InvalidDimensionsError: If the dimensions couldn't be parsed.
:raises InvalidArgumentsError: If the arguments are invalid.
:raises ~ValueError: If the arguments are wrong.
"""),
                      ################################
                      ("""
Example Function

Raises:
    InvalidDimensionsError

""", """
Example Function

:raises InvalidDimensionsError:
"""),
                      ################################
                      ("""
Example Function

Raises:
    Invalid Dimensions Error

""", """
Example Function

:raises Invalid Dimensions Error:
"""),
                      ################################
                      ("""
Example Function

Raises:
    Invalid Dimensions Error: With description

""", """
Example Function

:raises Invalid Dimensions Error: With description
"""),
                      ################################
                      ("""
Example Function

Raises:
    InvalidDimensionsError: If the dimensions couldn't be parsed.

""", """
Example Function

:raises InvalidDimensionsError: If the dimensions couldn't be parsed.
"""),
                      ################################
                      ("""
Example Function

Raises:
    Invalid Dimensions Error: If the dimensions couldn't be parsed.

""", """
Example Function

:raises Invalid Dimensions Error: If the dimensions couldn't be parsed.
"""),
                      ################################
                      ("""
Example Function

Raises:
    If the dimensions couldn't be parsed.

""", """
Example Function

:raises If the dimensions couldn't be parsed.:
"""),
                      ################################
                      ("""
Example Function

Raises:
    :class:`exc.InvalidDimensionsError`

""", """
Example Function

:raises exc.InvalidDimensionsError:
"""),
                      ################################
                      ("""
Example Function

Raises:
    :class:`exc.InvalidDimensionsError`: If the dimensions couldn't be parsed.

""", """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed.
"""),
                      ################################
                      ("""
Example Function

Raises:
    :class:`exc.InvalidDimensionsError`: If the dimensions couldn't be parsed,
       then a :class:`exc.InvalidDimensionsError` will be raised.

""", """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed,
    then a :class:`exc.InvalidDimensionsError` will be raised.
"""),
                      ################################
                      ("""
Example Function

Raises:
    :class:`exc.InvalidDimensionsError`: If the dimensions couldn't be parsed.
    :class:`exc.InvalidArgumentsError`: If the arguments are invalid.

""", """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed.
:raises exc.InvalidArgumentsError: If the arguments are invalid.
"""),
                      ################################
                      ("""
Example Function

Raises:
    :class:`exc.InvalidDimensionsError`
    :class:`exc.InvalidArgumentsError`

""", """
Example Function

:raises exc.InvalidDimensionsError:
:raises exc.InvalidArgumentsError:
""")]
        for docstring, expected in docstrings:
            actual = str(GoogleDocstring(docstring))
            self.assertEqual(expected, actual)

    def test_kwargs_in_arguments(self):
        docstring = """Allows to create attributes binded to this device.

Some other paragraph.

Code sample for usage::

  dev.bind(loopback=Loopback)
  dev.loopback.configure()

Arguments:
  **kwargs: name/class pairs that will create resource-managers
    bound as instance attributes to this instance. See code
    example above.
"""
        expected = """Allows to create attributes binded to this device.

Some other paragraph.

Code sample for usage::

  dev.bind(loopback=Loopback)
  dev.loopback.configure()

:param \\*\\*kwargs: name/class pairs that will create resource-managers
                   bound as instance attributes to this instance. See code
                   example above.
"""
        actual = str(GoogleDocstring(docstring))
        self.assertEqual(expected, actual)

    def test_section_header_formatting(self):
        docstrings = [("""
Summary line

Example:
    Multiline reStructuredText
    literal code block

""", """
Summary line

.. rubric:: Example

Multiline reStructuredText
literal code block
"""),
                      ################################
                      ("""
Summary line

Example::

    Multiline reStructuredText
    literal code block

""", """
Summary line

Example::

    Multiline reStructuredText
    literal code block
"""),
                      ################################
                      ("""
Summary line

:Example:

    Multiline reStructuredText
    literal code block

""", """
Summary line

:Example:

    Multiline reStructuredText
    literal code block
""")]
        for docstring, expected in docstrings:
            actual = str(GoogleDocstring(docstring))
            self.assertEqual(expected, actual)

    def test_list_in_parameter_description(self):
        docstring = """One line summary.

Parameters:
    no_list (int):
    one_bullet_empty (int):
        *
    one_bullet_single_line (int):
        - first line
    one_bullet_two_lines (int):
        +   first line
            continued
    two_bullets_single_line (int):
        -  first line
        -  second line
    two_bullets_two_lines (int):
        * first line
          continued
        * second line
          continued
    one_enumeration_single_line (int):
        1.  first line
    one_enumeration_two_lines (int):
        1)   first line
             continued
    two_enumerations_one_line (int):
        (iii) first line
        (iv) second line
    two_enumerations_two_lines (int):
        a. first line
           continued
        b. second line
           continued
    one_definition_one_line (int):
        item 1
            first line
    one_definition_two_lines (int):
        item 1
            first line
            continued
    two_definitions_one_line (int):
        item 1
            first line
        item 2
            second line
    two_definitions_two_lines (int):
        item 1
            first line
            continued
        item 2
            second line
            continued
    one_definition_blank_line (int):
        item 1

            first line

            extra first line

    two_definitions_blank_lines (int):
        item 1

            first line

            extra first line

        item 2

            second line

            extra second line

    definition_after_inline_text (int): text line

        item 1
            first line

    definition_after_normal_text (int):
        text line

        item 1
            first line
"""

        expected = """One line summary.

:param no_list:
:type no_list: int
:param one_bullet_empty:
                         *
:type one_bullet_empty: int
:param one_bullet_single_line:
                               - first line
:type one_bullet_single_line: int
:param one_bullet_two_lines:
                             +   first line
                                 continued
:type one_bullet_two_lines: int
:param two_bullets_single_line:
                                -  first line
                                -  second line
:type two_bullets_single_line: int
:param two_bullets_two_lines:
                              * first line
                                continued
                              * second line
                                continued
:type two_bullets_two_lines: int
:param one_enumeration_single_line:
                                    1.  first line
:type one_enumeration_single_line: int
:param one_enumeration_two_lines:
                                  1)   first line
                                       continued
:type one_enumeration_two_lines: int
:param two_enumerations_one_line:
                                  (iii) first line
                                  (iv) second line
:type two_enumerations_one_line: int
:param two_enumerations_two_lines:
                                   a. first line
                                      continued
                                   b. second line
                                      continued
:type two_enumerations_two_lines: int
:param one_definition_one_line:
                                item 1
                                    first line
:type one_definition_one_line: int
:param one_definition_two_lines:
                                 item 1
                                     first line
                                     continued
:type one_definition_two_lines: int
:param two_definitions_one_line:
                                 item 1
                                     first line
                                 item 2
                                     second line
:type two_definitions_one_line: int
:param two_definitions_two_lines:
                                  item 1
                                      first line
                                      continued
                                  item 2
                                      second line
                                      continued
:type two_definitions_two_lines: int
:param one_definition_blank_line:
                                  item 1

                                      first line

                                      extra first line
:type one_definition_blank_line: int
:param two_definitions_blank_lines:
                                    item 1

                                        first line

                                        extra first line

                                    item 2

                                        second line

                                        extra second line
:type two_definitions_blank_lines: int
:param definition_after_inline_text: text line

                                     item 1
                                         first line
:type definition_after_inline_text: int
:param definition_after_normal_text: text line

                                     item 1
                                         first line
:type definition_after_normal_text: int
"""
        config = Config(napoleon_use_param=True)
        actual = str(GoogleDocstring(docstring, config))
        self.assertEqual(expected, actual)

        expected = """One line summary.

:Parameters: * **no_list** (*int*)
             * **one_bullet_empty** (*int*) --

               *
             * **one_bullet_single_line** (*int*) --

               - first line
             * **one_bullet_two_lines** (*int*) --

               +   first line
                   continued
             * **two_bullets_single_line** (*int*) --

               -  first line
               -  second line
             * **two_bullets_two_lines** (*int*) --

               * first line
                 continued
               * second line
                 continued
             * **one_enumeration_single_line** (*int*) --

               1.  first line
             * **one_enumeration_two_lines** (*int*) --

               1)   first line
                    continued
             * **two_enumerations_one_line** (*int*) --

               (iii) first line
               (iv) second line
             * **two_enumerations_two_lines** (*int*) --

               a. first line
                  continued
               b. second line
                  continued
             * **one_definition_one_line** (*int*) --

               item 1
                   first line
             * **one_definition_two_lines** (*int*) --

               item 1
                   first line
                   continued
             * **two_definitions_one_line** (*int*) --

               item 1
                   first line
               item 2
                   second line
             * **two_definitions_two_lines** (*int*) --

               item 1
                   first line
                   continued
               item 2
                   second line
                   continued
             * **one_definition_blank_line** (*int*) --

               item 1

                   first line

                   extra first line
             * **two_definitions_blank_lines** (*int*) --

               item 1

                   first line

                   extra first line

               item 2

                   second line

                   extra second line
             * **definition_after_inline_text** (*int*) -- text line

               item 1
                   first line
             * **definition_after_normal_text** (*int*) -- text line

               item 1
                   first line
"""
        config = Config(napoleon_use_param=False)
        actual = str(GoogleDocstring(docstring, config))
        self.assertEqual(expected, actual)

    def test_custom_generic_sections(self):

        docstrings = (("""\
Really Important Details:
    You should listen to me!
""", """.. rubric:: Really Important Details

You should listen to me!
"""),
                      ("""\
Sooper Warning:
    Stop hitting yourself!
""", """:Warns: **Stop hitting yourself!**
"""),
                      ("""\
Params Style:
    arg1 (int): Description of arg1
    arg2 (str): Description of arg2

""", """\
:Params Style: * **arg1** (*int*) -- Description of arg1
               * **arg2** (*str*) -- Description of arg2
"""),
                      ("""\
Returns Style:
    description of custom section

""", """:Returns Style: description of custom section
"""))

        testConfig = Config(napoleon_custom_sections=['Really Important Details',
                                                      ('Sooper Warning', 'warns'),
                                                      ('Params Style', 'params_style'),
                                                      ('Returns Style', 'returns_style')])

        for docstring, expected in docstrings:
            actual = str(GoogleDocstring(docstring, testConfig))
            self.assertEqual(expected, actual)

    def test_noindex(self):
        docstring = """
Attributes:
    arg
        description

Methods:
    func(i, j)
        description
"""

        expected = """
.. attribute:: arg
   :noindex:

   description

.. method:: func(i, j)
   :noindex:

   
   description
"""  # NOQA
        config = Config()
        actual = str(GoogleDocstring(docstring, config=config, app=None, what='module',
                                     options={'noindex': True}))
        self.assertEqual(expected, actual)

    def test_keywords_with_types(self):
        docstring = """\
Do as you please

Keyword Args:
    gotham_is_yours (None): shall interfere.
"""
        actual = str(GoogleDocstring(docstring))
        expected = """\
Do as you please

:keyword gotham_is_yours: shall interfere.
:kwtype gotham_is_yours: None
"""
        self.assertEqual(expected, actual)

    def test_pep526_annotations(self):
        if sys.version_info >= (3, 6):
            # Test class attributes annotations
            config = Config(
                napoleon_attr_annotations=True
            )
            actual = str(GoogleDocstring(cleandoc(PEP526GoogleClass.__doc__), config, app=None, what="class",
                                         obj=PEP526GoogleClass))
            expected = """\
Sample class with PEP 526 annotations and google docstring

.. attribute:: attr1

   Attr1 description.

   :type: int

.. attribute:: attr2

   Attr2 description.

   :type: str
"""
            self.assertEqual(expected, actual)

    def test_preprocess_types(self):
        docstring = """\
Do as you please

Yield:
   str:Extended
"""
        actual = str(GoogleDocstring(docstring))
        expected = """\
Do as you please

:Yields: *str* -- Extended
"""
        self.assertEqual(expected, actual)

        config = Config(napoleon_preprocess_types=True)
        actual = str(GoogleDocstring(docstring, config))
        expected = """\
Do as you please

:Yields: :class:`str` -- Extended
"""
        self.assertEqual(expected, actual)


class NumpyDocstringTest(BaseDocstringTest):
    docstrings = [(
        """Single line summary""",
        """Single line summary"""
    ), (
        """
        Single line summary

        Extended description

        """,
        """
        Single line summary

        Extended description
        """
    ), (
        """
        Single line summary

        Parameters
        ----------
        arg1:str
            Extended
            description of arg1
        """,
        """
        Single line summary

        :Parameters: **arg1** (:class:`str`) -- Extended
                     description of arg1
        """
    ), (
        """
        Single line summary

        Parameters
        ----------
        arg1:str
            Extended
            description of arg1
        arg2 : int
            Extended
            description of arg2

        Keyword Arguments
        -----------------
          kwarg1:str
              Extended
              description of kwarg1
          kwarg2 : int
              Extended
              description of kwarg2
        """,
        """
        Single line summary

        :Parameters: * **arg1** (:class:`str`) -- Extended
                       description of arg1
                     * **arg2** (:class:`int`) -- Extended
                       description of arg2

        :Keyword Arguments: * **kwarg1** (:class:`str`) -- Extended
                              description of kwarg1
                            * **kwarg2** (:class:`int`) -- Extended
                              description of kwarg2
        """
    ), (
        """
        Single line summary

        Return
        ------
        str
            Extended
            description of return value
        """,
        """
        Single line summary

        :returns: :class:`str` -- Extended
                  description of return value
        """
    ), (
        """
        Single line summary

        Returns
        -------
        str
            Extended
            description of return value
        """,
        """
        Single line summary

        :returns: :class:`str` -- Extended
                  description of return value
        """
    ), (
        """
        Single line summary

        Parameters
        ----------
        arg1:str
             Extended description of arg1
        *args:
            Variable length argument list.
        **kwargs:
            Arbitrary keyword arguments.
        """,
        """
        Single line summary

        :Parameters: * **arg1** (:class:`str`) -- Extended description of arg1
                     * **\\*args** -- Variable length argument list.
                     * **\\*\\*kwargs** -- Arbitrary keyword arguments.
        """
    ), (
        """
        Single line summary

        Parameters
        ----------
        arg1:str
             Extended description of arg1
        *args, **kwargs:
            Variable length argument list and arbitrary keyword arguments.
        """,
        """
        Single line summary

        :Parameters: * **arg1** (:class:`str`) -- Extended description of arg1
                     * **\\*args, \\*\\*kwargs** -- Variable length argument list and arbitrary keyword arguments.
        """
    ), (
        """
        Single line summary

        Receive
        -------
        arg1:str
            Extended
            description of arg1
        arg2 : int
            Extended
            description of arg2
        """,
        """
        Single line summary

        :Receives: * **arg1** (:class:`str`) -- Extended
                     description of arg1
                   * **arg2** (:class:`int`) -- Extended
                     description of arg2
        """
    ), (
        """
        Single line summary

        Receives
        --------
        arg1:str
            Extended
            description of arg1
        arg2 : int
            Extended
            description of arg2
        """,
        """
        Single line summary

        :Receives: * **arg1** (:class:`str`) -- Extended
                     description of arg1
                   * **arg2** (:class:`int`) -- Extended
                     description of arg2
        """
    ), (
        """
        Single line summary

        Yield
        -----
        str
            Extended
            description of yielded value
        """,
        """
        Single line summary

        :Yields: :class:`str` -- Extended
                 description of yielded value
        """
    ), (
        """
        Single line summary

        Yields
        ------
        str
            Extended
            description of yielded value
        """,
        """
        Single line summary

        :Yields: :class:`str` -- Extended
                 description of yielded value
        """
    )]

    def test_sphinx_admonitions(self):
        admonition_map = {
            'Attention': 'attention',
            'Caution': 'caution',
            'Danger': 'danger',
            'Error': 'error',
            'Hint': 'hint',
            'Important': 'important',
            'Note': 'note',
            'Tip': 'tip',
            'Todo': 'todo',
            'Warning': 'warning',
            'Warnings': 'warning',
        }
        config = Config()
        for section, admonition in admonition_map.items():
            # Multiline
            actual = str(NumpyDocstring(("{}\n"
                                         "{}\n"
                                         "    this is the first line\n"
                                         "\n"
                                         "    and this is the second line\n"
                                         ).format(section, '-' * len(section)), config))
            expect = (".. {}::\n"
                      "\n"
                      "   this is the first line\n"
                      "   \n"
                      "   and this is the second line\n"
                      ).format(admonition)
            self.assertEqual(expect, actual)

            # Single line
            actual = str(NumpyDocstring(("{}\n"
                                         "{}\n"
                                         "    this is a single line\n"
                                         ).format(section, '-' * len(section)), config))
            expect = (".. {}:: this is a single line\n"
                      ).format(admonition)
            self.assertEqual(expect, actual)

    def test_docstrings(self):
        config = Config(
            napoleon_use_param=False,
            napoleon_use_rtype=False,
            napoleon_use_keyword=False,
            napoleon_preprocess_types=True)
        for docstring, expected in self.docstrings:
            actual = str(NumpyDocstring(dedent(docstring), config))
            expected = dedent(expected)
            self.assertEqual(expected, actual)

    def test_type_preprocessor(self):
        docstring = dedent("""
        Single line summary

        Parameters
        ----------
        arg1:str
            Extended
            description of arg1
        """)

        config = Config(napoleon_preprocess_types=False, napoleon_use_param=False)
        actual = str(NumpyDocstring(docstring, config))
        expected = dedent("""
        Single line summary

        :Parameters: **arg1** (*str*) -- Extended
                     description of arg1
        """)
        self.assertEqual(expected, actual)

    def test_parameters_with_class_reference(self):
        docstring = """\
Parameters
----------
param1 : :class:`MyClass <name.space.MyClass>` instance

Other Parameters
----------------
param2 : :class:`MyClass <name.space.MyClass>` instance

"""

        config = Config(napoleon_use_param=False)
        actual = str(NumpyDocstring(docstring, config))
        expected = """\
:Parameters: **param1** (:class:`MyClass <name.space.MyClass>` instance)

:Other Parameters: **param2** (:class:`MyClass <name.space.MyClass>` instance)
"""
        self.assertEqual(expected, actual)

        config = Config(napoleon_use_param=True)
        actual = str(NumpyDocstring(docstring, config))
        expected = """\
:param param1:
:type param1: :class:`MyClass <name.space.MyClass>` instance

:param param2:
:type param2: :class:`MyClass <name.space.MyClass>` instance
"""
        self.assertEqual(expected, actual)

    def test_multiple_parameters(self):
        docstring = """\
Parameters
----------
x1, x2 : array_like
    Input arrays, description of ``x1``, ``x2``.

"""

        config = Config(napoleon_use_param=False)
        actual = str(NumpyDocstring(docstring, config))
        expected = """\
:Parameters: **x1, x2** (*array_like*) -- Input arrays, description of ``x1``, ``x2``.
"""
        self.assertEqual(expected, actual)

        config = Config(napoleon_use_param=True)
        actual = str(NumpyDocstring(dedent(docstring), config))
        expected = """\
:param x1: Input arrays, description of ``x1``, ``x2``.
:type x1: array_like
:param x2: Input arrays, description of ``x1``, ``x2``.
:type x2: array_like
"""
        self.assertEqual(expected, actual)

    def test_parameters_without_class_reference(self):
        docstring = """\
Parameters
----------
param1 : MyClass instance

"""

        config = Config(napoleon_use_param=False)
        actual = str(NumpyDocstring(docstring, config))
        expected = """\
:Parameters: **param1** (*MyClass instance*)
"""
        self.assertEqual(expected, actual)

        config = Config(napoleon_use_param=True)
        actual = str(NumpyDocstring(dedent(docstring), config))
        expected = """\
:param param1:
:type param1: MyClass instance
"""
        self.assertEqual(expected, actual)

    def test_see_also_refs(self):
        docstring = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

See Also
--------
some, other, funcs
otherfunc : relationship

"""

        actual = str(NumpyDocstring(docstring))

        expected = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

.. seealso::

   :obj:`some`, :obj:`other`, :obj:`funcs`
   \n\
   :obj:`otherfunc`
       relationship
"""
        self.assertEqual(expected, actual)

        docstring = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

See Also
--------
some, other, funcs
otherfunc : relationship

"""

        config = Config()
        app = mock.Mock()
        actual = str(NumpyDocstring(docstring, config, app, "method"))

        expected = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

.. seealso::

   :obj:`some`, :obj:`other`, :obj:`funcs`
   \n\
   :obj:`otherfunc`
       relationship
"""
        self.assertEqual(expected, actual)

        docstring = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

See Also
--------
some, other, :func:`funcs`
otherfunc : relationship

"""
        translations = {
            "other": "MyClass.other",
            "otherfunc": ":func:`~my_package.otherfunc`",
        }
        config = Config(napoleon_type_aliases=translations)
        app = mock.Mock()
        actual = str(NumpyDocstring(docstring, config, app, "method"))

        expected = """\
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

.. seealso::

   :obj:`some`, :obj:`MyClass.other`, :func:`funcs`
   \n\
   :func:`~my_package.otherfunc`
       relationship
"""
        self.assertEqual(expected, actual)

    def test_colon_in_return_type(self):
        docstring = """
Summary

Returns
-------
:py:class:`~my_mod.my_class`
    an instance of :py:class:`~my_mod.my_class`
"""

        expected = """
Summary

:returns: an instance of :py:class:`~my_mod.my_class`
:rtype: :py:class:`~my_mod.my_class`
"""

        config = Config()
        app = mock.Mock()
        actual = str(NumpyDocstring(docstring, config, app, "method"))

        self.assertEqual(expected, actual)

    def test_underscore_in_attribute(self):
        docstring = """
Attributes
----------

arg_ : type
    some description
"""

        expected = """
:ivar arg_: some description
:vartype arg_: type
"""

        config = Config(napoleon_use_ivar=True)
        app = mock.Mock()
        actual = str(NumpyDocstring(docstring, config, app, "class"))

        self.assertEqual(expected, actual)

    def test_underscore_in_attribute_strip_signature_backslash(self):
        docstring = """
Attributes
----------

arg_ : type
    some description
"""

        expected = """
:ivar arg\\_: some description
:vartype arg\\_: type
"""

        config = Config(napoleon_use_ivar=True)
        config.strip_signature_backslash = True
        app = mock.Mock()
        actual = str(NumpyDocstring(docstring, config, app, "class"))

        self.assertEqual(expected, actual)

    def test_return_types(self):
        docstring = dedent("""
            Returns
            -------
            DataFrame
                a dataframe
        """)
        expected = dedent("""
           :returns: a dataframe
           :rtype: :class:`~pandas.DataFrame`
        """)
        translations = {
            "DataFrame": "~pandas.DataFrame",
        }
        config = Config(
            napoleon_use_param=True,
            napoleon_use_rtype=True,
            napoleon_preprocess_types=True,
            napoleon_type_aliases=translations,
        )
        actual = str(NumpyDocstring(docstring, config))
        self.assertEqual(expected, actual)

    def test_yield_types(self):
        docstring = dedent("""
            Example Function

            Yields
            ------
            scalar or array-like
                The result of the computation
        """)
        expected = dedent("""
            Example Function

            :Yields: :term:`scalar` or :class:`array-like <numpy.ndarray>` -- The result of the computation
        """)
        translations = {
            "scalar": ":term:`scalar`",
            "array-like": ":class:`array-like <numpy.ndarray>`",
        }
        config = Config(napoleon_type_aliases=translations, napoleon_preprocess_types=True)
        app = mock.Mock()
        actual = str(NumpyDocstring(docstring, config, app, "method"))
        self.assertEqual(expected, actual)

    def test_raises_types(self):
        docstrings = [("""
Example Function

Raises
------
  RuntimeError

      A setting wasn't specified, or was invalid.
  ValueError

      Something something value error.

""", """
Example Function

:raises RuntimeError: A setting wasn't specified, or was invalid.
:raises ValueError: Something something value error.
"""),
                      ################################
                      ("""
Example Function

Raises
------
InvalidDimensionsError

""", """
Example Function

:raises InvalidDimensionsError:
"""),
                      ################################
                      ("""
Example Function

Raises
------
Invalid Dimensions Error

""", """
Example Function

:raises Invalid Dimensions Error:
"""),
                      ################################
                      ("""
Example Function

Raises
------
Invalid Dimensions Error
    With description

""", """
Example Function

:raises Invalid Dimensions Error: With description
"""),
                      ################################
                      ("""
Example Function

Raises
------
InvalidDimensionsError
    If the dimensions couldn't be parsed.

""", """
Example Function

:raises InvalidDimensionsError: If the dimensions couldn't be parsed.
"""),
                      ################################
                      ("""
Example Function

Raises
------
Invalid Dimensions Error
    If the dimensions couldn't be parsed.

""", """
Example Function

:raises Invalid Dimensions Error: If the dimensions couldn't be parsed.
"""),
                      ################################
                      ("""
Example Function

Raises
------
If the dimensions couldn't be parsed.

""", """
Example Function

:raises If the dimensions couldn't be parsed.:
"""),
                      ################################
                      ("""
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`

""", """
Example Function

:raises exc.InvalidDimensionsError:
"""),
                      ################################
                      ("""
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`
    If the dimensions couldn't be parsed.

""", """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed.
"""),
                      ################################
                      ("""
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`
    If the dimensions couldn't be parsed,
    then a :class:`exc.InvalidDimensionsError` will be raised.

""", """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed,
    then a :class:`exc.InvalidDimensionsError` will be raised.
"""),
                      ################################
                      ("""
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`
    If the dimensions couldn't be parsed.
:class:`exc.InvalidArgumentsError`
    If the arguments are invalid.

""", """
Example Function

:raises exc.InvalidDimensionsError: If the dimensions couldn't be parsed.
:raises exc.InvalidArgumentsError: If the arguments are invalid.
"""),
                      ################################
                      ("""
Example Function

Raises
------
CustomError
    If the dimensions couldn't be parsed.

""", """
Example Function

:raises package.CustomError: If the dimensions couldn't be parsed.
"""),
                      ################################
                      ("""
Example Function

Raises
------
AnotherError
    If the dimensions couldn't be parsed.

""", """
Example Function

:raises ~package.AnotherError: If the dimensions couldn't be parsed.
"""),
                      ################################
                      ("""
Example Function

Raises
------
:class:`exc.InvalidDimensionsError`
:class:`exc.InvalidArgumentsError`

""", """
Example Function

:raises exc.InvalidDimensionsError:
:raises exc.InvalidArgumentsError:
""")]
        for docstring, expected in docstrings:
            translations = {
                "CustomError": "package.CustomError",
                "AnotherError": ":py:exc:`~package.AnotherError`",
            }
            config = Config(napoleon_type_aliases=translations, napoleon_preprocess_types=True)
            app = mock.Mock()
            actual = str(NumpyDocstring(docstring, config, app, "method"))
            self.assertEqual(expected, actual)

    def test_xrefs_in_return_type(self):
        docstring = """
Example Function

Returns
-------
:class:`numpy.ndarray`
    A :math:`n \\times 2` array containing
    a bunch of math items
"""
        expected = """
Example Function

:returns: A :math:`n \\times 2` array containing
          a bunch of math items
:rtype: :class:`numpy.ndarray`
"""
        config = Config()
        app = mock.Mock()
        actual = str(NumpyDocstring(docstring, config, app, "method"))
        self.assertEqual(expected, actual)

    def test_section_header_underline_length(self):
        docstrings = [("""
Summary line

Example
-
Multiline example
body

""", """
Summary line

Example
-
Multiline example
body
"""),
                      ################################
                      ("""
Summary line

Example
--
Multiline example
body

""", """
Summary line

.. rubric:: Example

Multiline example
body
"""),
                      ################################
                      ("""
Summary line

Example
-------
Multiline example
body

""", """
Summary line

.. rubric:: Example

Multiline example
body
"""),
                      ################################
                      ("""
Summary line

Example
------------
Multiline example
body

""", """
Summary line

.. rubric:: Example

Multiline example
body
""")]
        for docstring, expected in docstrings:
            actual = str(NumpyDocstring(docstring))
            self.assertEqual(expected, actual)

    def test_list_in_parameter_description(self):
        docstring = """One line summary.

Parameters
----------
no_list : int
one_bullet_empty : int
    *
one_bullet_single_line : int
    - first line
one_bullet_two_lines : int
    +   first line
        continued
two_bullets_single_line : int
    -  first line
    -  second line
two_bullets_two_lines : int
    * first line
      continued
    * second line
      continued
one_enumeration_single_line : int
    1.  first line
one_enumeration_two_lines : int
    1)   first line
         continued
two_enumerations_one_line : int
    (iii) first line
    (iv) second line
two_enumerations_two_lines : int
    a. first line
       continued
    b. second line
       continued
one_definition_one_line : int
    item 1
        first line
one_definition_two_lines : int
    item 1
        first line
        continued
two_definitions_one_line : int
    item 1
        first line
    item 2
        second line
two_definitions_two_lines : int
    item 1
        first line
        continued
    item 2
        second line
        continued
one_definition_blank_line : int
    item 1

        first line

        extra first line

two_definitions_blank_lines : int
    item 1

        first line

        extra first line

    item 2

        second line

        extra second line

definition_after_normal_text : int
    text line

    item 1
        first line
"""

        expected = """One line summary.

:param no_list:
:type no_list: int
:param one_bullet_empty:
                         *
:type one_bullet_empty: int
:param one_bullet_single_line:
                               - first line
:type one_bullet_single_line: int
:param one_bullet_two_lines:
                             +   first line
                                 continued
:type one_bullet_two_lines: int
:param two_bullets_single_line:
                                -  first line
                                -  second line
:type two_bullets_single_line: int
:param two_bullets_two_lines:
                              * first line
                                continued
                              * second line
                                continued
:type two_bullets_two_lines: int
:param one_enumeration_single_line:
                                    1.  first line
:type one_enumeration_single_line: int
:param one_enumeration_two_lines:
                                  1)   first line
                                       continued
:type one_enumeration_two_lines: int
:param two_enumerations_one_line:
                                  (iii) first line
                                  (iv) second line
:type two_enumerations_one_line: int
:param two_enumerations_two_lines:
                                   a. first line
                                      continued
                                   b. second line
                                      continued
:type two_enumerations_two_lines: int
:param one_definition_one_line:
                                item 1
                                    first line
:type one_definition_one_line: int
:param one_definition_two_lines:
                                 item 1
                                     first line
                                     continued
:type one_definition_two_lines: int
:param two_definitions_one_line:
                                 item 1
                                     first line
                                 item 2
                                     second line
:type two_definitions_one_line: int
:param two_definitions_two_lines:
                                  item 1
                                      first line
                                      continued
                                  item 2
                                      second line
                                      continued
:type two_definitions_two_lines: int
:param one_definition_blank_line:
                                  item 1

                                      first line

                                      extra first line
:type one_definition_blank_line: int
:param two_definitions_blank_lines:
                                    item 1

                                        first line

                                        extra first line

                                    item 2

                                        second line

                                        extra second line
:type two_definitions_blank_lines: int
:param definition_after_normal_text: text line

                                     item 1
                                         first line
:type definition_after_normal_text: int
"""
        config = Config(napoleon_use_param=True)
        actual = str(NumpyDocstring(docstring, config))
        self.assertEqual(expected, actual)

        expected = """One line summary.

:Parameters: * **no_list** (:class:`int`)
             * **one_bullet_empty** (:class:`int`) --

               *
             * **one_bullet_single_line** (:class:`int`) --

               - first line
             * **one_bullet_two_lines** (:class:`int`) --

               +   first line
                   continued
             * **two_bullets_single_line** (:class:`int`) --

               -  first line
               -  second line
             * **two_bullets_two_lines** (:class:`int`) --

               * first line
                 continued
               * second line
                 continued
             * **one_enumeration_single_line** (:class:`int`) --

               1.  first line
             * **one_enumeration_two_lines** (:class:`int`) --

               1)   first line
                    continued
             * **two_enumerations_one_line** (:class:`int`) --

               (iii) first line
               (iv) second line
             * **two_enumerations_two_lines** (:class:`int`) --

               a. first line
                  continued
               b. second line
                  continued
             * **one_definition_one_line** (:class:`int`) --

               item 1
                   first line
             * **one_definition_two_lines** (:class:`int`) --

               item 1
                   first line
                   continued
             * **two_definitions_one_line** (:class:`int`) --

               item 1
                   first line
               item 2
                   second line
             * **two_definitions_two_lines** (:class:`int`) --

               item 1
                   first line
                   continued
               item 2
                   second line
                   continued
             * **one_definition_blank_line** (:class:`int`) --

               item 1

                   first line

                   extra first line
             * **two_definitions_blank_lines** (:class:`int`) --

               item 1

                   first line

                   extra first line

               item 2

                   second line

                   extra second line
             * **definition_after_normal_text** (:class:`int`) -- text line

               item 1
                   first line
"""
        config = Config(napoleon_use_param=False, napoleon_preprocess_types=True)
        actual = str(NumpyDocstring(docstring, config))
        self.assertEqual(expected, actual)

    def test_token_type(self):
        tokens = (
            ("1", "literal"),
            ("-4.6", "literal"),
            ("2j", "literal"),
            ("'string'", "literal"),
            ('"another_string"', "literal"),
            ("{1, 2}", "literal"),
            ("{'va{ue', 'set'}", "literal"),
            ("optional", "control"),
            ("default", "control"),
            (", ", "delimiter"),
            (" of ", "delimiter"),
            (" or ", "delimiter"),
            (": ", "delimiter"),
            ("True", "obj"),
            ("None", "obj"),
            ("name", "obj"),
            (":py:class:`Enum`", "reference"),
        )

        for token, expected in tokens:
            actual = _token_type(token)
            self.assertEqual(expected, actual)

    def test_tokenize_type_spec(self):
        specs = (
            "str",
            "defaultdict",
            "int, float, or complex",
            "int or float or None, optional",
            '{"F", "C", "N"}',
            "{'F', 'C', 'N'}, default: 'F'",
            "{'F', 'C', 'N or C'}, default 'F'",
            "str, default: 'F or C'",
            "int, default: None",
            "int, default None",
            "int, default :obj:`None`",
            '"ma{icious"',
            r"'with \'quotes\''",
        )

        tokens = (
            ["str"],
            ["defaultdict"],
            ["int", ", ", "float", ", or ", "complex"],
            ["int", " or ", "float", " or ", "None", ", ", "optional"],
            ["{", '"F"', ", ", '"C"', ", ", '"N"', "}"],
            ["{", "'F'", ", ", "'C'", ", ", "'N'", "}", ", ", "default", ": ", "'F'"],
            ["{", "'F'", ", ", "'C'", ", ", "'N or C'", "}", ", ", "default", " ", "'F'"],
            ["str", ", ", "default", ": ", "'F or C'"],
            ["int", ", ", "default", ": ", "None"],
            ["int", ", ", "default", " ", "None"],
            ["int", ", ", "default", " ", ":obj:`None`"],
            ['"ma{icious"'],
            [r"'with \'quotes\''"],
        )

        for spec, expected in zip(specs, tokens):
            actual = _tokenize_type_spec(spec)
            self.assertEqual(expected, actual)

    def test_recombine_set_tokens(self):
        tokens = (
            ["{", "1", ", ", "2", "}"],
            ["{", '"F"', ", ", '"C"', ", ", '"N"', "}", ", ", "optional"],
            ["{", "'F'", ", ", "'C'", ", ", "'N'", "}", ", ", "default", ": ", "None"],
            ["{", "'F'", ", ", "'C'", ", ", "'N'", "}", ", ", "default", " ", "None"],
        )

        combined_tokens = (
            ["{1, 2}"],
            ['{"F", "C", "N"}', ", ", "optional"],
            ["{'F', 'C', 'N'}", ", ", "default", ": ", "None"],
            ["{'F', 'C', 'N'}", ", ", "default", " ", "None"],
        )

        for tokens_, expected in zip(tokens, combined_tokens):
            actual = _recombine_set_tokens(tokens_)
            self.assertEqual(expected, actual)

    def test_recombine_set_tokens_invalid(self):
        tokens = (
            ["{", "1", ", ", "2"],
            ['"F"', ", ", '"C"', ", ", '"N"', "}", ", ", "optional"],
            ["{", "1", ", ", "2", ", ", "default", ": ", "None"],
        )
        combined_tokens = (
            ["{1, 2"],
            ['"F"', ", ", '"C"', ", ", '"N"', "}", ", ", "optional"],
            ["{1, 2", ", ", "default", ": ", "None"],
        )

        for tokens_, expected in zip(tokens, combined_tokens):
            actual = _recombine_set_tokens(tokens_)
            self.assertEqual(expected, actual)

    def test_convert_numpy_type_spec(self):
        translations = {
            "DataFrame": "pandas.DataFrame",
        }

        specs = (
            "",
            "optional",
            "str, optional",
            "int or float or None, default: None",
            "int, default None",
            '{"F", "C", "N"}',
            "{'F', 'C', 'N'}, default: 'N'",
            "{'F', 'C', 'N'}, default 'N'",
            "DataFrame, optional",
        )

        converted = (
            "",
            "*optional*",
            ":class:`str`, *optional*",
            ":class:`int` or :class:`float` or :obj:`None`, *default*: :obj:`None`",
            ":class:`int`, *default* :obj:`None`",
            '``{"F", "C", "N"}``',
            "``{'F', 'C', 'N'}``, *default*: ``'N'``",
            "``{'F', 'C', 'N'}``, *default* ``'N'``",
            ":class:`pandas.DataFrame`, *optional*",
        )

        for spec, expected in zip(specs, converted):
            actual = _convert_numpy_type_spec(spec, translations=translations)
            self.assertEqual(expected, actual)

    def test_parameter_types(self):
        docstring = dedent("""\
            Parameters
            ----------
            param1 : DataFrame
                the data to work on
            param2 : int or float or None, optional
                a parameter with different types
            param3 : dict-like, optional
                a optional mapping
            param4 : int or float or None, optional
                a optional parameter with different types
            param5 : {"F", "C", "N"}, optional
                a optional parameter with fixed values
            param6 : int, default None
                different default format
            param7 : mapping of hashable to str, optional
                a optional mapping
            param8 : ... or Ellipsis
                ellipsis
        """)
        expected = dedent("""\
            :param param1: the data to work on
            :type param1: :class:`DataFrame`
            :param param2: a parameter with different types
            :type param2: :class:`int` or :class:`float` or :obj:`None`, *optional*
            :param param3: a optional mapping
            :type param3: :term:`dict-like <mapping>`, *optional*
            :param param4: a optional parameter with different types
            :type param4: :class:`int` or :class:`float` or :obj:`None`, *optional*
            :param param5: a optional parameter with fixed values
            :type param5: ``{"F", "C", "N"}``, *optional*
            :param param6: different default format
            :type param6: :class:`int`, *default* :obj:`None`
            :param param7: a optional mapping
            :type param7: :term:`mapping` of :term:`hashable` to :class:`str`, *optional*
            :param param8: ellipsis
            :type param8: :obj:`... <Ellipsis>` or :obj:`Ellipsis`
        """)
        translations = {
            "dict-like": ":term:`dict-like <mapping>`",
            "mapping": ":term:`mapping`",
            "hashable": ":term:`hashable`",
        }
        config = Config(
            napoleon_use_param=True,
            napoleon_use_rtype=True,
            napoleon_preprocess_types=True,
            napoleon_type_aliases=translations,
        )
        actual = str(NumpyDocstring(docstring, config))
        self.assertEqual(expected, actual)


@contextmanager
def warns(warning, match):
    match_re = re.compile(match)
    try:
        yield warning
    finally:
        raw_warnings = warning.getvalue()
        warnings = [w for w in raw_warnings.split("\n") if w.strip()]

        assert len(warnings) == 1 and all(match_re.match(w) for w in warnings)
        warning.truncate(0)


class TestNumpyDocstring:
    def test_token_type_invalid(self, warning):
        tokens = (
            "{1, 2",
            "}",
            "'abc",
            "def'",
            '"ghi',
            'jkl"',
        )
        errors = (
            r".+: invalid value set \(missing closing brace\):",
            r".+: invalid value set \(missing opening brace\):",
            r".+: malformed string literal \(missing closing quote\):",
            r".+: malformed string literal \(missing opening quote\):",
            r".+: malformed string literal \(missing closing quote\):",
            r".+: malformed string literal \(missing opening quote\):",
        )
        for token, error in zip(tokens, errors):
            with warns(warning, match=error):
                _token_type(token)

    @pytest.mark.parametrize(
        ("name", "expected"),
        (
            ("x, y, z", "x, y, z"),
            ("*args, **kwargs", r"\*args, \*\*kwargs"),
            ("*x, **y", r"\*x, \*\*y"),
        ),
    )
    def test_escape_args_and_kwargs(self, name, expected):
        numpy_docstring = NumpyDocstring("")
        actual = numpy_docstring._escape_args_and_kwargs(name)

        assert actual == expected

    def test_pep526_annotations(self):
        if sys.version_info >= (3, 6):
            # test class attributes annotations
            config = Config(
                napoleon_attr_annotations=True
            )
            actual = str(NumpyDocstring(cleandoc(PEP526NumpyClass.__doc__), config, app=None, what="class",
                                        obj=PEP526NumpyClass))
            expected = """\
Sample class with PEP 526 annotations and numpy docstring

.. attribute:: attr1

   Attr1 description

   :type: int

.. attribute:: attr2

   Attr2 description

   :type: str
"""
            print(actual)
            assert expected == actual
