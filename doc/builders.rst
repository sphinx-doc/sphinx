.. _builders:

Available builders
==================

.. module:: sphinx.builder
   :synopsis: Available built-in builder classes.

These are the built-in Sphinx builders.  More builders can be added by
:ref:`extensions <extensions>`.

The builder's "name" must be given to the **-b** command-line option of
:program:`sphinx-build` to select a builder.


.. class:: StandaloneHTMLBuilder

   This is the standard HTML builder.  Its output is a directory with HTML
   files, complete with style sheets and optionally the reST sources.  There are
   quite a few configuration values that customize the output of this builder,
   see the chapter :ref:`html-options` for details.

   Its name is ``html``.

.. class:: HTMLHelpBuilder

   This builder produces the same output as the standalone HTML builder, but
   also generates HTML Help support files that allow the Microsoft HTML Help
   Workshop to compile them into a CHM file.

   Its name is ``htmlhelp``. 

.. class:: WebHTMLBuilder

   This builder produces a directory with pickle files containing mostly HTML
   fragments and TOC information, for use of a web application (or custom
   postprocessing tool) that doesn't use the standard HTML templates.

   It also is the format used by the Sphinx Web application.  Its name is
   ``web``.

.. class:: LaTeXBuilder

   This builder produces a bunch of LaTeX files in the output directory.  You
   have to specify which documents are to be included in which LaTeX files via
   the :confval:`latex_documents` configuration value.  There are a few
   configuration values that customize the output of this builder, see the
   chapter :ref:`latex-options` for details.

   Its name is ``latex``.

.. class:: ChangesBuilder

   This builder produces an HTML overview of all :dir:`versionadded`,
   :dir:`versionchanged` and :dir:`deprecated` directives for the current
   :confval:`version`.  This is useful to generate a ChangeLog file, for
   example.

   Its name is ``changes``.

.. class:: CheckExternalLinksBuilder

   This builder scans all documents for external links, tries to open them with
   :mod:`urllib2`, and writes an overview which ones are broken and redirected
   to standard output and to :file:`output.txt` in the output directory.

   Its name is ``linkcheck``.


Built-in Sphinx extensions that offer more builders are:

* :mod:`~sphinx.ext.doctest`
* :mod:`~sphinx.ext.coverage`
