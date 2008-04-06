.. _extensions:

Sphinx Extensions
=================

.. module:: sphinx.application
   :synopsis: Application class and extensibility interface.

Since many projects will need special features in their documentation, Sphinx is
designed to be extensible on several levels.

First, you can add new :term:`builder`\s to support new output formats or
actions on the parsed documents.  Then, it is possible to register custom
reStructuredText roles and directives, extending the markup.  And finally, there
are so-called "hook points" at strategic places throughout the build process,
where an extension can register a hook and run specialized code.

The configuration file itself can be an extension, see the :confval:`extensions`
configuration value docs.

.. toctree::

   ext/appapi
   ext/builderapi


Builtin Sphinx extensions
-------------------------

These extensions are built in and can be activated by respective entries in the
:confval:`extensions` configuration value:

.. toctree::

   ext/autodoc
   ext/doctest
   ext/refcounting
   ext/ifconfig
   ext/coverage
