.. _domain-api:

Domain API
==========

.. module:: sphinx.domains

.. autoclass:: Domain
   :members:

.. autoclass:: ObjType

.. autoclass:: Index
   :members:

.. module:: sphinx.directives

.. autoclass:: ObjectDescription
   :members:
   :private-members: _table_of_contents_name, _toc_parents

Python Domain
-------------

.. module:: sphinx.domains.python

.. autoclass:: PythonDomain

   .. autoattribute:: objects
   .. autoattribute:: modules
   .. automethod:: note_object
   .. automethod:: note_module
