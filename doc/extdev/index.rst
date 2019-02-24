.. _dev-extensions:

Developing extensions for Sphinx
================================

Since many projects will need special features in their documentation, Sphinx is
designed to be extensible on several levels.

This is what you can do in an extension: First, you can add new
:term:`builder`\s to support new output formats or actions on the parsed
documents.  Then, it is possible to register custom reStructuredText roles and
directives, extending the markup.  And finally, there are so-called "hook
points" at strategic places throughout the build process, where an extension can
register a hook and run specialized code.

An extension is simply a Python module.  When an extension is loaded, Sphinx
imports this module and executes its ``setup()`` function, which in turn
notifies Sphinx of everything the extension offers -- see the extension tutorial
for examples.

The configuration file itself can be treated as an extension if it contains a
``setup()`` function.  All other extensions to load must be listed in the
:confval:`extensions` configuration value.

Discovery of builders by entry point
------------------------------------

.. versionadded:: 1.6

:term:`Builder` extensions can be discovered by means of `entry points`_ so
that they do not have to be listed in the :confval:`extensions` configuration
value.

Builder extensions should define an entry point in the ``sphinx.builders``
group. The name of the entry point needs to match your builder's
:attr:`~.Builder.name` attribute, which is the name passed to the
:option:`sphinx-build -b` option. The entry point value should equal the
dotted name of the extension module. Here is an example of how an entry point
for 'mybuilder' can be defined in the extension's ``setup.py``::

    setup(
        # ...
        entry_points={
            'sphinx.builders': [
                'mybuilder = my.extension.module',
            ],
        }
    )

Note that it is still necessary to register the builder using
:meth:`~.Sphinx.add_builder` in the extension's :func:`setup` function.

.. _entry points: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins

.. _important-objects:

Important objects
-----------------

There are several key objects whose API you will use while writing an
extension. These are:

**Application**
   The application object (usually called ``app``) is an instance of
   :class:`.Sphinx`.  It controls most high-level functionality, such as the
   setup of extensions, event dispatching and producing output (logging).

   If you have the environment object, the application is available as
   ``env.app``.

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

   The config is available as ``app.config`` or ``env.config``.

To see an example of use of these objects, refer to :doc:`../development/tutorials/index`.

.. _build-phases:

Build Phases
------------

One thing that is vital in order to understand extension mechanisms is the way
in which a Sphinx project is built: this works in several phases.

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
   documentation <http://docutils.sourceforge.net/docs/ref/doctree.html>`__.
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
   output using components called transforms.  For example, links are created for
   object references that exist, and simple literal nodes are created for those
   that don't.

**Phase 4: Writing**

   This phase converts the resolved doctrees to the desired output format, such
   as HTML or LaTeX.  This happens via a so-called docutils writer that visits
   the individual nodes of each doctree and produces some output in the process.

.. note::

   Some builders deviate from this general build plan, for example, the builder
   that checks external links does not need anything more than the parsed
   doctrees and therefore does not have phases 2--4.

To see an example of application, refer to :doc:`../development/tutorials/todo`.

.. _ext-metadata:

Extension metadata
------------------

.. versionadded:: 1.3

The ``setup()`` function can return a dictionary.  This is treated by Sphinx
as metadata of the extension.  Metadata keys currently recognized are:

* ``'version'``: a string that identifies the extension version.  It is used for
  extension version requirement checking (see :confval:`needs_extensions`) and
  informational purposes.  If not given, ``"unknown version"`` is substituted.
* ``'env_version'``: an integer that identifies the version of env data
  structure if the extension stores any data to environment.  It is used to
  detect the data structure has been changed from last build.  The extensions
  have to increment the version when data structure has changed.  If not given,
  Sphinx considers the extension does not stores any data to environment.
* ``'parallel_read_safe'``: a boolean that specifies if parallel reading of
  source files can be used when the extension is loaded.  It defaults to
  ``False``, i.e. you have to explicitly specify your extension to be
  parallel-read-safe after checking that it is.
* ``'parallel_write_safe'``: a boolean that specifies if parallel writing of
  output files can be used when the extension is loaded.  Since extensions
  usually don't negatively influence the process, this defaults to ``True``.

APIs used for writing extensions
--------------------------------

.. toctree::
   :maxdepth: 2

   appapi
   projectapi
   envapi
   builderapi
   collectorapi
   markupapi
   domainapi
   parserapi
   nodes
   logging
   i18n
   utils

.. _dev-deprecated-apis:

Deprecated APIs
---------------

On developing Sphinx, we are always careful to the compatibility of our APIs.
But, sometimes, the change of interface are needed for some reasons.  In such
cases, we've marked them as deprecated. And they are kept during the two
major versions (for more details, please see :ref:`deprecation-policy`).

The following is a list of deprecated interfaces.

.. tabularcolumns:: |>{\raggedright}\Y{.4}|>{\centering}\Y{.1}|>{\centering}\Y{.12}|>{\raggedright\arraybackslash}\Y{.38}|

.. |LaTeXHyphenate| raw:: latex

                    \hspace{0pt}

.. list-table:: deprecated APIs
   :header-rows: 1
   :class: deprecated
   :widths: 40, 10, 10, 40

   * - Target
     - |LaTeXHyphenate|\ Deprecated
     - (will be) Removed
     - Alternatives

   * - ``encoding`` argument of ``autodoc.Documenter.get_doc()``,
       ``autodoc.DocstringSignatureMixin.get_doc()``,
       ``autodoc.DocstringSignatureMixin._find_signature()``, and
       ``autodoc.ClassDocumenter.get_doc()``
     - 2.0
     - 4.0
     - N/A

   * - arguments of ``EpubBuilder.build_mimetype()``,
       ``EpubBuilder.build_container()``, ``EpubBuilder.build_content()``,
       ``EpubBuilder.build_toc()`` and ``EpubBuilder.build_epub()``
     - 2.0
     - 4.0
     - N/A

   * - arguments of ``Epub3Builder.build_navigation_doc()``
     - 2.0
     - 4.0
     - N/A

   * - ``nodetype`` argument of
       ``sphinx.search.WordCollector.is_meta_keywords()``
     - 2.0
     - 4.0
     - N/A

   * - ``suffix`` argument of ``BuildEnvironment.doc2path()``
     - 2.0
     - 4.0
     - N/A

   * - string style ``base`` argument of ``BuildEnvironment.doc2path()``
     - 2.0
     - 4.0
     - ``os.path.join()``

   * - ``sphinx.addnodes.abbreviation``
     - 2.0
     - 4.0
     - ``docutils.nodes.abbreviation``

   * - ``sphinx.builders.applehelp``
     - 2.0
     - 4.0
     - ``sphinxcontrib.applehelp``

   * - ``sphinx.builders.devhelp``
     - 2.0
     - 4.0
     - ``sphinxcontrib.devhelp``

   * - ``sphinx.builders.epub3.Epub3Builder.validate_config_value()``
     - 2.0
     - 4.0
     - ``sphinx.builders.epub3.validate_config_values()``

   * - ``sphinx.builders.html.JSONHTMLBuilder``
     - 2.0
     - 4.0
     - ``sphinx.builders.serializinghtml.JSONHTMLBuilder``

   * - ``sphinx.builders.html.PickleHTMLBuilder``
     - 2.0
     - 4.0
     - ``sphinx.builders.serializinghtml.PickleHTMLBuilder``

   * - ``sphinx.builders.html.SerializingHTMLBuilder``
     - 2.0
     - 4.0
     - ``sphinx.builders.serializinghtml.SerializingHTMLBuilder``

   * - ``sphinx.builders.html.SingleFileHTMLBuilder``
     - 2.0
     - 4.0
     - ``sphinx.builders.singlehtml.SingleFileHTMLBuilder``

   * - ``sphinx.builders.html.WebHTMLBuilder``
     - 2.0
     - 4.0
     - ``sphinx.builders.serializinghtml.PickleHTMLBuilder``

   * - ``sphinx.builders.htmlhelp``
     - 2.0
     - 4.0
     - ``sphinxcontrib.htmlhelp``

   * - ``sphinx.builders.htmlhelp.HTMLHelpBuilder.open_file()``
     - 2.0
     - 4.0
     - ``open()``

   * - ``sphinx.builders.qthelp``
     - 2.0
     - 4.0
     - ``sphinxcontrib.qthelp``

   * - ``sphinx.cmd.quickstart.term_decode()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.cmd.quickstart.TERM_ENCODING``
     - 2.0
     - 4.0
     - ``sys.stdin.encoding``

   * - ``sphinx.config.check_unicode()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.config.string_classes``
     - 2.0
     - 4.0
     - ``[str]``

   * - ``sphinx.domains.cpp.DefinitionError.description``
     - 2.0
     - 4.0
     - ``str(exc)``

   * - ``sphinx.domains.cpp.NoOldIdError.description``
     - 2.0
     - 4.0
     - ``str(exc)``

   * - ``sphinx.domains.cpp.UnsupportedMultiCharacterCharLiteral.decoded``
     - 2.0
     - 4.0
     - ``str(exc)``

   * - ``sphinx.ext.autosummary.Autosummary.warn()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.ext.autosummary.Autosummary.genopt``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.ext.autosummary.Autosummary.warnings``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.ext.autosummary.Autosummary.result``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.ext.doctest.doctest_encode()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.ext.jsmath``
     - 2.0
     - 4.0
     - ``sphinxcontrib.jsmath``

   * - ``sphinx.roles.abbr_role()``
     - 2.0
     - 4.0
     - ``sphinx.roles.Abbreviation``

   * - ``sphinx.roles.emph_literal_role()``
     - 2.0
     - 4.0
     - ``sphinx.roles.EmphasizedLiteral``

   * - ``sphinx.roles.menusel_role()``
     - 2.0
     - 4.0
     - ``sphinx.roles.GUILabel`` or ``sphinx.roles.MenuSelection``

   * - ``sphinx.roles.index_role()``
     - 2.0
     - 4.0
     - ``sphinx.roles.Index``

   * - ``sphinx.roles.indexmarkup_role()``
     - 2.0
     - 4.0
     - ``sphinx.roles.PEP`` or ``sphinx.roles.RFC``

   * - ``sphinx.testing.util.remove_unicode_literal()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.util.attrdict``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.util.force_decode()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.util.get_matching_docs()``
     - 2.0
     - 4.0
     - ``sphinx.util.get_matching_files()``

   * - ``sphinx.util.inspect.Parameter``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.util.jsonimpl``
     - 2.0
     - 4.0
     - ``sphinxcontrib.serializinghtml.jsonimpl``

   * - ``sphinx.util.osutil.EEXIST``
     - 2.0
     - 4.0
     - ``errno.EEXIST`` or ``FileExistsError``

   * - ``sphinx.util.osutil.EINVAL``
     - 2.0
     - 4.0
     - ``errno.EINVAL``

   * - ``sphinx.util.osutil.ENOENT``
     - 2.0
     - 4.0
     - ``errno.ENOENT`` or ``FileNotFoundError``

   * - ``sphinx.util.osutil.EPIPE``
     - 2.0
     - 4.0
     - ``errno.ENOENT`` or ``BrokenPipeError``

   * - ``sphinx.util.osutil.walk()``
     - 2.0
     - 4.0
     - ``os.walk()``

   * - ``sphinx.util.pycompat.NoneType``
     - 2.0
     - 4.0
     - ``sphinx.util.typing.NoneType``

   * - ``sphinx.util.pycompat.TextIOWrapper``
     - 2.0
     - 4.0
     - ``io.TextIOWrapper``

   * - ``sphinx.util.pycompat.UnicodeMixin``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.util.pycompat.htmlescape()``
     - 2.0
     - 4.0
     - ``html.escape()``

   * - ``sphinx.util.pycompat.indent()``
     - 2.0
     - 4.0
     - ``textwrap.indent()``

   * - ``sphinx.util.pycompat.sys_encoding``
     - 2.0
     - 4.0
     - ``sys.getdefaultencoding()``

   * - ``sphinx.util.pycompat.terminal_safe()``
     - 2.0
     - 4.0
     - ``sphinx.util.console.terminal_safe()``

   * - ``sphinx.util.pycompat.u``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.util.PeekableIterator``
     - 2.0
     - 4.0
     - N/A

   * - Omitting the ``filename`` argument in an overriddent
       ``IndexBuilder.feed()`` method.
     - 2.0
     - 4.0
     - ``IndexBuilder.feed(docname, filename, title, doctree)``

   * - ``sphinx.writers.latex.ExtBabel``
     - 2.0
     - 4.0
     - ``sphinx.builders.latex.util.ExtBabel``

   * - ``sphinx.writers.latex.LaTeXTranslator.babel_defmacro()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.application.Sphinx._setting_up_extension``
     - 2.0
     - 3.0
     - N/A

   * - The ``importer`` argument of ``sphinx.ext.autodoc.importer._MockModule``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.ext.autodoc.importer._MockImporter``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.io.SphinxBaseFileInput``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.io.SphinxFileInput.supported``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.io.SphinxRSTFileInput``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.registry.SphinxComponentRegistry.add_source_input()``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator._make_visit_admonition()``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.collect_footnotes()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.writers.texinfo.TexinfoTranslator._make_visit_admonition()``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.writers.text.TextTranslator._make_depart_admonition()``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.generate_numfig_format()``
     - 2.0
     - 4.0
     - N/A

   * - :rst:dir:`highlightlang`
     - 1.8
     - 4.0
     - :rst:dir:`highlight`

   * - :meth:`~sphinx.application.Sphinx.add_stylesheet()`
     - 1.8
     - 4.0
     - :meth:`~sphinx.application.Sphinx.add_css_file()`

   * - :meth:`~sphinx.application.Sphinx.add_javascript()`
     - 1.8
     - 4.0
     - :meth:`~sphinx.application.Sphinx.add_js_file()`

   * - :confval:`autodoc_default_flags`
     - 1.8
     - 4.0
     - :confval:`autodoc_default_options`

   * - ``content`` arguments of ``sphinx.util.image.guess_mimetype()``
     - 1.8
     - 3.0
     - N/A

   * - ``gettext_compact`` arguments of
       ``sphinx.util.i18n.find_catalog_source_files()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.io.SphinxI18nReader.set_lineno_for_reporter()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.io.SphinxI18nReader.line``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.directives.other.VersionChanges``
     - 1.8
     - 3.0
     - ``sphinx.domains.changeset.VersionChanges``

   * - ``sphinx.highlighting.PygmentsBridge.unhighlight()``
     - 1.8
     - 3.0
     - N/A

   * - ``trim_doctest_flags`` arguments of
       ``sphinx.highlighting.PygmentsBridge``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.ext.mathbase``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.ext.mathbase.MathDomain``
     - 1.8
     - 3.0
     - ``sphinx.domains.math.MathDomain``

   * - ``sphinx.ext.mathbase.MathDirective``
     - 1.8
     - 3.0
     - ``sphinx.directives.patches.MathDirective``

   * - ``sphinx.ext.mathbase.math_role()``
     - 1.8
     - 3.0
     - ``docutils.parsers.rst.roles.math_role()``

   * - ``sphinx.ext.mathbase.setup_math()``
     - 1.8
     - 3.0
     - :meth:`~sphinx.application.Sphinx.add_html_math_renderer()`

   * - ``sphinx.ext.mathbase.is_in_section_title()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.ext.mathbase.get_node_equation_number()``
     - 1.8
     - 3.0
     - ``sphinx.util.math.get_node_equation_number()``

   * - ``sphinx.ext.mathbase.wrap_displaymath()``
     - 1.8
     - 3.0
     - ``sphinx.util.math.wrap_displaymath()``

   * - ``sphinx.ext.mathbase.math`` (node)
     - 1.8
     - 3.0
     - ``docutils.nodes.math``

   * - ``sphinx.ext.mathbase.displaymath`` (node)
     - 1.8
     - 3.0
     - ``docutils.nodes.math_block``

   * - ``sphinx.ext.mathbase.eqref`` (node)
     - 1.8
     - 3.0
     - ``sphinx.builders.latex.nodes.math_reference``

   * - ``viewcode_import`` (config value)
     - 1.8
     - 3.0
     - :confval:`viewcode_follow_imported_members`

   * - ``sphinx.writers.latex.Table.caption_footnotetexts``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.Table.header_footnotetexts``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.footnotestack``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.in_container_literal_block``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.next_section_ids``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.next_hyperlink_ids``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.restrict_footnote()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.unrestrict_footnote()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.push_hyperlink_ids()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.pop_hyperlink_ids()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.bibitems``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.hlsettingstack``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.ExtBabel.get_shorthandoff()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.html.HTMLTranslator.highlightlang()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.html.HTMLTranslator.highlightlang_base()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.html.HTMLTranslator.highlightlangopts()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.html.HTMLTranslator.highlightlinenothreshold()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.html5.HTMLTranslator.highlightlang()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.html5.HTMLTranslator.highlightlang_base()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.html5.HTMLTranslator.highlightlangopts()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.html5.HTMLTranslator.highlightlinenothreshold()``
     - 1.8
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.check_latex_elements()``
     - 1.8
     - 3.0
     - Nothing

   * - ``sphinx.application.CONFIG_FILENAME``
     - 1.8
     - 3.0
     - ``sphinx.config.CONFIG_FILENAME``

   * - ``Config.check_unicode()``
     - 1.8
     - 3.0
     - ``sphinx.config.check_unicode()``

   * - ``Config.check_types()``
     - 1.8
     - 3.0
     - ``sphinx.config.check_confval_types()``

   * - ``dirname``, ``filename`` and ``tags`` arguments of
       ``Config.__init__()``
     - 1.8
     - 3.0
     - ``Config.read()``

   * - The value of :confval:`html_search_options`
     - 1.8
     - 3.0
     - see :confval:`html_search_options`

   * - ``sphinx.versioning.prepare()``
     - 1.8
     - 3.0
     - ``sphinx.versioning.UIDTransform``

   * - ``Sphinx.override_domain()``
     - 1.8
     - 3.0
     - :meth:`~sphinx.application.Sphinx.add_domain()`

   * - ``Sphinx.import_object()``
     - 1.8
     - 3.0
     - ``sphinx.util.import_object()``

   * - ``suffix`` argument of
       :meth:`~sphinx.application.Sphinx.add_source_parser()`
     - 1.8
     - 3.0
     - :meth:`~sphinx.application.Sphinx.add_source_suffix()`


   * - ``BuildEnvironment.load()``
     - 1.8
     - 3.0
     - ``pickle.load()``

   * - ``BuildEnvironment.loads()``
     - 1.8
     - 3.0
     - ``pickle.loads()``

   * - ``BuildEnvironment.frompickle()``
     - 1.8
     - 3.0
     - ``pickle.load()``

   * - ``BuildEnvironment.dump()``
     - 1.8
     - 3.0
     - ``pickle.dump()``

   * - ``BuildEnvironment.dumps()``
     - 1.8
     - 3.0
     - ``pickle.dumps()``

   * - ``BuildEnvironment.topickle()``
     - 1.8
     - 3.0
     - ``pickle.dump()``

   * - ``BuildEnvironment._nitpick_ignore``
     - 1.8
     - 3.0
     - :confval:`nitpick_ignore`

   * - ``BuildEnvironment.versionchanges``
     - 1.8
     - 3.0
     - N/A

   * - ``BuildEnvironment.update()``
     - 1.8
     - 3.0
     - ``Builder.read()``

   * - ``BuildEnvironment.read_doc()``
     - 1.8
     - 3.0
     - ``Builder.read_doc()``

   * - ``BuildEnvironment._read_serial()``
     - 1.8
     - 3.0
     - ``Builder.read()``

   * - ``BuildEnvironment._read_parallel()``
     - 1.8
     - 3.0
     - ``Builder.read()``

   * - ``BuildEnvironment.write_doctree()``
     - 1.8
     - 3.0
     - ``Builder.write_doctree()``

   * - ``BuildEnvironment.note_versionchange()``
     - 1.8
     - 3.0
     - ``ChangesDomain.note_changeset()``

   * - ``warn()`` (template helper function)
     - 1.8
     - 3.0
     - ``warning()``

   * - :confval:`source_parsers`
     - 1.8
     - 3.0
     - :meth:`~sphinx.application.Sphinx.add_source_parser()`

   * - ``sphinx.util.docutils.directive_helper()``
     - 1.8
     - 3.0
     - ``Directive`` class of docutils

   * - ``sphinx.cmdline``
     - 1.8
     - 3.0
     - ``sphinx.cmd.build``

   * - ``sphinx.make_mode``
     - 1.8
     - 3.0
     - ``sphinx.cmd.make_mode``

   * - ``sphinx.locale.l_()``
     - 1.8
     - 3.0
     - :func:`sphinx.locale._()`

   * - ``sphinx.locale.lazy_gettext()``
     - 1.8
     - 3.0
     - :func:`sphinx.locale._()`

   * - ``sphinx.locale.mygettext()``
     - 1.8
     - 3.0
     - :func:`sphinx.locale._()`

   * - ``sphinx.util.copy_static_entry()``
     - 1.5
     - 3.0
     - ``sphinx.util.fileutil.copy_asset()``

   * - ``sphinx.build_main()``
     - 1.7
     - 2.0
     - ``sphinx.cmd.build.build_main()``

   * - ``sphinx.ext.intersphinx.debug()``
     - 1.7
     - 2.0
     - ``sphinx.ext.intersphinx.inspect_main()``

   * - ``sphinx.ext.autodoc.format_annotation()``
     - 1.7
     - 2.0
     - ``sphinx.util.inspect.Signature``

   * - ``sphinx.ext.autodoc.formatargspec()``
     - 1.7
     - 2.0
     - ``sphinx.util.inspect.Signature``

   * - ``sphinx.ext.autodoc.AutodocReporter``
     - 1.7
     - 2.0
     - ``sphinx.util.docutils.switch_source_input()``

   * - ``sphinx.ext.autodoc.add_documenter()``
     - 1.7
     - 2.0
     - :meth:`~sphinx.application.Sphinx.add_autodocumenter()`

   * - ``sphinx.ext.autodoc.AutoDirective._register``
     - 1.7
     - 2.0
     - :meth:`~sphinx.application.Sphinx.add_autodocumenter()`

   * - ``AutoDirective._special_attrgetters``
     - 1.7
     - 2.0
     - :meth:`~sphinx.application.Sphinx.add_autodoc_attrgetter()`

   * - ``Sphinx.warn()``, ``Sphinx.info()``
     - 1.6
     - 2.0
     - :ref:`logging-api`

   * - ``BuildEnvironment.set_warnfunc()``
     - 1.6
     - 2.0
     - :ref:`logging-api`

   * - ``BuildEnvironment.note_toctree()``
     - 1.6
     - 2.0
     - ``Toctree.note()`` (in ``sphinx.environment.adapters.toctree``)

   * - ``BuildEnvironment.get_toc_for()``
     - 1.6
     - 2.0
     - ``Toctree.get_toc_for()`` (in ``sphinx.environment.adapters.toctree``)

   * - ``BuildEnvironment.get_toctree_for()``
     - 1.6
     - 2.0
     - ``Toctree.get_toctree_for()`` (in ``sphinx.environment.adapters.toctree``)

   * - ``BuildEnvironment.create_index()``
     - 1.6
     - 2.0
     - ``IndexEntries.create_index()`` (in ``sphinx.environment.adapters.indexentries``)

   * - ``sphinx.websupport``
     - 1.6
     - 2.0
     - `sphinxcontrib-websupport <https://pypi.org/project/sphinxcontrib-websupport/>`_

   * - ``StandaloneHTMLBuilder.css_files``
     - 1.6
     - 2.0
     - :meth:`~sphinx.application.Sphinx.add_stylesheet()`

   * - ``document.settings.gettext_compact``
     - 1.8
     - 1.8
     - :confval:`gettext_compact`

   * - ``Sphinx.status_iterator()``
     - 1.6
     - 1.7
     - ``sphinx.util.status_iterator()``

   * - ``Sphinx.old_status_iterator()``
     - 1.6
     - 1.7
     - ``sphinx.util.old_status_iterator()``

   * - ``Sphinx._directive_helper()``
     - 1.6
     - 1.7
     - ``sphinx.util.docutils.directive_helper()``

   * - ``sphinx.util.compat.Directive``
     - 1.6
     - 1.7
     - ``docutils.parsers.rst.Directive``

   * - ``sphinx.util.compat.docutils_version``
     - 1.6
     - 1.7
     - ``sphinx.util.docutils.__version_info__``

.. note:: On deprecating on public APIs (internal functions and classes),
          we also follow the policy as much as possible.
