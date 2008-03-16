.. highlight:: rest

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
  ``'python'`` as the majority of files will have to highlight Python snippets.

* Within Python highlighting mode, interactive sessions are recognized
  automatically and highlighted appropriately.

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
  * ``python`` (the default)
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

   The file name is relative to the current file's path.

   The directive also supports the ``linenos`` flag option to switch on line
   numbers, and a ``language`` option to select a language different from the
   current file's standard language.  Example with options::
    
      .. literalinclude:: example.rb
         :language: ruby
         :linenos:


.. rubric:: Footnotes

.. [1] There is a standard ``.. include`` directive, but it raises errors if the
       file is not found.  This one only emits a warning.
