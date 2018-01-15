.. _writing-builders:

Builder API
===========

.. todo:: Expand this.

.. currentmodule:: sphinx.builders

.. class:: Builder

   This is the base class for all builders.

   These attributes should be set on builder classes:

   .. autoattribute:: name
   .. autoattribute:: format
   .. autoattribute:: epilog
   .. autoattribute:: supported_image_types

   These methods are predefined and will be called from the application:

   .. automethod:: get_relative_uri
   .. automethod:: build_all
   .. automethod:: build_specific
   .. automethod:: build_update
   .. automethod:: build

   These methods can be overridden in concrete builder classes:

   .. automethod:: init
   .. automethod:: get_outdated_docs
   .. automethod:: get_target_uri
   .. automethod:: prepare_writing
   .. automethod:: write_doc
   .. automethod:: finish

