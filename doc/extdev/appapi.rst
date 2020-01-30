.. highlight:: rest

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

.. automethod:: Sphinx.setup_extension(name)

.. automethod:: Sphinx.require_sphinx(version)

.. automethod:: Sphinx.connect(event, callback)

.. automethod:: Sphinx.disconnect(listener_id)

.. automethod:: Sphinx.add_builder(builder)

.. automethod:: Sphinx.add_config_value(name, default, rebuild)

.. automethod:: Sphinx.add_event(name)

.. automethod:: Sphinx.set_translator(name, translator_class)

.. automethod:: Sphinx.add_node(node, \*\*kwds)

.. automethod:: Sphinx.add_enumerable_node(node, figtype, title_getter=None, \*\*kwds)

.. method:: Sphinx.add_directive(name, func, content, arguments, \*\*options)
.. automethod:: Sphinx.add_directive(name, directiveclass)

.. automethod:: Sphinx.add_role(name, role)

.. automethod:: Sphinx.add_generic_role(name, nodeclass)

.. automethod:: Sphinx.add_domain(domain)

.. automethod:: Sphinx.override_domain(domain)

.. method:: Sphinx.add_directive_to_domain(domain, name, func, content, arguments, \*\*options)
.. automethod:: Sphinx.add_directive_to_domain(domain, name, directiveclass)

.. automethod:: Sphinx.add_role_to_domain(domain, name, role)

.. automethod:: Sphinx.add_index_to_domain(domain, index)

.. automethod:: Sphinx.add_object_type(directivename, rolename, indextemplate='', parse_node=None, ref_nodeclass=None, objname='', doc_field_types=[])

.. automethod:: Sphinx.add_crossref_type(directivename, rolename, indextemplate='', ref_nodeclass=None, objname='')

.. automethod:: Sphinx.add_transform(transform)

.. automethod:: Sphinx.add_post_transform(transform)

.. automethod:: Sphinx.add_js_file(filename, **kwargs)

.. automethod:: Sphinx.add_css_file(filename, **kwargs)

.. automethod:: Sphinx.add_latex_package(packagename, options=None)

.. automethod:: Sphinx.add_lexer(alias, lexer)

.. automethod:: Sphinx.add_autodocumenter(cls)

.. automethod:: Sphinx.add_autodoc_attrgetter(type, getter)

.. automethod:: Sphinx.add_search_language(cls)

.. automethod:: Sphinx.add_source_suffix(suffix, filetype)

.. automethod:: Sphinx.add_source_parser(parser)

.. automethod:: Sphinx.add_env_collector(collector)

.. automethod:: Sphinx.add_html_theme(name, theme_path)

.. automethod:: Sphinx.add_html_math_renderer(name, inline_renderers, block_renderers)

.. automethod:: Sphinx.add_message_catalog(catalog, locale_dir)

.. automethod:: Sphinx.is_parallel_allowed(typ)

.. exception:: ExtensionError

   All these methods raise this exception if something went wrong with the
   extension API.


Emitting events
---------------

.. class:: Sphinx

   .. automethod:: emit(event, \*arguments)

   .. automethod:: emit_firstresult(event, \*arguments)


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


.. _events:

Sphinx core events
------------------

These events are known to the core.  The arguments shown are given to the
registered event handlers.  Use :meth:`.Sphinx.connect` in an extension's
``setup`` function (note that ``conf.py`` can also have a ``setup`` function) to
connect handlers to the events.  Example:

.. code-block:: python

   def source_read_handler(app, docname, source):
       print('do something here...')

   def setup(app):
       app.connect('source-read', source_read_handler)


.. event:: builder-inited (app)

   Emitted when the builder object has been created.  It is available as
   ``app.builder``.

.. event:: config-inited (app, config)

   Emitted when the config object has been initialized.

   .. versionadded:: 1.8

.. event:: env-get-outdated (app, env, added, changed, removed)

   Emitted when the environment determines which source files have changed and
   should be re-read.  *added*, *changed* and *removed* are sets of docnames
   that the environment has determined.  You can return a list of docnames to
   re-read in addition to these.

   .. versionadded:: 1.1

.. event:: env-purge-doc (app, env, docname)

   Emitted when all traces of a source file should be cleaned from the
   environment, that is, if the source file is removed or before it is freshly
   read.  This is for extensions that keep their own caches in attributes of the
   environment.

   For example, there is a cache of all modules on the environment.  When a
   source file has been changed, the cache's entries for the file are cleared,
   since the module declarations could have been removed from the file.

   .. versionadded:: 0.5

.. event:: env-before-read-docs (app, env, docnames)

   Emitted after the environment has determined the list of all added and
   changed files and just before it reads them.  It allows extension authors to
   reorder the list of docnames (*inplace*) before processing, or add more
   docnames that Sphinx did not consider changed (but never add any docnames
   that are not in ``env.found_docs``).

   You can also remove document names; do this with caution since it will make
   Sphinx treat changed files as unchanged.

   .. versionadded:: 1.3

.. event:: source-read (app, docname, source)

   Emitted when a source file has been read.  The *source* argument is a list
   whose single element is the contents of the source file.  You can process the
   contents and replace this item to implement source-level transformations.

   For example, if you want to use ``$`` signs to delimit inline math, like in
   LaTeX, you can use a regular expression to replace ``$...$`` by
   ``:math:`...```.

   .. versionadded:: 0.5

.. event:: object-description-transform (app, domain, objtype, contentnode)

   Emitted when an object description directive has run.  The *domain* and
   *objtype* arguments are strings indicating object description of the object.
   And *contentnode* is a content for the object.  It can be modified in-place.

   .. versionadded:: 2.4

.. event:: doctree-read (app, doctree)

   Emitted when a doctree has been parsed and read by the environment, and is
   about to be pickled.  The *doctree* can be modified in-place.

.. event:: missing-reference (app, env, node, contnode)

   Emitted when a cross-reference to a Python module or object cannot be
   resolved.  If the event handler can resolve the reference, it should return a
   new docutils node to be inserted in the document tree in place of the node
   *node*.  Usually this node is a :class:`reference` node containing *contnode*
   as a child.

   :param env: The build environment (``app.builder.env``).
   :param node: The :class:`pending_xref` node to be resolved.  Its attributes
      ``reftype``, ``reftarget``, ``modname`` and ``classname`` attributes
      determine the type and target of the reference.
   :param contnode: The node that carries the text and formatting inside the
      future reference and should be a child of the returned reference node.

   .. versionadded:: 0.5

.. event:: doctree-resolved (app, doctree, docname)

   Emitted when a doctree has been "resolved" by the environment, that is, all
   references have been resolved and TOCs have been inserted.  The *doctree* can
   be modified in place.

   Here is the place to replace custom nodes that don't have visitor methods in
   the writers, so that they don't cause errors when the writers encounter them.

.. event:: env-merge-info (app, env, docnames, other)

   This event is only emitted when parallel reading of documents is enabled.  It
   is emitted once for every subprocess that has read some documents.

   You must handle this event in an extension that stores data in the
   environment in a custom location.  Otherwise the environment in the main
   process will not be aware of the information stored in the subprocess.

   *other* is the environment object from the subprocess, *env* is the
   environment from the main process.  *docnames* is a set of document names
   that have been read in the subprocess.

   For a sample of how to deal with this event, look at the standard
   ``sphinx.ext.todo`` extension.  The implementation is often similar to that
   of :event:`env-purge-doc`, only that information is not removed, but added to
   the main environment from the other environment.

   .. versionadded:: 1.3

.. event:: env-updated (app, env)

   Emitted when the :meth:`update` method of the build environment has
   completed, that is, the environment and all doctrees are now up-to-date.

   You can return an iterable of docnames from the handler.  These documents
   will then be considered updated, and will be (re-)written during the writing
   phase.

   .. versionadded:: 0.5

   .. versionchanged:: 1.3
      The handlers' return value is now used.

.. event:: env-check-consistency (app, env)

   Emitted when Consistency checks phase.  You can check consistency of
   metadata for whole of documents.

   .. versionadded:: 1.6

      As a **experimental** event

.. event:: html-collect-pages (app)

   Emitted when the HTML builder is starting to write non-document pages.  You
   can add pages to write by returning an iterable from this event consisting of
   ``(pagename, context, templatename)``.

   .. versionadded:: 1.0

.. event:: html-page-context (app, pagename, templatename, context, doctree)

   Emitted when the HTML builder has created a context dictionary to render a
   template with -- this can be used to add custom elements to the context.

   The *pagename* argument is the canonical name of the page being rendered,
   that is, without ``.html`` suffix and using slashes as path separators.  The
   *templatename* is the name of the template to render, this will be
   ``'page.html'`` for all pages from reST documents.

   The *context* argument is a dictionary of values that are given to the
   template engine to render the page and can be modified to include custom
   values.  Keys must be strings.

   The *doctree* argument will be a doctree when the page is created from a reST
   documents; it will be ``None`` when the page is created from an HTML template
   alone.

   You can return a string from the handler, it will then replace
   ``'page.html'`` as the HTML template for this page.

   .. versionadded:: 0.4

   .. versionchanged:: 1.3
      The return value can now specify a template name.

.. event:: build-finished (app, exception)

   Emitted when a build has finished, before Sphinx exits, usually used for
   cleanup.  This event is emitted even when the build process raised an
   exception, given as the *exception* argument.  The exception is reraised in
   the application after the event handlers have run.  If the build process
   raised no exception, *exception* will be ``None``.  This allows to customize
   cleanup actions depending on the exception status.

   .. versionadded:: 0.5


Checking the Sphinx version
---------------------------

.. currentmodule:: sphinx

Use this to adapt your extension to API changes in Sphinx.

.. autodata:: version_info


The Config object
-----------------

.. currentmodule:: sphinx.config

.. autoclass:: Config


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
