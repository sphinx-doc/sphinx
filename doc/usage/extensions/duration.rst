:mod:`sphinx.ext.duration` -- Measure durations of Sphinx processing
====================================================================

.. module:: sphinx.ext.duration
   :synopsis: Measure durations of Sphinx processing

.. versionadded:: 2.4

This extension measures durations of Sphinx processing and show its
result at end of the build. It is useful for inspecting what document
is slowly built. Enable this extension by adding it to ``conf.py``:

.. code-block:: python

   extensions = ['sphinx.ext.duration']

Optionally, configure the extension by adding ``duration_options`` as a config value.
In ``conf.py``:

.. code-block:: python

   extensions = ['sphinx.ext.duration']

   # disable printing totals and writing durations
   # and only show the 10 slowest times
   duration_options = {
       'print_total': False,
       'print_slowest' : True,
       'durations': 10,
       'write_json' : False,
   }

   def setup(app):
       app.add_config_value('duration_options', duration_options, 'env')


Configuration
=============

.. confval:: duration_print_slowest
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Show the slowest durations in the build summary.

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

   Show the total reading duration in the build summary.

   .. versionadded:: 8.3

.. confval:: duration_write_json
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Write all reading durations to a JSON file ``reading_durations.json``
   in the build directory. File paths and durations (in seconds) are saved as
   keys and values, respectively.

   .. versionadded:: 8.3
