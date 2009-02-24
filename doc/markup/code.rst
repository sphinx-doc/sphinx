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

Syntax highlighting is done with `Pygments <http://pygments.org>`_ (if it's
installed) and handled in a smart way:

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
  used as follows::

     .. highlight:: c

  This language is used until the next ``highlight`` directive is encountered.

* For documents that have to show snippets in different languages, there's also
  a :dir:`code-block` directive that is given the highlighting language
  directly::

     .. code-block:: ruby

        Some Ruby code.

  The directive's alias name :dir:`sourcecode` works as well.

* The valid values for the highlighting language are:

  * ``none`` (no highlighting)
  * ``python`` (the default when :confval:`highlight_language` isn't set)
  * ``guess`` (let Pygments guess the lexer based on contents, only works with
    certain well-recognizable languages)
  * ``rest``
  * ``c``
  * ... and any other lexer name that Pygments supports.

* If highlighting with the selected language fails, the block is not highlighted
  in any way.

Line numbers
^^^^^^^^^^^^

If installed, Pygments can generate line numbers for code blocks.  For
automatically-highlighted blocks (those started by ``::``), line numbers must be
switched on in a :dir:`highlight` directive, with the ``linenothreshold``
option::

   .. highlight:: python
      :linenothreshold: 5

This will produce line numbers for all code blocks longer than five lines.

For :dir:`code-block` blocks, a ``linenos`` flag option can be given to switch
on line numbers for the individual block::

   .. code-block:: ruby
      :linenos:

      Some more Ruby code.


Includes
^^^^^^^^

.. directive:: .. literalinclude:: filename

   Longer displays of verbatim text may be included by storing the example text in
   an external file containing only plain text.  The file may be included using the
   ``literalinclude`` directive. [1]_ For example, to include the Python source file
   :file:`example.py`, use::

      .. literalinclude:: example.py

   The file name is usually relative to the current file's path.  However, if it
   is absolute (starting with ``/``), it is relative to the top source
   directory.

   The directive also supports the ``linenos`` flag option to switch on line
   numbers, and a ``language`` option to select a language different from the
   current file's standard language.  Example with options::

      .. literalinclude:: example.rb
         :language: ruby
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

   .. versionadded:: 0.4.3
      The ``encoding`` option.
   .. versionadded:: 0.6
      The ``pyobject``, ``lines``, ``start-after`` and ``end-before`` options,
      as well as support for absolute filenames.


.. rubric:: Footnotes

.. [1] There is a standard ``.. include`` directive, but it raises errors if the
       file is not found.  This one only emits a warning.
