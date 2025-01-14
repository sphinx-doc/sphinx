===============
Getting started
===============

Sphinx is a *documentation generator* or a tool that translates a set of plain
text source files into various output formats, automatically producing
cross-references, indices, etc.  That is, if you have a directory containing a
bunch of :doc:`/usage/restructuredtext/index` or :doc:`/usage/markdown`
documents, Sphinx can generate a series of HTML files, a PDF file (via LaTeX),
man pages and much more.

Sphinx focuses on documentation, in particular handwritten documentation,
however, Sphinx can also be used to generate blogs, homepages and even books.
Much of Sphinx's power comes from the richness of its default plain-text markup
format, :doc:`reStructuredText </usage/restructuredtext/index>`, along with
its :doc:`significant extensibility capabilities </development/index>`.

The goal of this document is to give you a quick taste of what Sphinx is and
how you might use it. When you're done here, you can check out the
:doc:`installation guide </usage/installation>` followed by the intro to the
default markup format used by Sphinx, :doc:`reStructuredText
</usage/restructuredtext/index>`.

For a great "introduction" to writing docs in general -- the whys and hows, see
also `Write the docs`__, written by Eric Holscher.

.. __: https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/


Setting up the documentation sources
------------------------------------

The root directory of a Sphinx collection of plain-text document sources is
called the :term:`source directory`.  This directory also contains the Sphinx
configuration file :file:`conf.py`, where you can configure all aspects of how
Sphinx reads your sources and builds your documentation.  [#]_

Sphinx comes with a script called :program:`sphinx-quickstart` that sets up a
source directory and creates a default :file:`conf.py` with the most useful
configuration values from a few questions it asks you. To use this, run:

.. code-block:: console

   $ sphinx-quickstart


Defining document structure
---------------------------

Let's assume you've run :program:`sphinx-quickstart`.  It created a source
directory with :file:`conf.py` and a root document, :file:`index.rst`.  The
main function of the :term:`root document` is to serve as a welcome page, and
to contain the root of the "table of contents tree" (or *toctree*).  This is one
of the main things that Sphinx adds to reStructuredText, a way to connect
multiple files to a single hierarchy of documents.

.. admonition:: reStructuredText directives
   :class: note

   ``toctree`` is a reStructuredText :dfn:`directive`, a very versatile piece
   of markup.  Directives can have arguments, options and content.

   *Arguments* are given directly after the double colon following the
   directive's name.  Each directive decides whether it can have arguments, and
   how many.

   *Options* are given after the arguments, in form of a "field list".  The
   ``maxdepth`` is such an option for the ``toctree`` directive.

   *Content* follows the options or arguments after a blank line.  Each
   directive decides whether to allow content, and what to do with it.

   A common gotcha with directives is that **the first line of the content must
   be indented to the same level as the options are**.

The ``toctree`` directive initially is empty, and looks like so:

.. code-block:: rst

   .. toctree::
      :maxdepth: 2

You add documents listing them in the *content* of the directive:

.. code-block:: rst

   .. toctree::
      :maxdepth: 2

      usage/installation
      usage/quickstart
      ...

This is exactly how the ``toctree`` for this documentation looks.  The
documents to include are given as :term:`document name`\ s, which in short
means that you leave off the file name extension and use forward slashes
(``/``) as directory separators.

.. seealso::

   Read more about :ref:`the toctree directive <toctree-directive>`.

You can now create the files you listed in the ``toctree`` and add content, and
their section titles will be inserted (up to the ``maxdepth`` level) at the
place where the ``toctree`` directive is placed.  Also, Sphinx now knows about
the order and hierarchy of your documents.  (They may contain ``toctree``
directives themselves, which means you can create deeply nested hierarchies if
necessary.)


Adding content
--------------

In Sphinx source files, you can use most features of standard
:term:`reStructuredText`.  There are also several features added by Sphinx.
For example, you can add cross-file references in a portable way (which works
for all output types) using the :rst:role:`ref` role.

For an example, if you are viewing the HTML version, you can look at the source
for this document -- use the "Show Source" link in the sidebar.

.. todo:: Update the below link when we add new guides on these.

.. seealso::

   :doc:`/usage/restructuredtext/index`
   for a more in-depth introduction to reStructuredText,
   including markup added by Sphinx.


Running the build
-----------------

Now that you have added some files and content, let's make a first build of the
docs.  A build is started with the :program:`sphinx-build` program:

.. code-block:: console

   $ sphinx-build -M html sourcedir outputdir

where *sourcedir* is the :term:`source directory`, and *outputdir* is the
directory in which you want to place the built documentation.
The :option:`-M <sphinx-build -M>` option selects a builder; in this example
Sphinx will build HTML files.

.. seealso::

   Refer to the :doc:`sphinx-build man page </man/sphinx-build>`
   for all options that :program:`sphinx-build` supports.

You can also build a **live version of the documentation** that you can preview
in the browser.
It will detect changes and reload the page any time you make edits.
To do so, use `sphinx-autobuild`_ to run the following command:

.. code-block:: console

   $ sphinx-autobuild source-dir output-dir

.. _sphinx-autobuild: https://github.com/sphinx-doc/sphinx-autobuild

However, :program:`sphinx-quickstart` script creates a :file:`Makefile` and a
:file:`make.bat` which make life even easier for you. These can be executed by
running :command:`make` with the name of the builder. For example.

.. code-block:: console

   $ make html

This will build HTML docs in the build directory you chose. Execute
:command:`make` without an argument to see which targets are available.

.. admonition:: How do I generate PDF documents?

   ``make latexpdf`` runs the :mod:`LaTeX builder
   <sphinx.builders.latex.LaTeXBuilder>` and readily invokes the pdfTeX
   toolchain for you.


.. todo:: Move this whole section into a guide on rST or directives

Documenting objects
-------------------

One of Sphinx's main objectives is easy documentation of :dfn:`objects` (in a
very general sense) in any :dfn:`domain`.  A domain is a collection of object
types that belong together, complete with markup to create and reference
descriptions of these objects.

The most prominent domain is the Python domain. For example, to document
Python's built-in function ``enumerate()``, you would add this to one of your
source files.

.. code-block:: rst

   .. py:function:: enumerate(sequence[, start=0])

      Return an iterator that yields tuples of an index and an item of the
      *sequence*. (And so on.)

This is rendered like this:

.. py:function:: enumerate(sequence[, start=0])

   Return an iterator that yields tuples of an index and an item of the
   *sequence*. (And so on.)

The argument of the directive is the :dfn:`signature` of the object you
describe, the content is the documentation for it.  Multiple signatures can be
given, each in its own line.

The Python domain also happens to be the default domain, so you don't need to
prefix the markup with the domain name.

.. code-block:: rst

   .. function:: enumerate(sequence[, start=0])

      ...

does the same job if you keep the default setting for the default domain.

There are several more directives for documenting other types of Python
objects, for example :rst:dir:`py:class` or :rst:dir:`py:method`.  There is
also a cross-referencing :dfn:`role` for each of these object types.  This
markup will create a link to the documentation of ``enumerate()``.

::

   The :py:func:`enumerate` function can be used for ...

And here is the proof: A link to :func:`enumerate`.

Again, the ``py:`` can be left out if the Python domain is the default one.  It
doesn't matter which file contains the actual documentation for
``enumerate()``; Sphinx will find it and create a link to it.

Each domain will have special rules for how the signatures can look like, and
make the formatted output look pretty, or add specific features like links to
parameter types, e.g. in the C/C++ domains.

.. seealso::

   :doc:`/usage/domains/index`
   for all the available domains and their directives/roles.


Basic configuration
-------------------

Earlier we mentioned that the :file:`conf.py` file controls how Sphinx
processes your documents.  In that file, which is executed as a Python source
file, you assign configuration values.  For advanced users: since it is
executed by Sphinx, you can do non-trivial tasks in it, like extending
:data:`sys.path` or importing a module to find out the version you are
documenting.

The config values that you probably want to change are already put into the
:file:`conf.py` by :program:`sphinx-quickstart` and initially commented out
(with standard Python syntax: a ``#`` comments the rest of the line).  To
change the default value, remove the hash sign and modify the value.  To
customize a config value that is not automatically added by
:program:`sphinx-quickstart`, just add an additional assignment.

Keep in mind that the file uses Python syntax for strings, numbers, lists and
so on.  The file is saved in UTF-8 by default, as indicated by the encoding
declaration in the first line.

.. seealso::

   :doc:`/usage/configuration`
   for documentation of all available config values.


.. todo:: Move this entire doc to a different section

Autodoc
-------

When documenting Python code, it is common to put a lot of documentation in the
source files, in documentation strings.  Sphinx supports the inclusion of
docstrings from your modules with an :dfn:`extension` (an extension is a Python
module that provides additional features for Sphinx projects) called *autodoc*.

.. seealso::

   :mod:`sphinx.ext.autodoc`
   for the complete description of the features of autodoc.

Intersphinx
-----------

Many Sphinx documents including the `Python documentation`_ are published on
the Internet.  When you want to make links to such documents from your
documentation, you can do it with :mod:`sphinx.ext.intersphinx`.

.. _Python documentation: https://docs.python.org/3

In order to use intersphinx, you need to activate it in :file:`conf.py` by
putting the string ``'sphinx.ext.intersphinx'`` into the :confval:`extensions`
list and set up the :confval:`intersphinx_mapping` config value.

For example, to link to ``io.open()`` in the Python library manual, you need to
setup your :confval:`intersphinx_mapping` like::

   intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}

And now, you can write a cross-reference like ``:py:func:`io.open```.  Any
cross-reference that has no matching target in the current documentation set,
will be looked up in the documentation sets configured in
:confval:`intersphinx_mapping` (this needs access to the URL in order to
download the list of valid targets).  Intersphinx also works for some other
:term:`domain`\'s roles including ``:ref:``, however it doesn't work for
``:doc:`` as that is non-domain role.

.. seealso::

   :mod:`sphinx.ext.intersphinx`
   for the complete description of the features of intersphinx.


More topics to be covered
-------------------------

- :doc:`Other extensions </usage/extensions/index>`:
- Static files
- :doc:`Selecting a theme </usage/theming>`
- :ref:`Templating <templating>`
- Using extensions
- :ref:`Writing extensions <dev-extensions>`


.. rubric:: Footnotes

.. [#] This is the usual layout.  However, :file:`conf.py` can also live in
       another directory, the :term:`configuration directory`.  Refer to the
       :doc:`sphinx-build man page </man/sphinx-build>` for more information.
