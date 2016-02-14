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
section names are used in whole of document, any one is used for a target.
