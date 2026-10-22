=====================
Translation progress
=====================

The :mod:`sphinx.ext.translation_progress` extension adds a note after the
title of a document when its translation is incomplete.  The note reports
the percentage of translatable elements that have been translated.

Enable the extension in :confval:`extensions`:

.. code-block:: python

   extensions = ['sphinx.ext.translation_progress']

The extension only adds a note when a translated document has at least one
untranslated element.  Documents without translation data and fully
translated documents are left unchanged.
