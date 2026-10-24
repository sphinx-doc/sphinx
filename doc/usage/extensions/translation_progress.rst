=====================
Translation progress
=====================

.. py:module:: sphinx.ext.translation_progress
   :synopsis: Report translation progress for documents

The :mod:`sphinx.ext.translation_progress` extension adds a note after the
title of a document when its translation is incomplete.  The note reports
the percentage of source-language words in translatable elements that have
been translated.

Enable the extension in :confval:`extensions`:

.. code-block:: python

   extensions = ['sphinx.ext.translation_progress']

The extension only adds a note when a translated document has at least one
untranslated element.  Documents without translation data and fully
translated documents are left unchanged.

.. confval:: translation_progress_title
   :type: :class:`str`
   :default: ``'Translation progress'``

   The title of the translation progress note.

.. confval:: translation_progress_message
   :type: :class:`str`
   :default: ``'This page is {percentage} translated based on word count. Some content is still in the original language.'``

   The message shown in the translation progress note.  The
   ``{percentage}`` placeholder is replaced by the percentage of
   source-language words in translated elements.
