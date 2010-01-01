.. _extensions:

Sphinx Extensions
=================

.. module:: sphinx.application
   :synopsis: Application class and extensibility interface.

Since many projects will need special features in their documentation, Sphinx is
designed to be extensible on several levels.

This is what you can do in an extension: First, you can add new
:term:`builder`\s to support new output formats or actions on the parsed
documents.  Then, it is possible to register custom reStructuredText roles and
directives, extending the markup.  And finally, there are so-called "hook
points" at strategic places throughout the build process, where an extension can
register a hook and run specialized code.

An extension is simply a Python module.  When an extension is loaded, Sphinx
imports this module and executes its ``setup()`` function, which in turn
notifies Sphinx of everything the extension offers -- see the extension tutorial
for examples.

The configuration file itself can be treated as an extension if it contains a
``setup()`` function.  All other extensions to load must be listed in the
:confval:`extensions` configuration value.

.. toctree::

   ext/tutorial
   ext/appapi
   ext/builderapi


Builtin Sphinx extensions
-------------------------

These extensions are built in and can be activated by respective entries in the
:confval:`extensions` configuration value:

.. toctree::

   ext/autodoc
   ext/autosummary
   ext/doctest
   ext/intersphinx
   ext/math
   ext/graphviz
   ext/inheritance
   ext/refcounting
   ext/ifconfig
   ext/coverage
   ext/todo


Third-party extensions
----------------------

There are several extensions that are not (yet) maintained in the Sphinx
distribution.  The `Wiki at BitBucket`_ maintains a list of those.

If you write an extension that you think others will find useful, please write
to the project mailing list (`join here <http://groups.google.com/group/sphinx-dev>`_)
and we'll find the proper way of including or hosting it for the public.

.. _Wiki at BitBucket: http://www.bitbucket.org/birkenfeld/sphinx/wiki/Home


Where to put your own extensions?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Extensions local to a project should be put within the project's directory
structure.  Set Python's module search path, ``sys.path``, accordingly so that
Sphinx can find them.
E.g., if your extension ``foo.py`` lies in the ``exts`` subdirectory of the
project root, put into :file:`conf.py`::

   import sys, os

   sys.path.append(os.path.abspath('exts'))

   extensions = ['foo']

You can also install extensions anywhere else on ``sys.path``, e.g. in the
``site-packages`` directory.
