Developing a "TODO" extension
=============================

The objective of this tutorial is to create a more comprehensive extension than
that created in :doc:`helloworld`. Whereas that guide just covered writing a
custom :term:`directive`, this guide adds multiple directives, along with custom
nodes, additional config values and custom event handlers. To this end, we will
cover a ``todo`` extension that adds capabilities to include todo entries in the
documentation, and to collect these in a central place. This is similar the
``sphinxext.todo`` extension distributed with Sphinx.


Overview
--------

.. note::
   To understand the design of this extension, refer to
   :ref:`important-objects` and :ref:`build-phases`.

We want the extension to add the following to Sphinx:

* A ``todo`` directive, containing some content that is marked with "TODO" and
  only shown in the output if a new config value is set. Todo entries should not
  be in the output by default.

* A ``todolist`` directive that creates a list of all todo entries throughout
  the documentation.

For that, we will need to add the following elements to Sphinx:

* New directives, called ``todo`` and ``todolist``.

* New document tree nodes to represent these directives, conventionally also
  called ``todo`` and ``todolist``.  We wouldn't need new nodes if the new
  directives only produced some content representable by existing nodes.

* A new config value ``todo_include_todos`` (config value names should start
  with the extension name, in order to stay unique) that controls whether todo
  entries make it into the output.

* New event handlers: one for the :event:`doctree-resolved` event, to
  replace the todo and todolist nodes, one for :event:`env-merge-info`
  to merge intermediate results from parallel builds, and one for
  :event:`env-purge-doc` (the reason for that will be covered later).


Prerequisites
-------------

As with :doc:`helloworld`, we will not be distributing this plugin via PyPI so
once again we need a Sphinx project to call this from. You can use an existing
project or create a new one using :program:`sphinx-quickstart`.

We assume you are using separate source (:file:`source`) and build
(:file:`build`) folders. Your extension file could be in any folder of your
project. In our case, let's do the following:

#. Create an :file:`_ext` folder in :file:`source`
#. Create a new Python file in the :file:`_ext` folder called :file:`todo.py`

Here is an example of the folder structure you might obtain:

.. code-block:: text

      └── source
          ├── _ext
          │   └── todo.py
          ├── _static
          ├── conf.py
          ├── somefolder
          ├── index.rst
          ├── somefile.rst
          └── someotherfile.rst


Writing the extension
---------------------

Open :file:`todo.py` and paste the following code in it, all of which we will
explain in detail shortly:

.. literalinclude:: examples/todo.py
   :language: python
   :linenos:

This is far more extensive extension than the one detailed in :doc:`helloworld`,
however, we will will look at each piece step-by-step to explain what's
happening.

.. rubric:: The node classes

Let's start with the node classes:

.. literalinclude:: examples/todo.py
   :language: python
   :linenos:
   :lines: 8-21

Node classes usually don't have to do anything except inherit from the standard
docutils classes defined in :mod:`docutils.nodes`.  ``todo`` inherits from
``Admonition`` because it should be handled like a note or warning, ``todolist``
is just a "general" node.

.. note::

   Many extensions will not have to create their own node classes and work fine
   with the nodes already provided by `docutils
   <http://docutils.sourceforge.net/docs/ref/doctree.html>`__ and :ref:`Sphinx
   <nodes>`.

.. attention::

   It is important to know that while you can extend Sphinx without
   leaving your ``conf.py``, if you declare an inherited node right
   there, you'll hit an unobvious :py:class:`PickleError`. So if
   something goes wrong, please make sure that you put inherited nodes
   into a separate Python module.

   For more details, see:

   - https://github.com/sphinx-doc/sphinx/issues/6751
   - https://github.com/sphinx-doc/sphinx/issues/1493
   - https://github.com/sphinx-doc/sphinx/issues/1424

.. rubric:: The directive classes

A directive class is a class deriving usually from
:class:`docutils.parsers.rst.Directive`. The directive interface is also
covered in detail in the `docutils documentation`_; the important thing is that
the class should have attributes that configure the allowed markup, and a
``run`` method that returns a list of nodes.

Looking first at the ``TodolistDirective`` directive:

.. literalinclude:: examples/todo.py
   :language: python
   :linenos:
   :lines: 24-27

It's very simple, creating and returning an instance of our ``todolist`` node
class.  The ``TodolistDirective`` directive itself has neither content nor
arguments that need to be handled. That brings us to the ``TodoDirective``
directive:

.. literalinclude:: examples/todo.py
   :language: python
   :linenos:
   :lines: 30-53

Several important things are covered here. First, as you can see, we're now
subclassing the :class:`~sphinx.util.docutils.SphinxDirective` helper class
instead of the usual :class:`~docutils.parsers.rst.Directive` class. This
gives us access to the :ref:`build environment instance <important-objects>`
using the ``self.env`` property. Without this, we'd have to use the rather
convoluted ``self.state.document.settings.env``. Then, to act as a link target
(from ``TodolistDirective``), the ``TodoDirective`` directive needs to return a
target node in addition to the ``todo`` node.  The target ID (in HTML, this will
be the anchor name) is generated by using ``env.new_serialno`` which returns a
new unique integer on each call and therefore leads to unique target names. The
target node is instantiated without any text (the first two arguments).

On creating admonition node, the content body of the directive are parsed using
``self.state.nested_parse``.  The first argument gives the content body, and
the second one gives content offset.  The third argument gives the parent node
of parsed result, in our case the ``todo`` node. Following this, the ``todo``
node is added to the environment.  This is needed to be able to create a list of
all todo entries throughout the documentation, in the place where the author
puts a ``todolist`` directive.  For this case, the environment attribute
``todo_all_todos`` is used (again, the name should be unique, so it is prefixed
by the extension name).  It does not exist when a new environment is created, so
the directive must check and create it if necessary.  Various information about
the todo entry's location are stored along with a copy of the node.

In the last line, the nodes that should be put into the doctree are returned:
the target node and the admonition node.

The node structure that the directive returns looks like this::

   +--------------------+
   | target node        |
   +--------------------+
   +--------------------+
   | todo node          |
   +--------------------+
     \__+--------------------+
        | admonition title   |
        +--------------------+
        | paragraph          |
        +--------------------+
        | ...                |
        +--------------------+

.. rubric:: The event handlers

Event handlers are one of Sphinx's most powerful features, providing a way to
do hook into any part of the documentation process. There are many events
provided by Sphinx itself, as detailed in :ref:`the API guide <events>`, and
we're going to use a subset of them here.

Let's look at the event handlers used in the above example.  First, the one for
the :event:`env-purge-doc` event:

.. literalinclude:: examples/todo.py
   :language: python
   :linenos:
   :lines: 56-61

Since we store information from source files in the environment, which is
persistent, it may become out of date when the source file changes.  Therefore,
before each source file is read, the environment's records of it are cleared,
and the :event:`env-purge-doc` event gives extensions a chance to do the same.
Here we clear out all todos whose docname matches the given one from the
``todo_all_todos`` list.  If there are todos left in the document, they will be
added again during parsing.

The next handler, for the :event:`env-merge-info` event, is used
during parallel builds. As during parallel builds all threads have
their own ``env``, there's multiple ``todo_all_todos`` lists that need
to be merged:

.. literalinclude:: examples/todo.py
   :language: python
   :linenos:
   :lines: 64-68


The other handler belongs to the :event:`doctree-resolved` event:

.. literalinclude:: examples/todo.py
   :language: python
   :linenos:
   :lines: 71-113

The :event:`doctree-resolved` event is emitted at the end of :ref:`phase 3
(resolving) <build-phases>` and allows custom resolving to be done. The handler
we have written for this event is a bit more involved. If the
``todo_include_todos`` config value (which we'll describe shortly) is false,
all ``todo`` and ``todolist`` nodes are removed from the documents. If not,
``todo`` nodes just stay where and how they are.  ``todolist`` nodes are
replaced by a list of todo entries, complete with backlinks to the location
where they come from.  The list items are composed of the nodes from the
``todo`` entry and docutils nodes created on the fly: a paragraph for each
entry, containing text that gives the location, and a link (reference node
containing an italic node) with the backreference. The reference URI is built
by :meth:`sphinx.builders.Builder.get_relative_uri` which creates a suitable
URI depending on the used builder, and appending the todo node's (the target's)
ID as the anchor name.

.. rubric:: The ``setup`` function

.. currentmodule:: sphinx.application

As noted :doc:`previously <helloworld>`, the ``setup`` function is a requirement
and is used to plug directives into Sphinx. However, we also use it to hook up
the other parts of our extension. Let's look at our ``setup`` function:

.. literalinclude:: examples/todo.py
   :language: python
   :linenos:
   :lines: 116-

The calls in this function refer to the classes and functions we added earlier.
What the individual calls do is the following:

* :meth:`~Sphinx.add_config_value` lets Sphinx know that it should recognize the
  new *config value* ``todo_include_todos``, whose default value should be
  ``False`` (this also tells Sphinx that it is a boolean value).

  If the third argument was ``'html'``, HTML documents would be full rebuild if the
  config value changed its value.  This is needed for config values that
  influence reading (build :ref:`phase 1 (reading) <build-phases>`).

* :meth:`~Sphinx.add_node` adds a new *node class* to the build system.  It also
  can specify visitor functions for each supported output format.  These visitor
  functions are needed when the new nodes stay until :ref:`phase 4 (writing)
  <build-phases>`. Since the ``todolist`` node is always replaced in
  :ref:`phase 3 (resolving) <build-phases>`, it doesn't need any.

* :meth:`~Sphinx.add_directive` adds a new *directive*, given by name and class.

* Finally, :meth:`~Sphinx.connect` adds an *event handler* to the event whose
  name is given by the first argument.  The event handler function is called
  with several arguments which are documented with the event.

With this, our extension is complete.


Using the extension
-------------------

As before, we need to enable the extension by declaring it in our
:file:`conf.py` file. There are two steps necessary here:

#. Add the :file:`_ext` directory to the `Python path`_ using
   ``sys.path.append``. This should be placed at the top of the file.

#. Update or create the :confval:`extensions` list and add the extension file
   name to the list

In addition, we may wish to set the ``todo_include_todos`` config value. As
noted above, this defaults to ``False`` but we can set it explicitly.

For example:

.. code-block:: python

   import os
   import sys

   sys.path.append(os.path.abspath("./_ext"))

   extensions = ['todo']

   todo_include_todos = False

You can now use the extension throughout your project. For example:

.. code-block:: rst
   :caption: index.rst

   Hello, world
   ============

   .. toctree::
      somefile.rst
      someotherfile.rst

   Hello world. Below is the list of TODOs.

   .. todolist::

.. code-block:: rst
   :caption: somefile.rst

   foo
   ===

   Some intro text here...

   .. todo:: Fix this

.. code-block:: rst
   :caption: someotherfile.rst

   bar
   ===

   Some more text here...

   .. todo:: Fix that

Because we have configured ``todo_include_todos`` to ``False``, we won't
actually see anything rendered for the ``todo`` and ``todolist`` directives.
However, if we toggle this to true, we will see the output described
previously.


Further reading
---------------

For more information, refer to the `docutils`_ documentation and
:doc:`/extdev/index`.


.. _docutils: http://docutils.sourceforge.net/docs/
.. _Python path: https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH
.. _docutils documentation: http://docutils.sourceforge.net/docs/ref/rst/directives.html
