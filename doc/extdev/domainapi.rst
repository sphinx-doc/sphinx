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

.. autofunction:: parse_annotation

   .. versionadded:: 9.3

.. autofunction:: parse_type_parameter_list

   .. versionadded:: 9.3

These functions parse standalone annotation and type parameter fragments into
Python domain signature nodes. Pass the current build environment so type names
use its module and class context. ``parse_type_parameter_list`` accepts the same
multiline and trailing comma flags as Python directives; syntax errors propagate
to the caller.
