.. highlight:: rest

:mod:`sphinx.ext.graphviz` -- Add Graphviz graphs
=================================================

.. module:: sphinx.ext.graphviz
   :synopsis: Support for Graphviz graphs.

.. versionadded:: 0.6

This extension allows you to embed `Graphviz <http://graphviz.org/>`_ graphs in
your documents.

It adds these directives:


.. directive:: graphviz

   Directive to embed graphviz code.  The input code for ``dot`` is given as the
   content.  For example::

      .. graphviz::

         digraph foo {
            "bar" -> "baz";
         }

   In HTML output, the code will be rendered to a PNG image.  In LaTeX output,
   the code will be rendered to an embeddable PDF file.


.. directive:: graph

   Directive for embedding a single undirected graph.  The name is given as a
   directive argument, the contents of the graph are the directive content.
   This is a convenience directive to generate ``graph <name> { <content> }``.

   For example::

      .. graph:: foo

         "bar" -- "baz";


.. directive:: digraph

   Directive for embedding a single directed graph.  The name is given as a
   directive argument, the contents of the graph are the directive content.
   This is a convenience directive to generate ``digraph <name> { <content> }``.

   For example::

      .. digraph:: foo

         "bar" -> "baz" -> "quux";


There are also these new config values:

.. confval:: graphviz_dot

   The command name with which to invoke ``dot``.  The default is ``'dot'``; you
   may need to set this to a full path if ``dot`` is not in the executable
   search path.

   Since this setting is not portable from system to system, it is normally not
   useful to set it in ``conf.py``; rather, giving it on the
   :program:`sphinx-build` command line via the :option:`-D` option should be
   preferable, like this::

      sphinx-build -b html -D graphviz_dot=C:\graphviz\bin\dot.exe . _build/html

.. confval:: graphviz_dot_args

   Additional command-line arguments to give to dot, as a list.  The default is
   an empty list.  This is the right place to set global graph, node or edge
   attributes via dot's ``-G``, ``-N`` and ``-E`` options.
