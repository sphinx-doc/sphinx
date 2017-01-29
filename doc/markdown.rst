.. highlightlang:: python

.. _markdown:

Markdown support
================

`Markdown <https://daringfireball.net/projects/markdown/>`__ is a lightweight markup language with a simplistic plain
text formatting syntax.
It exists in many syntactically different *flavors*.
To support Markdown-based documentation, Sphinx can use `CommonMark-py <https://github.com/rtfd/CommonMark-py>`__, a
Python package for parsing the `CommonMark <http://commonmark.org/>`__ flavor. In addition, Sphinx uses
`recommonmark <http://recommonmark.readthedocs.io/en/latest/index.html>`__, a Docutils bridge to CommonMark.


Configuration
-------------

To configure your Sphinx project for markdown support, proceed as follows:

#. Install CommonMark version **0.5.4** and recommonmark:

   ::

      pip install commonmark==0.5.4 recommonmark

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
