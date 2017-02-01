.. highlightlang:: python

.. _markdown:

Markdown support
================

`Markdown <https://daringfireball.net/projects/markdown/>`__ is a lightweight markup language with a simplistic plain
text formatting syntax.
It exists in many syntactically different *flavors*.
To support Markdown-based documentation, Sphinx can use
`recommonmark <http://recommonmark.readthedocs.io/en/latest/index.html>`__.
recommonmark is a Docutils bridge to `CommonMark-py <https://github.com/rtfd/CommonMark-py>`__, a
Python package for parsing the `CommonMark <http://commonmark.org/>`__ Markdown flavor.


Configuration
-------------

To configure your Sphinx project for Markdown support, proceed as follows:

#. Install recommonmark:

   ::

      pip install recommonmark

#. Add the Markdown parser to the ``source_parsers`` configuration variable in your Sphinx configuration file:

   ::

      source_parsers = {
         '.md': 'recommonmark.parser.CommonMarkParser',
      }

   You can replace `.md` with a filename extension of your choice.

#. Add the Markdown filename extension to the  ``source_suffix`` configuration variable:

   ::

      source_suffix = ['.rst', '.md']

#. You can further configure recommonmark to allow custom syntax that standard CommonMark doesn't support. Read more in
   the `recommonmark documentation <http://recommonmark.readthedocs.io/en/latest/auto_structify.html>`__.
