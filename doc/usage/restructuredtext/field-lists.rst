.. highlight:: rst

===========
Field Lists
===========

:ref:`As previously discussed <rst-field-lists>`, field lists are sequences of
fields marked up like this::

    :fieldname: Field content

Sphinx extends standard docutils behavior for field lists and adds some extra
functionality that is covered in this section.

.. note::

    The values of field lists will be parsed as
    strings. You cannot use Python collections such as lists or dictionaries.


.. _metadata:

File-wide metadata
------------------

A field list near the top of a file is normally parsed by docutils as the
*docinfo* and shown on the page.  However, in Sphinx, a field list preceding
any other markup is moved from the *docinfo* to the Sphinx environment as
document metadata, and is not displayed in the output.

.. note::

   A field list appearing after the document title *will* be part of the
   *docinfo* as normal and will be displayed in the output.


Special metadata fields
-----------------------

Sphinx provides custom behavior for bibliographic fields compared to docutils.

At the moment, these metadata fields are recognized:

``tocdepth``
   The maximum depth for a table of contents of this file. ::

       :tocdepth: 2

   .. note::

      This metadata affects the depth of the local toctree.  But it does not
      affect the depth of the *global* toctree.  So this does not change
      the sidebar of themes that use the global toctree.

   .. versionadded:: 0.4

``nocomments``
   If set, the web application won't display a comment form for a page
   generated from this source file. ::

       :nocomments:

``orphan``
   If set, warnings about this file not being included in any toctree will be
   suppressed. ::

       :orphan:

   .. versionadded:: 1.0

``no-search``
   Disable full text search for this document.

   .. code-block:: rst

      :no-search:

   .. note::
      The ``:no-search:`` option only disables full text search,
      meaning that object search will still be available even if
      ``:no-search:`` is set.

   .. versionadded:: 3.0

   .. versionchanged:: 7.3

      The file-wide metadata option ``:nosearch:`` was renamed
      to ``:no-search:``.
      The previous name has been retained as an alias,
      but will be deprecated and removed
      in a future version of Sphinx.
