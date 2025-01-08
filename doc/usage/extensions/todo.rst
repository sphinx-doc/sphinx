:mod:`sphinx.ext.todo` -- Support for todo items
================================================

.. module:: sphinx.ext.todo
   :synopsis: Allow inserting todo items into documents.
.. moduleauthor:: Daniel Bültmann

.. versionadded:: 0.5

.. role:: code-py(code)
   :language: Python

There are two additional directives when using this extension:

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

   If this is ``True``, :rst:dir:`todo` and :rst:dir:`todolist` produce output,
   else they produce nothing.

.. confval:: todo_emit_warnings
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If this is ``True``, :rst:dir:`todo` emits a warning for each TODO entries.

   .. versionadded:: 1.5

.. confval:: todo_link_only
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If this is ``True``, :rst:dir:`todolist` produce output without file path and
   line.

   .. versionadded:: 1.4

autodoc provides the following an additional event:

.. event:: todo-defined (app, node)

   .. versionadded:: 1.5

   Emitted when a todo is defined. *node* is the defined
   ``sphinx.ext.todo.todo_node`` node.
