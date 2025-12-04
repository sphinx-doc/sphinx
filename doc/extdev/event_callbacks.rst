.. _events:

Event callbacks API
===================

Connecting callback functions to events is a simple way to extend Sphinx,
by hooking into the build process at various points.

Use :meth:`.Sphinx.connect` in an extension's ``setup`` function,
or a ``setup`` function in your project's :file:`conf.py`,
to connect functions to the events:

.. code-block:: python

   def source_read_handler(app, docname, source):
       print('do something here...')

   def setup(app):
       app.connect('source-read', source_read_handler)

.. seealso::

   Extensions can add their own events by using :meth:`.Sphinx.add_event`,
   and calling them them with
   :meth:`.EventManager.emit` or :meth:`.EventManager.emit_firstresult`.

Core events overview
--------------------

Below is an overview of the core event that happens during a build.

.. code-block:: none

   1. event.config-inited(app,config)
   2. event.builder-inited(app)
   3. event.env-get-outdated(app, env, added, changed, removed)
   4. event.env-before-read-docs(app, env, docnames)

   for docname in docnames:
      5. event.env-purge-doc(app, env, docname)

      if doc changed and not removed:
         6. source-read(app, docname, source)
         7. run source parsers: text -> docutils.document
            - parsers can be added with the app.add_source_parser() API
            - event.include-read(app, relative_path, parent_docname, content)
              is called for each include directive
         8. apply transforms based on priority: docutils.document -> docutils.document
            - event.doctree-read(app, doctree) is called in the middle of transforms,
              transforms come before/after this event depending on their priority.

   9. event.env-merge-info(app, env, docnames, other)
      - if running in parallel mode, this event will be emitted for each process

   10. event.env-updated(app, env)
   11. event.env-get-updated(app, env)

   if environment is written to disk:
      12. event.env-check-consistency(app, env)

   13. event.write-started(app, builder)
       - This is called after ``app.parallel_ok`` has been set,
         which must not be altered by any event handler.

   # The updated-docs list can be builder dependent, but generally includes all new/changed documents,
   # plus any output from `env-get-updated`, and then all "parent" documents in the ToC tree
   # For builders that output a single page, they are first joined into a single doctree before post-transforms
   # or the doctree-resolved event is emitted
   for docname in updated-docs:
      14. apply post-transforms (by priority): docutils.document -> docutils.document
      15. event.doctree-resolved(app, doctree, docname)
          - In the event that any reference nodes fail to resolve, the following may emit:
          - event.missing-reference(app, env, node, contnode)
          - event.warn-missing-reference(app, domain, node)

   16. Generate output files
   17. event.build-finished(app, exception)

Here is also a flow diagram of the events,
within the context of the Sphinx build process:

.. graphviz:: /_static/diagrams/sphinx_core_events_flow.dot
   :caption: Sphinx core events flow

Core event details
------------------

Here is a more detailed list of these events.

.. event:: config-inited (app, config)

   :param app: :class:`.Sphinx`
   :param config: :class:`.Config`

   Emitted when the config object has been initialized.

   .. versionadded:: 1.8

.. event:: builder-inited (app)

   :param app: :class:`.Sphinx`

   Emitted when the builder object has been created
   (available as ``app.builder``).

.. event:: env-get-outdated (app, env, added, changed, removed)

   :param app: :class:`.Sphinx`
   :param env: :class:`.BuildEnvironment`
   :param added: ``Set[str]``
   :param changed: ``Set[str]``
   :param removed: ``Set[str]``
   :returns: ``Sequence[str]`` of additional docnames to re-read

   Emitted when the environment determines which source files have changed and
   should be re-read.
   *added*, *changed* and *removed* are sets of docnames
   that the environment has determined.
   You can return a list of docnames to re-read in addition to these.

   .. versionadded:: 1.1

.. event:: env-purge-doc (app, env, docname)

   :param app: :class:`.Sphinx`
   :param env: :class:`.BuildEnvironment`
   :param docname: ``str``

   Emitted when all traces of a source file should be cleaned from the
   environment, that is, if the source file is removed or before it is freshly read.
   This is for extensions that keep their own caches
   in attributes of the environment.

   For example, there is a cache of all modules on the environment.
   When a source file has been changed, the cache's entries for the file are cleared,
   since the module declarations could have been removed from the file.

   .. versionadded:: 0.5

.. event:: env-before-read-docs (app, env, docnames)

   :param app: :class:`.Sphinx`
   :param env: :class:`.BuildEnvironment`
   :param docnames: ``list[str]``

   Emitted after the environment has determined the list of all added and
   changed files and just before it reads them.
   It allows extension authors to reorder
   the list of docnames (*inplace*) before processing,
   or add more docnames that Sphinx did not consider changed
   (but never add any docnames that are not in :attr:`.found_docs`).

   You can also remove document names; do this with caution since it will make
   Sphinx treat changed files as unchanged.

   .. versionadded:: 1.3

.. event:: source-read (app, docname, content)

   :param app: :class:`.Sphinx`
   :param docname: ``str``
   :param content: ``list[str]``
      with a single element,
      representing the content of the included file.

   Emitted when a source file has been read.

   You can process the ``content`` and
   replace this item to implement source-level transformations.

   For example, if you want to use ``$`` signs to delimit inline math, like in
   LaTeX, you can use a regular expression to replace ``$...$`` by
   ``:math:`...```.

   .. versionadded:: 0.5

.. event:: include-read (app, relative_path, parent_docname, content)

   :param app: :class:`.Sphinx`
   :param relative_path: :class:`~pathlib.Path`
      representing the included file
      relative to the :term:`source directory`.
   :param parent_docname: ``str``
      of the document name that
      contains the :dudir:`include` directive.
   :param content: ``list[str]``
      with a single element,
      representing the content of the included file.

   Emitted when a file has been read with the :dudir:`include` directive.

   You can process the ``content`` and replace this item
   to transform the included content, as with the :event:`source-read` event.

   .. versionadded:: 7.2.5

   .. seealso:: The :dudir:`include` directive and the :event:`source-read` event.

.. event:: object-description-transform (app, domain, objtype, contentnode)

   :param app: :class:`.Sphinx`
   :param domain: ``str``
   :param objtype: ``str``
   :param contentnode: :class:`.desc_content`

   Emitted when an object description directive has run.  The *domain* and
   *objtype* arguments are strings indicating object description of the object.
   And *contentnode* is a content for the object.  It can be modified in-place.

   .. versionadded:: 2.4

.. event:: doctree-read (app, doctree)

   :param app: :class:`.Sphinx`
   :param doctree: :class:`docutils.nodes.document`

   Emitted when a doctree has been parsed and read by the environment, and is
   about to be pickled.
   The ``doctree`` can be modified in-place.

.. event:: missing-reference (app, env, node, contnode)

   :param app: :class:`.Sphinx`
   :param env: :class:`.BuildEnvironment`
   :param node: The :class:`.pending_xref` node to be resolved.
      Its ``reftype``, ``reftarget``, ``modname`` and ``classname`` attributes
      determine the type and target of the reference.
   :param contnode: The node that carries the text and formatting inside the
      future reference and should be a child of the returned reference node.
   :returns: A new node to be inserted in the document tree in place of the node,
      or ``None`` to let other handlers try.

   Emitted when a cross-reference to an object cannot be resolved.
   If the event handler can resolve the reference, it should return a
   new docutils node to be inserted in the document tree in place of the node
   *node*.  Usually this node is a :class:`~nodes.reference` node containing
   *contnode* as a child.
   If the handler can not resolve the cross-reference,
   it can either return ``None`` to let other handlers try,
   or raise :class:`~sphinx.errors.NoUri` to prevent other handlers in
   trying and suppress a warning about this cross-reference being unresolved.

   .. versionadded:: 0.5

.. event:: warn-missing-reference (app, domain, node)

   :param app: :class:`.Sphinx`
   :param domain: The :class:`.Domain` of the missing reference.
   :param node: The :class:`.pending_xref` node that could not be resolved.
   :returns: ``True`` if a warning was emitted, else ``None``

   Emitted when a cross-reference to an object cannot be resolved even after
   :event:`missing-reference`.
   If the event handler can emit warnings for the missing reference,
   it should return ``True``.
   The configuration variables
   :confval:`nitpick_ignore` and :confval:`nitpick_ignore_regex`
   prevent the event from being emitted for the corresponding nodes.

   .. versionadded:: 3.4

.. event:: doctree-resolved (app, doctree, docname)

   :param app: :class:`.Sphinx`
   :param doctree: :class:`docutils.nodes.document`
   :param docname: ``str``

   Emitted when a doctree has been "resolved" by the environment, that is, all
   references have been resolved and TOCs have been inserted.  The *doctree* can
   be modified in place.

   Here is the place to replace custom nodes that don't have visitor methods in
   the writers, so that they don't cause errors when the writers encounter them.

.. event:: env-merge-info (app, env, docnames, other)

   :param app: :class:`.Sphinx`
   :param env: :class:`.BuildEnvironment`
   :param docnames: ``list[str]``
   :param other: :class:`.BuildEnvironment`

   This event is only emitted when parallel reading of documents is enabled.  It
   is emitted once for every subprocess that has read some documents.

   You must handle this event in an extension that stores data in the
   environment in a custom location.  Otherwise the environment in the main
   process will not be aware of the information stored in the subprocess.

   *other* is the environment object from the subprocess, *env* is the
   environment from the main process.  *docnames* is a set of document names
   that have been read in the subprocess.

   .. versionadded:: 1.3

.. event:: env-updated (app, env)

   :param app: :class:`.Sphinx`
   :param env: :class:`.BuildEnvironment`
   :returns: iterable of ``str``

   Emitted after reading all documents, when the environment and all
   doctrees are now up-to-date.

   You can return an iterable of docnames from the handler.  These documents
   will then be considered updated, and will be (re-)written during the writing
   phase.

   .. versionadded:: 0.5

   .. versionchanged:: 1.3
      The handlers' return value is now used.

.. event:: env-get-updated (app, env)

   :param app: :class:`.Sphinx`
   :param env: :class:`.BuildEnvironment`
   :returns: iterable of ``str``

   Emitted when the environment determines which source files have changed and
   should be re-read.
   You can return an iterable of docnames to re-read.

.. event:: env-check-consistency (app, env)

   :param app: :class:`.Sphinx`
   :param env: :class:`.BuildEnvironment`

   Emitted when Consistency checks phase.  You can check consistency of
   metadata for whole of documents.

   .. versionadded:: 1.6

.. event:: write-started (app, builder)

   :param app: :class:`.Sphinx`
   :param builder: :class:`.Builder`

   Emitted before the builder starts to
   resolve and write documents.

   .. versionadded:: 7.4

.. event:: build-finished (app, exception)

   :param app: :class:`.Sphinx`
   :param exception: ``Exception`` or ``None``

   Emitted when a build has finished, before Sphinx exits, usually used for
   cleanup.  This event is emitted even when the build process raised an
   exception, given as the *exception* argument.  The exception is reraised in
   the application after the event handlers have run.  If the build process
   raised no exception, *exception* will be ``None``.  This allows to customize
   cleanup actions depending on the exception status.

   .. versionadded:: 0.5

Builder specific events
-----------------------

These events are emitted by specific builders.

.. event:: html-collect-pages (app)

   :param app: :class:`.Sphinx`
   :returns: iterable of ``(pagename, context, templatename)``
      where *pagename* and *templatename* are strings and
      *context* is a ``dict[str, Any]``.

   Emitted when the HTML builder is starting to write non-document pages.

   You can add pages to write by returning an iterable from this event.

   .. versionadded:: 1.0

.. event:: html-page-context (app, pagename, templatename, context, doctree)

   :param app: :class:`.Sphinx`
   :param pagename: ``str``
   :param templatename: ``str``
   :param context: ``dict[str, Any]``
   :param doctree: :class:`docutils.nodes.document` or ``None``
   :returns: ``str`` or ``None``

   Emitted when the HTML builder has created a context dictionary to render a
   template with -- this can be used to add custom elements to the context.

   The *pagename* argument is the canonical name of the page being rendered,
   that is, without ``.html`` suffix and using slashes as path separators.
   The *templatename* is the name of the template to render, this will be
   ``'page.html'`` for all pages from reStructuredText documents.

   The *context* argument is a dictionary of values that are given to the
   template engine to render the page and can be modified to include custom
   values.

   The *doctree* argument will be a doctree when
   the page is created from a reStructuredText documents;
   it will be ``None`` when the page is created from an HTML template alone.

   You can return a string from the handler, it will then replace
   ``'page.html'`` as the HTML template for this page.

   .. tip::

      You can install JS/CSS files for the specific page via
      :meth:`.Sphinx.add_js_file` and :meth:`.Sphinx.add_css_file`
      (since v3.5.0).

   .. versionadded:: 0.4

   .. versionchanged:: 1.3
      The return value can now specify a template name.

.. event:: linkcheck-process-uri (app, uri)

   :param app: :class:`.Sphinx`
   :param uri: ``str`` of the collected URI
   :returns: ``str`` or ``None``

   Emitted when the linkcheck builder collects hyperlinks from document.

   The event handlers can modify the URI by returning a string.

   .. versionadded:: 4.1
