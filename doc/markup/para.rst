.. highlight:: rest

Paragraph-level markup
----------------------

.. index:: note, warning
           pair: changes; in version

These directives create short paragraphs and can be used inside information
units as well as normal text:

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


--------------

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


Table-of-contents markup
------------------------

The :rst:dir:`toctree` directive, which generates tables of contents of
subdocuments, is described in :ref:`toctree-directive`.

For local tables of contents, use the standard reST :dudir:`contents directive
<table-of-contents>`.


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

   This directive is used to enclose a group of productions.  Each production is
   given on a single line and consists of a name, separated by a colon from the
   following definition.  If the definition spans multiple lines, each
   continuation line must begin with a colon placed at the same column as in the
   first line.

   The argument to :rst:dir:`productionlist` serves to distinguish different
   sets of production lists that belong to different grammars.

   Blank lines are not allowed within ``productionlist`` directive arguments.

   The definition can contain token names which are marked as interpreted text
   (e.g. ``sum ::= `integer` "+" `integer```) -- this generates cross-references
   to the productions of these tokens.  Outside of the production list, you can
   reference to token productions using :rst:role:`token`.

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
