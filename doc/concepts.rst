.. highlight:: rest

.. _concepts:

Sphinx concepts
===============

Document names
--------------

Since the reST source files can have different extensions (some people like
``.txt``, some like ``.rst`` -- the extension can be configured with
:confval:`source_suffix`) and different OSes have different path separators,
Sphinx abstracts them: all "document names" are relative to the :term:`source
directory`, the extension is stripped, and path separators are converted to
slashes.  All values, parameters and suchlike referring to "documents" expect
such a document name.

Examples for document names are ``index``, ``library/zipfile``, or
``reference/datamodel/types``.  Note that there is no leading slash.


The TOC tree
------------

.. index:: pair: table of; contents

Since reST does not have facilities to interconnect several documents, or split
documents into multiple output files, Sphinx uses a custom directive to add
relations between the single files the documentation is made of, as well as
tables of contents.  The ``toctree`` directive is the central element.

.. directive:: toctree

   This directive inserts a "TOC tree" at the current location, using the
   individual TOCs (including "sub-TOC trees") of the documents given in the
   directive body (whose path is relative to the document the directive occurs
   in).  A numeric ``maxdepth`` option may be given to indicate the depth of the
   tree; by default, all levels are included. [#]_

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
   * Sphinx knows that the relative order of the documents ``intro``,
     ``strings`` and so forth, and it knows that they are children of the shown
     document, the library index.  From this information it generates "next
     chapter", "previous chapter" and "parent chapter" links.

   Document titles in the :dir:`toctree` will be automatically read from the
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

   If you want to have section numbers even in HTML output, give the toctree a
   ``numbered`` flag option.  For example::

      .. toctree::
         :numbered:

         foo
         bar

   Numbering then starts at the heading of ``foo``.  Sub-toctrees are
   automatically numbered (don't give the ``numbered`` flag to those).

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

   You can also give a "hidden" option to the directive, like this::

      .. toctree::
         :hidden:

         doc_1
         doc_2

   This will still notify Sphinx of the document hierarchy, but not insert links
   into the document at the location of the directive -- this makes sense if you
   intend to insert these links yourself, in a different style, or in the HTML
   sidebar.

   In the end, all documents in the :term:`source directory` (or subdirectories)
   must occur in some ``toctree`` directive; Sphinx will emit a warning if it
   finds a file that is not included, because that means that this file will not
   be reachable through standard navigation.  Use :confval:`unused_docs` to
   explicitly exclude documents from building, and :confval:`exclude_trees` to
   exclude whole directories.

   The "master document" (selected by :confval:`master_doc`) is the "root" of
   the TOC tree hierarchy.  It can be used as the documentation's main page, or
   as a "full table of contents" if you don't give a ``maxdepth`` option.

   .. versionchanged:: 0.3
      Added "globbing" option.

   .. versionchanged:: 0.6
      Added "numbered" and "hidden" options as well as external links and
      support for "self" references.


Special names
-------------

Sphinx reserves some document names for its own use; you should not try to
create documents with these names -- it will cause problems.

The special document names (and pages generated for them) are:

* ``genindex``, ``modindex``, ``search``

  These are used for the general index, the module index, and the search page,
  respectively.

  The general index is populated with entries from modules, all index-generating
  :ref:`description units <desc-units>`, and from :dir:`index` directives.

  The module index contains one entry per :dir:`module` directive.

  The search page contains a form that uses the generated JSON search index and
  JavaScript to full-text search the generated documents for search words; it
  should work on every major browser that supports modern JavaScript.

* every name beginning with ``_``

  Though only few such names are currently used by Sphinx, you should not create
  documents or document-containing directories with such names.  (Using ``_`` as
  a prefix for a custom template directory is fine.)


.. rubric:: Footnotes

.. [#] The ``maxdepth`` option does not apply to the LaTeX writer, where the
       whole table of contents will always be presented at the begin of the
       document, and its depth is controlled by the ``tocdepth`` counter, which
       you can reset in your :confval:`latex_preamble` config value using
       e.g. ``\setcounter{tocdepth}{2}``.

.. [#] A note on available globbing syntax: you can use the standard shell
       constructs ``*``, ``?``, ``[...]`` and ``[!...]`` with the feature that
       these all don't match slashes.  A double star ``**`` can be used to match
       any sequence of characters *including* slashes.
