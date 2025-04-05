:mod:`sphinx.ext.duration` -- Measure durations of Sphinx processing
====================================================================

.. module:: sphinx.ext.duration
   :synopsis: Measure durations of Sphinx processing

.. versionadded:: 2.4

This extension measures durations of Sphinx processing and show its
result at end of the build.  It is useful for inspecting what document
is slowly built.

Configuration
=============

.. confval:: duration_options
   :type: :code-py:`dict[str, int]`
   :default: :code-py:`{'n_durations': 5}`

   A dictionary for configuring the behavior of the duration extension.

   The supported options are:

   * ``'n_durations'``: Maximum number of durations to show in the build summary.
     The durations are sorted in order from longest to shortest. Only the ``5`` slowest
     durations are shown by default. Set this to ``-1`` to show all durations.

   .. versionadded:: 8.3

Example configuration in `conf.py` to show all durations in the build summary

.. code-block:: python

   extensions = ['sphinx.ext.duration']
   duration_options = {'n_durations': -1}

   def setup(app):
       app.add_config_value('duration_options', duration_options, 'env')