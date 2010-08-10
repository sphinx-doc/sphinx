.. _storagebackends:

.. currentmodule:: sphinx.websupport.storage

Storage Backends
================

To create a custom storage backend you will need to subclass the
:class:`~StorageBackend` class. Then create an instance of the new class
and pass that as the `storage` keyword argument when you create the
:class:`~sphinx.websupport.WebSupport` object::

    support = Websupport(srcdir=srcdir,
                         builddir=builddir,
                         storage=MyStorage())

For more information about creating a custom storage backend, please see
the documentation of the :class:`StorageBackend` class below.

.. class:: StorageBackend

    Defines an interface for storage backends.

StorageBackend Methods
~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: sphinx.websupport.storage.StorageBackend.pre_build

.. automethod:: sphinx.websupport.storage.StorageBackend.add_node

.. automethod:: sphinx.websupport.storage.StorageBackend.post_build

.. automethod:: sphinx.websupport.storage.StorageBackend.add_comment

.. automethod:: sphinx.websupport.storage.StorageBackend.delete_comment

.. automethod:: sphinx.websupport.storage.StorageBackend.get_data

.. automethod:: sphinx.websupport.storage.StorageBackend.process_vote

.. automethod:: sphinx.websupport.storage.StorageBackend.update_username

.. automethod:: sphinx.websupport.storage.StorageBackend.accept_comment

.. automethod:: sphinx.websupport.storage.StorageBackend.reject_comment
