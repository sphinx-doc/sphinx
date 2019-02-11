.. highlight:: rest

:mod:`sphinx.ext.autosectionlabel` -- Allow reference sections using its title
==============================================================================

.. module:: sphinx.ext.autosectionlabel
   :synopsis: Allow reference section its title.

.. versionadded:: 1.4

This extension allows you to refer sections its title.  This affects to the
reference role (:rst:role:`ref`).

For example::

    A Plain Title
    -------------

    This is the text of the section.

    It refers to the section title, see :ref:`A Plain Title`.


Internally, this extension generates the labels for each section.  If same
section names are used in whole of document, any one is used for a target by
default. The ``autosectionlabel_prefix_document`` configuration variable can be
used to make headings which appear multiple times but in different documents
unique.


Configuration
-------------

.. confval:: autosectionlabel_prefix_document

   True to prefix each section label with the name of the document it is in,
   followed by a colon. For example, ``index:Introduction`` for a section
   called ``Introduction`` that appears in document ``index.rst``.  Useful for
   avoiding ambiguity when the same section heading appears in different
   documents.

.. confval:: autosectionlabel_maxdepth

   If set, autosectionlabel chooses the sections for labeling by its depth. For
   example, when set 1 to ``autosectionlabel_maxdepth``, labels are generated
   only for top level sections, and deeper sections are not labeled.  It
   defaults to ``None`` (disabled).
