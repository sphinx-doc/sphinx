:mod:`sphinx.ext.intersphinx` -- Link to other projects' documentation
======================================================================

.. module:: sphinx.ext.intersphinx
   :synopsis: Link to other Sphinx documentation.

.. index:: pair: automatic; linking

.. versionadded:: 0.5

This extension can generate automatic links to the documentation of Python
objects in other projects.  This works as follows:

* Each Sphinx HTML build creates a file named :file:`objects.inv` that
  contains a mapping from Python identifiers to URIs relative to the HTML set's
  root.

* Projects using the Intersphinx extension can specify the location of such
  mapping files in the :confval:`intersphinx_mapping` config value.  The mapping
  will then be used to resolve otherwise missing references to Python objects
  into links to the other documentation.

* By default, the mapping file is assumed to be at the same location as the rest
  of the documentation; however, the location of the mapping file can also be
  specified individually, e.g. if the docs should be buildable without Internet
  access.

To use intersphinx linking, add ``'sphinx.ext.intersphinx'`` to your
:confval:`extensions` config value, and use these new config values to activate
linking:

.. confval:: intersphinx_mapping

   A dictionary mapping URIs to either ``None`` or an URI.  The keys are the
   base URI of the foreign Sphinx documentation sets and can be local paths or
   HTTP URIs.  The values indicate where the inventory file can be found: they
   can be ``None`` (at the same location as the base URI) or another local or
   HTTP URI.

   Relative local paths in the keys are taken as relative to the base of the
   built documentation, while relative local paths in the values are taken as
   relative to the source directory.

   An example, to add links to modules and objects in the Python standard
   library documentation::

      intersphinx_mapping = {'http://docs.python.org/': None}

   This will download the corresponding :file:`objects.inv` file from the
   Internet and generate links to the pages under the given URI.  The downloaded
   inventory is cached in the Sphinx environment, so it must be redownloaded
   whenever you do a full rebuild.

   A second example, showing the meaning of a non-``None`` value::

      intersphinx_mapping = {'http://docs.python.org/': 'python-inv.txt'}

   This will read the inventory from :file:`python-inv.txt` in the source
   directory, but still generate links to the pages under
   ``http://docs.python.org/``.  It is up to you to update the inventory file
   as new objects are added to the Python documentation.

   When fetching remote inventory files, proxy settings will be read from
   the ``$HTTP_PROXY`` environment variable.

.. confval:: intersphinx_cache_limit

   The maximum number of days to cache remote inventories.  The default is
   ``5``, meaning five days.  Set this to a negative value to cache inventories
   for unlimited time.
