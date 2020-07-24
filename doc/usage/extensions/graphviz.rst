.. highlight:: rest

:mod:`sphinx.ext.graphviz` -- Add Graphviz graphs
=================================================

.. module:: sphinx.ext.graphviz
   :synopsis: Support for Graphviz graphs.

.. versionadded:: 0.6

This extension allows you to embed `Graphviz <https://graphviz.org/>`_ graphs in
your documents.

It adds these directives:

.. rst:directive:: graphviz

   Directive to embed graphviz code.  The input code for ``dot`` is given as the
   content.  For example::

      .. graphviz::

         digraph foo {
            "bar" -> "baz";
         }

   In HTML output, the code will be rendered to a PNG or SVG image (see
   :confval:`graphviz_output_format`).  In LaTeX output, the code will be
   rendered to an embeddable PDF file.

   You can also embed external dot files, by giving the file name as an
   argument to :rst:dir:`graphviz` and no additional content::

      .. graphviz:: external.dot

   As for all file references in Sphinx, if the filename is absolute, it is
   taken as relative to the source directory.

   .. versionchanged:: 1.1
      Added support for external files.

   .. rubric:: options

   .. rst:directive:option:: alt: alternate text
      :type: text

      The alternate text of the graph.  By default, the graph code is used to
      the alternate text.

      .. versionadded:: 1.0

   .. rst:directive:option:: align: alignment of the graph
      :type: left, center or right

      The horizontal alignment of the graph.

      .. versionadded:: 1.5

   .. rst:directive:option:: caption: caption of the graph
      :type: text

      The caption of the graph.

      .. versionadded:: 1.1

   .. rst:directive:option:: layout: layout type of the graph
      :type: text

      The layout of the graph (ex. ``dot``, ``neato`` and so on).  A path to the
      graphviz commands are also allowed.  By default, :confval:`graphviz_dot`
      is used.

      .. versionadded:: 1.4
      .. versionchanged:: 2.2

         Renamed from ``graphviz_dot``

   .. rst:directive:option:: name: label
      :type: text

      The label of the graph.

      .. versionadded:: 1.6

   .. rst:directive:option:: class: class names
      :type: a list of class names separeted by spaces

      The class name of the graph.

      .. versionadded:: 2.4


.. rst:directive:: graph

   Directive for embedding a single undirected graph.  The name is given as a
   directive argument, the contents of the graph are the directive content.
   This is a convenience directive to generate ``graph <name> { <content> }``.

   For example::

      .. graph:: foo

         "bar" -- "baz";

   .. note:: The graph name is passed unchanged to Graphviz.  If it contains
      non-alphanumeric characters (e.g. a dash), you will have to double-quote
      it.

   .. rubric:: options

   Same as :rst:dir:`graphviz`.

   .. rst:directive:option:: alt: alternate text
      :type: text

      .. versionadded:: 1.0

   .. rst:directive:option:: align: alignment of the graph
      :type: left, center or right

      .. versionadded:: 1.5

   .. rst:directive:option:: caption: caption of the graph
      :type: text

      .. versionadded:: 1.1

   .. rst:directive:option:: layout: layout type of the graph
      :type: text

      .. versionadded:: 1.4
      .. versionchanged:: 2.2

         Renamed from ``graphviz_dot``

   .. rst:directive:option:: name: label
      :type: text

      .. versionadded:: 1.6

   .. rst:directive:option:: class: class names
      :type: a list of class names separeted by spaces

      The class name of the graph.

      .. versionadded:: 2.4


.. rst:directive:: digraph

   Directive for embedding a single directed graph.  The name is given as a
   directive argument, the contents of the graph are the directive content.
   This is a convenience directive to generate ``digraph <name> { <content> }``.

   For example::

      .. digraph:: foo

         "bar" -> "baz" -> "quux";

   .. rubric:: options

   Same as :rst:dir:`graphviz`.

   .. rst:directive:option:: alt: alternate text
      :type: text

      .. versionadded:: 1.0

   .. rst:directive:option:: align: alignment of the graph
      :type: left, center or right

      .. versionadded:: 1.5

   .. rst:directive:option:: caption: caption of the graph
      :type: text

      .. versionadded:: 1.1

   .. rst:directive:option:: layout: layout type of the graph
      :type: text

      .. versionadded:: 1.4
      .. versionchanged:: 2.2

         Renamed from ``graphviz_dot``

   .. rst:directive:option:: name: label
      :type: text

      .. versionadded:: 1.6

   .. rst:directive:option:: class: class names
      :type: a list of class names separeted by spaces

      The class name of the graph.

      .. versionadded:: 2.4


There are also these config values:

.. confval:: graphviz_dot

   The command name with which to invoke ``dot``.  The default is ``'dot'``; you
   may need to set this to a full path if ``dot`` is not in the executable
   search path.

   Since this setting is not portable from system to system, it is normally not
   useful to set it in ``conf.py``; rather, giving it on the
   :program:`sphinx-build` command line via the :option:`-D <sphinx-build -D>`
   option should be preferable, like this::

      sphinx-build -b html -D graphviz_dot=C:\graphviz\bin\dot.exe . _build/html

.. confval:: graphviz_dot_args

   Additional command-line arguments to give to dot, as a list.  The default is
   an empty list.  This is the right place to set global graph, node or edge
   attributes via dot's ``-G``, ``-N`` and ``-E`` options.

.. confval:: graphviz_output_format

   The output format for Graphviz when building HTML files.  This must be either
   ``'png'`` or ``'svg'``; the default is ``'png'``. If ``'svg'`` is used, in
   order to make the URL links work properly, an appropriate ``target``
   attribute must be set, such as ``"_top"`` and ``"_blank"``. For example, the
   link in the following graph should work in the svg output: ::

       .. graphviz::

            digraph example {
                a [label="sphinx", href="http://sphinx-doc.org", target="_top"];
                b [label="other"];
                a -> b;
            }

   .. versionadded:: 1.0
      Previously, output always was PNG.
