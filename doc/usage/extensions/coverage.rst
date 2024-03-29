:mod:`sphinx.ext.coverage` -- Collect doc coverage stats
========================================================

.. module:: sphinx.ext.coverage
   :synopsis: Check Python modules and C API for coverage in the documentation.

This extension features one additional builder, the :class:`CoverageBuilder`.

.. class:: CoverageBuilder

   To use this builder, activate the coverage extension in your configuration
   file and give ``-M coverage`` on the command line.

.. todo:: Write this section.

Several configuration values can be used to specify what the builder
should check:

.. confval:: coverage_ignore_modules

.. confval:: coverage_ignore_functions

.. confval:: coverage_ignore_classes

.. confval:: coverage_ignore_pyobjects

   List of `Python regular expressions`_.

   If any of these regular expressions matches any part of the full import path
   of a Python object, that Python object is excluded from the documentation
   coverage report.

   .. _Python regular expressions: https://docs.python.org/library/re

   .. versionadded:: 2.1

.. confval:: coverage_c_path

.. confval:: coverage_c_regexes

.. confval:: coverage_ignore_c_items

.. confval:: coverage_write_headline

   Set to ``False`` to not write headlines.

   .. versionadded:: 1.1

.. confval:: coverage_skip_undoc_in_source

   Skip objects that are not documented in the source with a docstring.
   ``False`` by default.

   .. versionadded:: 1.1

.. confval:: coverage_show_missing_items

   Print objects that are missing to standard output also.
   ``False`` by default.

   .. versionadded:: 3.1

.. confval:: coverage_statistics_to_report

   Print a tabular report of the coverage statistics to the coverage report.
   ``True`` by default.

   Example output:

   .. code-block:: text

      +-----------------------+----------+--------------+
      | Module                | Coverage | Undocumented |
      +=======================+==========+==============+
      | package.foo_module    | 100.00%  | 0            |
      +-----------------------+----------+--------------+
      | package.bar_module    | 83.33%   | 1            |
      +-----------------------+----------+--------------+

   .. versionadded:: 7.2

.. confval:: coverage_statistics_to_stdout

   Print a tabular report of the coverage statistics to standard output.
   ``False`` by default.

   Example output:

   .. code-block:: text

      +-----------------------+----------+--------------+
      | Module                | Coverage | Undocumented |
      +=======================+==========+==============+
      | package.foo_module    | 100.00%  | 0            |
      +-----------------------+----------+--------------+
      | package.bar_module    | 83.33%   | 1            |
      +-----------------------+----------+--------------+

   .. versionadded:: 7.2
