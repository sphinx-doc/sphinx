:mod:`sphinx.ext.duration` -- Measure durations of Sphinx processing
====================================================================

.. module:: sphinx.ext.duration
   :synopsis: Measure durations of Sphinx processing

.. versionadded:: 2.4

This extension measures durations of Sphinx processing and is useful
for inspecting what document is slowly built. Durations are printed
to console at end of the build and a JSON file ``sphinx_reading_durations.json``
with durations is also saved to the output directory by default.

Enable this extension by adding it to ``conf.py``:

.. code-block:: python

   extensions = ['sphinx.ext.duration']


Configuration
=============

.. confval:: duration_print_slowest
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Show the slowest durations in the build summary, e.g.:

    .. code-block:: shell

        ====================== slowest 5 reading durations =======================
        0.012s toctree
        0.011s admonitions
        0.011s refs
        0.006s docfields
        0.005s figure

.. confval:: duration_n_slowest
   :type: :code-py:`int`
   :default: :code-py:`5`

   Maximum number of slowest durations to show in the build summary.
   The durations are sorted in order from slow to fast. Only the ``5`` slowest
   durations are shown by default. Set this to ``0`` to show all durations.

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
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Write the reading durations ``dict`` to a JSON file in the output directory.
   The ``dict`` contains file paths relative to ``outdir`` and durations in seconds.

   The file may be read and used for testing purposes, e.g.:

   .. code-block:: python

      import json

      with open( 'sphinx_reading_durations.json', 'r') as file:
          reading_durations = json.load(file)

   .. versionadded:: 8.3
