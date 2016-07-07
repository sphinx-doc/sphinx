.. highlight:: rest

:mod:`sphinx.ext.inheritance_diagram` -- Include inheritance diagrams
=====================================================================

.. module:: sphinx.ext.inheritance_diagram
   :synopsis: Support for displaying inheritance diagrams via graphviz.

.. versionadded:: 0.6

This extension allows you to include inheritance diagrams, rendered via the
:mod:`Graphviz extension <sphinx.ext.graphviz>`.

It adds this directive:

.. rst:directive:: inheritance-diagram

   This directive has one or more arguments, each giving a module or class
   name.  Class names can be unqualified; in that case they are taken to exist
   in the currently described module (see :rst:dir:`py:module`).

   For each given class, and each class in each given module, the base classes
   are determined.  Then, from all classes and their base classes, a graph is
   generated which is then rendered via the graphviz extension to a directed
   graph.

   This directive supports an option called ``parts`` that, if given, must be an
   integer, advising the directive to remove that many parts of module names
   from the displayed names.  (For example, if all your class names start with
   ``lib.``, you can give ``:parts: 1`` to remove that prefix from the displayed
   node names.)

   It also supports a ``private-bases`` flag option; if given, private base
   classes (those whose name starts with ``_``) will be included.

   You can use ``caption`` option to give a caption to the diagram.

   .. versionchanged:: 1.1
      Added ``private-bases`` option; previously, all bases were always
      included.

   .. versionchanged:: 1.5
      Added ``caption`` option


New config values are:

.. confval:: inheritance_graph_attrs

   A dictionary of graphviz graph attributes for inheritance diagrams.

   For example::

      inheritance_graph_attrs = dict(rankdir="LR", size='"6.0, 8.0"',
                                     fontsize=14, ratio='compress')

.. confval:: inheritance_node_attrs

   A dictionary of graphviz node attributes for inheritance diagrams.

   For example::

      inheritance_node_attrs = dict(shape='ellipse', fontsize=14, height=0.75,
                                    color='dodgerblue1', style='filled')

.. confval:: inheritance_edge_attrs

   A dictionary of graphviz edge attributes for inheritance diagrams.
