Introduction
============

This is the documentation for the Sphinx documentation builder.  Sphinx is a
tool that translates a set of reStructuredText_ source files into various output
formats, automatically producing cross-references, indices etc.  That is, if
you have a directory containing a bunch of reST-formatted documents (and
possibly subdirectories of docs in there as well), Sphinx can generate a
nicely-organized arrangement of HTML files (in some other directory) for easy
browsing and navigation.  But from the same source, it can also generate a
LaTeX file that you can compile into a PDF version of the documents.

The focus is on hand-written documentation, rather than auto-generated API docs.
Though there is limited support for that kind of docs as well (which is intended
to be freely mixed with hand-written content), if you need pure API docs have a
look at `Epydoc <http://epydoc.sf.net/>`_, which also understands reST.


Conversion from other systems
-----------------------------

This section is intended to collect helpful hints for those wanting to migrate
to reStructuredText/Sphinx from other documentation systems.

* Gerard Flanagan has written a script to convert pure HTML to reST; it can be
  found at `BitBucket
  <http://bitbucket.org/djerdo/musette/src/tip/musette/html/html2rest.py>`_.

* For converting the old Python docs to Sphinx, a converter was written which
  can be found at `the Python SVN repository
  <http://svn.python.org/projects/doctools/converter>`_.  It contains generic
  code to convert Python-doc-style LaTeX markup to Sphinx reST.

* Marcin Wojdyr has written a script to convert Docbook to reST with Sphinx
  markup; it is at `Google Code <http://code.google.com/p/db2rst/>`_.


Prerequisites
-------------

Sphinx needs at least **Python 2.4** to run.  If you like to have source code
highlighting support, you must also install the Pygments_ library, which you can
do via setuptools' easy_install.  Sphinx should work with docutils version 0.4
or some (not broken) SVN trunk snapshot.

.. _reStructuredText: http://docutils.sf.net/rst.html
.. _Pygments: http://pygments.org


Setting up the documentation sources
------------------------------------

The root directory of a documentation collection is called the :dfn:`source
directory`.  Normally, this directory also contains the Sphinx configuration
file :file:`conf.py`, but that file can also live in another directory, the
:dfn:`configuration directory`.

.. versionadded:: 0.3
   Support for a different configuration directory.

Sphinx comes with a script called :program:`sphinx-quickstart` that sets up a
source directory and creates a default :file:`conf.py` from a few questions it
asks you.  Just run ::

   $ sphinx-quickstart

and answer the questions.


Running a build
---------------

A build is started with the :program:`sphinx-build` script.  It is called
like this::

     $ sphinx-build -b latex sourcedir builddir

where *sourcedir* is the :term:`source directory`, and *builddir* is the
directory in which you want to place the built documentation (it must be an
existing directory).  The :option:`-b` option selects a builder; in this example
Sphinx will build LaTeX files.

The :program:`sphinx-build` script has several more options:

**-a**
   If given, always write all output files.  The default is to only write output
   files for new and changed source files.  (This may not apply to all
   builders.)

**-E**
   Don't use a saved :term:`environment` (the structure caching all
   cross-references), but rebuild it completely.  The default is to only read
   and parse source files that are new or have changed since the last run.

**-t** *tag*
   Define the tag *tag*.  This is relevant for :dir:`only` directives that only
   include their content if this tag is set.

   .. versionadded:: 0.6

**-d** *path*
   Since Sphinx has to read and parse all source files before it can write an
   output file, the parsed source files are cached as "doctree pickles".
   Normally, these files are put in a directory called :file:`.doctrees` under
   the build directory; with this option you can select a different cache
   directory (the doctrees can be shared between all builders).

**-c** *path*
   Don't look for the :file:`conf.py` in the source directory, but use the given
   configuration directory instead.  Note that various other files and paths
   given by configuration values are expected to be relative to the
   configuration directory, so they will have to be present at this location
   too.

   .. versionadded:: 0.3

**-C**
   Don't look for a configuration file; only take options via the ``-D`` option.

   .. versionadded:: 0.5

**-D** *setting=value*
   Override a configuration value set in the :file:`conf.py` file.  The value
   must be a string or dictionary value.  For the latter, supply the setting
   name and key like this: ``-D latex_elements.docclass=scrartcl``.

   .. versionchanged:: 0.6
      The value can now be a dictionary value.

**-A** *name=value*
   Make the *name* assigned to *value* in the HTML templates.

**-N**
   Do not do colored output.  (On Windows, colored output is disabled in any
   case.)

**-q**
   Do not output anything on standard output, only write warnings and errors to
   standard error.

**-Q**
   Do not output anything on standard output, also suppress warnings.  Only
   errors are written to standard error.

**-w** *file*
   Write warnings (and errors) to the given file, in addition to standard error.

**-W**
   Turn warnings into errors.  This means that the build stops at the first
   warning and ``sphinx-build`` exits with exit status 1.

**-P**
   (Useful for debugging only.)  Run the Python debugger, :mod:`pdb`, if an
   unhandled exception occurs while building.


You can also give one or more filenames on the command line after the source and
build directories.  Sphinx will then try to build only these output files (and
their dependencies).
