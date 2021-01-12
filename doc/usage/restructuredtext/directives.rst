.. highlight:: rst

==========
Directives
==========

:ref:`As previously discussed <rst-directives>`, a directive is a generic block
of explicit markup. While Docutils provides a number of directives, Sphinx
provides many more and uses directives as one of the primary extension
mechanisms.

See :doc:`/usage/restructuredtext/domains` for roles added by domains.

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

   To create table of contents for current document (.rst file), use the
   standard reST :dudir:`contents directive <table-of-contents>`.

.. rst:directive:: toctree

   This directive inserts a "TOC tree" at the current location, using the
   individual TOCs (including "sub-TOC trees") of the documents given in the
   directive body.  Relative document names (not beginning with a slash) are
   relative to the document the directive occurs in, absolute names are relative
   to the source directory.  A numeric ``maxdepth`` option may be given to
   indicate the depth of the tree; by default, all levels are included. [#]_

   The representation of "TOC tree" is changed in each output format.  The
   builders that output multiple files (ex. HTML) treat it as a collection of
   hyperlinks.  On the other hand, the builders that output a single file (ex.
   LaTeX, man page, etc.) replace it with the content of the documents on the
   TOC tree.

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

   You can use the ``caption`` option to provide a toctree caption and you can
   use the ``name`` option to provide an implicit target name that can be
   referenced by using :rst:role:`ref`::

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

  Though few such names are currently used by Sphinx, you should not
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

There are multiple ways to show syntax-highlighted literal code blocks in
Sphinx: using :ref:`reST doctest blocks <rst-doctest-blocks>`; using :ref:`reST
literal blocks <rst-literal-blocks>`, optionally in combination with the
:rst:dir:`highlight` directive; using the :rst:dir:`code-block` directive; and
using the :rst:dir:`literalinclude` directive. Doctest blocks can only be used
to show interactive Python sessions, while the remaining three can be used for
other languages. Of these three, literal blocks are useful when an entire
document, or at least large sections of it, use code blocks with the same
syntax and which should be styled in the same manner. On the other hand, the
:rst:dir:`code-block` directive makes more sense when you want more fine-tuned
control over the styling of each block or when you have a document containing
code blocks using multiple varied syntaxes. Finally, the
:rst:dir:`literalinclude` directive is useful for including entire code files
in your documentation.

In all cases, Syntax highlighting is provided by `Pygments
<http://pygments.org>`_. When using literal blocks, this is configured using
any :rst:dir:`highlight` directives in the source file. When a ``highlight``
directive is encountered, it is used until the next ``highlight`` directive is
encountered. If there is no ``highlight`` directive in the file, the global
highlighting language is used. This defaults to ``python`` but can be
configured using the :confval:`highlight_language` config value. The following
values are supported:

* ``none`` (no highlighting)
* ``default`` (similar to ``python3`` but with a fallback to ``none`` without
  warning highlighting fails; the default when :confval:`highlight_language`
  isn't set)
* ``guess`` (let Pygments guess the lexer based on contents, only works with
  certain well-recognizable languages)
* ``python``
* ``rest``
* ``c``
* ... and any other `lexer alias that Pygments supports`__

If highlighting with the selected language fails (i.e. Pygments emits an
"Error" token), the block is not highlighted in any way.

.. important::

   The list of lexer aliases supported is tied to the Pygment version. If you
   want to ensure consistent highlighting, you should fix your version of
   Pygments.

__ http://pygments.org/docs/lexers

.. rst:directive:: .. highlight:: language

   Example::

      .. highlight:: c

   This language is used until the next ``highlight`` directive is encountered.
   As discussed previously, *language* can be any lexer alias supported by
   Pygments.

   .. rubric:: options

   .. rst:directive:option:: linenothreshold: threshold
      :type: number (optional)

      Enable to generate line numbers for code blocks.

      This option takes an optional number as threshold parameter.  If any
      threshold given, the directive will produce line numbers only for the code
      blocks longer than N lines.  If not given, line numbers will be produced
      for all of code blocks.

      Example::

         .. highlight:: python
            :linenothreshold: 5

   .. rst:directive:option:: force
      :type: no value

      If given, minor errors on highlighting are ignored.

      .. versionadded:: 2.1

.. rst:directive:: .. code-block:: [language]

   Example::

      .. code-block:: ruby

         Some Ruby code.

   The directive's alias name :rst:dir:`sourcecode` works as well.  This
   directive takes a language name as an argument.  It can be any lexer alias
   supported by Pygments.  If it is not given, the setting of
   :rst:dir:`highlight` directive will be used.  If not set,
   :confval:`highlight_language` will be used.

   .. versionchanged:: 2.0
      The ``language`` argument becomes optional.

   .. rubric:: options

   .. rst:directive:option:: linenos
      :type: no value

      Enable to generate line numbers for the code block::

         .. code-block:: ruby
            :linenos:

            Some more Ruby code.

   .. rst:directive:option:: lineno-start: number
      :type: number

      Set the first line number of the code block.  If present, ``linenos``
      option is also automatically activated::

         .. code-block:: ruby
            :lineno-start: 10

            Some more Ruby code, with line numbering starting at 10.

      .. versionadded:: 1.3

   .. rst:directive:option:: emphasize-lines: line numbers
      :type: comma separated numbers

      Emphasize particular lines of the code block::

       .. code-block:: python
          :emphasize-lines: 3,5

          def some_function():
              interesting = False
              print 'This line is highlighted.'
              print 'This one is not...'
              print '...but this one is.'

      .. versionadded:: 1.1
      .. versionchanged:: 1.6.6
         LaTeX supports the ``emphasize-lines`` option.

   .. rst:directive:option: force
      :type: no value

      Ignore minor errors on highlighting

      .. versionchanged:: 2.1

   .. rst:directive:option:: caption: caption of code block
      :type: text

      Set a caption to the code block.

      .. versionadded:: 1.3

   .. rst:directive:option:: name: a label for hyperlink
      :type: text

      Define implicit target name that can be referenced by using
      :rst:role:`ref`.  For example::

        .. code-block:: python
           :caption: this.py
           :name: this-py

           print 'Explicit is better than implicit.'

      .. versionadded:: 1.3

   .. rst:directive:option:: dedent: number
      :type: number or no value

      Strip indentation characters from the code block.  When number given,
      leading N characters are removed.  When no argument given, leading spaces
      are removed via :func:`textwrap.dedent()`.  For example::

         .. code-block:: ruby
            :dedent: 4

                some ruby code

      .. versionadded:: 1.3
      .. versionchanged:: 3.5
         Support automatic dedent.

   .. rst:directive:option:: force
      :type: no value

      If given, minor errors on highlighting are ignored.

      .. versionadded:: 2.1

.. rst:directive:: .. literalinclude:: filename

   Longer displays of verbatim text may be included by storing the example text
   in an external file containing only plain text.  The file may be included
   using the ``literalinclude`` directive. [#]_ For example, to include the
   Python source file :file:`example.py`, use::

      .. literalinclude:: example.py

   The file name is usually relative to the current file's path.  However, if
   it is absolute (starting with ``/``), it is relative to the top source
   directory.

   **Additional options**

   Like :rst:dir:`code-block`, the directive supports the ``linenos`` flag
   option to switch on line numbers, the ``lineno-start`` option to select the
   first line number, the ``emphasize-lines`` option to emphasize particular
   lines, the ``name`` option to provide an implicit target name, the
   ``dedent`` option to strip indentation characters for the code block, and a
   ``language`` option to select a language different from the current file's
   standard language. In addition, it supports the ``caption`` option; however,
   this can be provided with no argument to use the filename as the caption.
   Example with options::

      .. literalinclude:: example.rb
         :language: ruby
         :emphasize-lines: 12,15-18
         :linenos:

   Tabs in the input are expanded if you give a ``tab-width`` option with the
   desired tab width.

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
   string are included. The ``start-at`` and ``end-at`` options behave in a
   similar way, but the lines containing the matched string are included.

   ``start-after``/``start-at`` and ``end-before``/``end-at`` can have same string.
   ``start-after``/``start-at`` filter lines before the line that contains
   option string (``start-at`` will keep the line). Then ``end-before``/``end-at``
   filter lines after the line that contains option string (``end-at`` will keep
   the line and ``end-before`` skip the first line).

   .. note::

      If you want to select only ``[second-section]`` of ini file like the
      following, you can use ``:start-at: [second-section]`` and
      ``:end-before: [third-section]``:

      .. code-block:: ini

         [first-section]

         var_in_first=true

         [second-section]

         var_in_second=true

         [third-section]

         var_in_third=true

      Useful cases of these option is working with tag comments.
      ``:start-after: [initialized]`` and ``:end-before: [initialized]`` options
      keep lines between comments:

      .. code-block:: py

         if __name__ == "__main__":
             # [initialize]
             app.start(":8000")
             # [initialize]


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

   A ``force`` option can ignore minor errors on highlighting.

   .. versionchanged:: 0.4.3
      Added the ``encoding`` option.

   .. versionchanged:: 0.6
      Added the ``pyobject``, ``lines``, ``start-after`` and ``end-before``
      options, as well as support for absolute filenames.

   .. versionchanged:: 1.0
      Added the ``prepend``, ``append``, and ``tab-width`` options.

   .. versionchanged:: 1.3
      Added the ``diff``, ``lineno-match``, ``caption``, ``name``, and
      ``dedent`` options.

   .. versionchanged:: 1.5
      Added the ``start-at``, and ``end-at`` options.

   .. versionchanged:: 1.6
      With both ``start-after`` and ``lines`` in use, the first line as per
      ``start-after`` is considered to be with line number ``1`` for ``lines``.

   .. versionchanged:: 2.1
      Added the ``force`` option.

   .. versionchanged:: 3.5
      Support automatic dedent.

.. _glossary-directive:

Glossary
--------

.. rst:directive:: .. glossary::

   This directive must contain a reST definition-list-like markup with terms and
   definitions.  The definitions will then be referenceable with the
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

   If you want to specify "grouping key" for general index entries, you can put
   a "key" as "term : key". For example::

      .. glossary::

         term 1 : A
         term 2 : B
            Definition of both terms.

   Note that "key" is used for grouping key as is.
   The "key" isn't normalized; key "A" and "a" become different groups.
   The whole characters in "key" is used instead of a first character; it is
   used for "Combining Character Sequence" and "Surrogate Pairs" grouping key.

   In i18n situation, you can specify "localized term : key" even if original
   text only have "term" part. In this case, translated "localized term" will be
   categorized in "key" group.

   .. versionadded:: 0.6
      You can now give the glossary directive a ``:sorted:`` flag that will
      automatically sort the entries alphabetically.

   .. versionchanged:: 1.1
      Now supports multiple terms and inline markup in terms.

   .. versionchanged:: 1.4
      Index key for glossary term should be considered *experimental*.


Meta-information markup
-----------------------

.. rst:directive:: .. sectionauthor:: name <email>

   Identifies the author of the current section.  The argument should include
   the author's name such that it can be used for presentation and email
   address.  The domain name portion of the address should be lower case.
   Example::

      .. sectionauthor:: Guido van Rossum <guido@python.org>

   By default, this markup isn't reflected in the output in any way (it helps
   keep track of contributions), but you can set the configuration value
   :confval:`show_authors` to ``True`` to make them produce a paragraph in the
   output.


.. rst:directive:: .. codeauthor:: name <email>

   The :rst:dir:`codeauthor` directive, which can appear multiple times, names
   the authors of the described code, just like :rst:dir:`sectionauthor` names
   the author(s) of a piece of documentation.  It too only produces output if
   the :confval:`show_authors` configuration value is ``True``.


Index-generating markup
-----------------------

Sphinx automatically creates index entries from all object descriptions (like
functions, classes or attributes) like discussed in
:doc:`/usage/restructuredtext/domains`.

However, there is also explicit markup available, to make the index more
comprehensive and enable index entries in documents where information is not
mainly contained in information units, such as the language reference.

.. rst:directive:: .. index:: <entries>

   This directive contains one or more index entries.  Each entry consists of a
   type and a value, separated by a colon.

   For example::

      .. index::
         single: execution; context
         module: __main__
         module: sys
         triple: module; search; path

      The execution context
      ---------------------

      ...

   This directive contains five entries, which will be converted to entries in
   the generated index which link to the exact location of the index statement
   (or, in case of offline media, the corresponding page number).

   Since index directives generate cross-reference targets at their location in
   the source, it makes sense to put them *before* the thing they refer to --
   e.g. a heading, as in the example above.

   The possible entry types are:

   single
      Creates a single index entry.  Can be made a subentry by separating the
      subentry text with a semicolon (this notation is also used below to
      describe what entries are created).
   pair
      ``pair: loop; statement`` is a shortcut that creates two index entries,
      namely ``loop; statement`` and ``statement; loop``.
   triple
      Likewise, ``triple: module; search; path`` is a shortcut that creates
      three index entries, which are ``module; search path``, ``search; path,
      module`` and ``path; module search``.
   see
      ``see: entry; other`` creates an index entry that refers from ``entry`` to
      ``other``.
   seealso
      Like ``see``, but inserts "see also" instead of "see".
   module, keyword, operator, object, exception, statement, builtin
      These all create two index entries.  For example, ``module: hashlib``
      creates the entries ``module; hashlib`` and ``hashlib; module``.  (These
      are Python-specific and therefore deprecated.)

   You can mark up "main" index entries by prefixing them with an exclamation
   mark.  The references to "main" entries are emphasized in the generated
   index.  For example, if two pages contain ::

      .. index:: Python

   and one page contains ::

      .. index:: ! Python

   then the backlink to the latter page is emphasized among the three backlinks.

   For index directives containing only "single" entries, there is a shorthand
   notation::

      .. index:: BNF, grammar, syntax, notation

   This creates four index entries.

   .. versionchanged:: 1.1
      Added ``see`` and ``seealso`` types, as well as marking main entries.

   .. rubric:: options

   .. rst:directive:option:: name: a label for hyperlink
      :type: text

      Define implicit target name that can be referenced by using
      :rst:role:`ref`.  For example::

        .. index:: Python
           :name: py-index

   .. versionadded:: 3.0

.. rst:role:: index

   While the :rst:dir:`index` directive is a block-level markup and links to the
   beginning of the next paragraph, there is also a corresponding role that sets
   the link target directly where it is used.

   The content of the role can be a simple phrase, which is then kept in the
   text and used as an index entry.  It can also be a combination of text and
   index entry, styled like with explicit targets of cross-references.  In that
   case, the "target" part can be a full entry as described for the directive
   above.  For example::

      This is a normal reST :index:`paragraph` that contains several
      :index:`index entries <pair: index; entry>`.

   .. versionadded:: 1.1


.. _tags:

Including content based on tags
-------------------------------

.. rst:directive:: .. only:: <expression>

   Include the content of the directive only if the *expression* is true.  The
   expression should consist of tags, like this::

      .. only:: html and draft

   Undefined tags are false, defined tags (via the ``-t`` command-line option or
   within :file:`conf.py`, see :ref:`here <conf-tags>`) are true.  Boolean
   expressions, also using parentheses (like ``html and (latex or draft)``) are
   supported.

   The *format* and the *name* of the current builder (``html``, ``latex`` or
   ``text``) are always set as a tag [#]_.  To make the distinction between
   format and name explicit, they are also added with the prefix ``format_`` and
   ``builder_``, e.g. the epub builder defines the tags  ``html``, ``epub``,
   ``format_html`` and ``builder_epub``.

   These standard tags are set *after* the configuration file is read, so they
   are not available there.

   All tags must follow the standard Python identifier syntax as set out in
   the `Identifiers and keywords
   <https://docs.python.org/3/reference/lexical_analysis.html#identifiers>`_
   documentation.  That is, a tag expression may only consist of tags that
   conform to the syntax of Python variables.  In ASCII, this consists of the
   uppercase and lowercase letters ``A`` through ``Z``, the underscore ``_``
   and, except for the first character, the digits ``0`` through ``9``.

   .. versionadded:: 0.6
   .. versionchanged:: 1.2
      Added the name of the builder and the prefixes.

   .. warning::

      This directive is designed to control only content of document.  It could
      not control sections, labels and so on.

.. _table-directives:

Tables
------

Use :ref:`reStructuredText tables <rst-tables>`, i.e. either

- grid table syntax (:duref:`ref <grid-tables>`),
- simple table syntax (:duref:`ref <simple-tables>`),
- :dudir:`csv-table` syntax,
- or :dudir:`list-table` syntax.

The :dudir:`table` directive serves as optional wrapper of the *grid* and
*simple* syntaxes.

They work fine in HTML output, however there are some gotchas when using tables
in LaTeX: the column width is hard to determine correctly automatically.  For
this reason, the following directive exists:

.. rst:directive:: .. tabularcolumns:: column spec

   This directive gives a "column spec" for the next table occurring in the
   source file.  The spec is the second argument to the LaTeX ``tabulary``
   package's environment (which Sphinx uses to translate tables).  It can have
   values like ::

      |l|l|l|

   which means three left-adjusted, nonbreaking columns.  For columns with
   longer text that should automatically be broken, use either the standard
   ``p{width}`` construct, or tabulary's automatic specifiers:

   +-----+------------------------------------------+
   |``L``| flush left column with automatic width   |
   +-----+------------------------------------------+
   |``R``| flush right column with automatic width  |
   +-----+------------------------------------------+
   |``C``| centered column with automatic width     |
   +-----+------------------------------------------+
   |``J``| justified column with automatic width    |
   +-----+------------------------------------------+

   The automatic widths of the ``LRCJ`` columns are attributed by ``tabulary``
   in proportion to the observed shares in a first pass where the table cells
   are rendered at their natural "horizontal" widths.

   By default, Sphinx uses a table layout with ``J`` for every column.

   .. versionadded:: 0.3

   .. versionchanged:: 1.6
      Merged cells may now contain multiple paragraphs and are much better
      handled, thanks to custom Sphinx LaTeX macros. This novel situation
      motivated the switch to ``J`` specifier and not ``L`` by default.

   .. hint::

      Sphinx actually uses ``T`` specifier having done ``\newcolumntype{T}{J}``.
      To revert to previous default, insert ``\newcolumntype{T}{L}`` in the
      LaTeX preamble (see :confval:`latex_elements`).

      A frequent issue with tabulary is that columns with little contents are
      "squeezed". The minimal column width is a tabulary parameter called
      ``\tymin``. You may set it globally in the LaTeX preamble via
      ``\setlength{\tymin}{40pt}`` for example.

      Else, use the :rst:dir:`tabularcolumns` directive with an explicit
      ``p{40pt}`` (for example) for that column. You may use also ``l``
      specifier but this makes the task of setting column widths more difficult
      if some merged cell intersects that column.

   .. warning::

      Tables with more than 30 rows are rendered using ``longtable``, not
      ``tabulary``, in order to allow pagebreaks. The ``L``, ``R``, ...
      specifiers do not work for these tables.

      Tables that contain list-like elements such as object descriptions,
      blockquotes or any kind of lists cannot be set out of the box with
      ``tabulary``. They are therefore set with the standard LaTeX ``tabular``
      (or ``longtable``) environment if you don't give a ``tabularcolumns``
      directive.  If you do, the table will be set with ``tabulary`` but you
      must use the ``p{width}`` construct (or Sphinx's ``\X`` and ``\Y``
      specifiers described below) for the columns containing these elements.

      Literal blocks do not work with ``tabulary`` at all, so tables containing
      a literal block are always set with ``tabular``. The verbatim environment
      used for literal blocks only works in ``p{width}`` (and ``\X`` or ``\Y``)
      columns, hence Sphinx generates such column specs for tables containing
      literal blocks.

   Since Sphinx 1.5, the ``\X{a}{b}`` specifier is used (there *is* a backslash
   in the specifier letter). It is like ``p{width}`` with the width set to a
   fraction ``a/b`` of the current line width. You can use it in the
   :rst:dir:`tabularcolumns` (it is not a problem if some LaTeX macro is also
   called ``\X``.)

   It is *not* needed for ``b`` to be the total number of columns, nor for the
   sum of the fractions of the ``\X`` specifiers to add  up to one. For example
   ``|\X{2}{5}|\X{1}{5}|\X{1}{5}|`` is legitimate and the table will occupy
   80% of the line width, the first of its three columns having the same width
   as the sum  of the next two.

   This is used by the ``:widths:`` option of the :dudir:`table` directive.

   Since Sphinx 1.6, there is also the ``\Y{f}`` specifier which admits a
   decimal argument, such has ``\Y{0.15}``: this would have the same effect as
   ``\X{3}{20}``.

   .. versionchanged:: 1.6

      Merged cells from complex grid tables (either multi-row, multi-column, or
      both) now allow blockquotes, lists, literal blocks, ... as do regular
      cells.

      Sphinx's merged cells interact well with ``p{width}``, ``\X{a}{b}``,
      ``\Y{f}`` and tabulary's columns.

   .. note::

      :rst:dir:`tabularcolumns` conflicts with ``:widths:`` option of table
      directives.  If both are specified, ``:widths:`` option will be ignored.


Math
----

The input language for mathematics is LaTeX markup.  This is the de-facto
standard for plain-text math notation and has the added advantage that no
further translation is necessary when building LaTeX output.

Keep in mind that when you put math markup in **Python docstrings** read by
:mod:`autodoc <sphinx.ext.autodoc>`, you either have to double all backslashes,
or use Python raw strings (``r"raw"``).

.. rst:directive:: math

   Directive for displayed math (math that takes the whole line for itself).

   The directive supports multiple equations, which should be separated by a
   blank line::

      .. math::

         (a + b)^2 = a^2 + 2ab + b^2

         (a - b)^2 = a^2 - 2ab + b^2

   In addition, each single equation is set within a ``split`` environment,
   which means that you can have multiple aligned lines in an equation,
   aligned at ``&`` and separated by ``\\``::

      .. math::

         (a + b)^2  &=  (a + b)(a + b) \\
                    &=  a^2 + 2ab + b^2

   For more details, look into the documentation of the `AmSMath LaTeX
   package`_.

   When the math is only one line of text, it can also be given as a directive
   argument::

      .. math:: (a + b)^2 = a^2 + 2ab + b^2

   Normally, equations are not numbered.  If you want your equation to get a
   number, use the ``label`` option.  When given, it selects an internal label
   for the equation, by which it can be cross-referenced, and causes an equation
   number to be issued.  See :rst:role:`eq` for an example.  The numbering
   style depends on the output format.

   There is also an option ``nowrap`` that prevents any wrapping of the given
   math in a math environment.  When you give this option, you must make sure
   yourself that the math is properly set up.  For example::

      .. math::
         :nowrap:

         \begin{eqnarray}
            y    & = & ax^2 + bx + c \\
            f(x) & = & x^2 + 2xy + y^2
         \end{eqnarray}

.. _AmSMath LaTeX package: https://www.ams.org/publications/authors/tex/amslatex

.. seealso::

   :ref:`math-support`
      Rendering options for math with HTML builders.

   :confval:`latex_engine`
      Explains how to configure LaTeX builder to support Unicode literals in
      math mark-up.


Grammar production displays
---------------------------

Special markup is available for displaying the productions of a formal grammar.
The markup is simple and does not attempt to model all aspects of BNF (or any
derived forms), but provides enough to allow context-free grammars to be
displayed in a way that causes uses of a symbol to be rendered as hyperlinks to
the definition of the symbol.  There is this directive:

.. rst:directive:: .. productionlist:: [productionGroup]

   This directive is used to enclose a group of productions.  Each production
   is given on a single line and consists of a name, separated by a colon from
   the following definition.  If the definition spans multiple lines, each
   continuation line must begin with a colon placed at the same column as in
   the first line.

   The *productionGroup* argument to :rst:dir:`productionlist` serves to
   distinguish different sets of production lists that belong to different
   grammars.  Multiple production lists with the same *productionGroup* thus
   define rules in the same scope.

   Blank lines are not allowed within ``productionlist`` directive arguments.

   The definition can contain token names which are marked as interpreted text
   (e.g. "``sum ::= `integer` "+" `integer```") -- this generates
   cross-references to the productions of these tokens.  Outside of the
   production list, you can reference to token productions using
   :rst:role:`token`.
   However, if you have given a *productionGroup* argument you must prefix the
   token name in the cross-reference with the group name and a colon,
   e.g., "``myGroup:sum``" instead of just "``sum``".
   If the group should not be shown in the title of the link either
   an explicit title can be given (e.g., "``myTitle <myGroup:sum>``"),
   or the target can be prefixed with a tilde (e.g., "``~myGroup:sum``").

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

.. [#] For most builders name and format are the same. At the moment only
       builders derived from the html builder distinguish between the builder
       format and the builder name.

       Note that the current builder tag is not available in ``conf.py``, it is
       only available after the builder is initialized.
