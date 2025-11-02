.. highlight:: rst

Application API
===============

.. module:: sphinx.application
   :synopsis: Application class and extensibility interface.


Each Sphinx extension is a Python module with at least a :func:`setup`
function.  This function is called at initialization time with one argument,
the application object representing the Sphinx process.

.. class:: Sphinx

   This application object has the public API described in the following.

Extension setup
---------------

These methods are usually called in an extension's ``setup()`` function.

Examples of using the Sphinx extension API can be seen in the :mod:`sphinx.ext`
package.

.. currentmodule:: sphinx.application

.. automethod:: Sphinx.setup_extension

.. automethod:: Sphinx.require_sphinx

.. automethod:: Sphinx.connect

.. automethod:: Sphinx.disconnect

.. automethod:: Sphinx.add_builder

.. automethod:: Sphinx.add_config_value

.. automethod:: Sphinx.add_event

.. automethod:: Sphinx.set_translator

.. automethod:: Sphinx.add_node

.. automethod:: Sphinx.add_enumerable_node

.. automethod:: Sphinx.add_directive

.. automethod:: Sphinx.add_role

.. automethod:: Sphinx.add_generic_role

.. automethod:: Sphinx.add_domain

.. automethod:: Sphinx.add_directive_to_domain

.. automethod:: Sphinx.add_role_to_domain

.. automethod:: Sphinx.add_index_to_domain

.. automethod:: Sphinx.add_object_type

.. automethod:: Sphinx.add_crossref_type

.. automethod:: Sphinx.add_transform

.. automethod:: Sphinx.add_post_transform

.. automethod:: Sphinx.add_js_file
.. versionchanged:: 7.1  Added CRC32 checksums to asset URIs for improved caching and integrity. When JavaScript files are added, a CRC32 checksum is now appended to the URI (e.g. ``_static/example.js?abcd1234``). This helps browsers detect when files have changed and refresh cached versions automatically. For more details, see the 7.1.0 changelog entry: https://www.sphinx-doc.org/en/master/changes.html#release-7-1-0-released-jul-24-2023 Site authors can also use the configuration options :confval:`html_js_files` and :confval:`html_static_path` to manage static JS files. Files in ``html_static_path`` override those added by extensions.
.. automethod:: Sphinx.add_css_file
.. versionchanged:: 7.1
Added CRC32 checksums to asset URIs for CSS files as well, following the same caching and integrity improvements as :meth:`.Sphinx.add_js_file`.h:`.Sphinx.add_js_file`.

.. automethod:: Sphinx.add_latex_package

.. automethod:: Sphinx.add_lexer

.. automethod:: Sphinx.add_autodocumenter

.. automethod:: Sphinx.add_autodoc_attrgetter

.. automethod:: Sphinx.add_search_language

.. automethod:: Sphinx.add_source_suffix

.. automethod:: Sphinx.add_source_parser

.. automethod:: Sphinx.add_env_collector

.. automethod:: Sphinx.add_html_theme

.. automethod:: Sphinx.add_html_math_renderer

.. automethod:: Sphinx.add_message_catalog

.. automethod:: Sphinx.is_parallel_allowed

.. automethod:: Sphinx.set_html_assets_policy

.. exception:: ExtensionError

   All these methods raise this exception if something went wrong with the
   extension API.


Emitting events
---------------

.. class:: Sphinx
   :no-index:

   .. automethod:: emit

   .. automethod:: emit_firstresult


Sphinx runtime information
--------------------------

The application object also provides runtime information as attributes.

.. attribute:: Sphinx.project

   Target project.  See :class:`.Project`.

.. attribute:: Sphinx.srcdir

   Source directory.

.. attribute:: Sphinx.confdir

   Directory containing ``conf.py``.

.. attribute:: Sphinx.doctreedir

   Directory for storing pickled doctrees.

.. attribute:: Sphinx.outdir

   Directory for storing built document.

.. autoattribute:: Sphinx.fresh_env_used

Sphinx core events
------------------

.. note:: Moved to :ref:`events`.

Checking the Sphinx version
---------------------------

.. currentmodule:: sphinx

Use this to adapt your extension to API changes in Sphinx.

.. autodata:: version_info


The Config object
-----------------

.. currentmodule:: sphinx.config

.. autoclass:: Config

.. py:class:: ENUM
   :no-typesetting:


.. _template-bridge:

The template bridge
-------------------

.. currentmodule:: sphinx.application

.. autoclass:: TemplateBridge
   :members:


.. _exceptions:

Exceptions
----------

.. module:: sphinx.errors

.. autoexception:: SphinxError

.. autoexception:: ConfigError

.. autoexception:: ExtensionError

.. autoexception:: ThemeError

.. autoexception:: VersionRequirementError
