:mod:`sphinx.ext.todo` -- Support for todo items
================================================

.. module:: sphinx.ext.todo
   :synopsis: Allow inserting todo items into documents.
.. moduleauthor:: Daniel Bültmann

.. versionadded:: 0.5

.. role:: code-py(code)
   :language: Python

This extension provides two directives and an inline role:

.. rst:role:: todo

   Use this role for short todo items within a paragraph.  For example,
   ``:todo:`add a reference here``` displays the todo text inline.

   Inline todo items are included in :rst:dir:`todolist`, emit the
   :event:`todo-defined` event, and honor the same configuration values as the
   :rst:dir:`todo` directive.

   .. versionadded:: 9.1.1

.. rst:directive:: todo

   Use this directive like, for example, :rst:dir:`note`.

   It will only show up in the output if :confval:`todo_include_todos` is
   ``True``.

   .. versionadded:: 1.3.2
      This directive supports an ``class`` option that determines the class
      attribute for HTML output.  If not given, the class defaults to
      ``admonition-todo``.


.. rst:directive:: todolist

   This directive is replaced by a list of all todo directives in the whole
   documentation, if :confval:`todo_include_todos` is ``True``.


These can be configured as seen below.

Configuration
-------------

.. confval:: todo_include_todos
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If this is ``True``, :rst:role:`todo`, :rst:dir:`todo`, and
   :rst:dir:`todolist` produce output, else they produce nothing.

.. confval:: todo_emit_warnings
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If this is ``True``, :rst:role:`todo` and :rst:dir:`todo` emit a warning for
   each TODO entry.

   .. versionadded:: 1.5

.. confval:: todo_link_only
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If this is ``True``, :rst:dir:`todolist` produce output without file path and
   line.

   .. versionadded:: 1.4

The extension provides the following additional event:

.. event:: todo-defined (app, node)

   .. versionadded:: 1.5

   Emitted when a todo is defined. *node* is the defined
   ``sphinx.ext.todo.todo_node`` or ``sphinx.ext.todo.todo_inline_node`` node.
