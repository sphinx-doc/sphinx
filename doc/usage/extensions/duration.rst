:mod:`sphinx.ext.duration` -- Measure durations of Sphinx processing
====================================================================

.. module:: sphinx.ext.duration
   :synopsis: Measure durations of Sphinx processing

.. versionadded:: 2.4

This extension measures durations of Sphinx processing when reading
documents and is useful for inspecting what document is slowly built.
Durations are printed to console at the end of the build and saved
to a JSON file in the output directory by default.

Enable this extension by adding ``'sphinx.ext.duration'`` to
the :confval:`extensions` list in your :file:`conf.py`:

.. code-block:: python

    extensions = [
        ...
        'sphinx.ext.duration',
    ]


Configuration
-------------

.. confval:: duration_print_total
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Show the total reading duration in the build summary, e.g.:

   .. code-block:: text

      ====================== total reading duration ==========================
      Total time reading 31 files: 0m 3.142s

   .. versionadded:: 9.0

.. confval:: duration_print_slowest
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Show the slowest durations in the build summary.
   The durations are sorted in order from slowest to fastest.
   This prints up to :confval:`duration_n_slowest` durations, e.g.:

   .. code-block:: text

      ====================== slowest 5 reading durations =======================
      0.012s spam
      0.011s ham
      0.011s eggs
      0.006s lobster
      0.005s beans

   .. versionadded:: 9.0

.. confval:: duration_n_slowest
   :type: :code-py:`int`
   :default: :code-py:`5`

   Maximum number of slowest durations to show in the build summary
   when :confval:`duration_print_slowest` is enabled.
   By default, only the ``5`` slowest durations are shown.
   Set this to ``0`` to show all durations.

   .. versionadded:: 9.0

.. confval:: duration_write_json
   :type: :code-py:`str | None`
   :default: :code-py:`'sphinx-reading-durations.json'`

   Write all reading durations to a JSON file in the output directory
   The file contents are a map of the document names to reading durations,
   where document names are strings and durations are floats in seconds.
   Set this value to an empty string or ``None`` to disable writing the file,
   or set it to a relative path to customize it.

   This may be useful for testing and setting a limit on reading times.

   .. versionadded:: 9.0

.. confval:: duration_limit
   :type: :code-py:`float | int | None`
   :default: :code-py:`None`

   Set a duration limit (in seconds) for reading a document.
   If any duration exceeds this value, a warning is emitted.

   .. versionadded:: 9.0
