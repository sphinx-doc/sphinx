.. _storagebackends:

.. currentmodule:: sphinx.websupport.storage

Storage Backends
================

To create a custom storage backend you will need to subclass the
:class:`StorageBackend` class.  Then create an instance of the new class and
pass that as the `storage` keyword argument when you create the
:class:`~.WebSupport` object::

   support = WebSupport(srcdir=srcdir,
                        builddir=builddir,
                        storage=MyStorage())

For more information about creating a custom storage backend, please see the
documentation of the :class:`StorageBackend` class below.

.. class:: StorageBackend

   Defines an interface for storage backends.


StorageBackend Methods
~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: StorageBackend.pre_build

.. automethod:: StorageBackend.add_node

.. automethod:: StorageBackend.post_build

.. automethod:: StorageBackend.add_comment

.. automethod:: StorageBackend.delete_comment

.. automethod:: StorageBackend.get_data

.. automethod:: StorageBackend.process_vote

.. automethod:: StorageBackend.update_username

.. automethod:: StorageBackend.accept_comment
