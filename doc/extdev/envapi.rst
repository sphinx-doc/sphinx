Build environment API
=====================

.. module:: sphinx.environment

.. class:: BuildEnvironment

   **Attributes**

   .. attribute:: app

      Reference to the :class:`.Sphinx` (application) object.

   .. attribute:: config

      Reference to the :class:`.Config` object.

   .. attribute:: srcdir

      Source directory.

   .. attribute:: confdir

      Directory containing ``conf.py``.

   .. attribute:: doctreedir

      Directory for storing pickled doctrees.

   .. attribute:: found_docs

      A set of all existing docnames.

   .. attribute:: metadata

      Dictionary mapping docnames to "metadata" (see :ref:`metadata`).

   .. attribute:: titles

      Dictionary mapping docnames to the docutils node for their main title.

   .. autoattribute:: docname

   **Utility methods**

   .. automethod:: warn

   .. automethod:: warn_node

   .. automethod:: doc2path

   .. automethod:: relfn2path

   .. automethod:: note_dependency

   .. automethod:: new_serialno

   .. automethod:: note_reread
