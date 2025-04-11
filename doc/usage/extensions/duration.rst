:mod:`sphinx.ext.duration` -- Measure durations of Sphinx processing
====================================================================

.. module:: sphinx.ext.duration
   :synopsis: Measure durations of Sphinx processing

.. versionadded:: 2.4

This extension measures durations of Sphinx processing and is useful
for inspecting what document is slowly built. Durations are printed
to console at the end of the build and saved to a JSON file in the
:attr:`~sphinx.application.Sphinx.outdir` by default.

Enable this extension by adding it to your :confval:`extensions`
configuration.

.. code-block:: python

    extensions = [
        ...
        'sphinx.ext.duration',
    ]

Configuration
=============

.. confval:: duration_print_slowest
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Show the slowest durations in the build summary. The durations
   are sorted in order from slow to fast. This prints up to
   :confval:`duration_n_slowest` durations to the console, e.g.:

   .. code-block:: shell

      ====================== slowest 5 reading durations =======================
      0.012s toctree
      0.011s admonitions
      0.011s refs
      0.006s docfields
      0.005s figure

   .. versionadded:: 8.3

.. confval:: duration_n_slowest
   :type: :code-py:`int`
   :default: :code-py:`5`

   Maximum number of slowest durations to show in the build summary
   when :confval:`duration_print_slowest` is enabled. Only the ``5``
   slowest durations are shown by default. Set this to ``0`` to show
   all durations.

   .. versionadded:: 8.3

.. confval:: duration_print_total
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Show the total reading duration in the build summary, e.g.:

   .. code-block:: shell

      ====================== total reading duration ==========================
      Total time reading 31 files:

      minutes:        0
      seconds:        3
      milliseconds: 142

   .. versionadded:: 8.3

.. confval:: duration_write_json
   :type: :code-py:`str | bool`
   :default: :code-py:`'sphinx_reading_durations.json'`

   Write all reading durations to a JSON file in the output directory.
   The file contents are dict-like and contain the document file paths
   (relative to ``outdir``) as and reading durations in seconds as
   values. Set this value to an empty string or ``False`` to disable
   writing the file, or set it to a relative path to customize it.

   This may be useful for testing and setting a limit on reading times.

   .. versionadded:: 8.3
