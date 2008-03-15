.. _glossary:

Glossary
========

.. glossary::

   builder
      A class (inheriting from :class:`~sphinx.builder.Builder`) that takes
      parsed documents and performs an action on them.  Normally, builders
      translate the documents to an output format, but it is also possible to
      use the builder builders that e.g. check for broken links in the
      documentation, or build coverage information.

      See :ref:`builders` for an overview over Sphinx' built-in builders.

   description unit
      XXX

   documentation root
      The directory which contains the documentation's :file:`conf.py` file and
      is therefore seen as one Sphinx project.

   environment
      A structure where information about all documents under the root is saved,
      and used for cross-referencing.  The environment is pickled after the
      parsing stage, so that successive runs only need to read and parse new and
      changed documents.
