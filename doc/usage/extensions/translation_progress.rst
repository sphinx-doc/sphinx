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

When none of the source words have been translated, the extension displays
a warning with a separate message. Documents without translation data and
fully translated documents are left unchanged.

The percentage is the ratio of translated source-language words, counted
before the translation replaces each element.  It is the same metric that
the ``|translation progress|`` substitution reports.

.. confval:: translation_progress_title
   :type: :code-py:`str`
   :default: ``'Translation progress'``

   The title of the note on partially translated pages.
   Fully untranslated pages use the standard, localized warning heading.

.. confval:: translation_progress_message
   :type: :code-py:`str`

   The message for a partially translated document. It defaults to
   ``'This page is {percentage} translated. Some content
   is still in the original language.'``

   The ``{percentage}`` placeholder is replaced by the percentage of
   source-language words in translated elements.

.. confval:: translation_progress_untranslated_message
   :type: :code-py:`str`

   The message shown when no source words have been translated.
   It defaults to ``'This page has not been translated yet and is displayed
   in the original language.'``

Both messages accept inline reStructuredText. For example, to include a
link to the translation project:

.. code-block:: python

   translation_progress_untranslated_message = (
       'This page has not been translated yet. '
       '`Help translate it <https://example.org/translations>`_.'
   )
