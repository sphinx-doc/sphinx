.. _invocation:

Invocation of sphinx-build
==========================

The :program:`sphinx-build` script builds a Sphinx documentation set.  It is
called like this::

     $ sphinx-build [options] sourcedir builddir [filenames]

where *sourcedir* is the :term:`source directory`, and *builddir* is the
directory in which you want to place the built documentation.  Most of the time,
you don't need to specify any *filenames*.

The :program:`sphinx-build` script has several options:

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

   See :ref:`builders` for a list of all builders shipped with Sphinx.
   Extensions can add their own builders.

.. option:: -a

   If given, always write all output files.  The default is to only write output
   files for new and changed source files.  (This may not apply to all
   builders.)

.. option:: -E

   Don't use a saved :term:`environment` (the structure caching all
   cross-references), but rebuild it completely.  The default is to only read
   and parse source files that are new or have changed since the last run.

.. option:: -t tag

   Define the tag *tag*.  This is relevant for :rst:dir:`only` directives that only
   include their content if this tag is set.

   .. versionadded:: 0.6

.. option:: -d path

   Since Sphinx has to read and parse all source files before it can write an
   output file, the parsed source files are cached as "doctree pickles".
   Normally, these files are put in a directory called :file:`.doctrees` under
   the build directory; with this option you can select a different cache
   directory (the doctrees can be shared between all builders).

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
   must be a string or dictionary value.  For the latter, supply the setting
   name and key like this: ``-D latex_elements.docclass=scrartcl``.  For boolean
   values, use ``0`` or ``1`` as the value.

   .. versionchanged:: 0.6
      The value can now be a dictionary value.

.. option:: -A name=value

   Make the *name* assigned to *value* in the HTML templates.

   .. versionadded:: 0.5

.. option:: -n

   Run in nit-picky mode.  Currently, this generates warnings for all missing
   references.

.. option:: -N

   Do not emit colored output.  (On Windows, colored output is disabled in any
   case.)

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

.. option:: -P

   (Useful for debugging only.)  Run the Python debugger, :mod:`pdb`, if an
   unhandled exception occurs while building.


You can also give one or more filenames on the command line after the source and
build directories.  Sphinx will then try to build only these output files (and
their dependencies).


Makefile options
----------------

The :file:`Makefile` and :file:`make.bat` files created by
:program:`sphinx-quickstart` usually run :program:`sphinx-build` only with the
:option:`-b` and :option:`-d` options.  However, they support the following
variables to customize behavior:

.. describe:: PAPER

   The value for :confval:`latex_paper_size`.

.. describe:: SPHINXBUILD

   The command to use instead of ``sphinx-build``.

.. describe:: BUILDDIR

   The build directory to use instead of the one chosen in
   :program:`sphinx-quickstart`.

.. describe:: SPHINXOPTS

   Additional options for :program:`sphinx-build`.


.. _invocation-apidoc:

Invocation of sphinx-apidoc
===========================

The :program:`sphinx-apidoc` generates completely automatic API documentation
for a Python package.  It is called like this::

     $ sphinx-apidoc [options] -o outputdir packagedir [pathnames]

where *packagedir* is the path to the package to document, and *outputdir* is
the directory where the generated sources are placed.  Any *pathnames* given
are paths to be excluded ignored during generation.

The :program:`sphinx-apidoc` script has several options:

.. program:: sphinx-apidoc

.. option:: -o outputdir

   Gives the directory in which to place the generated output.

.. option:: -f, --force

   Normally, sphinx-apidoc does not overwrite any files.  Use this option to
   force the overwrite of all files that it generates.

.. option:: -n, --dry-run

   With this option given, no files will be written at all.

.. option:: -s suffix

   This option selects the file name suffix of output files.  By default, this
   is ``rst``.

.. option:: -d maxdepth

   This sets the maximum depth of the table of contents, if one is generated.

.. option:: -T, --no-toc

   This prevents the generation of a table-of-contents file ``modules.rst``.
   This has no effect when :option:`--full` is given.

.. option:: -F, --full

   This option makes sphinx-apidoc create a full Sphinx project, using the same
   mechanism as :program:`sphinx-quickstart`.  Most configuration values are set
   to default values, but you can influence the most important ones using the
   following options.

.. option:: -H project

   Sets the project name to put in generated files (see :confval:`project`).

.. option:: -A author

   Sets the author name(s) to put in generated files (see :confval:`copyright`).

.. option:: -V version

   Sets the project version to put in generated files (see :confval:`version`).

.. option:: -R release

   Sets the project release to put in generated files (see :confval:`release`).
