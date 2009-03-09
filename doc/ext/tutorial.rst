.. _exttut:

Tutorial: Writing a simple extension
====================================

This section is intended as a walkthrough for the creation of custom extensions.
It covers the basics of writing and activating an extensions, as well as
commonly used features of extensions.

As an example, we will cover a "todo" extension that adds capabilities to
include todo entries in the documentation, and collecting these in a central
place.  (A similar "todo" extension is distributed with Sphinx.)


Build Phases
------------

One thing that is vital in order to understand extension mechanisms is the way
in which a Sphinx project is built: this works in several phases.

**Phase 0: Initialization**

   In this phase, almost nothing interesting for us happens.  The source
   directory is searched for source files, and extensions are initialized.
   Should a stored build environment exist, it is loaded, otherwise a new one is
   created.

**Phase 1: Reading**

   In Phase 1, all source files (and on subsequent builds, those that are new or
   changed) are read and parsed.  This is the phase where directives and roles
   are encountered by the docutils, and the corresponding functions are called.
   The output of this phase is a *doctree* for each source files, that is a tree
   of docutils nodes.  For document elements that aren't fully known until all
   existing files are read, temporary nodes are created.

   During reading, the build environment is updated with all meta- and cross
   reference data of the read documents, such as labels, the names of headings,
   described Python objects and index entries.  This will later be used to
   replace the temporary nodes.

   The parsed doctrees are stored on the disk, because it is not possible to
   hold all of them in memory.

**Phase 2: Consistency checks**

   Some checking is done to ensure no surprises in the built documents.

**Phase 3: Resolving**

   Now that the metadata and cross-reference data of all existing documents is
   known, all temporary nodes are replaced by nodes that can be converted into
   output.  For example, links are created for object references that exist, and
   simple literal nodes are created for those that don't.

**Phase 4: Writing**

   This phase converts the resolved doctrees to the desired output format, such
   as HTML or LaTeX.  This happens via a so-called docutils writer that visits
   the individual nodes of each doctree and produces some output in the process.

.. note::

   Some builders deviate from this general build plan, for example, the builder
   that checks external links does not need anything more than the parsed
   doctrees and therefore does not have phases 2--4.


Extension Design
----------------

We want the extension to add the following to Sphinx:

* A "todo" directive, containing some content that is marked with "TODO", and
  only shown in the output if a new config value is set.  (Todo entries should
  not be in the output by default.)

* A "todolist" directive that creates a list of all todo entries throughout the
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


The Setup Function
------------------

.. currentmodule:: sphinx.application

The new elements are added in the extension's setup function.  Let us create a
new Python module called :file:`todo.py` and add the setup function::

   def setup(app):
       app.add_config_value('todo_include_todos', False, False)

       app.add_node(todolist)
       app.add_node(todo,
                    html=(visit_todo_node, depart_todo_node),
                    latex=(visit_todo_node, depart_todo_node),
                    text=(visit_todo_node, depart_todo_node))

       app.add_directive('todo', TodoDirective)
       app.add_directive('todolist', TodolistDirective)
       app.connect('doctree-resolved', process_todo_nodes)
       app.connect('env-purge-doc', purge_todos)

The calls in this function refer to classes and functions not yet written.  What
the individual calls do is the following:

* :meth:`~Sphinx.add_config_value` lets Sphinx know that it should recognize the
  new *config value* ``todo_include_todos``, whose default value should be
  ``False`` (this also tells Sphinx that it is a boolean value).

  If the third argument was ``True``, all documents would be re-read if the
  config value changed its value.  This is needed for config values that
  influence reading (build phase 1).

* :meth:`~Sphinx.add_node` adds a new *node class* to the build system.  It also
  can specify visitor functions for each supported output format.  These visitor
  functions are needed when the new nodes stay until phase 4 -- since the
  ``todolist`` node is always replaced in phase 3, it doesn't need any.

  We need to create the two node classes ``todo`` and ``todolist`` later.

* :meth:`~Sphinx.add_directive` adds a new *directive*, given by name and class.

  The handler functions are created later.

* Finally, :meth:`~Sphinx.connect` adds an *event handler* to the event whose
  name is given by the first argument.  The event handler function is called
  with several arguments which are documented with the event.


The Node Classes
----------------

Let's start with the node classes::

   from docutils import nodes

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


The Directive Classes
---------------------

A directive class is a class deriving usually from
``docutils.parsers.rst.Directive``.  Since the class-based directive interface
doesn't exist yet in Docutils 0.4, Sphinx has another base class called
``sphinx.util.compat.Directive`` that you can derive your directive from, and it
will work with both Docutils 0.4 and 0.5 upwards.  The directive interface is
covered in detail in the docutils documentation; the important thing is that the
class has a method ``run`` that returns a list of nodes.

The ``todolist`` directive is quite simple::

   from sphinx.util.compat import Directive

   class TodolistDirective(Directive):

       def run(self):
           return [todolist('')]

An instance of our ``todolist`` node class is created and returned.  The
todolist directive has neither content nor arguments that need to be handled.

The ``todo`` directive function looks like this::

   from sphinx.util.compat import make_admonition

   class TodoDirective(Directive):

       # this enables content in the directive
       has_content = True

       def run(self):
           env = self.state.document.settings.env

           targetid = "todo-%s" % env.index_num
           env.index_num += 1
           targetnode = nodes.target('', '', ids=[targetid])

           ad = make_admonition(todo, self.name, [_('Todo')], self.options,
                                self.content, self.lineno, self.content_offset,
                                self.block_text, self.state, self.state_machine)

           if not hasattr(env, 'todo_all_todos'):
               env.todo_all_todos = []
           env.todo_all_todos.append({
               'docname': env.docname,
               'lineno': self.lineno,
               'todo': ad[0].deepcopy(),
               'target': targetnode,
           })

           return [targetnode] + ad

Several important things are covered here. First, as you can see, you can refer
to the build environment instance using ``self.state.document.settings.env``.

Then, to act as a link target (from the todolist), the todo directive needs to
return a target node in addition to the todo node.  The target ID (in HTML, this
will be the anchor name) is generated by using ``env.index_num`` which is
persistent between directive calls and therefore leads to unique target names.
The target node is instantiated without any text (the first two arguments).

An admonition is created using a standard docutils function (wrapped in Sphinx
for docutils cross-version compatibility).  The first argument gives the node
class, in our case ``todo``.  The third argument gives the admonition title (use
``arguments`` here to let the user specify the title).  A list of nodes is
returned from ``make_admonition``.

Then, the todo node is added to the environment.  This is needed to be able to
create a list of all todo entries throughout the documentation, in the place
where the author puts a ``todolist`` directive.  For this case, the environment
attribute ``todo_all_todos`` is used (again, the name should be unique, so it is
prefixed by the extension name).  It does not exist when a new environment is
created, so the directive must check and create it if necessary.  Various
information about the todo entry's location are stored along with a copy of the
node.

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


The Event Handlers
------------------

Finally, let's look at the event handlers.  First, the one for the
:event:`env-purge-doc` event::

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

The other handler belongs to the :event:`doctree-resolved` event.  This event is
emitted at the end of phase 3 and allows custom resolving to be done::

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

It is a bit more involved.  If our new "todo_include_todos" config value is
false, all todo and todolist nodes are removed from the documents.

If not, todo nodes just stay where and how they are.  Todolist nodes are
replaced by a list of todo entries, complete with backlinks to the location
where they come from.  The list items are composed of the nodes from the todo
entry and docutils nodes created on the fly: a paragraph for each entry,
containing text that gives the location, and a link (reference node containing
an italic node) with the backreference.  The reference URI is built by
``app.builder.get_relative_uri`` which creates a suitable URI depending on the
used builder, and appending the todo node's (the target's) ID as the anchor
name.

