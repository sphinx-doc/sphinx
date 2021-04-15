.. highlight:: python

.. _markdown:

========
Markdown
========

`Markdown`__ is a lightweight markup language with a simplistic plain text
formatting syntax.  It exists in many syntactically different *flavors*.  To
support Markdown-based documentation, Sphinx can use `MyST-Parser`__.
MyST-Parser is a Docutils bridge to `markdown-it-py`__, a Python package for
parsing the `CommonMark`__ Markdown flavor.

__ https://daringfireball.net/projects/markdown/
__ https://myst-parser.readthedocs.io/en/latest/
__ https://github.com/executablebooks/markdown-it-py
__ https://commonmark.org/

Configuration
-------------

To configure your Sphinx project for Markdown support, proceed as follows:

#. Install the Markdown parser *MyST-Parser*::

      pip install --upgrade myst-parser

#. Add *myst_parser* to the
   :confval:`list of configured extensions <extensions>`::

      extensions = ['myst_parser']

   .. note::
      MyST-Parser requires Sphinx 2.1 or newer.

#. If you want to use Markdown files with extensions other than ``.md``, adjust
   the :confval:`source_suffix` variable.  The following example configures
   Sphinx to parse all files with the extensions ``.md`` and ``.txt`` as
   Markdown::

      source_suffix = {
          '.rst': 'restructuredtext',
          '.txt': 'markdown',
          '.md': 'markdown',
      }

#. You can further configure *MyST-Parser* to allow custom syntax that
   standard *CommonMark* doesn't support.  Read more in the `MyST-Parser
   documentation`__.

__ https://myst-parser.readthedocs.io/en/latest/using/syntax-optional.html
