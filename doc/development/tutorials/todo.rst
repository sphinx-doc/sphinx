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

* A ``todolist`` directive that creates a list of all todo entries throughout the
  documentation.

For that, we will need to add the following elements to Sphinx:

* New directives, called ``todo`` and ``todolist``.

* New document tree nodes to represent these directives, conventionally also
  called ``todo`` and ``todolist``.  We wouldn't need new nodes if the new
  directives only produced some content representable by existing nodes.

* A new config value ``todo_include_todos`` (config value names should start
  with the extension name, in order to stay unique) that controls whether todo
  entries make it into the output.

* New event handlers: one for the :event:`doctree-resolved` event, to replace
  the todo and todolist nodes, and one for :event:`env-purge-doc` (the reason
  for that will be covered later).


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

.. code-block:: python

   from docutils import nodes
   from docutils.parsers.rst import Directive
   from sphinx.locale import _


   class todo(nodes.Admonition, nodes.Element):
       pass


   class todolist(nodes.General, nodes.Element):
       pass


   def visit_todo_node(self, node):
       self.visit_admonition(node)


   def depart_todo_node(self, node):
       self.depart_admonition(node)


   class TodolistDirective(Directive):

       def run(self):
           return [todolist('')]


   class TodoDirective(Directive):

       # this enables content in the directive
       has_content = True

       def run(self):
           env = self.state.document.settings.env

           targetid = 'todo-%d' % env.new_serialno('todo')
           targetnode = nodes.target('', '', ids=[targetid])

           todo_node = todo('\n'.join(self.content))
           todo_node += nodes.title(_('Todo'), _('Todo'))
           self.state.nested_parse(self.content, self.content_offset, todo_node)

           if not hasattr(env, 'todo_all_todos'):
               env.todo_all_todos = []

           env.todo_all_todos.append({
               'docname': env.docname,
               'lineno': self.lineno,
               'todo': todo_node.deepcopy(),
               'target': targetnode,
           })

           return [targetnode, todo_node]


   def purge_todos(app, env, docname):
       if not hasattr(env, 'todo_all_todos'):
           return
       env.todo_all_todos = [todo for todo in env.todo_all_todos
                             if todo['docname'] != docname]


   def process_todo_nodes(app, doctree, fromdocname):
       if not app.config.todo_include_todos:
           for node in doctree.traverse(todo):
               node.parent.remove(node)

       # Replace all todolist nodes with a list of the collected todos.
       # Augment each todo with a backlink to the original location.
       env = app.builder.env

       for node in doctree.traverse(todolist):
           if not app.config.todo_include_todos:
               node.replace_self([])
               continue

           content = []

           for todo_info in env.todo_all_todos:
               para = nodes.paragraph()
               filename = env.doc2path(todo_info['docname'], base=None)
               description = (
                   _('(The original entry is located in %s, line %d and can be found ') %
                   (filename, todo_info['lineno']))
               para += nodes.Text(description, description)

               # Create a reference
               newnode = nodes.reference('', '')
               innernode = nodes.emphasis(_('here'), _('here'))
               newnode['refdocname'] = todo_info['docname']
               newnode['refuri'] = app.builder.get_relative_uri(
                   fromdocname, todo_info['docname'])
               newnode['refuri'] += '#' + todo_info['target']['refid']
               newnode.append(innernode)
               para += newnode
               para += nodes.Text('.)', '.)')

               # Insert into the todolist
               content.append(todo_info['todo'])
               content.append(para)

           node.replace_self(content)


   def setup(app):
       app.add_config_value('todo_include_todos', False, 'html')

       app.add_node(todolist)
       app.add_node(todo,
                    html=(visit_todo_node, depart_todo_node),
                    latex=(visit_todo_node, depart_todo_node),
                    text=(visit_todo_node, depart_todo_node))

       app.add_directive('todo', TodoDirective)
       app.add_directive('todolist', TodolistDirective)
       app.connect('doctree-resolved', process_todo_nodes)
       app.connect('env-purge-doc', purge_todos)

       return {'version': '0.1'}   # identifies the version of our extension

This is far more extensive extension than the one detailed in :doc:`helloworld`,
however, we will will look at each piece step-by-step to explain what's
happening.

.. rubric:: The node classes

Let's start with the node classes:

.. todo:: Use literal-include

.. code-block:: python

   class todo(nodes.Admonition, nodes.Element):
       pass

   class todolist(nodes.General, nodes.Element):
       pass

   def visit_todo_node(self, node):
       self.visit_admonition(node)

   def depart_todo_node(self, node):
       self.depart_admonition(node)

Node classes usually don't have to do anything except inherit from the standard
docutils classes defined in :mod:`docutils.nodes`.  ``todo`` inherits from
``Admonition`` because it should be handled like a note or warning, ``todolist``
is just a "general" node.

.. note::

   Many extensions will not have to create their own node classes and work fine
   with the nodes already provided by `docutils
   <http://docutils.sourceforge.net/docs/ref/doctree.html>`__ and :ref:`Sphinx
   <nodes>`.

.. rubric:: The directive classes

A directive class is a class deriving usually from
:class:`docutils.parsers.rst.Directive`. The directive interface is also
covered in detail in the `docutils documentation`_; the important thing is that
the class should have attributes that configure the allowed markup, and a
``run`` method that returns a list of nodes.

Looking first at the ``TodolistDirective`` directive:

.. code-block:: python

   class TodolistDirective(Directive):

       def run(self):
           return [todolist('')]

It's very simple, creating and returning an instance of our ``todolist`` node
class.  The ``TodolistDirective`` directive itself has neither content nor
arguments that need to be handled. That brings us to the ``TodoDirective``
directive:

.. code-block:: python

   class TodoDirective(Directive):

       # this enables content in the directive
       has_content = True

       def run(self):
           env = self.state.document.settings.env

           targetid = "todo-%d" % env.new_serialno('todo')
           targetnode = nodes.target('', '', ids=[targetid])

           todo_node = todo('\n'.join(self.content))
           todo_node += nodes.title(_('Todo'), _('Todo'))
           self.state.nested_parse(self.content, self.content_offset, todo_node)

           if not hasattr(env, 'todo_all_todos'):
               env.todo_all_todos = []

           env.todo_all_todos.append({
               'docname': env.docname,
               'lineno': self.lineno,
               'todo': todo_node.deepcopy(),
               'target': targetnode,
           })

           return [targetnode, todo_node]

Several important things are covered here. First, as you can see, you can refer
to the :ref:`build environment instance <important-objects>` using
``self.state.document.settings.env``. Then, to act as a link target (from
``TodolistDirective``), the ``TodoDirective`` directive needs to return a target
node in addition to the ``todo`` node.  The target ID (in HTML, this will be the
anchor name) is generated by using ``env.new_serialno`` which returns a new
unique integer on each call and therefore leads to unique target names.  The
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

Event handlers are one of Sphinx's most powerful features, providing a way to do
hook into any part of the documentation process. There are many hooks available,
as detailed in :doc:`/extdev/appapi`, and we're going to use a subset of them
here.

Let's look at the event handlers used in the above example.  First, the one for
the :event:`env-purge-doc` event:

.. code-block:: python

   def purge_todos(app, env, docname):
       if not hasattr(env, 'todo_all_todos'):
           return
       env.todo_all_todos = [todo for todo in env.todo_all_todos
                             if todo['docname'] != docname]

Since we store information from source files in the environment, which is
persistent, it may become out of date when the source file changes.  Therefore,
before each source file is read, the environment's records of it are cleared,
and the :event:`env-purge-doc` event gives extensions a chance to do the same.
Here we clear out all todos whose docname matches the given one from the
``todo_all_todos`` list.  If there are todos left in the document, they will be
added again during parsing.

The other handler belongs to the :event:`doctree-resolved` event:

.. code-block:: python

   def process_todo_nodes(app, doctree, fromdocname):
       if not app.config.todo_include_todos:
           for node in doctree.traverse(todo):
               node.parent.remove(node)

       # Replace all todolist nodes with a list of the collected todos.
       # Augment each todo with a backlink to the original location.
       env = app.builder.env

       for node in doctree.traverse(todolist):
           if not app.config.todo_include_todos:
               node.replace_self([])
               continue

           content = []

           for todo_info in env.todo_all_todos:
               para = nodes.paragraph()
               filename = env.doc2path(todo_info['docname'], base=None)
               description = (
                   _('(The original entry is located in %s, line %d and can be found ') %
                   (filename, todo_info['lineno']))
               para += nodes.Text(description, description)

               # Create a reference
               newnode = nodes.reference('', '')
               innernode = nodes.emphasis(_('here'), _('here'))
               newnode['refdocname'] = todo_info['docname']
               newnode['refuri'] = app.builder.get_relative_uri(
                   fromdocname, todo_info['docname'])
               newnode['refuri'] += '#' + todo_info['target']['refid']
               newnode.append(innernode)
               para += newnode
               para += nodes.Text('.)', '.)')

               # Insert into the todolist
               content.append(todo_info['todo'])
               content.append(para)

           node.replace_self(content)

The :event:`doctree-resolved` event is emitted at the end of :ref:`phase 3
<build-phases>` and allows custom resolving to be done. The handler we have
written for this event is a bit more involved.  If the ``todo_include_todos``
config value (which we'll describe shortly) is false, all ``todo`` and
``todolist`` nodes are removed from the documents. If not, ``todo`` nodes just
stay where and how they are.  ``todolist`` nodes are replaced by a list of todo
entries, complete with backlinks to the location where they come from.  The list
items are composed of the nodes from the ``todo`` entry and docutils nodes
created on the fly: a paragraph for each entry, containing text that gives the
location, and a link (reference node containing an italic node) with the
backreference.  The reference URI is built by ``app.builder.get_relative_uri``
which creates a suitable URI depending on the used builder, and appending the
todo node's (the target's) ID as the anchor name.

.. rubric:: The ``setup`` function

.. currentmodule:: sphinx.application

As noted :doc:`previously <helloworld>`, the ``setup`` function is a requirement
and is used to plug directives into Sphinx. However, we also use it to hook up
the other parts of our extension. Let's look at our ``setup`` function:

.. code-block:: python

   def setup(app):
       app.add_config_value('todo_include_todos', False, 'html')

       app.add_node(todolist)
       app.add_node(todo,
                    html=(visit_todo_node, depart_todo_node),
                    latex=(visit_todo_node, depart_todo_node),
                    text=(visit_todo_node, depart_todo_node))

       app.add_directive('todo', TodoDirective)
       app.add_directive('todolist', TodolistDirective)
       app.connect('doctree-resolved', process_todo_nodes)
       app.connect('env-purge-doc', purge_todos)

       return {'version': '0.1'}   # identifies the version of our extension

The calls in this function refer to the classes and functions we added earlier.
What the individual calls do is the following:

* :meth:`~Sphinx.add_config_value` lets Sphinx know that it should recognize the
  new *config value* ``todo_include_todos``, whose default value should be
  ``False`` (this also tells Sphinx that it is a boolean value).

  If the third argument was ``'html'``, HTML documents would be full rebuild if the
  config value changed its value.  This is needed for config values that
  influence reading (build :ref:`phase 1 <build-phases>`).

* :meth:`~Sphinx.add_node` adds a new *node class* to the build system.  It also
  can specify visitor functions for each supported output format.  These visitor
  functions are needed when the new nodes stay until :ref:`phase 4 <build-phases>`
  -- since the ``todolist`` node is always replaced in :ref:`phase 3 <build-phases>`,
  it doesn't need any.

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

   extensions = ['helloworld']

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
