.. _ext-apidoc:

:mod:`sphinx.ext.apidoc` -- Generate API documentation from Python packages
===========================================================================

.. py:module:: sphinx.ext.apidoc
   :synopsis: Generate API documentation from Python modules

.. index:: pair: automatic; documentation
.. index:: pair: generation; documentation
.. index:: pair: generate; documentation

.. versionadded:: 8.2

.. role:: code-py(code)
   :language: Python

:mod:`sphinx.ext.apidoc` is a tool for automatic generation
of Sphinx sources from Python packages.
It provides the :program:`sphinx-apidoc` command-line tool as an extension,
allowing it to be run during the Sphinx build process.

The extension writes generated source files to a provided directory,
which are then read by Sphinx using the :mod:`sphinx.ext.autodoc` extension.

.. warning::

   :mod:`sphinx.ext.apidoc` generates source files that
   use :mod:`sphinx.ext.autodoc` to document all found modules.
   If any modules have side effects on import,
   these will be executed by ``autodoc`` when :program:`sphinx-build` is run.

   If you document scripts (as opposed to library modules),
   make sure their main routine is protected by
   an ``if __name__ == '__main__'`` condition.


Configuration
-------------

The apidoc extension uses the following configuration values:

.. confval:: apidoc_modules
   :type: :code-py:`Sequence[dict[str, Any]]`
   :default: :code-py:`()`

   A list or sequence of dictionaries describing modules to document.

   For example:

   .. code-block:: python

      apidoc_modules = [
          {'path': 'path/to/module', 'destination': 'source/'},
          {
              'path': 'path/to/another_module',
              'destination': 'source/',
              'exclude_patterns': ['**/test*'],
              'maxdepth': 4,
              'followlinks': False,
              'separatemodules': False,
              'includeprivate': False,
              'noheadings': False,
              'modulefirst': False,
              'implicit_namespaces': False,
              'automodule_options': {
                  'members', 'show-inheritance', 'undoc-members'
              },
          },
      ]


   Valid keys are:

   :code-py:`'path'`
     The path to the module to document (**required**).
     This must be absolute or relative to the configuration directory.

   :code-py:`'destination'`
     The output directory for generated files (**required**).
     This must be relative to the source directory,
     and will be created if it does not exist.

   :code-py:`'exclude_patterns'`
     See :confval:`apidoc_exclude_patterns`.

   :code-py:`'maxdepth'`
     See :confval:`apidoc_maxdepth`.

   :code-py:`'followlinks'`
     See :confval:`apidoc_followlinks`.

   :code-py:`'separatemodules'`
     See :confval:`apidoc_separatemodules`.

   :code-py:`'includeprivate'`
     See :confval:`apidoc_includeprivate`.

   :code-py:`'noheadings'`
     See :confval:`apidoc_noheadings`.

   :code-py:`'modulefirst'`
     See :confval:`apidoc_modulefirst`.

   :code-py:`'implicit_namespaces'`
     See :confval:`apidoc_implicit_namespaces`  

   :code-py:`'automodule_options'`
     See :confval:`apidoc_automodule_options`.  

The following configuration values are used as the defaults for all modules:

.. confval:: apidoc_exclude_patterns
   :type: :code-py:`Sequence[dict[str, Any]]`
   :default: :code-py:`()`

   A sequence of patterns to exclude from generation.
   These may be literal paths or :py:mod:`fnmatch`-style patterns.

.. confval:: apidoc_maxdepth
   :type: :code-py:`int`
   :default: :code-py:`4`

   The maximum depth of submodules to show in the generated table of contents.

.. confval:: apidoc_followlinks
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Follow symbolic links.

.. confval:: apidoc_separatemodules
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Put documentation for each module on an individual page.

.. confval:: apidoc_includeprivate
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Generate documentation for '_private' modules with leading underscores.

.. confval:: apidoc_noheadings
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Do not create headings for the modules/packages.
   Useful when source docstrings already contain headings.

.. confval:: apidoc_modulefirst
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Place module documentation before submodule documentation.

.. confval:: apidoc_implicit_namespaces
   :type: :code-py:`bool`
   :default: :code-py:`False`

   By default sphinx-apidoc processes sys.path searching for modules only.
   Python 3.3 introduced :pep:`420` implicit namespaces that allow module path
   structures such as ``foo/bar/module.py`` or ``foo/bar/baz/__init__.py``
   (notice that ``bar`` and ``foo`` are namespaces, not modules).

   Interpret module paths using :pep:`420` implicit namespaces.

.. confval:: apidoc_automodule_options
   :type: :code-py:`set[str]`
   :default: :code-py:`{'members', 'show-inheritance', 'undoc-members'}`

   Options to pass to generated :rst:dir:`automodule` directives.
