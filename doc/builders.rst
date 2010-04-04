.. _builders:

Available builders
==================

.. module:: sphinx.builders
   :synopsis: Available built-in builder classes.

These are the built-in Sphinx builders.  More builders can be added by
:ref:`extensions <extensions>`.

The builder's "name" must be given to the **-b** command-line option of
:program:`sphinx-build` to select a builder.


.. module:: sphinx.builders.html
.. class:: StandaloneHTMLBuilder

   This is the standard HTML builder.  Its output is a directory with HTML
   files, complete with style sheets and optionally the reST sources.  There are
   quite a few configuration values that customize the output of this builder,
   see the chapter :ref:`html-options` for details.

   Its name is ``html``.

.. class:: DirectoryHTMLBuilder

   This is a subclass of the standard HTML builder.  Its output is a directory
   with HTML files, where each file is called ``index.html`` and placed in a
   subdirectory named like its page name.  For example, the document
   ``markup/rest.rst`` will not result in an output file ``markup/rest.html``,
   but ``markup/rest/index.html``.  When generating links between pages, the
   ``index.html`` is omitted, so that the URL would look like ``markup/rest/``.

   Its name is ``dirhtml``.

   .. versionadded:: 0.6

.. class:: HTMLHelpBuilder

   This builder produces the same output as the standalone HTML builder, but
   also generates HTML Help support files that allow the Microsoft HTML Help
   Workshop to compile them into a CHM file.

   Its name is ``htmlhelp``.

.. module:: sphinx.builders.latex
.. class:: LaTeXBuilder

   This builder produces a bunch of LaTeX files in the output directory.  You
   have to specify which documents are to be included in which LaTeX files via
   the :confval:`latex_documents` configuration value.  There are a few
   configuration values that customize the output of this builder, see the
   chapter :ref:`latex-options` for details.

   .. note::

      The produced LaTeX file uses several LaTeX packages that may not be
      present in a "minimal" TeX distribution installation.  For TeXLive,
      the following packages need to be installed:

      * latex-recommended
      * latex-extra
      * fonts-recommended

   Its name is ``latex``.

Note that a direct PDF builder using ReportLab is available in `rst2pdf
<http://rst2pdf.googlecode.com>`_ version 0.12 or greater.  You need to add
``'rst2pdf.pdfbuilder'`` to your :confval:`extensions` to enable it, its name is
``pdf``.  Refer to the `rst2pdf manual
<http://lateral.netmanagers.com.ar/static/manual.pdf>`_ for details.

.. module:: sphinx.builders.text
.. class:: TextBuilder

   This builder produces a text file for each reST file -- this is almost the
   same as the reST source, but with much of the markup stripped for better
   readability.

   Its name is ``text``.

   .. versionadded:: 0.4

.. currentmodule:: sphinx.builders.html
.. class:: SerializingHTMLBuilder

   This builder uses a module that implements the Python serialization API
   (`pickle`, `simplejson`, `phpserialize`, and others) to dump the generated
   HTML documentation.  The pickle builder is a subclass of it.

   A concreate subclass of this builder serializing to the `PHP serialization`_
   format could look like this::

        import phpserialize

        class PHPSerializedBuilder(SerializingHTMLBuilder):
            name = 'phpserialized'
            implementation = phpserialize
            out_suffix = '.file.phpdump'
            globalcontext_filename = 'globalcontext.phpdump'
            searchindex_filename = 'searchindex.phpdump'

   .. _PHP serialization: http://pypi.python.org/pypi/phpserialize

   .. attribute:: implementation

      A module that implements `dump()`, `load()`, `dumps()` and `loads()`
      functions that conform to the functions with the same names from the
      pickle module.  Known modules implementing this interface are
      `simplejson` (or `json` in Python 2.6), `phpserialize`, `plistlib`,
      and others.

   .. attribute:: out_suffix

      The suffix for all regular files.

   .. attribute:: globalcontext_filename

      The filename for the file that contains the "global context".  This
      is a dict with some general configuration values such as the name
      of the project.

   .. attribute:: searchindex_filename

      The filename for the search index Sphinx generates.


   See :ref:`serialization-details` for details about the output format.

   .. versionadded:: 0.5

.. class:: PickleHTMLBuilder

   This builder produces a directory with pickle files containing mostly HTML
   fragments and TOC information, for use of a web application (or custom
   postprocessing tool) that doesn't use the standard HTML templates.

   See :ref:`serialization-details` for details about the output format.

   Its name is ``pickle``.  (The old name ``web`` still works as well.)

   The file suffix is ``.fpickle``.  The global context is called
   ``globalcontext.pickle``, the search index ``searchindex.pickle``.

.. class:: JSONHTMLBuilder

   This builder produces a directory with JSON files containing mostly HTML
   fragments and TOC information, for use of a web application (or custom
   postprocessing tool) that doesn't use the standard HTML templates.

   See :ref:`serialization-details` for details about the output format.

   Its name is ``json``.

   The file suffix is ``.fjson``.  The global context is called
   ``globalcontext.json``, the search index ``searchindex.json``.

   .. versionadded:: 0.5

.. module:: sphinx.builders.changes
.. class:: ChangesBuilder

   This builder produces an HTML overview of all :dir:`versionadded`,
   :dir:`versionchanged` and :dir:`deprecated` directives for the current
   :confval:`version`.  This is useful to generate a ChangeLog file, for
   example.

   Its name is ``changes``.

.. module:: sphinx.builders.linkcheck
.. class:: CheckExternalLinksBuilder

   This builder scans all documents for external links, tries to open them with
   :mod:`urllib2`, and writes an overview which ones are broken and redirected
   to standard output and to :file:`output.txt` in the output directory.

   Its name is ``linkcheck``.


Built-in Sphinx extensions that offer more builders are:

* :mod:`~sphinx.ext.doctest`
* :mod:`~sphinx.ext.coverage`


.. _serialization-details:

Serialization builder details
-----------------------------

All serialization builders outputs one file per source file and a few special
files.  They also copy the reST source files in the directory ``_sources``
under the output directory.

The :class:`PickleHTMLBuilder` is a builtin subclass that implements the pickle
serialization interface.

The files per source file have the extensions of
:attr:`~SerializingHTMLBuilder.out_suffix`, and are arranged in directories
just as the source files are.  They unserialize to a dictionary (or dictionary
like structure) with these keys:

``body``
   The HTML "body" (that is, the HTML rendering of the source file), as rendered
   by the HTML translator.

``title``
   The title of the document, as HTML (may contain markup).

``toc``
   The table of contents for the file, rendered as an HTML ``<ul>``.

``display_toc``
   A boolean that is ``True`` if the ``toc`` contains more than one entry.

``current_page_name``
   The document name of the current file.

``parents``, ``prev`` and ``next``
   Information about related chapters in the TOC tree.  Each relation is a
   dictionary with the keys ``link`` (HREF for the relation) and ``title``
   (title of the related document, as HTML).  ``parents`` is a list of
   relations, while ``prev`` and ``next`` are a single relation.

``sourcename``
   The name of the source file under ``_sources``.

The special files are located in the root output directory.  They are:

:attr:`SerializingHTMLBuilder.globalcontext_filename`
   A pickled dict with these keys:

   ``project``, ``copyright``, ``release``, ``version``
      The same values as given in the configuration file.

   ``style``, ``use_modindex``
      :confval:`html_style` and :confval:`html_use_modindex`, respectively.

   ``last_updated``
      Date of last build.

   ``builder``
      Name of the used builder, in the case of pickles this is always
      ``'pickle'``.

   ``titles``
      A dictionary of all documents' titles, as HTML strings.

:attr:`SerializingHTMLBuilder.searchindex_filename`
   An index that can be used for searching the documentation.  It is a pickled
   list with these entries:

   * A list of indexed docnames.
   * A list of document titles, as HTML strings, in the same order as the first
     list.
   * A dict mapping word roots (processed by an English-language stemmer) to a
     list of integers, which are indices into the first list.

``environment.pickle``
   The build environment.  This is always a pickle file, independent of the
   builder and a copy of the environment that was used when the builder was
   started.  (XXX: document common members)

   Unlike the other pickle files this pickle file requires that the sphinx
   module is available on unpickling.
