.. highlightlang:: python

.. _build-config:

The build configuration file
============================

.. module:: conf
   :synopsis: Build configuration file.

The :term:`configuration directory` must contain a file named :file:`conf.py`.
This file (containing Python code) is called the "build configuration file" and
contains all configuration needed to customize Sphinx input and output behavior.

The configuration file is executed as Python code at build time (using
:func:`execfile`, and with the current directory set to its containing
directory), and therefore can execute arbitrarily complex code.  Sphinx then
reads simple names from the file's namespace as its configuration.

Important points to note:

* If not otherwise documented, values must be strings, and their default is the
  empty string.

* The term "fully-qualified name" refers to a string that names an importable
  Python object inside a module; for example, the FQN
  ``"sphinx.builders.Builder"`` means the ``Builder`` class in the
  ``sphinx.builders`` module.

* Remember that document names use ``/`` as the path separator and don't contain
  the file name extension.

* Since :file:`conf.py` is read as a Python file, the usual rules apply for
  encodings and Unicode support: declare the encoding using an encoding cookie
  (a comment like ``# -*- coding: utf-8 -*-``) and use Unicode string literals
  when you include non-ASCII characters in configuration values.

* The contents of the config namespace are pickled (so that Sphinx can find out
  when configuration changes), so it may not contain unpickleable values --
  delete them from the namespace with ``del`` if appropriate.  Modules are
  removed automatically, so you don't need to ``del`` your imports after use.

* There is a special object named ``tags`` available in the config file.
  It can be used to query and change the tags (see :ref:`tags`).  Use
  ``tags.has('tag')`` to query, ``tags.add('tag')`` and ``tags.remove('tag')``
  to change.


General configuration
---------------------

.. confval:: extensions

   A list of strings that are module names of Sphinx extensions.  These can be
   extensions coming with Sphinx (named ``sphinx.ext.*``) or custom ones.

   Note that you can extend :data:`sys.path` within the conf file if your
   extensions live in another directory -- but make sure you use absolute paths.
   If your extension path is relative to the :term:`configuration directory`,
   use :func:`os.path.abspath` like so::

      import sys, os

      sys.path.append(os.path.abspath('sphinxext'))

      extensions = ['extname']

   That way, you can load an extension called ``extname`` from the subdirectory
   ``sphinxext``.

   The configuration file itself can be an extension; for that, you only need to
   provide a :func:`setup` function in it.

.. confval:: source_suffix

   The file name extension of source files.  Only files with this suffix will be
   read as sources.  Default is ``'.rst'``.

.. confval:: source_encoding

   The encoding of all reST source files.  The recommended encoding, and the
   default value, is ``'utf-8-sig'``.

   .. versionadded:: 0.5
      Previously, Sphinx accepted only UTF-8 encoded sources.

.. confval:: master_doc

   The document name of the "master" document, that is, the document that
   contains the root :rst:dir:`toctree` directive.  Default is ``'contents'``.

.. confval:: exclude_patterns

   A list of glob-style patterns that should be excluded when looking for source
   files. [1]_ They are matched against the source file names relative to the
   source directory, using slashes as directory separators on all platforms.

   Example patterns:

   - ``'library/xml.rst'`` -- ignores the ``library/xml.rst`` file (replaces
     entry in :confval:`unused_docs`)
   - ``'library/xml'`` -- ignores the ``library/xml`` directory (replaces entry
     in :confval:`exclude_trees`)
   - ``'library/xml*'`` -- ignores all files and directories starting with
     ``library/xml``
   - ``'**/.svn'`` -- ignores all ``.svn`` directories (replaces entry in
     :confval:`exclude_dirnames`)

   :confval:`exclude_patterns` is also consulted when looking for static files
   in :confval:`html_static_path`.

   .. versionadded:: 1.0

.. confval:: unused_docs

   A list of document names that are present, but not currently included in the
   toctree.  Use this setting to suppress the warning that is normally emitted
   in that case.

   .. deprecated:: 1.0
      Use :confval:`exclude_patterns` instead.

.. confval:: exclude_trees

   A list of directory paths, relative to the source directory, that are to be
   recursively excluded from the search for source files, that is, their
   subdirectories won't be searched too.  The default is ``[]``.

   .. versionadded:: 0.4

   .. deprecated:: 1.0
      Use :confval:`exclude_patterns` instead.

.. confval:: exclude_dirnames

   A list of directory names that are to be excluded from any recursive
   operation Sphinx performs (e.g. searching for source files or copying static
   files).  This is useful, for example, to exclude version-control-specific
   directories like ``'CVS'``.  The default is ``[]``.

   .. versionadded:: 0.5

   .. deprecated:: 1.0
      Use :confval:`exclude_patterns` instead.

.. confval:: templates_path

   A list of paths that contain extra templates (or templates that overwrite
   builtin/theme-specific templates).  Relative paths are taken as relative to
   the configuration directory.

.. confval:: template_bridge

   A string with the fully-qualified name of a callable (or simply a class) that
   returns an instance of :class:`~sphinx.application.TemplateBridge`.  This
   instance is then used to render HTML documents, and possibly the output of
   other builders (currently the changes builder).  (Note that the template
   bridge must be made theme-aware if HTML themes are to be used.)

.. confval:: rst_epilog

   .. index:: pair: global; substitutions

   A string of reStructuredText that will be included at the end of every source
   file that is read.  This is the right place to add substitutions that should
   be available in every file.  An example::

      rst_epilog = """
      .. |psf| replace:: Python Software Foundation
      """

   .. versionadded:: 0.6

.. confval:: rst_prolog

   A string of reStructuredText that will be included at the beginning of every
   source file that is read.

   .. versionadded:: 1.0

.. confval:: primary_domain

   .. index:: default; domain
              primary; domain

   The name of the default :ref:`domain <domains>`.  Can also be ``None`` to
   disable a default domain.  The default is ``'py'``.  Those objects in other
   domains (whether the domain name is given explicitly, or selected by a
   :rst:dir:`default-domain` directive) will have the domain name explicitly
   prepended when named (e.g., when the default domain is C, Python functions
   will be named "Python function", not just "function").

   .. versionadded:: 1.0

.. confval:: default_role

   .. index:: default; role

   The name of a reST role (builtin or Sphinx extension) to use as the default
   role, that is, for text marked up ```like this```.  This can be set to
   ``'py:obj'`` to make ```filter``` a cross-reference to the Python function
   "filter".  The default is ``None``, which doesn't reassign the default role.

   The default role can always be set within individual documents using the
   standard reST :rst:dir:`default-role` directive.

   .. versionadded:: 0.4

.. confval:: keep_warnings

   If true, keep warnings as "system message" paragraphs in the built documents.
   Regardless of this setting, warnings are always written to the standard error
   stream when ``sphinx-build`` is run.

   The default is ``False``, the pre-0.5 behavior was to always keep them.

   .. versionadded:: 0.5

.. confval:: needs_sphinx

   If set to a ``major.minor`` version string like ``'1.1'``, Sphinx will
   compare it with its version and refuse to build if it is too old.  Default is
   no requirement.

   .. versionadded:: 1.0

.. confval:: nitpicky

   If true, Sphinx will warn about *all* references where the target cannot be
   found.  Default is ``False``.  You can activate this mode temporarily using
   the :option:`-n` command-line switch.

   .. versionadded:: 1.0

.. confval:: nitpick_ignore

   A list of ``(type, target)`` tuples (by default empty) that should be ignored
   when generating warnings in "nitpicky mode".  Note that ``type`` should
   include the domain name.  An example entry would be ``('py:func', 'int')``.

   .. versionadded:: 1.1


Project information
-------------------

.. confval:: project

   The documented project's name.

.. confval:: copyright

   A copyright statement in the style ``'2008, Author Name'``.

.. confval:: version

   The major project version, used as the replacement for ``|version|``.  For
   example, for the Python documentation, this may be something like ``2.6``.

.. confval:: release

   The full project version, used as the replacement for ``|release|`` and
   e.g. in the HTML templates.  For example, for the Python documentation, this
   may be something like ``2.6.0rc1``.

   If you don't need the separation provided between :confval:`version` and
   :confval:`release`, just set them both to the same value.

.. confval:: today
             today_fmt

   These values determine how to format the current date, used as the
   replacement for ``|today|``.

   * If you set :confval:`today` to a non-empty value, it is used.
   * Otherwise, the current time is formatted using :func:`time.strftime` and
     the format given in :confval:`today_fmt`.

   The default is no :confval:`today` and a :confval:`today_fmt` of ``'%B %d,
   %Y'`` (or, if translation is enabled with :confval:`language`, am equivalent
   %format for the selected locale).

.. confval:: highlight_language

   The default language to highlight source code in.  The default is
   ``'python'``.  The value should be a valid Pygments lexer name, see
   :ref:`code-examples` for more details.

   .. versionadded:: 0.5

.. confval:: pygments_style

   The style name to use for Pygments highlighting of source code.  The default
   style is selected by the theme for HTML output, and ``'sphinx'`` otherwise.

   .. versionchanged:: 0.3
      If the value is a fully-qualified name of a custom Pygments style class,
      this is then used as custom style.

.. confval:: add_function_parentheses

   A boolean that decides whether parentheses are appended to function and
   method role text (e.g. the content of ``:func:`input```) to signify that the
   name is callable.  Default is ``True``.

.. confval:: add_module_names

   A boolean that decides whether module names are prepended to all
   :term:`object` names (for object types where a "module" of some kind is
   defined), e.g. for :rst:dir:`py:function` directives.  Default is ``True``.

.. confval:: show_authors

   A boolean that decides whether :rst:dir:`codeauthor` and
   :rst:dir:`sectionauthor` directives produce any output in the built files.

.. confval:: modindex_common_prefix

   A list of prefixes that are ignored for sorting the Python module index
   (e.g., if this is set to ``['foo.']``, then ``foo.bar`` is shown under ``B``,
   not ``F``). This can be handy if you document a project that consists of a
   single package.  Works only for the HTML builder currently.  Default is
   ``[]``.

   .. versionadded:: 0.6

.. confval:: trim_footnote_reference_space

   Trim spaces before footnote references that are necessary for the reST parser
   to recognize the footnote, but do not look too nice in the output.

   .. versionadded:: 0.6

.. confval:: trim_doctest_flags

   If true, doctest flags (comments looking like ``# doctest: FLAG, ...``) at
   the ends of lines and ``<BLANKLINE>`` markers are removed for all code
   blocks showing interactive Python sessions (i.e. doctests).  Default is
   true.  See the extension :mod:`~sphinx.ext.doctest` for more possibilities
   of including doctests.

   .. versionadded:: 1.0
   .. versionchanged:: 1.1
      Now also removes ``<BLANKLINE>``.


.. _intl-options:

Options for internationalization
--------------------------------

These options influence Sphinx' *Native Language Support*.  See the
documentation on :ref:`intl` for details.

.. confval:: language

   The code for the language the docs are written in.  Any text automatically
   generated by Sphinx will be in that language.  Also, Sphinx will try to
   substitute individual paragraphs from your documents with the translation
   sets obtained from :confval:`locale_dirs`.  In the LaTeX builder, a suitable
   language will be selected as an option for the *Babel* package.  Default is
   ``None``, which means that no translation will be done.

   .. versionadded:: 0.5

   Currently supported languages by Sphinx are:

   * ``bn`` -- Bengali
   * ``ca`` -- Catalan
   * ``cs`` -- Czech
   * ``da`` -- Danish
   * ``de`` -- German
   * ``en`` -- English
   * ``es`` -- Spanish
   * ``et`` -- Estonian
   * ``fa`` -- Iranian
   * ``fi`` -- Finnish
   * ``fr`` -- French
   * ``hr`` -- Croatian
   * ``it`` -- Italian
   * ``ja`` -- Japanese
   * ``ko`` -- Korean
   * ``lt`` -- Lithuanian
   * ``lv`` -- Latvian
   * ``ne`` -- Nepali
   * ``nl`` -- Dutch
   * ``pl`` -- Polish
   * ``pt_BR`` -- Brazilian Portuguese
   * ``ru`` -- Russian
   * ``sl`` -- Slovenian
   * ``sv`` -- Swedish
   * ``tr`` -- Turkish
   * ``uk_UA`` -- Ukrainian
   * ``zh_CN`` -- Simplified Chinese
   * ``zh_TW`` -- Traditional Chinese

.. confval:: locale_dirs

   .. versionadded:: 0.5

   Directories in which to search for additional message catalogs (see
   :confval:`language`), relative to the source directory.  The directories on
   this path are searched by the standard :mod:`gettext` module.

   Internal messages are fetched from a text domain of ``sphinx``; so if you
   add the directory :file:`./locale` to this settting, the message catalogs
   (compiled from ``.po`` format using :program:`msgfmt`) must be in
   :file:`./locale/{language}/LC_MESSAGES/sphinx.mo`.  The text domain of
   individual documents depends on :confval:`gettext_compact`.

   The default is ``[]``.

.. confval:: gettext_compact

   .. versionadded:: 1.1

   If true, a document's text domain is its docname if it is a top-level
   project file and its very base directory otherwise.

   By default, the document ``markup/code.rst`` ends up in the ``markup`` text
   domain.  With this option set to ``False``, it is ``markup/code``.


.. _html-options:

Options for HTML output
-----------------------

These options influence HTML as well as HTML Help output, and other builders
that use Sphinx' HTMLWriter class.

.. confval:: html_theme

   The "theme" that the HTML output should use.  See the :doc:`section about
   theming <theming>`.  The default is ``'default'``.

   .. versionadded:: 0.6

.. confval:: html_theme_options

   A dictionary of options that influence the look and feel of the selected
   theme.  These are theme-specific.  For the options understood by the builtin
   themes, see :ref:`this section <builtin-themes>`.

   .. versionadded:: 0.6

.. confval:: html_theme_path

   A list of paths that contain custom themes, either as subdirectories or as
   zip files.  Relative paths are taken as relative to the configuration
   directory.

   .. versionadded:: 0.6

.. confval:: html_style

   The style sheet to use for HTML pages.  A file of that name must exist either
   in Sphinx' :file:`static/` path, or in one of the custom paths given in
   :confval:`html_static_path`.  Default is the stylesheet given by the selected
   theme.  If you only want to add or override a few things compared to the
   theme's stylesheet, use CSS ``@import`` to import the theme's stylesheet.

.. confval:: html_title

   The "title" for HTML documentation generated with Sphinx' own templates.
   This is appended to the ``<title>`` tag of individual pages, and used in the
   navigation bar as the "topmost" element.  It defaults to :samp:`'{<project>}
   v{<revision>} documentation'`, where the placeholders are replaced by the
   config values of the same name.

.. confval:: html_short_title

   A shorter "title" for the HTML docs.  This is used in for links in the header
   and in the HTML Help docs.  If not given, it defaults to the value of
   :confval:`html_title`.

   .. versionadded:: 0.4

.. confval:: html_context

   A dictionary of values to pass into the template engine's context for all
   pages.  Single values can also be put in this dictionary using the
   :option:`-A` command-line option of ``sphinx-build``.

   .. versionadded:: 0.5

.. confval:: html_logo

   If given, this must be the name of an image file that is the logo of the
   docs.  It is placed at the top of the sidebar; its width should therefore not
   exceed 200 pixels.  Default: ``None``.

   .. versionadded:: 0.4.1
      The image file will be copied to the ``_static`` directory of the output
      HTML, so an already existing file with that name will be overwritten.

.. confval:: html_favicon

   If given, this must be the name of an image file (within the static path, see
   below) that is the favicon of the docs.  Modern browsers use this as icon for
   tabs, windows and bookmarks.  It should be a Windows-style icon file
   (``.ico``), which is 16x16 or 32x32 pixels large.  Default: ``None``.

   .. versionadded:: 0.4

.. confval:: html_static_path

   A list of paths that contain custom static files (such as style sheets or
   script files).  Relative paths are taken as relative to the configuration
   directory.  They are copied to the output directory after the theme's static
   files, so a file named :file:`default.css` will overwrite the theme's
   :file:`default.css`.

   .. versionchanged:: 0.4
      The paths in :confval:`html_static_path` can now contain subdirectories.

   .. versionchanged:: 1.0
      The entries in :confval:`html_static_path` can now be single files.

.. confval:: html_last_updated_fmt

   If this is not the empty string, a 'Last updated on:' timestamp is inserted
   at every page bottom, using the given :func:`strftime` format.  Default is
   ``'%b %d, %Y'`` (or a locale-dependent equivalent).

.. confval:: html_use_smartypants

   If true, *SmartyPants* will be used to convert quotes and dashes to
   typographically correct entities.  Default: ``True``.

.. confval:: html_add_permalinks

   Sphinx will add "permalinks" for each heading and description environment as
   paragraph signs that become visible when the mouse hovers over them.

   This value determines the text for the permalink; it defaults to ``"¶"``.
   Set it to ``None`` or the empty string to disable permalinks.

   .. versionadded:: 0.6
      Previously, this was always activated.

   .. versionchanged:: 1.1
      This can now be a string to select the actual text of the link.
      Previously, only boolean values were accepted.

.. confval:: html_sidebars

   Custom sidebar templates, must be a dictionary that maps document names to
   template names.

   The keys can contain glob-style patterns [1]_, in which case all matching
   documents will get the specified sidebars.  (A warning is emitted when a
   more than one glob-style pattern matches for any document.)

   The values can be either lists or single strings.

   * If a value is a list, it specifies the complete list of sidebar templates
     to include.  If all or some of the default sidebars are to be included,
     they must be put into this list as well.

     The default sidebars (for documents that don't match any pattern) are:
     ``['localtoc.html', 'relations.html', 'sourcelink.html',
     'searchbox.html']``.

   * If a value is a single string, it specifies a custom sidebar to be added
     between the ``'sourcelink.html'`` and ``'searchbox.html'`` entries.  This
     is for compatibility with Sphinx versions before 1.0.

   Builtin sidebar templates that can be rendered are:

   * **localtoc.html** -- a fine-grained table of contents of the current document
   * **globaltoc.html** -- a coarse-grained table of contents for the whole
     documentation set, collapsed
   * **relations.html** -- two links to the previous and next documents
   * **sourcelink.html** -- a link to the source of the current document, if
     enabled in :confval:`html_show_sourcelink`
   * **searchbox.html** -- the "quick search" box

   Example::

      html_sidebars = {
         '**': ['globaltoc.html', 'sourcelink.html', 'searchbox.html'],
         'using/windows': ['windowssidebar.html', 'searchbox.html'],
      }

   This will render the custom template ``windowssidebar.html`` and the quick
   search box within the sidebar of the given document, and render the default
   sidebars for all other pages (except that the local TOC is replaced by the
   global TOC).

   .. versionadded:: 1.0
      The ability to use globbing keys and to specify multiple sidebars.

   Note that this value only has no effect if the chosen theme does not possess
   a sidebar, like the builtin **scrolls** and **haiku** themes.

.. confval:: html_additional_pages

   Additional templates that should be rendered to HTML pages, must be a
   dictionary that maps document names to template names.

   Example::

      html_additional_pages = {
          'download': 'customdownload.html',
      }

   This will render the template ``customdownload.html`` as the page
   ``download.html``.

.. confval:: html_domain_indices

   If true, generate domain-specific indices in addition to the general index.
   For e.g. the Python domain, this is the global module index.  Default is
   ``True``.

   This value can be a bool or a list of index names that should be generated.
   To find out the index name for a specific index, look at the HTML file name.
   For example, the Python module index has the name ``'py-modindex'``.

   .. versionadded:: 1.0

.. confval:: html_use_modindex

   If true, add a module index to the HTML documents.   Default is ``True``.

   .. deprecated:: 1.0
      Use :confval:`html_domain_indices`.

.. confval:: html_use_index

   If true, add an index to the HTML documents.  Default is ``True``.

   .. versionadded:: 0.4

.. confval:: html_split_index

   If true, the index is generated twice: once as a single page with all the
   entries, and once as one page per starting letter.  Default is ``False``.

   .. versionadded:: 0.4

.. confval:: html_copy_source

   If true, the reST sources are included in the HTML build as
   :file:`_sources/{name}`.  The default is ``True``.

   .. warning::

      If this config value is set to ``False``, the JavaScript search function
      will only display the titles of matching documents, and no excerpt from
      the matching contents.

.. confval:: html_show_sourcelink

   If true (and :confval:`html_copy_source` is true as well), links to the
   reST sources will be added to the sidebar.  The default is ``True``.

   .. versionadded:: 0.6

.. confval:: html_use_opensearch

   If nonempty, an `OpenSearch <http://opensearch.org>` description file will be
   output, and all pages will contain a ``<link>`` tag referring to it.  Since
   OpenSearch doesn't support relative URLs for its search page location, the
   value of this option must be the base URL from which these documents are
   served (without trailing slash), e.g. ``"http://docs.python.org"``.  The
   default is ``''``.

.. confval:: html_file_suffix

   This is the file name suffix for generated HTML files.  The default is
   ``".html"``.

   .. versionadded:: 0.4

.. confval:: html_link_suffix

   Suffix for generated links to HTML files.  The default is whatever
   :confval:`html_file_suffix` is set to; it can be set differently (e.g. to
   support different web server setups).

   .. versionadded:: 0.6

.. confval:: html_translator_class

   A string with the fully-qualified name of a HTML Translator class, that is, a
   subclass of Sphinx' :class:`~sphinx.writers.html.HTMLTranslator`, that is used
   to translate document trees to HTML.  Default is ``None`` (use the builtin
   translator).

.. confval:: html_show_copyright

   If true, "(C) Copyright ..." is shown in the HTML footer. Default is ``True``.

   .. versionadded:: 1.0

.. confval:: html_show_sphinx

   If true, "Created using Sphinx" is shown in the HTML footer.  Default is
   ``True``.

   .. versionadded:: 0.4

.. confval:: html_output_encoding

   Encoding of HTML output files. Default is ``'utf-8'``.  Note that this
   encoding name must both be a valid Python encoding name and a valid HTML
   ``charset`` value.

   .. versionadded:: 1.0

.. confval:: html_compact_lists

   If true, list items containing only a single paragraph will not be rendered
   with a ``<p>`` element.  This is standard docutils behavior.  Default:
   ``True``.

   .. versionadded:: 1.0

.. confval:: html_secnumber_suffix

   Suffix for section numbers.  Default: ``". "``.  Set to ``" "`` to suppress
   the final dot on section numbers.

   .. versionadded:: 1.0

.. confval:: html_search_language

   Language to be used for generating the HTML full-text search index.  This
   defaults to the global language selected with :confval:`language`.  If there
   is no support for this language, ``"en"`` is used which selects the English
   language.

   Support is present for these languages:

   * ``en`` -- English
   * ``ja`` -- Japanese

   .. versionadded:: 1.1

.. confval:: html_search_options

   A dictionary with options for the search language support, empty by default.
   The meaning of these options depends on the language selected.

   The English support has no options.

   The Japanese support has these options:

   * ``type`` -- ``'mecab'`` or ``'default'`` (selects either MeCab or
     TinySegmenter word splitter algorithm)
   * ``dic_enc`` -- the encoding for the MeCab algorithm
   * ``dict`` -- the dictionary to use for the MeCab algorithm
   * ``lib`` -- the library name for finding the MeCab library via ctypes if the
     Python binding is not installed

   .. versionadded:: 1.1

.. confval:: htmlhelp_basename

   Output file base name for HTML help builder.  Default is ``'pydoc'``.


.. _epub-options:

Options for epub output
-----------------------

These options influence the epub output.  As this builder derives from the HTML
builder, the HTML options also apply where appropriate.  The actual values for
some of the options is not really important, they just have to be entered into
the `Dublin Core metadata <http://dublincore.org/>`_.

.. confval:: epub_basename

   The basename for the epub file.  It defaults to the :confval:`project` name.

.. confval:: epub_theme

   The HTML theme for the epub output.  Since the default themes are not
   optimized for small screen space, using the same theme for HTML and epub
   output is usually not wise.  This defaults to ``'epub'``, a theme designed to
   save visual space.

.. confval:: epub_title

   The title of the document.  It defaults to the :confval:`html_title` option
   but can be set independently for epub creation.

.. confval:: epub_author

   The author of the document.  This is put in the Dublin Core metadata.  The
   default value is ``'unknown'``.

.. confval:: epub_language

   The language of the document.  This is put in the Dublin Core metadata.  The
   default is the :confval:`language` option or ``'en'`` if unset.

.. confval:: epub_publisher

   The publisher of the document.  This is put in the Dublin Core metadata.  You
   may use any sensible string, e.g. the project homepage.  The default value is
   ``'unknown'``.

.. confval:: epub_copyright

   The copyright of the document.  It defaults to the :confval:`copyright`
   option but can be set independently for epub creation.

.. confval:: epub_identifier

   An identifier for the document.  This is put in the Dublin Core metadata.
   For published documents this is the ISBN number, but you can also use an
   alternative scheme, e.g. the project homepage.  The default value is
   ``'unknown'``.

.. confval:: epub_scheme

   The publication scheme for the :confval:`epub_identifier`.  This is put in
   the Dublin Core metadata.  For published books the scheme is ``'ISBN'``.  If
   you use the project homepage, ``'URL'`` seems reasonable.  The default value
   is ``'unknown'``.

.. confval:: epub_uid

   A unique identifier for the document.  This is put in the Dublin Core
   metadata.  You may use a random string.  The default value is ``'unknown'``.

.. confval:: epub_cover

   The cover page information.  This is a tuple containing the filenames of
   the cover image and the html template.  The rendered html cover page is
   inserted as the first item in the spine in :file:`content.opf`.  If the
   template filename is empty, no html cover page is created.  No cover at all
   is created if the tuple is empty.  Examples::

      epub_cover = ('_static/cover.png', 'epub-cover.html')
      epub_cover = ('_static/cover.png', '')
      epub_cover = ()

   The default value is ``()``.

   .. versionadded:: 1.1

.. confval:: epub_pre_files

   Additional files that should be inserted before the text generated by
   Sphinx. It is a list of tuples containing the file name and the title.
   If the title is empty, no entry is added to :file:`toc.ncx`.  Example::

      epub_pre_files = [
          ('index.html', 'Welcome'),
      ]

   The default value is ``[]``.

.. confval:: epub_post_files

   Additional files that should be inserted after the text generated by Sphinx.
   It is a list of tuples containing the file name and the title.  This option
   can be used to add an appendix.  If the title is empty, no entry is added
   to :file:`toc.ncx`.  The default value is ``[]``.

.. confval:: epub_exclude_files

   A list of files that are generated/copied in the build directory but should
   not be included in the epub file.  The default value is ``[]``.

.. confval:: epub_tocdepth

   The depth of the table of contents in the file :file:`toc.ncx`.  It should
   be an integer greater than zero.  The default value is 3.  Note: A deeply
   nested table of contents may be difficult to navigate.

.. confval:: epub_tocdup

   This flag determines if a toc entry is inserted again at the beginning of
   it's nested toc listing.  This allows easier navitation to the top of
   a chapter, but can be confusing because it mixes entries of differnet
   depth in one list.  The default value is ``True``.


.. _latex-options:

Options for LaTeX output
------------------------

These options influence LaTeX output.

.. confval:: latex_documents

   This value determines how to group the document tree into LaTeX source files.
   It must be a list of tuples ``(startdocname, targetname, title, author,
   documentclass, toctree_only)``, where the items are:

   * *startdocname*: document name that is the "root" of the LaTeX file.  All
     documents referenced by it in TOC trees will be included in the LaTeX file
     too.  (If you want only one LaTeX file, use your :confval:`master_doc`
     here.)
   * *targetname*: file name of the LaTeX file in the output directory.
   * *title*: LaTeX document title.  Can be empty to use the title of the
     *startdoc*.  This is inserted as LaTeX markup, so special characters like a
     backslash or ampersand must be represented by the proper LaTeX commands if
     they are to be inserted literally.
   * *author*: Author for the LaTeX document.  The same LaTeX markup caveat as
     for *title* applies.  Use ``\and`` to separate multiple authors, as in:
     ``'John \and Sarah'``.
   * *documentclass*: Normally, one of ``'manual'`` or ``'howto'`` (provided by
     Sphinx).  Other document classes can be given, but they must include the
     "sphinx" package in order to define Sphinx' custom LaTeX commands.
     "howto" documents will not get appendices.  Also, howtos will have a simpler
     title page.
   * *toctree_only*: Must be ``True`` or ``False``.  If ``True``, the *startdoc*
     document itself is not included in the output, only the documents
     referenced by it via TOC trees.  With this option, you can put extra stuff
     in the master document that shows up in the HTML, but not the LaTeX output.

   .. versionadded:: 0.3
      The 6th item ``toctree_only``.  Tuples with 5 items are still accepted.

.. confval:: latex_logo

   If given, this must be the name of an image file (relative to the
   configuration directory) that is the logo of the docs.  It is placed at the
   top of the title page.  Default: ``None``.

.. confval:: latex_use_parts

   If true, the topmost sectioning unit is parts, else it is chapters.  Default:
   ``False``.

   .. versionadded:: 0.3

.. confval:: latex_appendices

   A list of document names to append as an appendix to all manuals.

.. confval:: latex_domain_indices

   If true, generate domain-specific indices in addition to the general index.
   For e.g. the Python domain, this is the global module index.  Default is
   ``True``.

   This value can be a bool or a list of index names that should be generated,
   like for :confval:`html_domain_indices`.

   .. versionadded:: 1.0

.. confval:: latex_use_modindex

   If true, add a module index to LaTeX documents.   Default is ``True``.

   .. deprecated:: 1.0
      Use :confval:`latex_domain_indices`.

.. confval:: latex_show_pagerefs

   If true, add page references after internal references.  This is very useful
   for printed copies of the manual.  Default is ``False``.

   .. versionadded:: 1.0

.. confval:: latex_show_urls

   Control whether to display URL addresses.  This is very useful for printed
   copies of the manual.  The setting can have the following values:

   * ``'no'`` -- do not display URLs (default)
   * ``'footnote'`` -- display URLs in footnotes
   * ``'inline'`` -- display URLs inline in parentheses

   .. versionadded:: 1.0
   .. versionchanged:: 1.1
      This value is now a string; previously it was a boolean value, and a true
      value selected the ``'inline'`` display.  For backwards compatibility,
      ``True`` is still accepted.

.. confval:: latex_elements

   .. versionadded:: 0.5

   A dictionary that contains LaTeX snippets that override those Sphinx usually
   puts into the generated ``.tex`` files.

   Keep in mind that backslashes must be doubled in Python string literals to
   avoid interpretation as escape sequences.

   * Keys that you may want to override include:

     ``'papersize'``
        Paper size option of the document class (``'a4paper'`` or
        ``'letterpaper'``), default ``'letterpaper'``.
     ``'pointsize'``
        Point size option of the document class (``'10pt'``, ``'11pt'`` or
        ``'12pt'``), default ``'10pt'``.
     ``'babel'``
        "babel" package inclusion, default ``'\\usepackage{babel}'``.
     ``'fontpkg'``
        Font package inclusion, default ``'\\usepackage{times}'`` (which uses
        Times and Helvetica).  You can set this to ``''`` to use the Computer
        Modern fonts.
     ``'fncychap'``
        Inclusion of the "fncychap" package (which makes fancy chapter titles),
        default ``'\\usepackage[Bjarne]{fncychap}'`` for English documentation,
        ``'\\usepackage[Sonny]{fncychap}'`` for internationalized docs (because
        the "Bjarne" style uses numbers spelled out in English).  Other
        "fncychap" styles you can try include "Lenny", "Glenn", "Conny" and
        "Rejne".  You can also set this to ``''`` to disable fncychap.
     ``'preamble'``
        Additional preamble content, default empty.
     ``'footer'```
        Additional footer content (before the indices), default empty.

   * Keys that don't need be overridden unless in special cases are:

     ``'inputenc'``
        "inputenc" package inclusion, default
        ``'\\usepackage[utf8]{inputenc}'``.
     ``'fontenc'``
        "fontenc" package inclusion, default ``'\\usepackage[T1]{fontenc}'``.
     ``'maketitle'``
        "maketitle" call, default ``'\\maketitle'``.  Override if you want to
        generate a differently-styled title page.
     ``'tableofcontents'``
        "tableofcontents" call, default ``'\\tableofcontents'``.  Override if
        you want to generate a different table of contents or put content
        between the title page and the TOC.
     ``'printindex'``
        "printindex" call, the last thing in the file, default
        ``'\\printindex'``.  Override if you want to generate the index
        differently or append some content after the index.

   * Keys that are set by other options and therefore should not be overridden are:

     ``'docclass'``
     ``'classoptions'``
     ``'title'``
     ``'date'``
     ``'release'``
     ``'author'``
     ``'logo'``
     ``'releasename'``
     ``'makeindex'``
     ``'shorthandoff'``

.. confval:: latex_docclass

   A dictionary mapping ``'howto'`` and ``'manual'`` to names of real document
   classes that will be used as the base for the two Sphinx classes.  Default
   is to use ``'article'`` for ``'howto'`` and ``'report'`` for ``'manual'``.

   .. versionadded:: 1.0

.. confval:: latex_additional_files

   A list of file names, relative to the configuration directory, to copy to the
   build directory when building LaTeX output.  This is useful to copy files
   that Sphinx doesn't copy automatically, e.g. if they are referenced in custom
   LaTeX added in ``latex_elements``.  Image files that are referenced in source
   files (e.g. via ``.. image::``) are copied automatically.

   You have to make sure yourself that the filenames don't collide with those of
   any automatically copied files.

   .. versionadded:: 0.6

.. confval:: latex_preamble

   Additional LaTeX markup for the preamble.

   .. deprecated:: 0.5
      Use the ``'preamble'`` key in the :confval:`latex_elements` value.

.. confval:: latex_paper_size

   The output paper size (``'letter'`` or ``'a4'``).  Default is ``'letter'``.

   .. deprecated:: 0.5
      Use the ``'papersize'`` key in the :confval:`latex_elements` value.

.. confval:: latex_font_size

   The font size ('10pt', '11pt' or '12pt'). Default is ``'10pt'``.

   .. deprecated:: 0.5
      Use the ``'pointsize'`` key in the :confval:`latex_elements` value.


.. _text-options:

Options for text output
-----------------------

These options influence text output.

.. confval:: text_newlines

   Determines which end-of-line character(s) are used in text output.

   * ``'unix'``: use Unix-style line endings (``\n``)
   * ``'windows'``: use Windows-style line endings (``\r\n``)
   * ``'native'``: use the line ending style of the platform the documentation
     is built on

   Default: ``'unix'``.

   .. versionadded:: 1.1

.. confval:: text_sectionchars

   A string of 7 characters that should be used for underlining sections.
   The first character is used for first-level headings, the second for
   second-level headings and so on.

   The default is ``'*=-~"+`'``.

   .. versionadded:: 1.1


.. _man-options:

Options for manual page output
------------------------------

These options influence manual page output.

.. confval:: man_pages

   This value determines how to group the document tree into manual pages.  It
   must be a list of tuples ``(startdocname, name, description, authors,
   section)``, where the items are:

   * *startdocname*: document name that is the "root" of the manual page.  All
     documents referenced by it in TOC trees will be included in the manual file
     too.  (If you want one master manual page, use your :confval:`master_doc`
     here.)
   * *name*: name of the manual page.  This should be a short string without
     spaces or special characters.  It is used to determine the file name as
     well as the name of the manual page (in the NAME section).
   * *description*: description of the manual page.  This is used in the NAME
     section.
   * *authors*: A list of strings with authors, or a single string.  Can be an
     empty string or list if you do not want to automatically generate an
     AUTHORS section in the manual page.
   * *section*: The manual page section.  Used for the output file name as well
     as in the manual page header.

   .. versionadded:: 1.0

.. confval:: man_show_urls

   If true, add URL addresses after links.  Default is ``False``.

   .. versionadded:: 1.1


.. _texinfo-options:

Options for Texinfo output
--------------------------

These options influence Texinfo output.

.. confval:: texinfo_documents

   This value determines how to group the document tree into Texinfo source
   files.  It must be a list of tuples ``(startdocname, targetname, title,
   author, dir_entry, description, category, toctree_only)``, where the items
   are:

   * *startdocname*: document name that is the "root" of the Texinfo file.  All
     documents referenced by it in TOC trees will be included in the Texinfo
     file too.  (If you want only one Texinfo file, use your
     :confval:`master_doc` here.)
   * *targetname*: file name (no extension) of the Texinfo file in the output
     directory.
   * *title*: Texinfo document title.  Can be empty to use the title of the
     *startdoc*.  Inserted as Texinfo markup, so special characters like @ and
     {} will need to be escaped to be inserted literally.
   * *author*: Author for the Texinfo document.  Inserted as Texinfo markup.
     Use ``@*`` to separate multiple authors, as in: ``'John@*Sarah'``.
   * *dir_entry*: The name that will appear in the top-level ``DIR`` menu file.
   * *description*: Descriptive text to appear in the top-level ``DIR`` menu
     file.
   * *category*: Specifies the section which this entry will appear in the
     top-level ``DIR`` menu file.
   * *toctree_only*: Must be ``True`` or ``False``.  If ``True``, the *startdoc*
     document itself is not included in the output, only the documents
     referenced by it via TOC trees.  With this option, you can put extra stuff
     in the master document that shows up in the HTML, but not the Texinfo
     output.

   .. versionadded:: 1.1

.. confval:: texinfo_appendices

   A list of document names to append as an appendix to all manuals.

   .. versionadded:: 1.1

.. confval:: texinfo_domain_indices

   If true, generate domain-specific indices in addition to the general index.
   For e.g. the Python domain, this is the global module index.  Default is
   ``True``.

   This value can be a bool or a list of index names that should be generated,
   like for :confval:`html_domain_indices`.

   .. versionadded:: 1.1

.. confval:: texinfo_show_urls

   Control how to display URL addresses.

   * ``'footnote'`` -- display URLs in footnotes (default)
   * ``'no'`` -- do not display URLs
   * ``'inline'`` -- display URLs inline in parentheses

   .. versionadded:: 1.1

.. confval:: texinfo_elements

   A dictionary that contains Texinfo snippets that override those Sphinx
   usually puts into the generated ``.texi`` files.

   * Keys that you may want to override include:

     ``'paragraphindent'``
        Number of spaces to indent the first line of each paragraph, default
        ``2``.  Specify ``0`` for no indentation.

     ``'exampleindent'``
        Number of spaces to indent the lines for examples or literal blocks,
        default ``4``.  Specify ``0`` for no indentation.

     ``'preamble'``
        Texinfo markup inserted near the beginning of the file.

     ``'copying'``
        Texinfo markup inserted within the ``@copying`` block and displayed
        after the title.  The default value consists of a simple title page
        identifying the project.

   * Keys that are set by other options and therefore should not be overridden
     are:

     ``'author'``
     ``'body'``
     ``'date'``
     ``'direntry'``
     ``'filename'``
     ``'project'``
     ``'release'``
     ``'title'``
     ``'direntry'``

   .. versionadded:: 1.1


Options for the linkcheck builder
---------------------------------

.. confval:: linkcheck_ignore

   A list of regular expressions that match URIs that should not be checked
   when doing a ``linkcheck`` build.  Example::

      linkcheck_ignore = [r'http://localhost:\d+/']

   .. versionadded:: 1.1

.. confval:: linkcheck_timeout

   A timeout value, in seconds, for the linkcheck builder.  **Only works in
   Python 2.6 and higher.**  The default is to use Python's global socket
   timeout.

   .. versionadded:: 1.1

.. confval:: linkcheck_workers

   The number of worker threads to use when checking links.  Default is 5
   threads.

   .. versionadded:: 1.1


.. rubric:: Footnotes

.. [1] A note on available globbing syntax: you can use the standard shell
       constructs ``*``, ``?``, ``[...]`` and ``[!...]`` with the feature that
       these all don't match slashes.  A double star ``**`` can be used to match
       any sequence of characters *including* slashes.
