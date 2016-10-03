.. highlight:: rest

.. _code-examples:

Showing code examples
---------------------

.. index:: pair: code; examples
           single: sourcecode

Examples of Python source code or interactive sessions are represented using
standard reST literal blocks.  They are started by a ``::`` at the end of the
preceding paragraph and delimited by indentation.

Representing an interactive session requires including the prompts and output
along with the Python code.  No special markup is required for interactive
sessions.  After the last line of input or output presented, there should not be
an "unused" primary prompt; this is an example of what *not* to do::

   >>> 1 + 1
   2
   >>>

Syntax highlighting is done with `Pygments <http://pygments.org>`_ and handled
in a smart way:

* There is a "highlighting language" for each source file.  Per default, this is
  ``'python'`` as the majority of files will have to highlight Python snippets,
  but the doc-wide default can be set with the :confval:`highlight_language`
  config value.

* Within Python highlighting mode, interactive sessions are recognized
  automatically and highlighted appropriately.  Normal Python code is only
  highlighted if it is parseable (so you can use Python as the default, but
  interspersed snippets of shell commands or other code blocks will not be
  highlighted as Python).

* The highlighting language can be changed using the ``highlight`` directive,
  used as follows:

  .. rst:directive:: .. highlight:: language

     Example::

        .. highlight:: c

     This language is used until the next ``highlight`` directive is encountered.

* For documents that have to show snippets in different languages, there's also
  a :rst:dir:`code-block` directive that is given the highlighting language
  directly:

  .. rst:directive:: .. code-block:: language

     Use it like this::

        .. code-block:: ruby

           Some Ruby code.

     The directive's alias name :rst:dir:`sourcecode` works as well.

* The valid values for the highlighting language are:

  * ``none`` (no highlighting)
  * ``python`` (the default when :confval:`highlight_language` isn't set)
  * ``guess`` (let Pygments guess the lexer based on contents, only works with
    certain well-recognizable languages)
  * ``rest``
  * ``c``
  * ... and any other `lexer alias that Pygments supports
    <http://pygments.org/docs/lexers/>`_.

* If highlighting with the selected language fails (i.e. Pygments emits an
  "Error" token), the block is not highlighted in any way.

Line numbers
^^^^^^^^^^^^

Pygments can generate line numbers for code blocks.  For
automatically-highlighted blocks (those started by ``::``), line numbers must be
switched on in a :rst:dir:`highlight` directive, with the ``linenothreshold``
option::

   .. highlight:: python
      :linenothreshold: 5

This will produce line numbers for all code blocks longer than five lines.

For :rst:dir:`code-block` blocks, a ``linenos`` flag option can be given to
switch on line numbers for the individual block::

   .. code-block:: ruby
      :linenos:

      Some more Ruby code.

The first line number can be selected with the ``lineno-start`` option.  If
present, ``linenos`` is automatically activated as well.

   .. code-block:: ruby
      :lineno-start: 10

      Some more Ruby code, with line numbering starting at 10.

Additionally, an ``emphasize-lines`` option can be given to have Pygments
emphasize particular lines::

    .. code-block:: python
       :emphasize-lines: 3,5

       def some_function():
           interesting = False
           print 'This line is highlighted.'
           print 'This one is not...'
           print '...but this one is.'

.. versionchanged:: 1.1
   ``emphasize-lines`` has been added.

.. versionchanged:: 1.3
   ``lineno-start`` has been added.


Includes
^^^^^^^^

.. rst:directive:: .. literalinclude:: filename

   Longer displays of verbatim text may be included by storing the example text
   in an external file containing only plain text.  The file may be included
   using the ``literalinclude`` directive. [1]_ For example, to include the
   Python source file :file:`example.py`, use::

      .. literalinclude:: example.py

   The file name is usually relative to the current file's path.  However, if it
   is absolute (starting with ``/``), it is relative to the top source
   directory.

   Tabs in the input are expanded if you give a ``tab-width`` option with the
   desired tab width.

   Like :rst:dir:`code-block`, the directive supports the ``linenos`` flag
   option to switch on line numbers, the ``lineno-start`` option to select the
   first line number, the ``emphasize-lines`` option to emphasize particular
   lines, and a ``language`` option to select a language different from the
   current file's standard language.  Example with options::

      .. literalinclude:: example.rb
         :language: ruby
         :emphasize-lines: 12,15-18
         :linenos:

   Include files are assumed to be encoded in the :confval:`source_encoding`.
   If the file has a different encoding, you can specify it with the
   ``encoding`` option::

      .. literalinclude:: example.py
         :encoding: latin-1

   The directive also supports including only parts of the file.  If it is a
   Python module, you can select a class, function or method to include using
   the ``pyobject`` option::

      .. literalinclude:: example.py
         :pyobject: Timer.start

   This would only include the code lines belonging to the ``start()`` method in
   the ``Timer`` class within the file.

   Alternately, you can specify exactly which lines to include by giving a
   ``lines`` option::

      .. literalinclude:: example.py
         :lines: 1,3,5-10,20-

   This includes the lines 1, 3, 5 to 10 and lines 20 to the last line.

   Another way to control which part of the file is included is to use the
   ``start-after`` and ``end-before`` options (or only one of them).  If
   ``start-after`` is given as a string option, only lines that follow the first
   line containing that string are included.  If ``end-before`` is given as a
   string option, only lines that precede the first lines containing that string
   are included.

   When specifying particular parts of a file to display, it can be useful to
   display exactly which lines are being presented.
   This can be done using the ``lineno-match`` option.

   You can prepend and/or append a line to the included code, using the
   ``prepend`` and ``append`` option, respectively.  This is useful e.g. for
   highlighting PHP code that doesn't include the ``<?php``/``?>`` markers.


   If you want to show the diff of the code, you can specify the old
   file by giving a ``diff`` option::

      .. literalinclude:: example.py
         :diff: example.py.orig

   This shows the diff between example.py and example.py.orig with unified diff
   format.

   .. versionadded:: 0.4.3
      The ``encoding`` option.
   .. versionadded:: 0.6
      The ``pyobject``, ``lines``, ``start-after`` and ``end-before`` options,
      as well as support for absolute filenames.
   .. versionadded:: 1.0
      The ``prepend`` and ``append`` options, as well as ``tab-width``.
   .. versionadded:: 1.3
      The ``diff`` option.
      The ``lineno-match`` option.


Caption and name
^^^^^^^^^^^^^^^^

.. versionadded:: 1.3

A ``caption`` option can be given to show that name before the code block.
A ``name`` option can be provided implicit target name that can be referenced
by using :rst:role:`ref`.
For example::

   .. code-block:: python
      :caption: this.py
      :name: this-py

      print 'Explicit is better than implicit.'


:rst:dir:`literalinclude` also supports the ``caption`` and ``name`` option.
``caption`` has a additional feature that if you leave the value empty, the shown
filename will be exactly the one given as an argument.


Dedent
^^^^^^

.. versionadded:: 1.3

A ``dedent`` option can be given to strip indentation characters from the code
block. For example::

   .. literalinclude:: example.rb
      :language: ruby
      :dedent: 4
      :lines: 10-15

:rst:dir:`code-block` also supports the ``dedent`` option.


.. rubric:: Footnotes

.. [1] There is a standard ``.. include`` directive, but it raises errors if the
       file is not found.  This one only emits a warning.
