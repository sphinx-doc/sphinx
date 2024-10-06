.. _glossary:

Glossary
========

.. glossary::

   builder
      A class (inheriting from :class:`~sphinx.builders.Builder`) that takes
      parsed documents and performs an action on them.  Normally, builders
      translate the documents to an output format, but it is also possible to
      use builders that e.g. check for broken links in the documentation, or
      build coverage information.

      See :doc:`/usage/builders/index` for an overview over Sphinx's built-in
      builders.

   configuration directory
      The directory containing :file:`conf.py`.  By default, this is the same as
      the :term:`source directory`, but can be set differently with the **-c**
      command-line option.

   directive
      A reStructuredText markup element that allows marking a block of content
      with special meaning.  Directives are supplied not only by docutils, but
      Sphinx and custom extensions can add their own.  The basic directive
      syntax looks like this:

      .. code-block:: rst

         .. directive-name:: argument ...
            :option: value

            Content of the directive.

      See :ref:`rst-directives` for more information.

   document name
      Since reStructuredText source files can have different extensions
      (some people like ``.txt``, some like ``.rst`` -- the extension can be
      configured with :confval:`source_suffix`)
      and different OSes have different path
      separators, Sphinx abstracts them: :dfn:`document names` are always
      relative to the :term:`source directory`, the extension is stripped, and
      path separators are converted to slashes.  All values, parameters and such
      referring to "documents" expect such document names.

      Examples for document names are ``index``, ``library/zipfile``, or
      ``reference/datamodel/types``.  Note that there is no leading or trailing
      slash.

   domain
      A domain is a collection of markup (reStructuredText :term:`directive`\ s
      and :term:`role`\ s) to describe and link to :term:`object`\ s belonging
      together, e.g. elements of a programming language.  Directive and role
      names in a domain have names like ``domain:name``, e.g. ``py:function``.

      Having domains means that there are no naming problems when one set of
      documentation wants to refer to e.g. C++ and Python classes.  It also
      means that extensions that support the documentation of whole new
      languages are much easier to write.

      For more information, refer to :doc:`/usage/domains/index`.

   environment
      A structure where information about all documents under the root is saved,
      and used for cross-referencing.  The environment is pickled after the
      parsing stage, so that successive runs only need to read and parse new and
      changed documents.

   extension
     A custom :term:`role`, :term:`directive` or other aspect of Sphinx that
     allows users to modify any aspect of the build process within Sphinx.

     For more information, refer to :doc:`/usage/extensions/index`.

   master document
      The document that contains the root :rst:dir:`toctree` directive.

   root document
      Same as :term:`master document`.

   object
      The basic building block of Sphinx documentation.  Every "object
      directive" (e.g. :rst:dir:`py:function` or :rst:dir:`object`) creates such
      a block; and most objects can be cross-referenced to.

   RemoveInSphinxXXXWarning
      The feature which is warned will be removed in Sphinx-XXX version.
      It usually caused from Sphinx extensions which is using deprecated.
      See also :ref:`when-deprecation-warnings-are-displayed`.

   role
      A reStructuredText markup element that allows marking a piece of text.
      Like directives, roles are extensible.  The basic syntax looks like this:
      ``:rolename:`content```.  See :ref:`rst-inline-markup` for details.

   source directory
      The directory which, including its subdirectories, contains all source
      files for one Sphinx project.

   reStructuredText
      An easy-to-read, what-you-see-is-what-you-get plaintext markup syntax and
      parser system.
