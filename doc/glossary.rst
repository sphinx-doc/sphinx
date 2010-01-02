.. _glossary:

Glossary
========

.. glossary::

   builder
      A class (inheriting from :class:`~sphinx.builders.Builder`) that takes
      parsed documents and performs an action on them.  Normally, builders
      translate the documents to an output format, but it is also possible to
      use the builder builders that e.g. check for broken links in the
      documentation, or build coverage information.

      See :ref:`builders` for an overview over Sphinx' built-in builders.

   configuration directory
      The directory containing :file:`conf.py`.  By default, this is the same as
      the :term:`source directory`, but can be set differently with the **-c**
      command-line option.

   environment
      A structure where information about all documents under the root is saved,
      and used for cross-referencing.  The environment is pickled after the
      parsing stage, so that successive runs only need to read and parse new and
      changed documents.

   object
      The basic building block of Sphinx documentation.  Every "object
      directive" (e.g. :dir:`function` or :dir:`object`) creates such a block;
      and most objects can be cross-referenced to.

   source directory
      The directory which, including its subdirectories, contains all source
      files for one Sphinx project.
