.. highlight:: rst

:mod:`sphinx.ext.autosectionlabel` -- Allow referencing sections by their title
===============================================================================

.. module:: sphinx.ext.autosectionlabel
   :synopsis: Allow referencing sections by their title.

.. versionadded:: 1.4

.. role:: code-py(code)
   :language: Python

By default, cross-references to sections use labels (see :rst:role:`ref`).
This extension allows you to instead refer to sections by their title.

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
   :type: :code-py:`bool`
   :default: :code-py:`False`

   True to prefix each section label with the name of the document it is in,
   followed by a colon. For example, ``index:Introduction`` for a section
   called ``Introduction`` that appears in document ``index.rst``.  Useful for
   avoiding ambiguity when the same section heading appears in different
   documents.

.. confval:: autosectionlabel_maxdepth
   :type: :code-py:`int | None`
   :default: :code-py:`None`

   If set, autosectionlabel chooses the sections for labeling by its depth. For
   example, when set 1 to ``autosectionlabel_maxdepth``, labels are generated
   only for top level sections, and deeper sections are not labeled.  It
   defaults to ``None`` (i.e. all sections are labeled).


Debugging
---------

The ``WARNING: undefined label`` indicates that your reference in
:rst:role:`ref` is mis-spelled. Invoking :program:`sphinx-build` with ``-vvv``
(see :option:`-v`) will print all section names and the labels that have been
generated for them. This output can help finding the right reference label.
