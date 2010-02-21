.. highlight:: rest

:mod:`sphinx.ext.autosummary` -- Generate autodoc summaries
===========================================================

.. module:: sphinx.ext.autosummary
   :synopsis: Generate autodoc summaries

.. versionadded:: 0.6

This extension generates function/method/attribute summary lists, similar to
those output e.g. by Epydoc and other API doc generation tools.  This is
especially useful when your docstrings are long and detailed, and putting each
one of them on a separate page makes them easier to read.

The :mod:`sphinx.ext.autosummary` extension does this in two parts:

1. There is an :dir:`autosummary` directive for generating summary listings that
   contain links to the documented items, and short summary blurbs extracted
   from their docstrings.

2. The convenience script :program:`sphinx-autogen` or the new
   :confval:`autosummary_generate` config value can be used to generate short
   "stub" files for the entries listed in the :dir:`autosummary` directives.
   These by default contain only the corresponding :mod:`sphinx.ext.autodoc`
   directive.


.. directive:: autosummary

   Insert a table that contains links to documented items, and a short summary
   blurb (the first sentence of the docstring) for each of them.  The
   :dir:`autosummary` directive can also optionally serve as a :dir:`toctree`
   entry for the included items.

   For example, ::

       .. currentmodule:: sphinx

       .. autosummary::

          environment.BuildEnvironment
          util.relative_uri

   produces a table like this:

       .. currentmodule:: sphinx

       .. autosummary::

          environment.BuildEnvironment
          util.relative_uri

       .. currentmodule:: sphinx.ext.autosummary

   Autosummary preprocesses the docstrings and signatures with the same
   :event:`autodoc-process-docstring` and :event:`autodoc-process-signature`
   hooks as :mod:`~sphinx.ext.autodoc`.


   **Options**

   * If you want the :dir:`autosummary` table to also serve as a :dir:`toctree`
     entry, use the ``toctree`` option, for example::

         .. autosummary::
            :toctree: DIRNAME

            sphinx.environment.BuildEnvironment
            sphinx.util.relative_uri

     The ``toctree`` option also signals to the :program:`sphinx-autogen` script
     that stub pages should be generated for the entries listed in this
     directive.  The option accepts a directory name as an argument;
     :program:`sphinx-autogen` will by default place its output in this
     directory. If no argument is given, output is placed in the same directory
     as the file that contains the directive.

   * If you don't want the :dir:`autosummary` to show function signatures in the
     listing, include the ``nosignatures`` option::

         .. autosummary::
            :nosignatures:

            sphinx.environment.BuildEnvironment
            sphinx.util.relative_uri


:program:`sphinx-autogen` -- generate autodoc stub pages
--------------------------------------------------------

The :program:`sphinx-autogen` script can be used to conveniently generate stub
documentation pages for items included in :dir:`autosummary` listings.

For example, the command ::

    $ sphinx-autogen -o generated *.rst

will read all :dir:`autosummary` tables in the :file:`*.rst` files that have the
``:toctree:`` option set, and output corresponding stub pages in directory
``generated`` for all documented items.  The generated pages by default contain
text of the form::

    sphinx.util.relative_uri
    ========================

    .. autofunction:: sphinx.util.relative_uri

If the ``-o`` option is not given, the script will place the output files in the
directories specified in the ``:toctree:`` options.


Generating stub pages automatically
-----------------------------------

If you do not want to create stub pages with :program:`sphinx-autogen`, you can
also use this new config value:

.. confval:: autosummary_generate

   A list of documents for which stub pages should be generated.

   The new files will be placed in the directories specified in the
   ``:toctree:`` options of the directives.
