.. _websupportapi:

.. currentmodule:: sphinxcontrib.websupport

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
       If the static files should be created in a different location
       **and not in** ``'/static'``, this should be a string with the name of
       that location (e.g. ``builddir + '/static_files'``).

       .. note::
           If you specify ``staticdir``, you will typically want to adjust
           ``staticroot`` accordingly.

   staticroot
       If the static files are not served from ``'/static'``, this should be a
       string with the name of that location (e.g. ``'/static_files'``).

   docroot
       If the documentation is not served from the base path of a URL, this
       should be a string specifying that path (e.g. ``'docs'``).


.. versionchanged:: 1.6

   WebSupport class is moved to sphinxcontrib.websupport from sphinx.websupport.
   Please add ``sphinxcontrib-websupport`` package in your dependency and use
   moved class instead.


Methods
-------

.. automethod:: sphinxcontrib.websupport.WebSupport.build

.. automethod:: sphinxcontrib.websupport.WebSupport.get_document

.. automethod:: sphinxcontrib.websupport.WebSupport.get_data

.. automethod:: sphinxcontrib.websupport.WebSupport.add_comment

.. automethod:: sphinxcontrib.websupport.WebSupport.process_vote

.. automethod:: sphinxcontrib.websupport.WebSupport.get_search_results
