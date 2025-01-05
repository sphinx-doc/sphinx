:mod:`sphinx.ext.coverage` -- Collect doc coverage stats
========================================================

.. module:: sphinx.ext.coverage
   :synopsis: Check Python modules and C API for coverage in the documentation.

This extension features one additional builder, the :class:`CoverageBuilder`.

.. todo:: Write this section.

.. note::

   The :doc:`sphinx-apidoc </man/sphinx-apidoc>` command can be used to
   automatically generate API documentation for all code in a project,
   avoiding the need to manually author these documents and keep them up-to-date.

.. warning::

   :mod:`~sphinx.ext.coverage` **imports** the modules to be documented.
   If any modules have side effects on import,
   these will be executed by the coverage builder when ``sphinx-build`` is run.

   If you document scripts (as opposed to library modules),
   make sure their main routine is protected by a
   ``if __name__ == '__main__'`` condition.

.. note::

   For Sphinx (actually, the Python interpreter that executes Sphinx)
   to find your module, it must be importable.
   That means that the module or the package must be in
   one of the directories on :data:`sys.path` -- adapt your :data:`sys.path`
   in the configuration file accordingly.

To use this builder, activate the coverage extension in your configuration file
and run ``sphinx-build -M coverage`` on the command line.


Builder
-------

.. py:class:: CoverageBuilder


Configuration
-------------

Several configuration values can be used to specify
what the builder should check:

.. confval:: coverage_modules
   :type: ``list[str]``
   :default: ``[]``

   List of Python packages or modules to test coverage for.
   When this is provided, Sphinx will introspect each package
   or module provided in this list as well
   as all sub-packages and sub-modules found in each.
   When this is not provided, Sphinx will only provide coverage
   for Python packages and modules that it is aware of:
   that is, any modules documented using the :rst:dir:`py:module` directive
   provided in the :doc:`Python domain </usage/domains/python>`
   or the :rst:dir:`automodule` directive provided by the
   :mod:`~sphinx.ext.autodoc` extension.

   .. versionadded:: 7.4

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
