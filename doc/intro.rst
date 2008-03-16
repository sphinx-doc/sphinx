Introduction
============

This is the documentation for the Sphinx documentation builder.  Sphinx is a
tool that translates a set of reStructuredText_ source files into various output
formats, automatically producing cross-references, indices etc.

.. XXX web app

Prerequisites
-------------

Sphinx needs at least **Python 2.4** to run.  If you like to have source code
highlighting support, you must also install the Pygments_ library, which you can
do via setuptools' easy_install.

.. _reStructuredText: http://docutils.sf.net/rst.html
.. _Pygments: http://pygments.org


Setting up a documentation root
-------------------------------

The root directory of a documentation collection is called the
:dfn:`documentation root`.  There's nothing special about it; it just needs to
contain the Sphinx configuration file, :file:`conf.py`.

Sphinx comes with a script called :program:`sphinx-quickstart.py` that sets up a
documentation root and creates a default :file:`conf.py` from a few questions
it asks you.  Just run ::

   $ sphinx-quickstart.py

and answer the questions.


Running a build
---------------

A build is started with the :program:`sphinx-build.py` script.  It is called
like this::

     $ sphinx-build.py -b latex sourcedir builddir

where *sourcedir* is the :term:`documentation root`, and *builddir* is the
directory in which you want to place the built documentation (it must be an
existing directory).  The :option:`-b` option selects a builder; in this example
Sphinx will build LaTeX files.

The :program:`sphinx-build.py` script has several more options:

**-a**
   If given, always write all output files.  The default is to only write output
   files for new and changed source files.  (This may not apply to all
   builders.)

**-E**
   Don't use a saved :term:`environment` (the structure caching all
   cross-references), but rebuild it completely.  The default is to only read
   and parse source files that are new or have changed since the last run.

**-d** *path*
   Since Sphinx has to read and parse all source files before it can write an
   output file, the parsed source files are cached as "doctree pickles".
   Normally, these files are put in a directory called :file:`.doctrees` under
   the build directory; with this option you can select a different cache
   directory (the doctrees can be shared between all builders).

**-D** *setting=value*
   Override a configuration value set in the :file:`conf.py` file.  (The value
   must be a string value.)

**-N**
   Do not do colored output.  (On Windows, colored output is disabled in any
   case.)

**-q**
   Do not output anything on standard output, only write warnings to standard
   error.

**-P**
   (Useful for debugging only.)  Run the Python debugger, :mod:`pdb`, if an
   unhandled exception occurs while building.


You can also give one or more filenames on the command line after the source and
build directories.  Sphinx will then try to build only these output files (and
their dependencies).
