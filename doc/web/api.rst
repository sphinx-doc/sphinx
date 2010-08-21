.. _websupportapi:

.. currentmodule:: sphinx.websupport

The WebSupport Class
====================

.. class:: WebSupport

   The main API class for the web support package.  All interactions with the
   web support package should occur through this class.

   The class takes the following keyword arguments:

   srcdir
      The directory containing reStructuredText source files.

   builddir
      The directory that build data and static files should be placed in.  This
      should be used when creating a :class:`WebSupport` object that will be
      used to build data.

   datadir
      The directory that the web support data is in.  This should be used when
      creating a :class:`WebSupport` object that will be used to retrieve data.

   search
       This may contain either a string (e.g. 'xapian') referencing a built-in
       search adapter to use, or an instance of a subclass of
       :class:`~.search.BaseSearch`.

   storage
       This may contain either a string representing a database uri, or an
       instance of a subclass of :class:`~.storage.StorageBackend`.  If this is
       not provided, a new sqlite database will be created.

   moderation_callback
       A callable to be called when a new comment is added that is not
       displayed.  It must accept one argument: a dictionary representing the
       comment that was added.

   staticdir
       If static files are served from a location besides ``'/static'``, this
       should be a string with the name of that location
       (e.g. ``'/static_files'``).

   docroot
       If the documentation is not served from the base path of a URL, this
       should be a string specifying that path (e.g. ``'docs'``).


Methods
~~~~~~~

.. automethod:: sphinx.websupport.WebSupport.build

.. automethod:: sphinx.websupport.WebSupport.get_document

.. automethod:: sphinx.websupport.WebSupport.get_data

.. automethod:: sphinx.websupport.WebSupport.add_comment

.. automethod:: sphinx.websupport.WebSupport.process_vote

.. automethod:: sphinx.websupport.WebSupport.get_search_results
