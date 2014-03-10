# -*- coding: utf-8 -*-
"""
    test_napoleon_docstring
    ~~~~~~~~~~~~~~~~~~~~~~~

    Tests for :mod:`sphinx.ext.napoleon.docstring` module.


    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import textwrap
from sphinx.ext.napoleon import Config
from sphinx.ext.napoleon.docstring import GoogleDocstring, NumpyDocstring
from unittest import TestCase

try:
    # Python >=3.3
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


class BaseDocstringTest(TestCase):
    pass


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

        :Parameters: **arg1** (*str*) --
                     Extended
                     description of arg1"""
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

        :Parameters: * **arg1** (*str*) --
                       Extended
                       description of arg1
                     * **arg2** (*int*) --
                       Extended
                       description of arg2

        :Keyword Arguments: * **kwarg1** (*str*) --
                              Extended
                              description of kwarg1
                            * **kwarg2** (*int*) --
                              Extended
                              description of kwarg2"""
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

        :Parameters: * **arg1** (*str*) --
                       Extended
                       description of arg1
                     * **arg2** (*int*) --
                       Extended
                       description of arg2

        :Keyword Arguments: * **kwarg1** (*str*) --
                              Extended
                              description of kwarg1
                            * **kwarg2** (*int*) --
                              Extended
                              description of kwarg2"""
    ), (
        """
        Single line summary

        Return:
          str:Extended
          description of return value
        """,
        """
        Single line summary

        :returns: *str* --
                  Extended
                  description of return value"""
    ), (
        """
        Single line summary

        Returns:
          str:Extended
          description of return value
        """,
        """
        Single line summary

        :returns: *str* --
                  Extended
                  description of return value"""
    )]

    def test_docstrings(self):
        config = Config(napoleon_use_param=False, napoleon_use_rtype=False)
        for docstring, expected in self.docstrings:
            actual = str(GoogleDocstring(textwrap.dedent(docstring), config))
            expected = textwrap.dedent(expected)
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

        :Parameters: **arg1** (*str*) --
                     Extended
                     description of arg1"""
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

        :Parameters: * **arg1** (*str*) --
                       Extended
                       description of arg1
                     * **arg2** (*int*) --
                       Extended
                       description of arg2

        :Keyword Arguments: * **kwarg1** (*str*) --
                              Extended
                              description of kwarg1
                            * **kwarg2** (*int*) --
                              Extended
                              description of kwarg2"""
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

        :returns: *str* --
                  Extended
                  description of return value"""
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

        :returns: *str* --
                  Extended
                  description of return value"""
    )]

    def test_docstrings(self):
        config = Config(napoleon_use_param=False, napoleon_use_rtype=False)
        for docstring, expected in self.docstrings:
            actual = str(NumpyDocstring(textwrap.dedent(docstring), config))
            expected = textwrap.dedent(expected)
            self.assertEqual(expected, actual)

    def test_parameters_with_class_reference(self):
        docstring = """
            Parameters
            ----------
            param1 : :class:`MyClass <name.space.MyClass>` instance

            """

        config = Config(napoleon_use_param=False)
        actual = str(NumpyDocstring(textwrap.dedent(docstring), config))
        expected = textwrap.dedent("""
            :Parameters: **param1** (:class:`MyClass <name.space.MyClass>` instance)
            """)
        self.assertEqual(expected, actual)

        config = Config(napoleon_use_param=True)
        actual = str(NumpyDocstring(textwrap.dedent(docstring), config))
        expected = textwrap.dedent("""

            :type param1: :class:`MyClass <name.space.MyClass>` instance
            """)
        self.assertEqual(expected, actual)

    def test_parameters_without_class_reference(self):
        docstring = """
            Parameters
            ----------
            param1 : MyClass instance

            """

        config = Config(napoleon_use_param=False)
        actual = str(NumpyDocstring(textwrap.dedent(docstring), config))
        expected = textwrap.dedent("""
            :Parameters: **param1** (*MyClass instance*)
            """)
        self.assertEqual(expected, actual)

        config = Config(napoleon_use_param=True)
        actual = str(NumpyDocstring(textwrap.dedent(docstring), config))
        expected = textwrap.dedent("""

            :type param1: MyClass instance
            """)
        self.assertEqual(expected, actual)

    def test_see_also_refs(self):
        docstring = """
            numpy.multivariate_normal(mean, cov, shape=None, spam=None)

            See Also
            --------
            some, other, funcs
            otherfunc : relationship

            """

        actual = str(NumpyDocstring(textwrap.dedent(docstring)))

        expected = """
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

.. seealso::
\n   :obj:`some`, :obj:`other`, :obj:`funcs`
   \n   :obj:`otherfunc`
       relationship
"""
        self.assertEqual(expected, actual)

        docstring = """
            numpy.multivariate_normal(mean, cov, shape=None, spam=None)

            See Also
            --------
            some, other, funcs
            otherfunc : relationship

            """

        config = Config()
        app = Mock()
        actual = str(NumpyDocstring(textwrap.dedent(docstring), config, app, "method"))

        expected = """
numpy.multivariate_normal(mean, cov, shape=None, spam=None)

.. seealso::
\n   :meth:`some`, :meth:`other`, :meth:`funcs`
   \n   :meth:`otherfunc`
       relationship
"""
        self.assertEqual(expected, actual)
