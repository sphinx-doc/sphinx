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

   tutorial
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

   * - ``sphinx.ext.config.check_unicode()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.ext.doctest.doctest_encode()``
     - 2.0
     - 4.0
     - N/A

   * - ``sphinx.testing.util.remove_unicode_literal()``
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

   * - ``sphinx.util.osutil.walk()``
     - 2.0
     - 4.0
     - ``os.walk()``

   * - ``sphinx.util.pycompat.u``
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

   * - ``sphinx.io.SphinxRSTFileInput``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator._make_visit_admonition()``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.writers.texinfo.TexinfoTranslator._make_visit_admonition()``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.writers.text.TextTranslator._make_depart_admonition()``
     - 2.0
     - 3.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.babel_defmacro()``
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
