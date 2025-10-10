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
documentation processing.  For a list of available builders, refer to
:doc:`/usage/builders/index`.

By default, everything that is outdated is built.  Output only for selected
files can be built by specifying individual filenames.

Options
-------

.. program:: sphinx-build

.. _make_mode:

.. option:: -M buildername

   Select a builder, using the *make-mode*.
   See :doc:`/usage/builders/index` for a list of all of Sphinx's built-in builders.
   Extensions can add their own builders.

   .. important::
      Sphinx only recognizes the ``-M`` option if it is used first, along with
      the source and output directories, before any other options are passed.
      For example::

          sphinx-build -M html ./source ./build --fail-on-warning

   The *make-mode* provides the same build functionality as
   a default :ref:`Makefile or Make.bat <makefile_options>`,
   and provides the following additional build pipelines:

   *latexpdf*
     Build LaTeX files and run them through :program:`pdflatex`, or as per
     :confval:`latex_engine` setting.
     If :confval:`language` is set to ``'ja'``, will use automatically
     the :program:`platex/dvipdfmx` latex to PDF pipeline.

   *info*
     Build Texinfo files and run them through :program:`makeinfo`.

   *help*
      Output a list of valid builder targets, and exit.

   .. note::

      The default output directory locations when using *make-mode*
      differ from the defaults when using :option:`-b`.

      * doctrees are saved to ``<outputdir>/doctrees``
      * output files are saved to ``<outputdir>/<builder name>``

   .. versionadded:: 1.2.1

.. option:: -b buildername, --builder buildername

   Selects a builder.

   See :doc:`/usage/builders/index` for a list of all of Sphinx's built-in builders.
   Extensions can add their own builders.

   .. versionchanged:: 7.3
      Add ``--builder`` long option.

.. option:: -a, --write-all

   If given, always write all output files. The default is to only write output
   files for new and changed source files. (This may not apply to all
   builders.)

   .. note:: This option does not re-read source files.
             To read and re-process every file,
             use :option:`--fresh-env` instead.

   .. versionchanged:: 7.3
      Add ``--write-all`` long option.

.. option:: -E, --fresh-env

   Don't use a saved :term:`environment` (the structure caching all
   cross-references), but rebuild it completely.  The default is to only read
   and parse source files that are new or have changed since the last run.

   .. versionchanged:: 7.3
      Add ``--fresh-env`` long option.

.. option:: -t tag, --tag tag

   Define the tag *tag*.
   This is relevant for :rst:dir:`only` directives that
   include their content only if certain tags are set.
   See :ref:`including content based on tags <tags>` for further detail.

   .. versionadded:: 0.6

   .. versionchanged:: 7.3
      Add ``--tag`` long option.

.. option:: -d path, --doctree-dir path

   Since Sphinx has to read and parse all source files before it can write an
   output file, the parsed source files are cached as "doctree pickles".
   Normally, these files are put in a directory called :file:`.doctrees` under
   the build directory; with this option you can select a different cache
   directory (the doctrees can be shared between all builders).

   .. versionchanged:: 7.3
      Add ``--doctree-dir`` long option.

.. option:: -j N, --jobs N

   Distribute the build over *N* processes in parallel, to make building on
   multiprocessor machines more effective.
   This feature only works on systems supporting "fork". Windows is not supported.
   Note that not all parts and not all builders of Sphinx can be parallelized.
   If ``auto`` argument is given,
   Sphinx uses the number of CPUs as *N*. Defaults to 1.

   .. versionadded:: 1.2
      This option should be considered *experimental*.

   .. versionchanged:: 1.7
      Support ``auto`` argument.

   .. versionchanged:: 6.2
      Add ``--jobs`` long option.

.. option:: -c path, --conf-dir path

   Don't look for the :file:`conf.py` in the source directory, but use the given
   configuration directory instead.  Note that various other files and paths
   given by configuration values are expected to be relative to the
   configuration directory, so they will have to be present at this location
   too.

   .. versionadded:: 0.3

   .. versionchanged:: 7.3
      Add ``--conf-dir`` long option.

.. option:: -C, --isolated

   Don't look for a configuration file; only take options via the :option:`--define` option.

   .. versionadded:: 0.5

   .. versionchanged:: 7.3
      Add ``--isolated`` long option.

.. option:: -D setting=value, --define setting=value

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

   .. versionchanged:: 7.3
      Add ``--define`` long option.

.. option:: -A name=value, --html-define name=value

   Make the *name* assigned to *value* in the HTML templates.

   .. versionadded:: 0.5

   .. versionchanged:: 7.3
      Add ``--html-define`` long option.

.. option:: -n, --nitpicky

   Run in nitpicky mode.  Currently, this generates warnings for all missing
   references.  See the config value :confval:`nitpick_ignore` for a way to
   exclude some references as "known missing".

   .. versionchanged:: 7.3
      Add ``--nitpicky`` long option.

.. option:: -N, --no-color

   Do not emit colored output.

   .. versionchanged:: 1.6
      Add ``--no-color`` long option.

.. option:: --color

   Emit colored output. Auto-detected by default.

   .. versionadded:: 1.6

.. option:: -v, --verbose

   Increase verbosity (log-level).  This option can be given up to three times
   to get more debug logging output.  It implies :option:`-T`.

   .. versionadded:: 1.2

   .. versionchanged:: 7.3
      Add ``--verbose`` long option.

.. option:: -q, --quiet

   Do not output anything on standard output, only write warnings and errors to
   standard error.

   .. versionchanged:: 7.3
      Add ``--quiet`` long option.

.. option:: -Q, --silent

   Do not output anything on standard output, also suppress warnings.  Only
   errors are written to standard error.

   .. versionchanged:: 7.3
      Add ``--silent`` long option.

.. option:: -w file, --warning-file file

   Write warnings (and errors) to the given file, in addition to standard error.

   .. versionchanged:: 7.3

      ANSI control sequences are stripped when writing to *file*.

   .. versionchanged:: 7.3
      Add ``--warning-file`` long option.

.. option:: -W, --fail-on-warning

   Turn warnings into errors.
   This means that :program:`sphinx-build` exits with exit status 1
   if any warnings are generated during the build.

   .. versionchanged:: 7.3
      Add ``--fail-on-warning`` long option.
   .. versionchanged:: 8.1
      :program:`sphinx-build` no longer exits on the first warning,
      but instead runs the entire build and exits with exit status 1
      if any warnings were generated.
      This behaviour was previously enabled with :option:`--keep-going`.

.. option:: --keep-going

   From Sphinx 8.1, :option:`!--keep-going` is always enabled.
   Previously, it was only applicable whilst using :option:`--fail-on-warning`,
   which by default exited :program:`sphinx-build` on the first warning.
   Using :option:`!--keep-going` runs :program:`sphinx-build` to completion
   and exits with exit status 1 if errors are encountered.

   .. versionadded:: 1.8
   .. versionchanged:: 8.1
      :program:`sphinx-build` no longer exits on the first warning,
      meaning that in effect :option:`!--keep-going` is always enabled.
      The option is retained for compatibility, but may be removed at some
      later date.

   .. xref RemovedInSphinx10Warning: deprecate this option in Sphinx 10
                                     or no earlier than 2026-01-01.

.. option:: -T, --show-traceback

   Display the full traceback when an unhandled exception occurs.  Otherwise,
   only a summary is displayed and the traceback information is saved to a file
   for further analysis.

   .. versionadded:: 1.2

   .. versionchanged:: 7.3
      Add ``--show-traceback`` long option.

.. option:: -P, --pdb

   (Useful for debugging only.)  Run the Python debugger, :mod:`pdb`, if an
   unhandled exception occurs while building.

   .. versionchanged:: 7.3
      Add ``--pdb`` long option.

.. option:: --exception-on-warning

   Raise an exception when a warning is emitted during the build.
   This can be useful in combination with :option:`--pdb` to debug warnings.

   .. versionadded:: 8.1

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

.. describe:: NO_COLOR

   When set (regardless of value), :program:`sphinx-build`  will not use color
   in terminal output. ``NO_COLOR`` takes precedence over ``FORCE_COLOR``. See
   `no-color.org <https://no-color.org/>`__ for other libraries supporting this
   community standard.

   .. versionadded:: 4.5.0

.. describe:: FORCE_COLOR

   When set (regardless of value), :program:`sphinx-build` will use color in
   terminal output. ``NO_COLOR`` takes precedence over ``FORCE_COLOR``.

   .. versionadded:: 4.5.0

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
