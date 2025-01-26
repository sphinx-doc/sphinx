.. _domain-api:

Domain API
==========

.. module:: sphinx.domains

.. autoclass:: Domain
   :members:

.. autoclass:: ObjType

.. autoclass:: Index
   :members:

.. autoclass:: IndexEntry
   :members:
   :member-order: bysource

.. module:: sphinx.directives

.. autoclass:: ObjectDescription
   :members:
   :private-members: _toc_entry_name, _object_hierarchy_parts

Python Domain
-------------

.. module:: sphinx.domains.python

.. autoclass:: PythonDomain

   .. autoattribute:: objects
   .. autoattribute:: modules
   .. automethod:: note_object
   .. automethod:: note_module
