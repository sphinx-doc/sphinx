.. highlight:: rest

.. _concepts:

Sphinx concepts
===============

Document names
--------------

Since the reST source files can have different extensions (some people like
``.txt``, some like ``.rst`` -- the extension can be configured with
:confval:`source_suffix`) and different OSes have different path separators,
Sphinx abstracts them: all "document names" are relative to the
:term:`documentation root`, the extension is stripped, and path separators are
converted to slashes.  All values, parameters and suchlike referring to
"documents" expect such a document name.


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
   tree; by default, all levels are included.

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

   In the end, all documents under the :term:`documentation root` must occur in
   one ``toctree`` directive; Sphinx will emit a warning if it finds a file that
   is not included, because that means that this file will not be reachable
   through standard navigation.  Use :confval:`unused_documents` to explicitly
   exclude documents from this check.

   The "master document" (selected by :confval:`master_doc`) is the "root" of
   the TOC tree hierarchy.  It can be used as the documentation's main page, or
   as a "full table of contents" if you don't give a ``maxdepth`` option.
