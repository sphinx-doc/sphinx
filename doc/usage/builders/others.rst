==============
Other Builders
==============

Text builder
------------

.. versionadded:: 0.4

This builder produces a text file for each reST file -- this is almost the
same as the reST source, but with much of the markup stripped for better
readability.

.. module:: sphinx.builders.text
.. class:: TextBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Man page builder
----------------

.. versionadded:: 1.0

This builder produces manual pages in the groff format.  You have to specify
which documents are to be included in which manual pages via the
:confval:`man_pages` configuration value.

.. module:: sphinx.builders.manpage
.. class:: ManualPageBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Texinfo builder
---------------

.. versionadded:: 1.1

This builder produces Texinfo files that can be processed into Info files by
the :program:`makeinfo` program.  You have to specify which documents are to
be included in which Texinfo files via the :confval:`texinfo_documents`
configuration value.

The Info format is the basis of the on-line help system used by GNU Emacs and
the terminal-based program :program:`info`.  See :ref:`texinfo-faq` for more
details.  The Texinfo format is the official documentation system used by the
GNU project.  More information on Texinfo can be found at
`<https://www.gnu.org/software/texinfo/>`_.

.. module:: sphinx.builders.texinfo
.. class:: TexinfoBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Message Catalog builder
-----------------------

.. versionadded:: 1.1

This builder produces gettext-style message catalogs.  Each top-level file or
subdirectory grows a single ``.pot`` catalog template.

See the documentation on :ref:`intl` for further reference.

.. module:: sphinx.builders.gettext
.. class:: MessageCatalogBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Changes builder
---------------

This builder produces an HTML overview of all :rst:dir:`versionadded`,
:rst:dir:`versionchanged` and :rst:dir:`deprecated` directives for the
current :confval:`version`.  This is useful to generate a ChangeLog file, for
example.

.. module:: sphinx.builders.changes
.. class:: ChangesBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Dummy builder
-------------

.. versionadded:: 1.4

This builder produces no output.  The input is only parsed and checked for
consistency.  This is useful for linting purposes.

.. module:: sphinx.builders.dummy
.. class:: DummyBuilder

   .. autoattribute:: name

   .. autoattribute:: supported_image_types


Link check builder
------------------

.. versionchanged:: 1.5

   The ``linkcheck`` builder now uses the ``requests`` module internally.

This builder scans all documents for external links, tries to open them with
``requests``, and writes an overview which ones are broken and redirected to
standard output and to :file:`output.txt` in the output directory.

.. module:: sphinx.builders.linkcheck
.. class:: CheckExternalLinksBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types
