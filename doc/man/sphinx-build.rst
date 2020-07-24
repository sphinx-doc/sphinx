sphinx-build
============

Synopsis
--------

**sphinx-build** [*options*] <*sourcedir*> <*outputdir*> [*filenames* ...]

Description
-----------

:program:`sphinx-build` generates documentation from the files in
``<sourcedir>`` and places it in the ``<outputdir>``.

:program:`sphinx-build` looks for ``<sourcedir>/conf.py`` for the configuration
settings.  :manpage:`sphinx-quickstart(1)` may be used to generate template
files, including ``conf.py``.

:program:`sphinx-build` can create documentation in different formats.  A
format is selected by specifying the builder name on the command line; it
defaults to HTML.  Builders can also perform other tasks related to
documentation processing.

By default, everything that is outdated is built.  Output only for selected
files can be built by specifying individual filenames.

For a list of available options, refer to :option:`sphinx-build -b`.

Options
-------

.. program:: sphinx-build

.. option:: -b buildername

   The most important option: it selects a builder.  The most common builders
   are:

   **html**
      Build HTML pages.  This is the default builder.

   **dirhtml**
      Build HTML pages, but with a single directory per document.  Makes for
      prettier URLs (no ``.html``) if served from a webserver.

   **singlehtml**
      Build a single HTML with the whole content.

   **htmlhelp**, **qthelp**, **devhelp**, **epub**
      Build HTML files with additional information for building a documentation
      collection in one of these formats.

   **applehelp**
      Build an Apple Help Book.  Requires :program:`hiutil` and
      :program:`codesign`, which are not Open Source and presently only
      available on Mac OS X 10.6 and higher.

   **latex**
      Build LaTeX sources that can be compiled to a PDF document using
      :program:`pdflatex`.

   **man**
      Build manual pages in groff format for UNIX systems.

   **texinfo**
      Build Texinfo files that can be processed into Info files using
      :program:`makeinfo`.

   **text**
      Build plain text files.

   **gettext**
      Build gettext-style message catalogs (``.pot`` files).

   **doctest**
      Run all doctests in the documentation, if the :mod:`~sphinx.ext.doctest`
      extension is enabled.

   **linkcheck**
      Check the integrity of all external links.

   **xml**
     Build Docutils-native XML files.

   **pseudoxml**
     Build compact pretty-printed "pseudo-XML" files displaying the
     internal structure of the intermediate document trees.

   See :doc:`/usage/builders/index` for a list of all builders shipped with
   Sphinx.  Extensions can add their own builders.

.. _make_mode:

.. option:: -M buildername

   Alternative to :option:`-b`. Uses the Sphinx :program:`make_mode` module,
   which provides the same build functionality as a default :ref:`Makefile or
   Make.bat <makefile_options>`. In addition to all Sphinx
   :doc:`/usage/builders/index`, the following build pipelines are available:

   **latexpdf**
     Build LaTeX files and run them through :program:`pdflatex`, or as per
     :confval:`latex_engine` setting.
     If :confval:`language` is set to ``'ja'``, will use automatically
     the :program:`platex/dvipdfmx` latex to PDF pipeline.

   **info**
     Build Texinfo files and run them through :program:`makeinfo`.

   .. important::
      Sphinx only recognizes the ``-M`` option if it is placed first.

   .. versionadded:: 1.2.1

.. option:: -a

   If given, always write all output files. The default is to only write output
   files for new and changed source files. (This may not apply to all
   builders.)

.. option:: -E

   Don't use a saved :term:`environment` (the structure caching all
   cross-references), but rebuild it completely.  The default is to only read
   and parse source files that are new or have changed since the last run.

.. option:: -t tag

   Define the tag *tag*.  This is relevant for :rst:dir:`only` directives that
   only include their content if this tag is set.

   .. versionadded:: 0.6

.. option:: -d path

   Since Sphinx has to read and parse all source files before it can write an
   output file, the parsed source files are cached as "doctree pickles".
   Normally, these files are put in a directory called :file:`.doctrees` under
   the build directory; with this option you can select a different cache
   directory (the doctrees can be shared between all builders).

.. option:: -j N

   Distribute the build over *N* processes in parallel, to make building on
   multiprocessor machines more effective.  Note that not all parts and not all
   builders of Sphinx can be parallelized.  If ``auto`` argument is given,
   Sphinx uses the number of CPUs as *N*.

   .. versionadded:: 1.2
      This option should be considered *experimental*.

   .. versionchanged:: 1.7
      Support ``auto`` argument.

.. option:: -c path

   Don't look for the :file:`conf.py` in the source directory, but use the given
   configuration directory instead.  Note that various other files and paths
   given by configuration values are expected to be relative to the
   configuration directory, so they will have to be present at this location
   too.

   .. versionadded:: 0.3

.. option:: -C

   Don't look for a configuration file; only take options via the ``-D`` option.

   .. versionadded:: 0.5

.. option:: -D setting=value

   Override a configuration value set in the :file:`conf.py` file.  The value
   must be a number, string, list or dictionary value.

   For lists, you can separate elements with a comma like this: ``-D
   html_theme_path=path1,path2``.

   For dictionary values, supply the setting name and key like this:
   ``-D latex_elements.docclass=scrartcl``.

   For boolean values, use ``0`` or ``1`` as the value.

   .. versionchanged:: 0.6
      The value can now be a dictionary value.

   .. versionchanged:: 1.3
      The value can now also be a list value.

.. option:: -A name=value

   Make the *name* assigned to *value* in the HTML templates.

   .. versionadded:: 0.5

.. option:: -n

   Run in nit-picky mode.  Currently, this generates warnings for all missing
   references.  See the config value :confval:`nitpick_ignore` for a way to
   exclude some references as "known missing".

.. option:: -N

   Do not emit colored output.

.. option:: -v

   Increase verbosity (loglevel).  This option can be given up to three times
   to get more debug logging output.  It implies :option:`-T`.

   .. versionadded:: 1.2

.. option:: -q

   Do not output anything on standard output, only write warnings and errors to
   standard error.

.. option:: -Q

   Do not output anything on standard output, also suppress warnings.  Only
   errors are written to standard error.

.. option:: -w file

   Write warnings (and errors) to the given file, in addition to standard error.

.. option:: -W

   Turn warnings into errors.  This means that the build stops at the first
   warning and ``sphinx-build`` exits with exit status 1.

.. option:: --keep-going

   With -W option, keep going processing when getting warnings to the end
   of build, and ``sphinx-build`` exits with exit status 1.

   .. versionadded:: 1.8

.. option:: -T

   Display the full traceback when an unhandled exception occurs.  Otherwise,
   only a summary is displayed and the traceback information is saved to a file
   for further analysis.

   .. versionadded:: 1.2

.. option:: -P

   (Useful for debugging only.)  Run the Python debugger, :mod:`pdb`, if an
   unhandled exception occurs while building.

.. option:: -h, --help, --version

   Display usage summary or Sphinx version.

   .. versionadded:: 1.2

You can also give one or more filenames on the command line after the source
and build directories. Sphinx will then try to build only these output files
(and their dependencies).

Environment Variables
---------------------

The :program:`sphinx-build` refers following environment variables:

.. describe:: MAKE

   A path to make command.  A command name is also allowed.
   :program:`sphinx-build` uses it to invoke sub-build process on make-mode.

.. _makefile_options:

.. rubric:: Makefile Options

The :file:`Makefile` and :file:`make.bat` files created by
:program:`sphinx-quickstart` usually run :program:`sphinx-build` only with the
:option:`-b` and :option:`-d` options.  However, they support the following
variables to customize behavior:

.. describe:: PAPER

   This sets the ``'papersize'`` key of :confval:`latex_elements`:
   i.e. ``PAPER=a4`` sets it to ``'a4paper'`` and ``PAPER=letter`` to
   ``'letterpaper'``.

   .. note::

      Usage of this environment variable got broken at Sphinx 1.5 as
      ``a4`` or ``letter`` ended up as option to LaTeX document in
      place of the needed ``a4paper``, resp. ``letterpaper``.  Fixed at
      1.7.7.

.. describe:: SPHINXBUILD

   The command to use instead of ``sphinx-build``.

.. describe:: BUILDDIR

   The build directory to use instead of the one chosen in
   :program:`sphinx-quickstart`.

.. describe:: SPHINXOPTS

   Additional options for :program:`sphinx-build`. These options can
   also be set via the shortcut variable **O** (capital 'o').

.. _when-deprecation-warnings-are-displayed:

Deprecation Warnings
--------------------

If any deprecation warning like ``RemovedInSphinxXXXWarning`` are displayed
when building a user's document, some Sphinx extension is using deprecated
features. In that case, please report it to author of the extension.

To disable the deprecation warnings, please set ``PYTHONWARNINGS=`` environment
variable to your environment. For example:

* ``PYTHONWARNINGS= make html`` (Linux/Mac)
* ``export PYTHONWARNINGS=`` and do ``make html`` (Linux/Mac)
* ``set PYTHONWARNINGS=`` and do ``make html`` (Windows)
* modify your Makefile/make.bat and set the environment variable

See also
--------

:manpage:`sphinx-quickstart(1)`
