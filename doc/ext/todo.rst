:mod:`sphinx.ext.todo` -- Support for todo items
================================================

.. module:: sphinx.ext.todo
   :synopsis: Allow inserting todo items into documents.
.. moduleauthor:: Daniel Bültmann

.. versionadded:: 0.5

There are two additional directives when using this extension:

.. rst:directive:: todo

   Use this directive like, for example, :rst:dir:`note`.

   It will only show up in the output if :confval:`todo_include_todos` is true.


.. rst:directive:: todolist

   This directive is replaced by a list of all todo directives in the whole
   documentation, if :confval:`todo_include_todos` is true.


There is also an additional config value:

.. confval:: todo_include_todos

   If this is ``True``, :rst:dir:`todo` and :rst:dir:`todolist` produce output, else
   they produce nothing.  The default is ``False``.
