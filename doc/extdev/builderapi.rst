.. _writing-builders:

Builder API
===========

.. currentmodule:: sphinx.builders

.. class:: Builder

   This is the base class for all builders.

   It follows this basic workflow:

   .. graphviz:: /_static/diagrams/sphinx_build_flow.dot
      :caption: UML for the standard Sphinx build workflow

   .. rubric:: Overridable Attributes

   These attributes should be set on builder sub-classes:

   .. autoattribute:: name
   .. autoattribute:: format
   .. autoattribute:: epilog
   .. autoattribute:: allow_parallel
   .. autoattribute:: supported_image_types
   .. autoattribute:: supported_remote_images
   .. autoattribute:: supported_data_uri_images
   .. autoattribute:: default_translator_class

   .. rubric:: Core Methods

   These methods are predefined and should generally not be overridden,
   since they form the core of the build process:

   .. automethod:: build_all
   .. automethod:: build_specific
   .. automethod:: build_update
   .. automethod:: build
   .. automethod:: read
   .. automethod:: read_doc
   .. automethod:: write_doctree

   .. rubric:: Overridable Methods

   These must be implemented in builder sub-classes:

   .. automethod:: get_outdated_docs
   .. automethod:: prepare_writing
   .. automethod:: write_doc
   .. automethod:: get_target_uri

   These methods can be overridden in builder sub-classes:

   .. automethod:: init
   .. automethod:: write
   .. automethod:: copy_assets
   .. automethod:: get_relative_uri
   .. automethod:: finish

   .. rubric:: Attributes

   Attributes that are callable from the builder instance:

   .. attribute:: events

      An :class:`.EventManager` object.
