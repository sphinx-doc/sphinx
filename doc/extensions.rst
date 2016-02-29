.. _extensions:

Sphinx Extensions
=================

Since many projects will need special features in their documentation, Sphinx
allows to add "extensions" to the build process, each of which can modify almost
any aspect of document processing.

This chapter describes the extensions bundled with Sphinx.  For the API
documentation on writing your own extension, see :ref:`dev-extensions`.

Builtin Sphinx extensions
-------------------------

These extensions are built in and can be activated by respective entries in the
:confval:`extensions` configuration value:

.. toctree::

   ext/autodoc
   ext/autosectionlabel
   ext/autosummary
   ext/coverage
   ext/doctest
   ext/extlinks
   ext/githubpages
   ext/graphviz
   ext/ifconfig
   ext/inheritance
   ext/intersphinx
   ext/linkcode
   ext/math
   ext/napoleon
   ext/todo
   ext/viewcode


Third-party extensions
----------------------

You can find several extensions contributed by users in the `Sphinx Contrib`_
repository.  It is open for anyone who wants to maintain an extension
publicly; just send a short message asking for write permissions.

There are also several extensions hosted elsewhere.  The `Sphinx extension
survey <http://sphinxext-survey.readthedocs.org/en/latest/>`__ contains a
comprehensive list.

If you write an extension that you think others will find useful or you think
should be included as a part of Sphinx, please write to the project mailing
list (`join here <https://groups.google.com/forum/#!forum/sphinx-dev>`_).

.. _Sphinx Contrib: https://bitbucket.org/birkenfeld/sphinx-contrib


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
