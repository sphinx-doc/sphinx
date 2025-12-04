.. _dev-extensions:

Sphinx API
==========

Since many projects will need special features in their documentation, Sphinx
is designed to be extensible on several levels.

Here are a few things you can do in an extension:

* Add new :term:`builder`\s to support new output formats or actions on the
  parsed documents.
* Register custom reStructuredText roles and directives, extending the markup
  using the :doc:`markupapi`.
* Add custom code to so-called "hook points" at strategic places throughout the
  build process, allowing you to register a hook and run specialized code.
  For example, see the :ref:`events`.

An extension is simply a Python module with a ``setup()`` function. A user
activates the extension by placing the extension's module name
(or a sub-module) in their :confval:`extensions` configuration value.

When :program:`sphinx-build` is executed, Sphinx will attempt to import each
module that is listed, and execute ``yourmodule.setup(app)``. This
function is used to prepare the extension (e.g., by executing Python code),
linking resources that Sphinx uses in the build process (like CSS or HTML
files), and notifying Sphinx of everything the extension offers (such
as directive or role definitions). The ``app`` argument is an instance of
:class:`.Sphinx` and gives you control over most aspects of the Sphinx build.

.. note::

    The configuration file itself can be treated as an extension if it
    contains a ``setup()`` function.  All other extensions to load must be
    listed in the :confval:`extensions` configuration value.

The rest of this page describes some high-level aspects of developing
extensions and various parts of Sphinx's behavior that you can control.
For some examples of how extensions can be built and used to control different
parts of Sphinx, see the :ref:`extension-tutorials-index`.

.. _important-objects:

Important objects
-----------------

There are several key objects whose API you will use while writing an
extension. These are:

**Application**
   The application object (usually called ``app``) is an instance of
   :class:`.Sphinx`.
   It controls most high-level functionality, such as loading config,
   initialising the environment, and the setup of extensions.

**Environment**
   The build environment object (usually called ``env``) is an instance of
   :class:`.BuildEnvironment`.  It is responsible for parsing the source
   documents, stores all metadata about the document collection and is
   serialized to disk after each build.

   Its API provides methods to do with access to metadata, resolving references,
   etc.  It can also be used by extensions to cache information that should
   persist for incremental rebuilds.

   If you have the application or builder object, the environment is available
   as ``app.env`` or ``builder.env``.
   In :class:`.SphinxDirective`, :class:`.SphinxRole`, or :class:`.SphinxTransform`
   subclasses, the environment is available as ``self.env``.

**Builder**
   The builder object (usually called ``builder``) is an instance of a specific
   subclass of :class:`.Builder`.  Each builder class knows how to convert the
   parsed documents into an output format, or otherwise process them (e.g. check
   external links).

   If you have the application object, the builder is available as
   ``app.builder``.

**Config**
   The config object (usually called ``config``) provides the values of
   configuration values set in :file:`conf.py` as attributes.  It is an instance
   of :class:`.Config`.

   The config is available as ``env.config``, ``builder.config``, or ``app.config``.
   In :class:`.SphinxDirective`, :class:`.SphinxRole`, or :class:`.SphinxTransform`
   subclasses, the environment is available as ``self.config``.

**Events**
   The event manager object (usually called ``events``) manages and dispatches
   Sphinx's events system.
   It is an instance of :class:`.EventManager`.

   The event manager is available as ``env.events``, ``builder.events``,
   or ``app.events``.

To see an example of use of these objects, refer to
:ref:`the tutorials <extension-tutorials-index>`.

.. _build-phases:

Build phases
------------

One thing that is vital in order to understand extension mechanisms is the way
in which a Sphinx project is built: this works in several phases.

.. graphviz:: /_static/diagrams/sphinx_build_phases.dot
   :caption: Build phases

**Phase 0: Initialization**

In this phase, almost nothing of interest to us happens.  The source
directory is searched for source files, and extensions are initialized.
Should a stored build environment exist, it is loaded, otherwise a new one is
created.

**Phase 1: Reading**

In Phase 1, all source files (and on subsequent builds, those that are new or
changed) are read and parsed.  This is the phase where directives and roles
are encountered by docutils, and the corresponding code is executed.  The
output of this phase is a *doctree* for each source file; that is a tree of
docutils nodes.  For document elements that aren't fully known until all
existing files are read, temporary nodes are created.

There are nodes provided by docutils, which are documented `in the docutils
documentation <https://docutils.sourceforge.io/docs/ref/doctree.html>`__.
Additional nodes are provided by Sphinx and :ref:`documented here <nodes>`.

During reading, the build environment is updated with all meta- and cross
reference data of the read documents, such as labels, the names of headings,
described Python objects and index entries.  This will later be used to
replace the temporary nodes.

The parsed doctrees are stored on the disk, because it is not possible to
hold all of them in memory.

**Phase 2: Consistency checks**

Some checking is done to ensure no surprises in the built documents.

**Phase 3: Resolving**

Now that the metadata and cross-reference data of all existing documents is
known, all temporary nodes are replaced by nodes that can be converted into
output using components called transforms.  For example, links are created
for object references that exist, and simple literal nodes are created for
those that don't.

**Phase 4: Writing**

This phase converts the resolved doctrees to the desired output format, such
as HTML or LaTeX.  This happens via a so-called docutils writer that visits
the individual nodes of each doctree and produces some output in the process.

.. note::

   Some builders deviate from this general build plan, for example, the builder
   that checks external links does not need anything more than the parsed
   doctrees and therefore does not have phases 2--4.

To see an example of application, refer to :ref:`tutorial-extend-build`.

.. _ext-metadata:

Extension metadata
------------------

.. versionadded:: 1.3

The ``setup()`` function should return a dictionary.
This is treated by Sphinx as metadata of the extension.
Metadata keys currently recognized are:

``'version'``
  A string that identifies the extension version.
  It is used for extension version requirement checking
  (see :confval:`needs_extensions`) and informational purposes.
  If no version string is returned, ``'unknown version'`` is used by default.

``'env_version'``
  A non-zero positive integer integer that records
  the version of data stored in the environment by the extension.

  .. attention::
     If ``'env_version'`` is not set, the extension **must not**
     store any data or state directly on the environment object  (``env``).

  This key must be defined if the extension uses the ``env`` object to store data.
  The version number must be incremented whenever the type, structure,  or meaning
  of the stored data change, to ensure Sphinx does not try and load invalid data
  from a cached environment.

  .. versionadded:: 1.8

``'parallel_read_safe'``
  A boolean that specifies if parallel reading of source files
  can be used when the extension is loaded.
  It defaults to ``False``, meaning that you have to explicitly specify
  your extension to be safe for parallel reading after checking that it is.

  .. important::

     When *parallel-read-safe* is ``True``,
     the extension must satisfy the following conditions:

     * The core logic of the extension is parallelly executable during
       the reading phase.
     * It has event handlers for :event:`env-merge-info` and
       :event:`env-purge-doc` events if it stores data to the build
       environment object (``env``) during the reading phase.

``'parallel_write_safe'``
  A boolean that specifies if parallel writing of output files
  can be used when the extension is loaded.
  Since extensions usually don't negatively influence the process,
  this defaults to ``True``.

  .. important::

     When *parallel-write-safe* is ``True``,
     the extension must satisfy the following conditions:

     * The core logic of the extension is parallelly executable during
       the writing phase.


APIs used for writing extensions
--------------------------------

These sections provide a more complete description of the tools at your
disposal when developing Sphinx extensions. Some are core to Sphinx
(such as the :doc:`appapi`) while others trigger specific behavior
(such as the :doc:`i18n`)

.. toctree::
   :maxdepth: 2

   appapi
   event_callbacks
   projectapi
   envapi
   builderapi
   eventapi
   collectorapi
   markupapi
   domainapi
   parserapi
   nodes
   logging
   i18n
   utils
   testing
   deprecated
