.. highlight:: python

.. _markdown:

========
Markdown
========

`Markdown`__ is a lightweight markup language with a simplistic plain text
formatting syntax.  It exists in many syntactically different *flavors*.  To
support Markdown-based documentation, Sphinx can use `recommonmark`__.
recommonmark is a Docutils bridge to `CommonMark-py`__, a Python package for
parsing the `CommonMark`__ Markdown flavor.

__ https://daringfireball.net/projects/markdown/
__ https://recommonmark.readthedocs.io/en/latest/index.html
__ https://github.com/rtfd/CommonMark-py
__ https://commonmark.org/

Configuration
-------------

To configure your Sphinx project for Markdown support, proceed as follows:

#. Install the Markdown parser *recommonmark*::

      pip install --upgrade recommonmark

   .. note::

      The configuration as explained here requires recommonmark version
      0.5.0 or later.

#. Add *recommonmark* to the
   :confval:`list of configured extensions <extensions>`::

      extensions = ['recommonmark']

   .. versionchanged:: 1.8
      Version 1.8 deprecates and version 3.0 removes the ``source_parsers``
      configuration variable that was used by older *recommonmark* versions.

#. If you want to use Markdown files with extensions other than ``.md``, adjust
   the :confval:`source_suffix` variable.  The following example configures
   Sphinx to parse all files with the extensions ``.md`` and ``.txt`` as
   Markdown::

      source_suffix = {
          '.rst': 'restructuredtext',
          '.txt': 'markdown',
          '.md': 'markdown',
      }

#. You can further configure *recommonmark* to allow custom syntax that
   standard *CommonMark* doesn't support.  Read more in the `recommonmark
   documentation`__.

__ https://recommonmark.readthedocs.io/en/latest/auto_structify.html
