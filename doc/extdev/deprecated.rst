.. _dev-deprecated-apis:

Deprecated APIs
===============

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

   * - ``sphinx.ext.autodoc.AttributeDocumenter.isinstanceattribute()``
     - 3.5
     - 5.0
     - N/A

   * - ``sphinx.ext.autodoc.importer.get_module_members()``
     - 3.5
     - 5.0
     - ``sphinx.ext.autodoc.ModuleDocumenter.get_module_members()``

   * - The ``follow_wrapped`` argument of ``sphinx.util.inspect.signature()``
     - 3.4
     - 5.0
     - N/A

   * - The ``no_docstring`` argument of
       ``sphinx.ext.autodoc.Documenter.add_content()``
     - 3.4
     - 5.0
     - ``sphinx.ext.autodoc.Documenter.get_doc()``

   * - ``sphinx.ext.autodoc.Documenter.get_object_members()``
     - 3.4
     - 6.0
     - ``sphinx.ext.autodoc.ClassDocumenter.get_object_members()``

   * - ``sphinx.ext.autodoc.DataDeclarationDocumenter``
     - 3.4
     - 5.0
     - ``sphinx.ext.autodoc.DataDocumenter``

   * - ``sphinx.ext.autodoc.GenericAliasDocumenter``
     - 3.4
     - 5.0
     - ``sphinx.ext.autodoc.DataDocumenter``

   * - ``sphinx.ext.autodoc.InstanceAttributeDocumenter``
     - 3.4
     - 5.0
     - ``sphinx.ext.autodoc.AttributeDocumenter``

   * - ``sphinx.ext.autodoc.SlotsAttributeDocumenter``
     - 3.4
     - 5.0
     - ``sphinx.ext.autodoc.AttributeDocumenter``

   * - ``sphinx.ext.autodoc.TypeVarDocumenter``
     - 3.4
     - 5.0
     - ``sphinx.ext.autodoc.DataDocumenter``

   * - ``sphinx.ext.autodoc.directive.DocumenterBridge.reporter``
     - 3.5
     - 5.0
     - ``sphinx.util.logging``

   * - ``sphinx.ext.autodoc.importer._getannotations()``
     - 3.4
     - 4.0
     - ``sphinx.util.inspect.getannotations()``

   * - ``sphinx.ext.autodoc.importer._getmro()``
     - 3.4
     - 4.0
     - ``sphinx.util.inspect.getmro()``

   * - ``sphinx.pycode.ModuleAnalyzer.parse()``
     - 3.4
     - 5.0
     - ``sphinx.pycode.ModuleAnalyzer.analyze()``

   * - ``sphinx.util.osutil.movefile()``
     - 3.4
     - 5.0
     - ``os.replace()``

   * - ``sphinx.util.requests.is_ssl_error()``
     - 3.4
     - 5.0
     - N/A

   * - ``sphinx.builders.latex.LaTeXBuilder.usepackages``
     - 3.3
     - 5.0
     - N/A

   * - ``sphinx.builders.latex.LaTeXBuilder.usepackages_afger_hyperref``
     - 3.3
     - 5.0
     - N/A

   * - ``sphinx.ext.autodoc.SingledispatchFunctionDocumenter``
     - 3.3
     - 5.0
     - ``sphinx.ext.autodoc.FunctionDocumenter``

   * - ``sphinx.ext.autodoc.SingledispatchMethodDocumenter``
     - 3.3
     - 5.0
     - ``sphinx.ext.autodoc.MethodDocumenter``

   * - ``sphinx.ext.autodoc.members_set_option()``
     - 3.2
     - 5.0
     - N/A

   * - ``sphinx.ext.autodoc.merge_special_members_option()``
     - 3.2
     - 5.0
     - ``sphinx.ext.autodoc.merge_members_option()``

   * - ``sphinx.writers.texinfo.TexinfoWriter.desc``
     - 3.2
     - 5.0
     - ``sphinx.writers.texinfo.TexinfoWriter.descs``

   * - The first argument for
       ``sphinx.ext.autosummary.generate.AutosummaryRenderer`` has been changed
       to Sphinx object
     - 3.1
     - 5.0
     - N/A

   * - ``sphinx.ext.autosummary.generate.AutosummaryRenderer`` takes an object
       type as an argument
     - 3.1
     - 5.0
     - N/A

   * - The ``ignore`` argument of ``sphinx.ext.autodoc.Documenter.get_doc()``
     - 3.1
     - 5.0
     - N/A

   * - The ``template_dir`` argument of
       ``sphinx.ext.autosummary.generate.AutosummaryRenderer``
     - 3.1
     - 5.0
     - N/A

   * - The ``module`` argument of
       ``sphinx.ext.autosummary.generate.find_autosummary_in_docstring()``
     - 3.0
     - 5.0
     - N/A

   * - The ``builder`` argument of
       ``sphinx.ext.autosummary.generate.generate_autosummary_docs()``
     - 3.1
     - 5.0
     - N/A

   * - The ``template_dir`` argument of
       ``sphinx.ext.autosummary.generate.generate_autosummary_docs()``
     - 3.1
     - 5.0
     - N/A

   * - ``sphinx.ext.autosummary.generate.AutosummaryRenderer.exists()``
     - 3.1
     - 5.0
     - N/A

   * - The ``ignore`` argument of ``sphinx.util.docstring.prepare_docstring()``
     - 3.1
     - 5.0
     - N/A

   * - ``sphinx.util.rpartition()``
     - 3.1
     - 5.0
     - ``str.rpartition()``

   * - ``desc_signature['first']``
     -
     - 3.0
     - N/A

   * - ``sphinx.directives.DescDirective``
     - 3.0
     - 5.0
     - ``sphinx.directives.ObjectDescription``

   * - ``sphinx.domains.std.StandardDomain.add_object()``
     - 3.0
     - 5.0
     - ``sphinx.domains.std.StandardDomain.note_object()``

   * - ``sphinx.domains.python.PyDecoratorMixin``
     - 3.0
     - 5.0
     - N/A

   * - ``sphinx.ext.autodoc.get_documenters()``
     - 3.0
     - 5.0
     - ``sphinx.registry.documenters``

   * - ``sphinx.ext.autosummary.process_autosummary_toc()``
     - 3.0
     - 5.0
     - N/A

   * - ``sphinx.parsers.Parser.app``
     - 3.0
     - 5.0
     - N/A

   * - ``sphinx.testing.path.Path.text()``
     - 3.0
     - 5.0
     - ``sphinx.testing.path.Path.read_text()``

   * - ``sphinx.testing.path.Path.bytes()``
     - 3.0
     - 5.0
     - ``sphinx.testing.path.Path.read_bytes()``

   * - ``sphinx.util.inspect.getargspec()``
     - 3.0
     - 5.0
     - ``inspect.getargspec()``

   * - ``sphinx.writers.latex.LaTeXWriter.format_docclass()``
     - 3.0
     - 5.0
     - LaTeX Themes

   * - ``decode`` argument of ``sphinx.pycode.ModuleAnalyzer()``
     - 2.4
     - 4.0
     - N/A

   * - ``sphinx.directives.other.Index``
     - 2.4
     - 4.0
     - ``sphinx.domains.index.IndexDirective``

   * - ``sphinx.environment.temp_data['gloss_entries']``
     - 2.4
     - 4.0
     - ``documents.nameids``

   * - ``sphinx.environment.BuildEnvironment.indexentries``
     - 2.4
     - 4.0
     - ``sphinx.domains.index.IndexDomain``

   * - ``sphinx.environment.collectors.indexentries.IndexEntriesCollector``
     - 2.4
     - 4.0
     - ``sphinx.domains.index.IndexDomain``

   * - ``sphinx.io.FiletypeNotFoundError``
     - 2.4
     - 4.0
     - ``sphinx.errors.FiletypeNotFoundError``

   * - ``sphinx.ext.apidoc.INITPY``
     - 2.4
     - 4.0
     - N/A

   * - ``sphinx.ext.apidoc.shall_skip()``
     - 2.4
     - 4.0
     - ``sphinx.ext.apidoc.is_skipped_package``

   * - ``sphinx.io.get_filetype()``
     - 2.4
     - 4.0
     - ``sphinx.util.get_filetype()``

   * - ``sphinx.pycode.ModuleAnalyzer.encoding``
     - 2.4
     - 4.0
     - N/A

   * - ``sphinx.roles.Index``
     - 2.4
     - 4.0
     - ``sphinx.domains.index.IndexRole``

   * - ``sphinx.util.detect_encoding()``
     - 2.4
     - 4.0
     - ``tokenize.detect_encoding()``

   * - ``sphinx.util.get_module_source()``
     - 2.4
     - 4.0
     - N/A

   * - ``sphinx.util.inspect.Signature``
     - 2.4
     - 4.0
     - ``sphinx.util.inspect.signature`` and
       ``sphinx.util.inspect.stringify_signature()``

   * - ``sphinx.util.inspect.safe_getmembers()``
     - 2.4
     - 4.0
     - ``inspect.getmembers()``

   * - ``sphinx.writers.latex.LaTeXTranslator.settings.author``
     - 2.4
     - 4.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.settings.contentsname``
     - 2.4
     - 4.0
     - ``document['contentsname']``

   * - ``sphinx.writers.latex.LaTeXTranslator.settings.docclass``
     - 2.4
     - 4.0
     - ``document['docclass']``

   * - ``sphinx.writers.latex.LaTeXTranslator.settings.docname``
     - 2.4
     - 4.0
     - N/A

   * - ``sphinx.writers.latex.LaTeXTranslator.settings.title``
     - 2.4
     - 4.0
     - N/A

   * - ``sphinx.writers.latex.ADDITIONAL_SETTINGS``
     - 2.4
     - 4.0
     - ``sphinx.builders.latex.constants.ADDITIONAL_SETTINGS``

   * - ``sphinx.writers.latex.DEFAULT_SETTINGS``
     - 2.4
     - 4.0
     - ``sphinx.builders.latex.constants.DEFAULT_SETTINGS``

   * - ``sphinx.writers.latex.LUALATEX_DEFAULT_FONTPKG``
     - 2.4
     - 4.0
     - ``sphinx.builders.latex.constants.LUALATEX_DEFAULT_FONTPKG``

   * - ``sphinx.writers.latex.PDFLATEX_DEFAULT_FONTPKG``
     - 2.4
     - 4.0
     - ``sphinx.builders.latex.constants.PDFLATEX_DEFAULT_FONTPKG``

   * - ``sphinx.writers.latex.XELATEX_DEFAULT_FONTPKG``
     - 2.4
     - 4.0
     - ``sphinx.builders.latex.constants.XELATEX_DEFAULT_FONTPKG``

   * - ``sphinx.writers.latex.XELATEX_GREEK_DEFAULT_FONTPKG``
     - 2.4
     - 4.0
     - ``sphinx.builders.latex.constants.XELATEX_GREEK_DEFAULT_FONTPKG``

   * - ``sphinx.builders.gettext.POHEADER``
     - 2.3
     - 4.0
     - ``sphinx/templates/gettext/message.pot_t`` (template file)

   * - ``sphinx.io.SphinxStandaloneReader.app``
     - 2.3
     - 4.0
     - ``sphinx.io.SphinxStandaloneReader.setup()``

   * - ``sphinx.io.SphinxStandaloneReader.env``
     - 2.3
     - 4.0
     - ``sphinx.io.SphinxStandaloneReader.setup()``

   * - ``sphinx.util.texescape.tex_escape_map``
     - 2.3
     - 4.0
     - ``sphinx.util.texescape.escape()``

   * - ``sphinx.util.texescape.tex_hl_escape_map_new``
     - 2.3
     - 4.0
     - ``sphinx.util.texescape.hlescape()``

   * - ``sphinx.writers.latex.LaTeXTranslator.no_contractions``
     - 2.3
     - 4.0
     - N/A

   * - ``sphinx.domains.math.MathDomain.add_equation()``
     - 2.2
     - 4.0
     - ``sphinx.domains.math.MathDomain.note_equation()``

   * - ``sphinx.domains.math.MathDomain.get_next_equation_number()``
     - 2.2
     - 4.0
     - ``sphinx.domains.math.MathDomain.note_equation()``

   * - The ``info`` and ``warn`` arguments of
       ``sphinx.ext.autosummary.generate.generate_autosummary_docs()``
     - 2.2
     - 4.0
     - ``logging.info()`` and ``logging.warning()``

   * - ``sphinx.ext.autosummary.generate._simple_info()``
     - 2.2
     - 4.0
     - ``logging.info()``

   * - ``sphinx.ext.autosummary.generate._simple_warn()``
     - 2.2
     - 4.0
     - ``logging.warning()``

   * - ``sphinx.ext.todo.merge_info()``
     - 2.2
     - 4.0
     - ``sphinx.ext.todo.TodoDomain``

   * - ``sphinx.ext.todo.process_todo_nodes()``
     - 2.2
     - 4.0
     - ``sphinx.ext.todo.TodoDomain``

   * - ``sphinx.ext.todo.process_todos()``
     - 2.2
     - 4.0
     - ``sphinx.ext.todo.TodoDomain``

   * - ``sphinx.ext.todo.purge_todos()``
     - 2.2
     - 4.0
     - ``sphinx.ext.todo.TodoDomain``

   * - ``sphinx.builders.latex.LaTeXBuilder.apply_transforms()``
     - 2.1
     - 4.0
     - N/A

   * - ``sphinx.builders._epub_base.EpubBuilder.esc()``
     - 2.1
     - 4.0
     - ``html.escape()``

   * - ``sphinx.directives.Acks``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.Acks``

   * - ``sphinx.directives.Author``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.Author``

   * - ``sphinx.directives.Centered``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.Centered``

   * - ``sphinx.directives.Class``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.Class``

   * - ``sphinx.directives.CodeBlock``
     - 2.1
     - 4.0
     - ``sphinx.directives.code.CodeBlock``

   * - ``sphinx.directives.Figure``
     - 2.1
     - 4.0
     - ``sphinx.directives.patches.Figure``

   * - ``sphinx.directives.HList``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.HList``

   * - ``sphinx.directives.Highlight``
     - 2.1
     - 4.0
     - ``sphinx.directives.code.Highlight``

   * - ``sphinx.directives.Include``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.Include``

   * - ``sphinx.directives.Index``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.Index``

   * - ``sphinx.directives.LiteralInclude``
     - 2.1
     - 4.0
     - ``sphinx.directives.code.LiteralInclude``

   * - ``sphinx.directives.Meta``
     - 2.1
     - 4.0
     - ``sphinx.directives.patches.Meta``

   * - ``sphinx.directives.Only``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.Only``

   * - ``sphinx.directives.SeeAlso``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.SeeAlso``

   * - ``sphinx.directives.TabularColumns``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.TabularColumns``

   * - ``sphinx.directives.TocTree``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.TocTree``

   * - ``sphinx.directives.VersionChange``
     - 2.1
     - 4.0
     - ``sphinx.directives.other.VersionChange``

   * - ``sphinx.domains.python.PyClassmember``
     - 2.1
     - 4.0
     - ``sphinx.domains.python.PyAttribute``,
       ``sphinx.domains.python.PyMethod``,
       ``sphinx.domains.python.PyClassMethod``,
       ``sphinx.domains.python.PyObject`` and
       ``sphinx.domains.python.PyStaticMethod``

   * - ``sphinx.domains.python.PyModulelevel``
     - 2.1
     - 4.0
     - ``sphinx.domains.python.PyFunction``,
       ``sphinx.domains.python.PyObject`` and
       ``sphinx.domains.python.PyVariable``

   * - ``sphinx.domains.std.StandardDomain._resolve_citation_xref()``
     - 2.1
     - 4.0
     - ``sphinx.domains.citation.CitationDomain.resolve_xref()``

   * - ``sphinx.domains.std.StandardDomain.note_citations()``
     - 2.1
     - 4.0
     - ``sphinx.domains.citation.CitationDomain.note_citation()``

   * - ``sphinx.domains.std.StandardDomain.note_citation_refs()``
     - 2.1
     - 4.0
     - ``sphinx.domains.citation.CitationDomain.note_citation_reference()``

   * - ``sphinx.domains.std.StandardDomain.note_labels()``
     - 2.1
     - 4.0
     - ``sphinx.domains.std.StandardDomain.process_doc()``

   * - ``sphinx.environment.NoUri``
     - 2.1
     - 4.0
     - ``sphinx.errors.NoUri``
   * - ``sphinx.ext.apidoc.format_directive()``
     - 2.1
     - 4.0
     - N/A

   * - ``sphinx.ext.apidoc.format_heading()``
     - 2.1
     - 4.0
     - N/A

   * - ``sphinx.ext.apidoc.makename()``
     - 2.1
     - 4.0
     - ``sphinx.ext.apidoc.module_join()``

   * - ``sphinx.ext.autodoc.importer.MockFinder``
     - 2.1
     - 4.0
     - ``sphinx.ext.autodoc.mock.MockFinder``

   * - ``sphinx.ext.autodoc.importer.MockLoader``
     - 2.1
     - 4.0
     - ``sphinx.ext.autodoc.mock.MockLoader``

   * - ``sphinx.ext.autodoc.importer.mock()``
     - 2.1
     - 4.0
     - ``sphinx.ext.autodoc.mock.mock()``

   * - ``sphinx.ext.autosummary.autolink_role()``
     - 2.1
     - 4.0
     - ``sphinx.ext.autosummary.AutoLink``

   * - ``sphinx.ext.imgmath.DOC_BODY``
     - 2.1
     - 4.0
     - N/A

   * - ``sphinx.ext.imgmath.DOC_BODY_PREVIEW``
     - 2.1
     - 4.0
     - N/A

   * - ``sphinx.ext.imgmath.DOC_HEAD``
     - 2.1
     - 4.0
     - N/A

   * - ``sphinx.transforms.CitationReferences``
     - 2.1
     - 4.0
     - ``sphinx.domains.citation.CitationReferenceTransform``

   * - ``sphinx.transforms.SmartQuotesSkipper``
     - 2.1
     - 4.0
     - ``sphinx.domains.citation.CitationDefinitionTransform``

   * - ``sphinx.util.docfields.DocFieldTransformer.preprocess_fieldtypes()``
     - 2.1
     - 4.0
     - ``sphinx.directives.ObjectDescription.get_field_type_map()``

   * - ``sphinx.util.node.find_source_node()``
     - 2.1
     - 4.0
     - ``sphinx.util.node.get_node_source()``

   * - ``sphinx.util.i18n.find_catalog()``
     - 2.1
     - 4.0
     - ``sphinx.util.i18n.docname_to_domain()``

   * - ``sphinx.util.i18n.find_catalog_files()``
     - 2.1
     - 4.0
     - ``sphinx.util.i18n.CatalogRepository``

   * - ``sphinx.util.i18n.find_catalog_source_files()``
     - 2.1
     - 4.0
     - ``sphinx.util.i18n.CatalogRepository``

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
     - `sphinxcontrib-websupport`_

       .. _sphinxcontrib-websupport: https://pypi.org/project/sphinxcontrib-websupport/

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
