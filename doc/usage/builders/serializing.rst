.. _serialization-details:

====================
Serializing builders
====================

All serialization builders outputs one file per source file and a few special
files.  They also copy the reST source files in the directory ``_sources``
under the output directory.

The :class:`.PickleHTMLBuilder` is a builtin subclass that implements the pickle
serialization interface.

The files per source file have the extensions of
:attr:`~.SerializingHTMLBuilder.out_suffix`, and are arranged in directories
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

:attr:`.SerializingHTMLBuilder.globalcontext_filename`
   A pickled dict with these keys:

   ``project``, ``copyright``, ``release``, ``version``
      The same values as given in the configuration file.

   ``style``
      :confval:`html_style`.

   ``last_updated``
      Date of last build.

   ``builder``
      Name of the used builder, in the case of pickles this is always
      ``'pickle'``.

   ``titles``
      A dictionary of all documents' titles, as HTML strings.

:attr:`.SerializingHTMLBuilder.searchindex_filename`
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
   started.

   .. todo:: Document common members.

   Unlike the other pickle files this pickle file requires that the ``sphinx``
   package is available on unpickling.


Serializing HTML builder
------------------------

.. versionadded:: 0.5

This builder uses a module that implements the Python serialization API
(``pickle``, ``simplejson``, ``phpserialize``, and others) to dump the
generated HTML documentation. It is the base builder for all other serializing
builders, such as the ``pickle`` builder.

A concrete subclass of this builder serializing to the `PHP serialization`_
format could look like this:

.. code-block:: python

   import phpserialize

   class PHPSerializedBuilder(SerializingHTMLBuilder):
       name = 'phpserialized'
       implementation = phpserialize
       out_suffix = '.file.phpdump'
       globalcontext_filename = 'globalcontext.phpdump'
       searchindex_filename = 'searchindex.phpdump'

.. _PHP serialization: https://pypi.org/project/phpserialize/

See :ref:`serialization-details` for details about the output format.

.. currentmodule:: sphinxcontrib.serializinghtml
.. class:: SerializingHTMLBuilder

   .. attribute:: implementation

      A module that implements `dump()`, `load()`, `dumps()` and `loads()`
      functions that conform to the functions with the same names from the
      pickle module.  Known modules implementing this interface are
      `simplejson`, `phpserialize`, `plistlib`, and others.

   .. attribute:: out_suffix

      The suffix for all regular files.

   .. attribute:: globalcontext_filename

      The filename for the file that contains the "global context".  This
      is a dict with some general configuration values such as the name
      of the project.

   .. attribute:: searchindex_filename

      The filename for the search index Sphinx generates.


Pickle HTML builder
-------------------

This builder produces a directory with pickle files containing mostly HTML
fragments and TOC information, for use of a web application (or custom
postprocessing tool) that doesn't use the standard HTML templates.

See :ref:`serialization-details` for details about the output format.
The file suffix is ``.fpickle``.  The global context is called
``globalcontext.pickle``, the search index ``searchindex.pickle``.

.. class:: PickleHTMLBuilder

   .. autoattribute:: name

      The old name ``web`` still works as well.

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


JSON HTML builder
-----------------

.. versionadded:: 0.5

This builder produces a directory with JSON files containing mostly HTML
fragments and TOC information, for use of a web application (or custom
postprocessing tool) that doesn't use the standard HTML templates.

See :ref:`serialization-details` for details about the output format.
The file suffix is ``.fjson``.  The global context is called
``globalcontext.json``, the search index ``searchindex.json``.

.. class:: JSONHTMLBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types
