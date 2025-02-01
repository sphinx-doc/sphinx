Build environment API
=====================

.. module:: sphinx.environment

.. class:: BuildEnvironment

   **Attributes**

   .. attribute:: app

      Reference to the :class:`.Sphinx` (application) object.

   .. attribute:: config

      Reference to the :class:`.Config` object.

   .. attribute:: project

      Target project.  See :class:`.Project`.

   .. attribute:: srcdir

      Source directory.

   .. attribute:: doctreedir

      Directory for storing pickled doctrees.

   .. attribute:: events

      An :class:`.EventManager` object.

   .. attribute:: found_docs

      A set of all existing docnames.

   .. attribute:: metadata

      Dictionary mapping docnames to "metadata" (see :ref:`metadata`).

   .. attribute:: titles

      Dictionary mapping docnames to the docutils node for their main title.

   .. autoattribute:: docname

   .. autoattribute:: parser

   **Per-document attributes**

   .. attribute:: current_document

      Temporary data storage while reading a document.

      Extensions may use the mapping interface provided by
      ``env.current_document`` to store data relating to the current document,
      but should use a unique prefix to avoid name clashes.

      .. important::
         Only the following attributes constitute the public API.
         The type itself and any methods or other attributes remain private,
         experimental, and will be changed or removed without notice.

      .. attribute:: current_document.docname
         :type: str

         The document name ('docname') for the current document.

      .. attribute:: current_document.default_role
         :type: str

         The default role for the current document.
         Set by the :dudir:`default-role` directive.

      .. attribute:: current_document.default_domain
         :type: Domain | None

         The default domain for the current document.
         Set by the :rst:dir:`default-domain` directive.

      .. attribute:: current_document.highlight_language
         :type: str

         The default language for syntax highlighting.
         Set by the :rst:dir:`highlight` directive to override
         the :confval:`highlight_language` config value.

      .. attribute:: current_document._parser
         :type: Parser | None

         *This attribute is experimental and may be changed without notice.*

         The parser being used to parse the current document.

   **Utility methods**

   .. automethod:: doc2path

   .. automethod:: relfn2path

   .. automethod:: note_dependency

   .. automethod:: new_serialno

   .. automethod:: note_reread
