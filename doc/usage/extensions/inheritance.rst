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
   integer, advising the directive to keep that many dot-separated parts
   in the displayed names (from right to left). For example, ``parts=1`` will
   only display class names, without the names of the modules that contain
   them.

   .. versionchanged:: 2.0
      The value of for ``parts`` can also be negative, indicating how many
      parts to drop from the left.  For example, if all your class names start
      with ``lib.``, you can give ``:parts: -1`` to remove that prefix from the
      displayed node names.

   The directive also supports a ``private-bases`` flag option; if given,
   private base classes (those whose name starts with ``_``) will be included.

   You can use ``caption`` option to give a caption to the diagram.

   .. versionchanged:: 1.1
      Added ``private-bases`` option; previously, all bases were always
      included.

   .. versionchanged:: 1.5
      Added ``caption`` option

   It also supports a ``top-classes`` option which requires one or more class
   names separated by comma. If specified inheritance traversal will stop at the
   specified class names. Given the following Python module::

        """
               A
              / \
             B   C
            / \ / \
           E   D   F
        """

        class A:
            pass

        class B(A):
            pass

        class C(A):
            pass

        class D(B, C):
            pass

        class E(B):
            pass

        class F(C):
            pass

   If you have specified a module in the inheritance diagram like this::

        .. inheritance-diagram:: dummy.test
           :top-classes: dummy.test.B, dummy.test.C

   any base classes which are ancestors to ``top-classes`` and are also defined
   in the same module will be rendered as stand alone nodes. In this example
   class A will be rendered as stand alone node in the graph. This is a known
   issue due to how this extension works internally.

   If you don't want class A (or any other ancestors) to be visible then specify
   only the classes you would like to generate the diagram for like this::

        .. inheritance-diagram:: dummy.test.D dummy.test.E dummy.test.F
           :top-classes: dummy.test.B, dummy.test.C

   .. versionchanged:: 1.7
      Added ``top-classes`` option to limit the scope of inheritance graphs.


Examples
--------

The following are different inheritance diagrams for the internal
``InheritanceDiagram`` class that implements the directive.

With full names::

   .. inheritance-diagram:: sphinx.ext.inheritance_diagram.InheritanceDiagram

.. inheritance-diagram:: sphinx.ext.inheritance_diagram.InheritanceDiagram


Showing class names only::

   .. inheritance-diagram:: sphinx.ext.inheritance_diagram.InheritanceDiagram
      :parts: 1

.. inheritance-diagram:: sphinx.ext.inheritance_diagram.InheritanceDiagram
   :parts: 1

Stopping the diagram at :class:`sphinx.util.docutils.SphinxDirective` (the
highest superclass still part of Sphinx), and dropping the common left-most
part (``sphinx``) from all names::

   .. inheritance-diagram:: sphinx.ext.inheritance_diagram.InheritanceDiagram
      :top-classes: sphinx.util.docutils.SphinxDirective
      :parts: -1

.. inheritance-diagram:: sphinx.ext.inheritance_diagram.InheritanceDiagram
   :top-classes: sphinx.util.docutils.SphinxDirective
   :parts: -1



Configuration
-------------

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

.. confval:: inheritance_alias

   Allows mapping the full qualified name of the class to custom values
   (useful when exposing the underlying path of a class is not desirable,
   e.g. it's a private class and should not be instantiated by the user).

   For example::

      inheritance_alias = {'_pytest.Magic': 'pytest.Magic'}
