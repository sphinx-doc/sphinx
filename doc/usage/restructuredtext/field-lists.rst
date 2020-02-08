.. highlight:: rst

===========
Field Lists
===========

:ref:`As previously discussed <rst-field-lists>`, field lists are sequences of
fields marked up like this::

    :fieldname: Field content

Sphinx provides custom behavior for bibliographic fields compared to docutils.

.. _metadata:

File-wide metadata
------------------

A field list near the top of a file is normally parsed by docutils as the
*docinfo* which is generally used to record the author, date of publication and
other metadata.  However, in Sphinx, a field list preceding any other markup is
moved from the *docinfo* to the Sphinx environment as document metadata and is
not displayed in the output; a field list appearing after the document title
will be part of the *docinfo* as normal and will be displayed in the output.

At the moment, these metadata fields are recognized:

``tocdepth``
   The maximum depth for a table of contents of this file. ::

       :tocdepth: 2

   .. note::

      This metadata effects to the depth of local toctree.  But it does not
      effect to the depth of *global* toctree.  So this would not be change
      the sidebar of some themes which uses global one.

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
