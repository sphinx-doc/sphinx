=============
HTML Builders
=============

All HTML builders generate HTML output files but vary in how this output is
structured and what additional artifacts are included. Specifically, the
`Directory HTML builder`_ and `Single HTML builder`_ are variants of the
default `Standalone HTML builder`_ that generate output in different formats,
while the remaining builders generate the same output but also generate
additional files required by specific applications or use cases.


Standalone HTML builder
-----------------------

This is the standard HTML builder.  Its output is a directory with HTML files,
complete with style sheets and optionally the reST sources.  There are quite a
few configuration values that customize the output of this builder, see the
chapter :ref:`html-options` for details.

.. module:: sphinx.builders.html
.. class:: StandaloneHTMLBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Directory HTML builder
----------------------

.. versionadded:: 0.6

This is a variant of the standard HTML builder. Its output is a directory
with HTML files, where each file is called ``index.html`` and placed in a
subdirectory named like its page name.  For example, the document
``markup/rest.rst`` will not result in an output file ``markup/rest.html``,
but ``markup/rest/index.html``.  When generating links between pages, the
``index.html`` is omitted, so that the URL would look like ``markup/rest/``.

.. module:: sphinx.builders.dirhtml
.. class:: DirectoryHTMLBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Single HTML builder
-------------------

.. versionadded:: 1.0

This is an HTML builder that combines the whole project in one output file.
(Obviously this only works with smaller projects.)  The file is named like
the master document.  No indices will be generated.

.. module:: sphinx.builders.singlehtml
.. class:: SingleFileHTMLBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


HTML Help builder
-----------------

This builder produces the same output as the standalone HTML builder, but
also generates HTML Help support files that allow the Microsoft HTML Help
Workshop to compile them into a CHM file.

.. module:: sphinxcontrib.htmlhelp
.. class:: HTMLHelpBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Qt Help builder
---------------

.. versionchanged:: 2.0

   Moved to sphinxcontrib.qthelp from sphinx.builders package.

This builder produces the same output as the standalone HTML builder, but
also generates `Qt help <https://doc.qt.io/qt-5/qthelp-framework.html>`__
collection support files that allow the Qt collection generator to compile
them.

.. module:: sphinxcontrib.qthelp
.. class:: QtHelpBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Apple Help Book builder
-----------------------

.. versionadded:: 1.3

.. versionchanged:: 2.0

   Moved to sphinxcontrib.applehelp from sphinx.builders package.

This builder produces an Apple Help Book based on the same output as the
standalone HTML builder.

If the source directory contains any ``.lproj`` folders, the one
corresponding to the selected language will have its contents merged with
the generated output.  These folders will be ignored by all other
documentation types.

In order to generate a valid help book, this builder requires the command
line tool :program:`hiutil`, which is only available on Mac OS X 10.6 and
above.  You can disable the indexing step by setting
:confval:`applehelp_disable_external_tools` to ``True``, in which case the
output will not be valid until :program:`hiutil` has been run on all of the
``.lproj`` folders within the bundle.

.. module:: sphinxcontrib.applehelp
.. class:: AppleHelpBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


GNOME Devhelp builder
---------------------

.. versionchanged:: 2.0

   Moved to sphinxcontrib.devhelp from sphinx.builders package.

This builder produces the same output as the standalone HTML builder, but
also generates `GNOME Devhelp <https://wiki.gnome.org/Apps/Devhelp>`__
support file that allows the GNOME Devhelp reader to view them.

.. module:: sphinxcontrib.devhelp
.. class:: DevhelpBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


EPUB 3 builder
--------------

.. versionadded:: 1.4

.. versionchanged:: 1.5

   Used for the default builder of the ``epub`` format.

This builder produces the same output as the standalone HTML builder, but
also generates an *EPUB* file for ebook readers.  See :ref:`epub-faq` for
details about it.  For definition of the epub format, refer to
`<http://idpf.org/epub>`__ and `<https://en.wikipedia.org/wiki/EPUB>`__.
The builder creates *EPUB 3* files.

.. module:: sphinx.builders.epub3
.. class:: Epub3Builder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types
