.. highlight:: rest

Paragraph-level markup
----------------------

.. index:: note, warning
           pair: changes; in version

These directives create short paragraphs and can be used inside information
units as well as normal text:

.. directive:: note

   An especially important bit of information about an API that a user should be
   aware of when using whatever bit of API the note pertains to.  The content of
   the directive should be written in complete sentences and include all
   appropriate punctuation.

   Example::

      .. note::

         This function is not suitable for sending spam e-mails.

.. directive:: warning

   An important bit of information about an API that a user should be very aware
   of when using whatever bit of API the warning pertains to.  The content of
   the directive should be written in complete sentences and include all
   appropriate punctuation. This differs from ``note`` in that it is recommended
   over ``note`` for information regarding security.

.. directive:: .. versionadded:: version

   This directive documents the version of the project which added the described
   feature to the library or C API. When this applies to an entire module, it
   should be placed at the top of the module section before any prose.

   The first argument must be given and is the version in question; you can add
   a second argument consisting of a *brief* explanation of the change.

   Example::

      .. versionadded:: 2.5
         The `spam` parameter.

   Note that there must be no blank line between the directive head and the
   explanation; this is to make these blocks visually continuous in the markup.

.. directive:: .. versionchanged:: version

   Similar to ``versionadded``, but describes when and what changed in the named
   feature in some way (new parameters, changed side effects, etc.).

--------------

.. directive:: seealso

   Many sections include a list of references to module documentation or
   external documents.  These lists are created using the ``seealso`` directive.

   The ``seealso`` directive is typically placed in a section just before any
   sub-sections.  For the HTML output, it is shown boxed off from the main flow
   of the text.

   The content of the ``seealso`` directive should be a reST definition list.
   Example::

      .. seealso::

         Module :mod:`zipfile`
            Documentation of the :mod:`zipfile` standard module.

         `GNU tar manual, Basic Tar Format <http://link>`_
            Documentation for tar archive files, including GNU tar extensions.

   There's also a "short form" allowed that looks like this::

      .. seealso:: modules :mod:`zipfile`, :mod:`tarfile`

   .. versionadded:: 0.5
      The short form.

.. directive:: .. rubric:: title

   This directive creates a paragraph heading that is not used to create a
   table of contents node.

   .. note::

      If the *title* of the rubric is "Footnotes" (or the selected language's
      equivalent), this rubric is ignored by the LaTeX writer, since it is
      assumed to only contain footnote definitions and therefore would create an
      empty heading.


.. directive:: centered

   This directive creates a centered boldfaced line of text.  Use it as follows::

      .. centered:: LICENSE AGREEMENT


.. directive:: hlist

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


Table-of-contents markup
------------------------

The :dir:`toctree` directive, which generates tables of contents of
subdocuments, is described in "Sphinx concepts".

For local tables of contents, use the standard reST :dir:`contents` directive.


Index-generating markup
-----------------------

Sphinx automatically creates index entries from all information units (like
functions, classes or attributes) like discussed before.

However, there is also an explicit directive available, to make the index more
comprehensive and enable index entries in documents where information is not
mainly contained in information units, such as the language reference.

.. directive:: .. index:: <entries>

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

   This directive contains five entries, which will be converted to entries in the
   generated index which link to the exact location of the index statement (or, in
   case of offline media, the corresponding page number).

   Since index directives generate cross-reference targets at their location in
   the source, it makes sense to put them *before* the thing they refer to --
   e.g. a heading, as in the example above.

   The possible entry types are:

   single
      Creates a single index entry.  Can be made a subentry by separating the
      subentry text with a semicolon (this notation is also used below to describe
      what entries are created).
   pair
      ``pair: loop; statement`` is a shortcut that creates two index entries,
      namely ``loop; statement`` and ``statement; loop``.
   triple
      Likewise, ``triple: module; search; path`` is a shortcut that creates three
      index entries, which are ``module; search path``, ``search; path, module`` and
      ``path; module search``.
   module, keyword, operator, object, exception, statement, builtin
      These all create two index entries.  For example, ``module: hashlib`` creates
      the entries ``module; hashlib`` and ``hashlib; module``.

   For index directives containing only "single" entries, there is a shorthand
   notation::

      .. index:: BNF, grammar, syntax, notation

   This creates four index entries.


Glossary
--------

.. directive:: glossary

   This directive must contain a reST definition list with terms and
   definitions.  The definitions will then be referencable with the :role:`term`
   role.  Example::

      .. glossary::

         environment
            A structure where information about all documents under the root is
            saved, and used for cross-referencing.  The environment is pickled
            after the parsing stage, so that successive runs only need to read
            and parse new and changed documents.

         source directory
            The directory which, including its subdirectories, contains all
            source files for one Sphinx project.

   .. versionadded:: 0.6
      You can now give the glossary directive a ``:sorted:`` flag that will
      automatically sort the entries alphabetically.


Grammar production displays
---------------------------

Special markup is available for displaying the productions of a formal grammar.
The markup is simple and does not attempt to model all aspects of BNF (or any
derived forms), but provides enough to allow context-free grammars to be
displayed in a way that causes uses of a symbol to be rendered as hyperlinks to
the definition of the symbol.  There is this directive:

.. directive:: productionlist

   This directive is used to enclose a group of productions.  Each production is
   given on a single line and consists of a name, separated by a colon from the
   following definition.  If the definition spans multiple lines, each
   continuation line must begin with a colon placed at the same column as in the
   first line.

   Blank lines are not allowed within ``productionlist`` directive arguments.

   The definition can contain token names which are marked as interpreted text
   (e.g. ``sum ::= `integer` "+" `integer```) -- this generates cross-references
   to the productions of these tokens.

   Note that no further reST parsing is done in the production, so that you
   don't have to escape ``*`` or ``|`` characters.

.. XXX describe optional first parameter

The following is an example taken from the Python Reference Manual::

   .. productionlist::
      try_stmt: try1_stmt | try2_stmt
      try1_stmt: "try" ":" `suite`
               : ("except" [`expression` ["," `target`]] ":" `suite`)+
               : ["else" ":" `suite`]
               : ["finally" ":" `suite`]
      try2_stmt: "try" ":" `suite`
               : "finally" ":" `suite`
