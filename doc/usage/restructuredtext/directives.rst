.. highlight:: rst

==========
Directives
==========

:ref:`As previously discussed <rst-directives>`, a directive is a generic block
of explicit markup. While Docutils provides a number of directives, Sphinx
provides many more and uses directives as one of the primary extension
mechanisms.

.. seealso::

   Refer to the :ref:`reStructuredText Primer <rst-directives>` for an overview
   of the directives provided by Docutils.


.. _toctree-directive:

Table of contents
-----------------

.. index:: pair: table of; contents

Since reST does not have facilities to interconnect several documents, or split
documents into multiple output files, Sphinx uses a custom directive to add
relations between the single files the documentation is made of, as well as
tables of contents.  The ``toctree`` directive is the central element.

.. note::

   Simple "inclusion" of one file in another can be done with the
   :dudir:`include` directive.

.. note::

   For local tables of contents, use the standard reST :dudir:`contents
   directive <table-of-contents>`.

.. rst:directive:: toctree

   This directive inserts a "TOC tree" at the current location, using the
   individual TOCs (including "sub-TOC trees") of the documents given in the
   directive body.  Relative document names (not beginning with a slash) are
   relative to the document the directive occurs in, absolute names are relative
   to the source directory.  A numeric ``maxdepth`` option may be given to
   indicate the depth of the tree; by default, all levels are included. [#]_

   Consider this example (taken from the Python docs' library reference index)::

      .. toctree::
         :maxdepth: 2

         intro
         strings
         datatypes
         numeric
         (many more documents listed here)

   This accomplishes two things:

   * Tables of contents from all those documents are inserted, with a maximum
     depth of two, that means one nested heading.  ``toctree`` directives in
     those documents are also taken into account.
   * Sphinx knows the relative order of the documents ``intro``,
     ``strings`` and so forth, and it knows that they are children of the shown
     document, the library index.  From this information it generates "next
     chapter", "previous chapter" and "parent chapter" links.

   **Entries**

   Document titles in the :rst:dir:`toctree` will be automatically read from the
   title of the referenced document. If that isn't what you want, you can
   specify an explicit title and target using a similar syntax to reST
   hyperlinks (and Sphinx's :ref:`cross-referencing syntax <xref-syntax>`). This
   looks like::

       .. toctree::

          intro
          All about strings <strings>
          datatypes

   The second line above will link to the ``strings`` document, but will use the
   title "All about strings" instead of the title of the ``strings`` document.

   You can also add external links, by giving an HTTP URL instead of a document
   name.

   **Section numbering**

   If you want to have section numbers even in HTML output, give the
   **toplevel** toctree a ``numbered`` option.  For example::

      .. toctree::
         :numbered:

         foo
         bar

   Numbering then starts at the heading of ``foo``.  Sub-toctrees are
   automatically numbered (don't give the ``numbered`` flag to those).

   Numbering up to a specific depth is also possible, by giving the depth as a
   numeric argument to ``numbered``.

   **Additional options**

   You can use ``caption`` option to provide a toctree caption and you can use
   ``name`` option to provide implicit target name that can be referenced by
   using :rst:role:`ref`::

      .. toctree::
         :caption: Table of Contents
         :name: mastertoc

         foo

   If you want only the titles of documents in the tree to show up, not other
   headings of the same level, you can use the ``titlesonly`` option::

      .. toctree::
         :titlesonly:

         foo
         bar

   You can use "globbing" in toctree directives, by giving the ``glob`` flag
   option.  All entries are then matched against the list of available
   documents, and matches are inserted into the list alphabetically.  Example::

      .. toctree::
         :glob:

         intro*
         recipe/*
         *

   This includes first all documents whose names start with ``intro``, then all
   documents in the ``recipe`` folder, then all remaining documents (except the
   one containing the directive, of course.) [#]_

   The special entry name ``self`` stands for the document containing the
   toctree directive.  This is useful if you want to generate a "sitemap" from
   the toctree.

   You can use the ``reversed`` flag option to reverse the order of the entries
   in the list. This can be useful when using the ``glob`` flag option to
   reverse the ordering of the files.  Example::

      .. toctree::
         :glob:
         :reversed:

         recipe/*

   You can also give a "hidden" option to the directive, like this::

      .. toctree::
         :hidden:

         doc_1
         doc_2

   This will still notify Sphinx of the document hierarchy, but not insert links
   into the document at the location of the directive -- this makes sense if you
   intend to insert these links yourself, in a different style, or in the HTML
   sidebar.

   In cases where you want to have only one top-level toctree and hide all other
   lower level toctrees you can add the "includehidden" option to the top-level
   toctree entry::

      .. toctree::
         :includehidden:

         doc_1
         doc_2

   All other toctree entries can then be eliminated by the "hidden" option.

   In the end, all documents in the :term:`source directory` (or subdirectories)
   must occur in some ``toctree`` directive; Sphinx will emit a warning if it
   finds a file that is not included, because that means that this file will not
   be reachable through standard navigation.

   Use :confval:`exclude_patterns` to explicitly exclude documents or
   directories from building completely.  Use :ref:`the "orphan" metadata
   <metadata>` to let a document be built, but notify Sphinx that it is not
   reachable via a toctree.

   The "master document" (selected by :confval:`master_doc`) is the "root" of
   the TOC tree hierarchy.  It can be used as the documentation's main page, or
   as a "full table of contents" if you don't give a ``maxdepth`` option.

   .. versionchanged:: 0.3
      Added "globbing" option.

   .. versionchanged:: 0.6
      Added "numbered" and "hidden" options as well as external links and
      support for "self" references.

   .. versionchanged:: 1.0
      Added "titlesonly" option.

   .. versionchanged:: 1.1
      Added numeric argument to "numbered".

   .. versionchanged:: 1.2
      Added "includehidden" option.

   .. versionchanged:: 1.3
      Added "caption" and "name" option.

Special names
^^^^^^^^^^^^^

Sphinx reserves some document names for its own use; you should not try to
create documents with these names -- it will cause problems.

The special document names (and pages generated for them) are:

* ``genindex``, ``modindex``, ``search``

  These are used for the general index, the Python module index, and the search
  page, respectively.

  The general index is populated with entries from modules, all
  index-generating :ref:`object descriptions <basic-domain-markup>`, and from
  :rst:dir:`index` directives.

  The Python module index contains one entry per :rst:dir:`py:module`
  directive.

  The search page contains a form that uses the generated JSON search index and
  JavaScript to full-text search the generated documents for search words; it
  should work on every major browser that supports modern JavaScript.

* every name beginning with ``_``

  Though only few such names are currently used by Sphinx, you should not
  create documents or document-containing directories with such names.  (Using
  ``_`` as a prefix for a custom template directory is fine.)

.. warning::

   Be careful with unusual characters in filenames.  Some formats may interpret
   these characters in unexpected ways:

   * Do not use the colon ``:`` for HTML based formats.  Links to other parts
     may not work.

   * Do not use the plus ``+`` for the ePub format.  Some resources may not be
     found.


Paragraph-level markup
----------------------

.. index:: note, warning
           pair: changes; in version

These directives create short paragraphs and can be used inside information
units as well as normal text.

.. rst:directive:: .. note::

   An especially important bit of information about an API that a user should be
   aware of when using whatever bit of API the note pertains to.  The content of
   the directive should be written in complete sentences and include all
   appropriate punctuation.

   Example::

      .. note::

         This function is not suitable for sending spam e-mails.

.. rst:directive:: .. warning::

   An important bit of information about an API that a user should be very aware
   of when using whatever bit of API the warning pertains to.  The content of
   the directive should be written in complete sentences and include all
   appropriate punctuation. This differs from :rst:dir:`note` in that it is
   recommended over :rst:dir:`note` for information regarding security.

.. rst:directive:: .. versionadded:: version

   This directive documents the version of the project which added the described
   feature to the library or C API. When this applies to an entire module, it
   should be placed at the top of the module section before any prose.

   The first argument must be given and is the version in question; you can add
   a second argument consisting of a *brief* explanation of the change.

   Example::

      .. versionadded:: 2.5
         The *spam* parameter.

   Note that there must be no blank line between the directive head and the
   explanation; this is to make these blocks visually continuous in the markup.

.. rst:directive:: .. versionchanged:: version

   Similar to :rst:dir:`versionadded`, but describes when and what changed in
   the named feature in some way (new parameters, changed side effects, etc.).

.. rst:directive:: .. deprecated:: version

   Similar to :rst:dir:`versionchanged`, but describes when the feature was
   deprecated.  An explanation can also be given, for example to inform the
   reader what should be used instead.  Example::

      .. deprecated:: 3.1
         Use :func:`spam` instead.

.. rst:directive:: seealso

   Many sections include a list of references to module documentation or
   external documents.  These lists are created using the :rst:dir:`seealso`
   directive.

   The :rst:dir:`seealso` directive is typically placed in a section just before
   any subsections.  For the HTML output, it is shown boxed off from the main
   flow of the text.

   The content of the :rst:dir:`seealso` directive should be a reST definition
   list. Example::

      .. seealso::

         Module :py:mod:`zipfile`
            Documentation of the :py:mod:`zipfile` standard module.

         `GNU tar manual, Basic Tar Format <http://link>`_
            Documentation for tar archive files, including GNU tar extensions.

   There's also a "short form" allowed that looks like this::

      .. seealso:: modules :py:mod:`zipfile`, :py:mod:`tarfile`

   .. versionadded:: 0.5
      The short form.

.. rst:directive:: .. rubric:: title

   This directive creates a paragraph heading that is not used to create a
   table of contents node.

   .. note::

      If the *title* of the rubric is "Footnotes" (or the selected language's
      equivalent), this rubric is ignored by the LaTeX writer, since it is
      assumed to only contain footnote definitions and therefore would create an
      empty heading.

.. rst:directive:: centered

   This directive creates a centered boldfaced line of text.  Use it as
   follows::

      .. centered:: LICENSE AGREEMENT

   .. deprecated:: 1.1
      This presentation-only directive is a legacy from older versions.  Use a
      :rst:dir:`rst-class` directive instead and add an appropriate style.

.. rst:directive:: hlist

   This directive must contain a bullet list.  It will transform it into a more
   compact list by either distributing more than one item horizontally, or
   reducing spacing between items, depending on the builder.

   For builders that support the horizontal distribution, there is a ``columns``
   option that specifies the number of columns; it defaults to 2.  Example::

      .. hlist::
         :columns: 3

         * A list of
         * short items
         * that should be
         * displayed
         * horizontally

   .. versionadded:: 0.6


.. _code-examples:

Showing code examples
---------------------

.. index:: pair: code; examples
           single: sourcecode

.. todo:: Rework this to remove the bullet points

Examples of Python source code or interactive sessions are represented using
standard reST literal blocks.  They are started by a ``::`` at the end of the
preceding paragraph and delimited by indentation.

Representing an interactive session requires including the prompts and output
along with the Python code.  No special markup is required for interactive
sessions.  After the last line of input or output presented, there should not
be an "unused" primary prompt; this is an example of what *not* to do::

   >>> 1 + 1
   2
   >>>

Syntax highlighting is done with `Pygments <http://pygments.org>`_ and handled
in a smart way:

* There is a "highlighting language" for each source file.  Per default, this
  is ``'python'`` as the majority of files will have to highlight Python
  snippets, but the doc-wide default can be set with the
  :confval:`highlight_language` config value.

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

     This language is used until the next ``highlight`` directive is
     encountered.

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
automatically-highlighted blocks (those started by ``::``), line numbers must
be switched on in a :rst:dir:`highlight` directive, with the
``linenothreshold`` option::

   .. highlight:: python
      :linenothreshold: 5

This will produce line numbers for all code blocks longer than five lines.

For :rst:dir:`code-block` blocks, a ``linenos`` flag option can be given to
switch on line numbers for the individual block::

   .. code-block:: ruby
      :linenos:

      Some more Ruby code.

The first line number can be selected with the ``lineno-start`` option.  If
present, ``linenos`` flag is automatically activated::

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

.. versionchanged:: 1.6.6
   LaTeX supports the ``emphasize-lines`` option.

Includes
^^^^^^^^

.. rst:directive:: .. literalinclude:: filename

   Longer displays of verbatim text may be included by storing the example text
   in an external file containing only plain text.  The file may be included
   using the ``literalinclude`` directive. [#]_ For example, to include the
   Python source file :file:`example.py`, use::

      .. literalinclude:: example.py

   The file name is usually relative to the current file's path.  However, if
   it is absolute (starting with ``/``), it is relative to the top source
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

   This would only include the code lines belonging to the ``start()`` method
   in the ``Timer`` class within the file.

   Alternately, you can specify exactly which lines to include by giving a
   ``lines`` option::

      .. literalinclude:: example.py
         :lines: 1,3,5-10,20-

   This includes the lines 1, 3, 5 to 10 and lines 20 to the last line.

   Another way to control which part of the file is included is to use the
   ``start-after`` and ``end-before`` options (or only one of them).  If
   ``start-after`` is given as a string option, only lines that follow the
   first line containing that string are included.  If ``end-before`` is given
   as a string option, only lines that precede the first lines containing that
   string are included.

   With lines selected using ``start-after`` it is still possible to use
   ``lines``, the first allowed line having by convention the line number
   ``1``.

   When lines have been selected in any of the ways described above, the line
   numbers in ``emphasize-lines`` refer to those selected lines, counted
   consecutively starting at ``1``.

   When specifying particular parts of a file to display, it can be useful to
   display the original line numbers. This can be done using the
   ``lineno-match`` option, which is however allowed only when the selection
   consists of contiguous lines.

   You can prepend and/or append a line to the included code, using the
   ``prepend`` and ``append`` option, respectively.  This is useful e.g. for
   highlighting PHP code that doesn't include the ``<?php``/``?>`` markers.

   If you want to show the diff of the code, you can specify the old file by
   giving a ``diff`` option::

      .. literalinclude:: example.py
         :diff: example.py.orig

   This shows the diff between ``example.py`` and ``example.py.orig`` with
   unified diff format.

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
   .. versionchanged:: 1.6
      With both ``start-after`` and ``lines`` in use, the first line as per
      ``start-after`` is considered to be with line number ``1`` for ``lines``.

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
``caption`` has an additional feature that if you leave the value empty, the
shown filename will be exactly the one given as an argument.

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


.. _glossary-directive:

Glossary
--------

.. rst:directive:: .. glossary::

   This directive must contain a reST definition-list-like markup with terms and
   definitions.  The definitions will then be referencable with the
   :rst:role:`term` role.  Example::

      .. glossary::

         environment
            A structure where information about all documents under the root is
            saved, and used for cross-referencing.  The environment is pickled
            after the parsing stage, so that successive runs only need to read
            and parse new and changed documents.

         source directory
            The directory which, including its subdirectories, contains all
            source files for one Sphinx project.

   In contrast to regular definition lists, *multiple* terms per entry are
   allowed, and inline markup is allowed in terms.  You can link to all of the
   terms.  For example::

      .. glossary::

         term 1
         term 2
            Definition of both terms.

   (When the glossary is sorted, the first term determines the sort order.)

   If you want to specify "grouping key" for general index entries, you can put a "key"
   as "term : key". For example::

      .. glossary::

         term 1 : A
         term 2 : B
            Definition of both terms.

   Note that "key" is used for grouping key as is.
   The "key" isn't normalized; key "A" and "a" become different groups.
   The whole characters in "key" is used instead of a first character; it is used for
   "Combining Character Sequence" and "Surrogate Pairs" grouping key.

   In i18n situation, you can specify "localized term : key" even if original text only
   have "term" part. In this case, translated "localized term" will be categorized in
   "key" group.

   .. versionadded:: 0.6
      You can now give the glossary directive a ``:sorted:`` flag that will
      automatically sort the entries alphabetically.

   .. versionchanged:: 1.1
      Now supports multiple terms and inline markup in terms.

   .. versionchanged:: 1.4
      Index key for glossary term should be considered *experimental*.


Grammar production displays
---------------------------

Special markup is available for displaying the productions of a formal grammar.
The markup is simple and does not attempt to model all aspects of BNF (or any
derived forms), but provides enough to allow context-free grammars to be
displayed in a way that causes uses of a symbol to be rendered as hyperlinks to
the definition of the symbol.  There is this directive:

.. rst:directive:: .. productionlist:: [name]

   This directive is used to enclose a group of productions.  Each production
   is given on a single line and consists of a name, separated by a colon from
   the following definition.  If the definition spans multiple lines, each
   continuation line must begin with a colon placed at the same column as in
   the first line.

   The argument to :rst:dir:`productionlist` serves to distinguish different
   sets of production lists that belong to different grammars.

   Blank lines are not allowed within ``productionlist`` directive arguments.

   The definition can contain token names which are marked as interpreted text
   (e.g. ``sum ::= `integer` "+" `integer```) -- this generates
   cross-references to the productions of these tokens.  Outside of the
   production list, you can reference to token productions using
   :rst:role:`token`.

   Note that no further reST parsing is done in the production, so that you
   don't have to escape ``*`` or ``|`` characters.

The following is an example taken from the Python Reference Manual::

   .. productionlist::
      try_stmt: try1_stmt | try2_stmt
      try1_stmt: "try" ":" `suite`
               : ("except" [`expression` ["," `target`]] ":" `suite`)+
               : ["else" ":" `suite`]
               : ["finally" ":" `suite`]
      try2_stmt: "try" ":" `suite`
               : "finally" ":" `suite`


.. rubric:: Footnotes

.. [#] The LaTeX writer only refers the ``maxdepth`` option of first toctree
       directive in the document.

.. [#] A note on available globbing syntax: you can use the standard shell
       constructs ``*``, ``?``, ``[...]`` and ``[!...]`` with the feature that
       these all don't match slashes.  A double star ``**`` can be used to
       match any sequence of characters *including* slashes.

.. [#] There is a standard ``.. include`` directive, but it raises errors if the
       file is not found.  This one only emits a warning.
