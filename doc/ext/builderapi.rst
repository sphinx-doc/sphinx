.. _writing-builders:

Writing new builders
====================

XXX to be expanded.

.. class:: sphinx.builder.Builder

   This is the base class for all builders.

   These methods are predefined and will be called from the application:

   .. automethod:: load_env
   .. automethod:: get_relative_uri
   .. automethod:: build_all
   .. automethod:: build_specific
   .. automethod:: build_update
   .. automethod:: build

   These methods must be overridden in concrete builder classes:

   .. automethod:: init
   .. automethod:: get_outdated_docs
   .. automethod:: get_target_uri
   .. automethod:: prepare_writing
   .. automethod:: write_doc
   .. automethod:: finish
