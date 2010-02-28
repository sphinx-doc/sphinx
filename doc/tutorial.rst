.. highlight:: rst

Sphinx Tutorial -- your first documentation
===========================================

This document is meant to give an overview of all common tasks while using
Sphinx.  The green arrows designate "more info" links leading to advanced
sections about the described task.


Setting up the documentation sources
------------------------------------

The root directory of a documentation collection is called the :term:`source
directory`.  This directory also contains the Sphinx configuration file
:file:`conf.py`, where you can configure all aspects of how Sphinx reads your
sources and builds your documentation.  [#]_

Sphinx comes with a script called :program:`sphinx-quickstart` that sets up a
source directory and creates a default :file:`conf.py` with the most useful
configuration values from a few questions it asks you.  Just run ::

   $ sphinx-quickstart

and answer its questions.


Adding some content
-------------------

Let's assume you've run :program:`sphinx-quickstart`.  It created a source
directory with :file:`conf.py` and a master document, :file:`index.rst` (if you
accepted the defaults).  The main function of the :term:`master document` is to
serve as a welcome page, and to contain the root of the "table of contents tree"
(or *toctree*).  This is one of the main things that Sphinx adds to
reStructuredText, a way to connect multiple files to a single hierarchy of
documents.

.. sidebar:: reStructuredText directives

   ``toctree`` is a reStructuredText :dfn:`directive`, a very versatile piece of
   markup.  Directives can have arguments, options and content.

   *Arguments* are given directly after the double colon following the
   directive's name.  Each directive decides whether it can have arguments, and
   how many.

   *Options* are given after the arguments, in form of a "field list".  The
   ``maxdepth`` is such an option for the ``toctree`` directive.

   *Content* follows the options or arguments after a blank line.  Each
   directive decides whether to allow content, and what to do with it.

   A common gotcha with directives is that **the first line of the content must
   be indented to the same level as the options are**.


The toctree directive initially is empty, and looks like this::

   .. toctree::
      :maxdepth: 2

You add documents listing them in the *content* of the directive::

   .. toctree::
      :maxdepth: 2

      intro
      tutorial
      ...

This is exactly how the toctree for this documentation looks.  The documents to
include are given as :term:`document name`\ s, which in short means that you
leave off the file name extension and use slashes as directory separators.

|more| Read more about :ref:`the toctree directive <toctree-directive>`.

You can now create the files you listed in the toctree, and their section titles
will be inserted (up to the "maxdepth" level) at the place where the toctree
directive is placed.  Also, Sphinx now knows about the order and hierarchy of
your documents.  (They may contain ``toctree`` directives themselves, which
means you can create deeply nested hierarchies if necessary.)


Running the build
-----------------

A build is started with the :program:`sphinx-build` script.  It is called
like this::

   $ sphinx-build -b html sourcedir builddir

where *sourcedir* is the :term:`source directory`, and *builddir* is the
directory in which you want to place the built documentation.  The :option:`-b`
option selects a builder; in this example Sphinx will build LaTeX files.

However, :program:`sphinx-quickstart` script creates a :file:`Makefile` and a
:file:`make.bat` which make life even easier for you:  with them you only need
to run ::

   $ make html

to build HTML docs in the build directory you chose.

|more| See :ref:`invocation` for all options that :program:`sphinx-build`
supports.


Topics to be covered
--------------------

- Autodoc
- Domains
- Basic configuration
- Selecting a theme
- Templating
- Using extensions
- Writing extensions


.. rubric:: Footnotes

.. [#] This is the usual lay-out.  However, :file:`conf.py` can also live in
       another directory, the :term:`configuration directory`.  See
       :ref:`invocation`.

.. |more| image:: more.png
          :align: middle
          :alt: more info
