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

.. _conf-tags:

* There is a special object named ``tags`` available in the config file.
  It can be used to query and change the tags (see :ref:`tags`).  Use
  ``tags.has('tag')`` to query, ``tags.add('tag')`` and ``tags.remove('tag')``
  to change. Only tags set via the ``-t`` command-line option or via
  ``tags.add('tag')`` can be queried using ``tags.has('tag')``.
  Note that the current builder tag is not available in ``conf.py``, as it is
  created *after* the builder is initialized.


General configuration
---------------------

.. confval:: extensions

   A list of strings that are module names of :ref:`extensions`. These can be
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

   The file name extension, or list of extensions, of source files.  Only files
   with this suffix will be read as sources.  Default is ``'.rst'``.

   .. versionchanged:: 1.3
      Can now be a list of extensions.

.. confval:: source_encoding

   The encoding of all reST source files.  The recommended encoding, and the
   default value, is ``'utf-8-sig'``.

   .. versionadded:: 0.5
      Previously, Sphinx accepted only UTF-8 encoded sources.

.. confval:: source_parsers

   If given, a dictionary of parser classes for different source suffices.  The
   keys are the suffix, the values can be either a class or a string giving a
   fully-qualified name of a parser class.  The parser class can be either
   ``docutils.parsers.Parser`` or :class:`sphinx.parsers.Parser`.  Files with a
   suffix that is not in the dictionary will be parsed with the default
   reStructuredText parser.


   For example::

      source_parsers = {'.md': 'some.markdown.module.Parser'}

   .. versionadded:: 1.3

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
   in :confval:`html_static_path` and :confval:`html_extra_path`.

   .. versionadded:: 1.0

.. confval:: templates_path

   A list of paths that contain extra templates (or templates that overwrite
   builtin/theme-specific templates).  Relative paths are taken as relative to
   the configuration directory.

   .. versionchanged:: 1.3
      As these files are not meant to be built, they are automatically added to
      :confval:`exclude_patterns`.

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

.. confval:: suppress_warnings

   A list of warning types to suppress arbitrary warning messages.

   Sphinx supports following warning types:

   * app.add_node
   * app.add_directive
   * app.add_role
   * app.add_generic_role
   * app.add_source_parser
   * image.data_uri
   * image.nonlocal_uri
   * ref.term
   * ref.ref
   * ref.numref
   * ref.keyword
   * ref.option
   * ref.citation
   * ref.doc

   You can choose from these types.

   Now, this option should be considered *experimental*.

   .. versionadded:: 1.4

.. confval:: needs_sphinx

   If set to a ``major.minor`` version string like ``'1.1'``, Sphinx will
   compare it with its version and refuse to build if it is too old.  Default is
   no requirement.

   .. versionadded:: 1.0

   .. versionchanged:: 1.4
      also accepts micro version string

.. confval:: needs_extensions

   This value can be a dictionary specifying version requirements for extensions
   in :confval:`extensions`, e.g. ``needs_extensions =
   {'sphinxcontrib.something': '1.5'}``.  The version strings should be in the
   form ``major.minor``.  Requirements do not have to be specified for all
   extensions, only for those you want to check.

   This requires that the extension specifies its version to Sphinx (see
   :ref:`dev-extensions` for how to do that).

   .. versionadded:: 1.3

.. confval:: nitpicky

   If true, Sphinx will warn about *all* references where the target cannot be
   found.  Default is ``False``.  You can activate this mode temporarily using
   the :option:`-n <sphinx-build -n>` command-line switch.

   .. versionadded:: 1.0

.. confval:: nitpick_ignore

   A list of ``(type, target)`` tuples (by default empty) that should be ignored
   when generating warnings in "nitpicky mode".  Note that ``type`` should
   include the domain name if present.  Example entries would be ``('py:func',
   'int')`` or ``('envvar', 'LD_LIBRARY_PATH')``.

   .. versionadded:: 1.1

.. confval:: numfig

   If true, figures, tables and code-blocks are automatically numbered if they
   have a caption.  At same time, the `numref` role is enabled.  For now, it
   works only with the HTML builder and LaTeX builder. Default is ``False``.

   .. note::

      LaTeX builder always assign numbers whether this option is enabled or not.

   .. versionadded:: 1.3

.. confval:: numfig_format

   A dictionary mapping ``'figure'``, ``'table'``, ``'code-block'`` and
   ``'section'`` to strings that are used for format of figure numbers.
   As a special character, `%s` and `{number}` will be replaced to figure
   number.  `{name}` will be replaced to figure caption.

   Default is to use ``'Fig. %s'`` for ``'figure'``, ``'Table %s'`` for
   ``'table'``, ``'Listing %s'`` for ``'code-block'`` and ``'Section'`` for
   ``'section'``.

   .. versionadded:: 1.3

   .. versionchanged:: 1.5
      Support format of section. Allow to refer the caption of figures.

.. confval:: numfig_secnum_depth

   The scope of figure numbers, that is, the numfig feature numbers figures
   in which scope. ``0`` means "whole document". ``1`` means "in a section".
   Sphinx numbers like x.1, x.2, x.3... ``2`` means "in a subsection". Sphinx
   numbers like x.x.1, x.x.2, x.x.3..., and so on. Default is ``1``.

   .. versionadded:: 1.3

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
   %Y'`` (or, if translation is enabled with :confval:`language`, an equivalent
   format for the selected locale).

   .. versionchanged:: 1.4

      Format specification was changed from strftime to Locale Data Markup
      Language. strftime format is also supported for backward compatibility
      until Sphinx-1.5.

   .. versionchanged:: 1.4.1

      Format specification was changed again from Locale Data Markup Language
      to strftime.  LDML format is also supported for backward compatibility
      until Sphinx-1.5.

.. confval:: highlight_language

   The default language to highlight source code in.  The default is
   ``'python3'``.  The value should be a valid Pygments lexer name, see
   :ref:`code-examples` for more details.

   .. versionadded:: 0.5

   .. versionchanged:: 1.4
      The default is now ``'default'``. It is similar to ``'python3'``;
      it is mostly a superset of ``'python'``. but it fallbacks to
      ``'none'`` without warning if failed.  ``'python3'`` and other
      languages will emit warning if failed.  If you prefer Python 2
      only highlighting, you can set it back to ``'python'``.

.. confval:: highlight_options

   A dictionary of options that modify how the lexer specified by
   :confval:`highlight_language` generates highlighted source code. These are
   lexer-specific; for the options understood by each, see the
   `Pygments documentation <http://pygments.org/docs/lexers/>`_.

   .. versionadded:: 1.3

.. confval:: pygments_style

   The style name to use for Pygments highlighting of source code.  If not set,
   either the theme's default style or ``'sphinx'`` is selected for HTML output.

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
   ``True``.  See the extension :mod:`~sphinx.ext.doctest` for more
   possibilities of including doctests.

   .. versionadded:: 1.0
   .. versionchanged:: 1.1
      Now also removes ``<BLANKLINE>``.


.. _intl-options:

Options for internationalization
--------------------------------

These options influence Sphinx's *Native Language Support*.  See the
documentation on :ref:`intl` for details.

.. confval:: language

   The code for the language the docs are written in.  Any text automatically
   generated by Sphinx will be in that language.  Also, Sphinx will try to
   substitute individual paragraphs from your documents with the translation
   sets obtained from :confval:`locale_dirs`.  Sphinx will search
   language-specific figures named by `figure_language_filename` and substitute
   them for original figures.  In the LaTeX builder, a suitable language will
   be selected as an option for the *Babel* package.  Default is ``None``,
   which means that no translation will be done.

   .. versionadded:: 0.5

   .. versionchanged:: 1.4

      Support figure substitution

   Currently supported languages by Sphinx are:

   * ``bn`` -- Bengali
   * ``ca`` -- Catalan
   * ``cs`` -- Czech
   * ``da`` -- Danish
   * ``de`` -- German
   * ``en`` -- English
   * ``es`` -- Spanish
   * ``et`` -- Estonian
   * ``eu`` -- Basque
   * ``fa`` -- Iranian
   * ``fi`` -- Finnish
   * ``fr`` -- French
   * ``he`` -- Hebrew
   * ``hr`` -- Croatian
   * ``hu`` -- Hungarian
   * ``id`` -- Indonesian
   * ``it`` -- Italian
   * ``ja`` -- Japanese
   * ``ko`` -- Korean
   * ``lt`` -- Lithuanian
   * ``lv`` -- Latvian
   * ``mk`` -- Macedonian
   * ``nb_NO`` -- Norwegian Bokmal
   * ``ne`` -- Nepali
   * ``nl`` -- Dutch
   * ``pl`` -- Polish
   * ``pt_BR`` -- Brazilian Portuguese
   * ``pt_PT`` -- European Portuguese
   * ``ru`` -- Russian
   * ``si`` -- Sinhala
   * ``sk`` -- Slovak
   * ``sl`` -- Slovenian
   * ``sv`` -- Swedish
   * ``tr`` -- Turkish
   * ``uk_UA`` -- Ukrainian
   * ``vi`` -- Vietnamese
   * ``zh_CN`` -- Simplified Chinese
   * ``zh_TW`` -- Traditional Chinese

.. confval:: locale_dirs

   .. versionadded:: 0.5

   Directories in which to search for additional message catalogs (see
   :confval:`language`), relative to the source directory.  The directories on
   this path are searched by the standard :mod:`gettext` module.

   Internal messages are fetched from a text domain of ``sphinx``; so if you
   add the directory :file:`./locale` to this setting, the message catalogs
   (compiled from ``.po`` format using :program:`msgfmt`) must be in
   :file:`./locale/{language}/LC_MESSAGES/sphinx.mo`.  The text domain of
   individual documents depends on :confval:`gettext_compact`.

   The default is ``['locales']``.

   .. versionchanged:: 1.5
      Use ``locales`` directory as a default value

.. confval:: gettext_compact

   .. versionadded:: 1.1

   If true, a document's text domain is its docname if it is a top-level
   project file and its very base directory otherwise.

   By default, the document ``markup/code.rst`` ends up in the ``markup`` text
   domain.  With this option set to ``False``, it is ``markup/code``.

.. confval:: gettext_uuid

   If true, Sphinx generates uuid information for version tracking in message
   catalogs. It is used for:

   * Add uid line for each msgids in .pot files.
   * Calculate similarity between new msgids and previously saved old msgids.
     This calculation takes a long time.

   If you want to accelerate the calculation, you can use
   ``python-levenshtein`` 3rd-party package written in C by using
   :command:`pip install python-levenshtein`.

   The default is ``False``.

   .. versionadded:: 1.3

.. confval:: gettext_location

   If true, Sphinx generates location information for messages in message
   catalogs.

   The default is ``True``.

   .. versionadded:: 1.3

.. confval:: gettext_auto_build

   If true, Sphinx builds mo file for each translation catalog files.

   The default is ``True``.

   .. versionadded:: 1.3

.. confval:: gettext_additional_targets

   To specify names to enable gettext extracting and translation applying for
   i18n additionally. You can specify below names:

   :index: index terms
   :literal-block: literal blocks: ``::`` and ``code-block``.
   :doctest-block: doctest block
   :raw: raw content
   :image: image/figure uri and alt

   For example: ``gettext_additional_targets = ['literal-block', 'image']``.

   The default is ``[]``.

   .. versionadded:: 1.3

.. confval:: figure_language_filename

   The filename format for language-specific figures.  The default value is
   ``{root}.{language}{ext}``.  It will be expanded to
   ``dirname/filename.en.png`` from ``.. image:: dirname/filename.png``.
   The available format tokens are:

   * ``{root}`` - the filename, including any path component, without the file
     extension, e.g. ``dirname/filename``
   * ``{path}`` - the directory path component of the filename, with a trailing
     slash if non-empty, e.g. ``dirname/``
   * ``{basename}`` - the filename without the directory path or file extension
     components, e.g. ``filename``
   * ``{ext}`` - the file extension, e.g. ``.png``
   * ``{language}`` - the translation language, e.g. ``en``

   For example, setting this to ``{path}{language}/{basename}{ext}`` will
   expand to ``dirname/en/filename.png`` instead.

   .. versionadded:: 1.4

   .. versionchanged:: 1.5
      Added ``{path}`` and ``{basename}`` tokens.

.. _html-options:

Options for HTML output
-----------------------

These options influence HTML as well as HTML Help output, and other builders
that use Sphinx's HTMLWriter class.

.. confval:: html_theme

   The "theme" that the HTML output should use.  See the :doc:`section about
   theming <theming>`.  The default is ``'alabaster'``.

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
   in Sphinx's :file:`static/` path, or in one of the custom paths given in
   :confval:`html_static_path`.  Default is the stylesheet given by the selected
   theme.  If you only want to add or override a few things compared to the
   theme's stylesheet, use CSS ``@import`` to import the theme's stylesheet.

.. confval:: html_title

   The "title" for HTML documentation generated with Sphinx's own templates.
   This is appended to the ``<title>`` tag of individual pages, and used in the
   navigation bar as the "topmost" element.  It defaults to :samp:`'{<project>}
   v{<revision>} documentation'`.

.. confval:: html_short_title

   A shorter "title" for the HTML docs.  This is used in for links in the header
   and in the HTML Help docs.  If not given, it defaults to the value of
   :confval:`html_title`.

   .. versionadded:: 0.4

.. confval:: html_context

   A dictionary of values to pass into the template engine's context for all
   pages.  Single values can also be put in this dictionary using the
   :option:`-A <sphinx-build -A>` command-line option of ``sphinx-build``.

   .. versionadded:: 0.5

.. confval:: html_logo

   If given, this must be the name of an image file (path relative to the
   :term:`configuration directory`) that is the logo of the docs.  It is placed
   at the top of the sidebar; its width should therefore not exceed 200 pixels.
   Default: ``None``.

   .. versionadded:: 0.4.1
      The image file will be copied to the ``_static`` directory of the output
      HTML, but only if the file does not already exist there.

.. confval:: html_favicon

   If given, this must be the name of an image file (path relative to the
   :term:`configuration directory`) that is the favicon of the docs.  Modern
   browsers use this as the icon for tabs, windows and bookmarks.  It should
   be a Windows-style icon file (``.ico``), which is 16x16 or 32x32
   pixels large.  Default: ``None``.

   .. versionadded:: 0.4
      The image file will be copied to the ``_static`` directory of the output
      HTML, but only if the file does not already exist there.

.. confval:: html_static_path

   A list of paths that contain custom static files (such as style
   sheets or script files).  Relative paths are taken as relative to
   the configuration directory.  They are copied to the output's
   :file:`_static` directory after the theme's static files, so a file
   named :file:`default.css` will overwrite the theme's
   :file:`default.css`.

   .. versionchanged:: 0.4
      The paths in :confval:`html_static_path` can now contain subdirectories.

   .. versionchanged:: 1.0
      The entries in :confval:`html_static_path` can now be single files.

.. confval:: html_extra_path

   A list of paths that contain extra files not directly related to
   the documentation, such as :file:`robots.txt` or :file:`.htaccess`.
   Relative paths are taken as relative to the configuration
   directory.  They are copied to the output directory.  They will
   overwrite any existing file of the same name.

   As these files are not meant to be built, they are automatically added to
   :confval:`exclude_patterns`.

   .. versionadded:: 1.2

   .. versionchanged:: 1.4
      The dotfiles in the extra directory will be copied to the output directory.
      And it refers :confval:`exclude_patterns` on copying extra files and
      directories, and ignores if path matches to patterns.

.. confval:: html_last_updated_fmt

   If this is not None, a 'Last updated on:' timestamp is inserted
   at every page bottom, using the given :func:`strftime` format.
   The empty string is equivalent to ``'%b %d, %Y'`` (or a
   locale-dependent equivalent).

   .. versionchanged:: 1.4

      Format specification was changed from strftime to Locale Data Markup
      Language. strftime format is also supported for backward compatibility
      until Sphinx-1.5.

   .. versionchanged:: 1.4.1

      Format specification was changed again from Locale Data Markup Language
      to strftime.  LDML format is also supported for backward compatibility
      until Sphinx-1.5.


.. confval:: html_use_smartypants

   If true, `SmartyPants <http://daringfireball.net/projects/smartypants/>`_
   will be used to convert quotes and dashes to typographically correct
   entities.  Default: ``True``.

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

   * **localtoc.html** -- a fine-grained table of contents of the current
     document
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

.. confval:: html_sourcelink_suffix

   Suffix to be appended to source links (see :confval:`html_show_sourcelink`),
   unless they have this suffix already.  Default is ``'.txt'``.

   .. versionadded:: 1.5

.. confval:: html_use_opensearch

   If nonempty, an `OpenSearch <http://www.opensearch.org/Home>`_ description file will be
   output, and all pages will contain a ``<link>`` tag referring to it.  Since
   OpenSearch doesn't support relative URLs for its search page location, the
   value of this option must be the base URL from which these documents are
   served (without trailing slash), e.g. ``"https://docs.python.org"``.  The
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
   subclass of Sphinx's :class:`~sphinx.writers.html.HTMLTranslator`, that is
   used to translate document trees to HTML.  Default is ``None`` (use the
   builtin translator).

   .. seealso::  :meth:`~sphinx.application.Sphinx.set_translator`

   .. deprecated:: 1.5

      Implement your translator as extension and use `Sphinx.set_translator`
      instead.

.. confval:: html_show_copyright

   If true, "(C) Copyright ..." is shown in the HTML footer. Default is
   ``True``.

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

   * ``da`` -- Danish
   * ``nl`` -- Dutch
   * ``en`` -- English
   * ``fi`` -- Finnish
   * ``fr`` -- French
   * ``de`` -- German
   * ``hu`` -- Hungarian
   * ``it`` -- Italian
   * ``ja`` -- Japanese
   * ``no`` -- Norwegian
   * ``pt`` -- Portuguese
   * ``ro`` -- Romanian
   * ``ru`` -- Russian
   * ``es`` -- Spanish
   * ``sv`` -- Swedish
   * ``tr`` -- Turkish
   * ``zh`` -- Chinese

   .. admonition:: Accelerating build speed

      Each language (except Japanese) provides its own stemming algorithm.
      Sphinx uses a Python implementation by default.  You can use a C
      implementation to accelerate building the index file.

      * `PorterStemmer <https://pypi.python.org/pypi/PorterStemmer>`_ (``en``)
      * `PyStemmer <https://pypi.python.org/pypi/PyStemmer>`_ (all languages)

   .. versionadded:: 1.1
      With support for ``en`` and ``ja``.

   .. versionchanged:: 1.3
      Added additional languages.

.. confval:: html_search_options

   A dictionary with options for the search language support, empty by default.
   The meaning of these options depends on the language selected.

   The English support has no options.

   The Japanese support has these options:

   :type:
      _`type` is dotted module path string to specify Splitter implementation which
      should be derived from :class:`sphinx.search.ja.BaseSplitter`.
      If not specified or None is specified, ``'sphinx.search.ja.DefaultSplitter'`` will
      be used.

      You can choose from these modules:

      :'sphinx.search.ja.DefaultSplitter':
         TinySegmenter algorithm. This is default splitter.
      :'sphinx.search.ja.MeCabSplitter':
         MeCab binding. To use this splitter, 'mecab' python binding or dynamic link
         library ('libmecab.so' for linux, 'libmecab.dll' for windows) is required.
      :'sphinx.search.ja.JanomeSplitter':
         Janome binding. To use this splitter,
         `Janome <https://pypi.python.org/pypi/Janome>`_ is required.

      To keep compatibility, ``'mecab'``, ``'janome'`` and ``'default'`` are also
      acceptable. However it will be deprecated in Sphinx-1.6.


   Other option values depend on splitter value which you choose.

   Options for ``'mecab'``:
      :dic_enc:
         _`dic_enc option` is the encoding for the MeCab algorithm.
      :dict:
         _`dict option` is the dictionary to use for the MeCab algorithm.
      :lib:
         _`lib option` is the library name for finding the MeCab library via ctypes if
         the Python binding is not installed.

      For example::

          html_search_options = {
              'type': 'mecab',
              'dic_enc': 'utf-8',
              'dict': '/path/to/mecab.dic',
              'lib': '/path/to/libmecab.so',
          }

   Options for ``'janome'``:
      :user_dic: _`user_dic option` is the user dictionary file path for Janome.
      :user_dic_enc:
         _`user_dic_enc option` is the encoding for the user dictionary file specified by
         ``user_dic`` option. Default is 'utf8'.

   .. versionadded:: 1.1

   .. versionchanged:: 1.4
      html_search_options for Japanese is re-organized and any custom splitter can be
      used by `type`_ settings.


   The Chinese support has these options:

   * ``dict``  -- the ``jieba`` dictionary path if want to use
     custom dictionary.

.. confval:: html_search_scorer

   The name of a JavaScript file (relative to the configuration directory) that
   implements a search results scorer.  If empty, the default will be used.

   .. XXX describe interface for scorer here

   .. versionadded:: 1.2

.. confval:: html_scaled_image_link

   If true, images itself links to the original image if it doesn't have
   'target' option or scale related options: 'scale', 'width', 'height'.
   The default is ``True``.

   .. versionadded:: 1.3

.. confval:: htmlhelp_basename

   Output file base name for HTML help builder.  Default is ``'pydoc'``.


.. _applehelp-options:

Options for Apple Help output
-----------------------------

.. versionadded:: 1.3

These options influence the Apple Help output.  This builder derives from the
HTML builder, so the HTML options also apply where appropriate.

.. note::

   Apple Help output will only work on Mac OS X 10.6 and higher, as it
   requires the :program:`hiutil` and :program:`codesign` command line tools,
   neither of which are Open Source.

   You can disable the use of these tools using
   :confval:`applehelp_disable_external_tools`, but the result will not be a
   valid help book until the indexer is run over the ``.lproj`` folders within
   the bundle.

.. confval:: applehelp_bundle_name

   The basename for the Apple Help Book.  Defaults to the :confval:`project`
   name.

.. confval:: applehelp_bundle_id

   The bundle ID for the help book bundle.

   .. warning::

      You *must* set this value in order to generate Apple Help.

.. confval:: applehelp_dev_region

   The development region.  Defaults to ``'en-us'``, which is Apple’s
   recommended setting.

.. confval:: applehelp_bundle_version

   The bundle version (as a string).  Defaults to ``'1'``.

.. confval:: applehelp_icon

   The help bundle icon file, or ``None`` for no icon.  According to Apple’s
   documentation, this should be a 16-by-16 pixel version of the application’s
   icon with a transparent background, saved as a PNG file.

.. confval:: applehelp_kb_product

   The product tag for use with :confval:`applehelp_kb_url`.  Defaults to
   :samp:`'{<project>}-{<release>}'`.

.. confval:: applehelp_kb_url

   The URL for your knowledgebase server,
   e.g. ``https://example.com/kbsearch.py?p='product'&q='query'&l='lang'``.
   Help Viewer will replace the values ``'product'``, ``'query'`` and
   ``'lang'`` at runtime with the contents of :confval:`applehelp_kb_product`,
   the text entered by the user in the search box and the user’s system
   language respectively.

   Defaults to ``None`` for no remote search.

.. confval:: applehelp_remote_url

   The URL for remote content.  You can place a copy of your Help Book’s
   ``Resources`` folder at this location and Help Viewer will attempt to use
   it to fetch updated content.

   e.g. if you set it to ``https://example.com/help/Foo/`` and Help Viewer
   wants a copy of ``index.html`` for an English speaking customer, it will
   look at ``https://example.com/help/Foo/en.lproj/index.html``.

   Defaults to ``None`` for no remote content.

.. confval:: applehelp_index_anchors

   If ``True``, tell the help indexer to index anchors in the generated HTML.
   This can be useful for jumping to a particular topic using the
   ``AHLookupAnchor`` function or the ``openHelpAnchor:inBook:`` method in
   your code.  It also allows you to use ``help:anchor`` URLs; see the Apple
   documentation for more information on this topic.

.. confval:: applehelp_min_term_length

   Controls the minimum term length for the help indexer.  Defaults to
   ``None``, which means the default will be used.

.. confval:: applehelp_stopwords

   Either a language specification (to use the built-in stopwords), or the
   path to a stopwords plist, or ``None`` if you do not want to use stopwords.
   The default stopwords plist can be found at
   ``/usr/share/hiutil/Stopwords.plist`` and contains, at time of writing,
   stopwords for the following languages:

   =========  ====
   Language   Code
   =========  ====
   English    en
   German     de
   Spanish    es
   French     fr
   Swedish    sv
   Hungarian  hu
   Italian    it
   =========  ====

   Defaults to :confval:`language`, or if that is not set, to :confval:`en`.

.. confval:: applehelp_locale

   Specifies the locale to generate help for.  This is used to determine
   the name of the ``.lproj`` folder inside the Help Book’s ``Resources``, and
   is passed to the help indexer.

   Defaults to :confval:`language`, or if that is not set, to :confval:`en`.

.. confval:: applehelp_title

   Specifies the help book title.  Defaults to :samp:`'{<project>} Help'`.

.. confval:: applehelp_codesign_identity

   Specifies the identity to use for code signing, or ``None`` if code signing
   is not to be performed.

   Defaults to the value of the environment variable ``CODE_SIGN_IDENTITY``,
   which is set by Xcode for script build phases, or ``None`` if that variable
   is not set.

.. confval:: applehelp_codesign_flags

   A *list* of additional arguments to pass to :program:`codesign` when
   signing the help book.

   Defaults to a list based on the value of the environment variable
   ``OTHER_CODE_SIGN_FLAGS``, which is set by Xcode for script build phases,
   or the empty list if that variable is not set.

.. confval:: applehelp_indexer_path

   The path to the :program:`hiutil` program.  Defaults to
   ``'/usr/bin/hiutil'``.

.. confval:: applehelp_codesign_path

   The path to the :program:`codesign` program.  Defaults to
   ``'/usr/bin/codesign'``.

.. confval:: applehelp_disable_external_tools

   If ``True``, the builder will not run the indexer or the code signing tool,
   no matter what other settings are specified.

   This is mainly useful for testing, or where you want to run the Sphinx
   build on a non-Mac OS X platform and then complete the final steps on OS X
   for some reason.

   Defaults to ``False``.


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

.. confval:: epub_theme_options

   A dictionary of options that influence the look and feel of the selected
   theme.  These are theme-specific.  For the options understood by the builtin
   themes, see :ref:`this section <builtin-themes>`.

   .. versionadded:: 1.2

.. confval:: epub_title

   The title of the document.  It defaults to the :confval:`html_title` option
   but can be set independently for epub creation.

.. confval:: epub_description

   The description of the document. The default value is ``''``.

   .. versionadded:: 1.4

   .. versionchanged:: 1.5
      Renamed from ``epub3_description``

.. confval:: epub_author

   The author of the document.  This is put in the Dublin Core metadata.  The
   default value is ``'unknown'``.

.. confval:: epub_contributor

   The name of a person, organization, etc. that played a secondary role in
   the creation of the content of an EPUB Publication. The default value is
   ``'unknown'``.

   .. versionadded:: 1.4

   .. versionchanged:: 1.5
      Renamed from ``epub3_contributor``

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

.. confval:: epub_guide

   Meta data for the guide element of :file:`content.opf`. This is a
   sequence of tuples containing the *type*, the *uri* and the *title* of
   the optional guide information. See the OPF documentation
   at `<http://idpf.org/epub>`_ for details. If possible, default entries
   for the *cover* and *toc* types are automatically inserted. However,
   the types can be explicitly overwritten if the default entries are not
   appropriate. Example::

      epub_guide = (('cover', 'cover.html', u'Cover Page'),)

   The default value is ``()``.

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
   its nested toc listing.  This allows easier navigation to the top of
   a chapter, but can be confusing because it mixes entries of different
   depth in one list.  The default value is ``True``.

   .. note::

      ``epub3`` builder ignores ``epub_tocdup`` option(always ``False``)

.. confval:: epub_tocscope

   This setting control the scope of the epub table of contents.  The setting
   can have the following values:

   * ``'default'`` -- include all toc entries that are not hidden (default)
   * ``'includehidden'`` -- include all toc entries

   .. versionadded:: 1.2

.. confval:: epub_fix_images

   This flag determines if sphinx should try to fix image formats that are not
   supported by some epub readers.  At the moment palette images with a small
   color table are upgraded.  You need the Python Image Library (Pillow the
   successor of the PIL) installed to use this option.  The default value is
   ``False`` because the automatic conversion may lose information.

   .. versionadded:: 1.2

.. confval:: epub_max_image_width

   This option specifies the maximum width of images.  If it is set to a value
   greater than zero, images with a width larger than the given value are
   scaled accordingly.  If it is zero, no scaling is performed. The default
   value is ``0``.  You need the Python Image Library (Pillow) installed to use
   this option.

   .. versionadded:: 1.2

.. confval:: epub_show_urls

   Control whether to display URL addresses. This is very useful for
   readers that have no other means to display the linked URL. The
   settings can have the following values:

   * ``'inline'`` -- display URLs inline in parentheses (default)
   * ``'footnote'`` -- display URLs in footnotes
   * ``'no'`` -- do not display URLs

   The display of inline URLs can be customized by adding CSS rules for the
   class ``link-target``.

   .. versionadded:: 1.2

.. confval:: epub_use_index

   If true, add an index to the epub document.  It defaults to the
   :confval:`html_use_index` option but can be set independently for epub
   creation.

   .. versionadded:: 1.2

.. confval:: epub_writing_mode

   It specifies writing direction. It can accept ``'horizontal'`` (default) and
   ``'vertical'``

   .. list-table::
      :header-rows: 1
      :stub-columns: 1

      - * ``epub_writing_mode``
        * ``'horizontal'``
        * ``'vertical'``
      - * writing-mode [#]_
        * ``horizontal-tb``
        * ``vertical-rl``
      - * page progression
        * left to right
        * right to left
      - * iBook's Scroll Theme support
        * scroll-axis is vertical.
        * scroll-axis is horizontal.

   .. [#] https://developer.mozilla.org/en-US/docs/Web/CSS/writing-mode

.. confval:: epub3_page_progression_direction

   The global direction in which the content flows.
   Allowed values are ``'ltr'`` (left-to-right), ``'rtl'`` (right-to-left) and
   ``'default'``. The default value is ``'ltr'``.

   When the ``'default'`` value is specified, the Author is expressing no
   preference and the Reading System may chose the rendering direction.

   .. versionadded:: 1.4

   .. deprecated:: 1.5
      Use ``epub_writing_mode`` instead.

.. _latex-options:

Options for LaTeX output
------------------------

These options influence LaTeX output. See further :doc:`latex`.

.. confval:: latex_engine

   The LaTeX engine to build the docs.  The setting can have the following
   values:

   * pdflatex -- PDFLaTeX (default)
   * xelatex -- XeLaTeX
   * lualatex -- LuaLaTeX
   * platex -- pLaTeX (default if `language` is 'ja')

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
   * *documentclass*: Normally, one of ``'manual'`` or ``'howto'`` (provided
     by Sphinx and based on ``'report'``, resp. ``'article'``; Japanese
     documents use ``'jsbook'``, resp. ``'jreport'``.) "howto" (non-Japanese)
     documents will not get appendices. Also they have a simpler title page.
     Other document classes can be given. Independently of the document class,
     the "sphinx" package is always loaded in order to define Sphinx's custom
     LaTeX commands.

   * *toctree_only*: Must be ``True`` or ``False``.  If true, the *startdoc*
     document itself is not included in the output, only the documents
     referenced by it via TOC trees.  With this option, you can put extra stuff
     in the master document that shows up in the HTML, but not the LaTeX output.

   .. versionadded:: 1.2
      In the past including your own document class required you to prepend the
      document class name with the string "sphinx". This is not necessary
      anymore.

   .. versionadded:: 0.3
      The 6th item ``toctree_only``.  Tuples with 5 items are still accepted.

.. confval:: latex_logo

   If given, this must be the name of an image file (relative to the
   configuration directory) that is the logo of the docs.  It is placed at the
   top of the title page.  Default: ``None``.

.. confval:: latex_toplevel_sectioning

   This value determines the topmost sectioning unit. It should be chosen from
   ``part``, ``chapter`` or ``section``. The default is ``None``; the topmost
   sectioning unit is switched by documentclass. ``section`` is used if
   documentclass will be ``howto``, otherwise ``chapter`` will be used.

   .. versionadded:: 1.4

.. confval:: latex_use_parts

   If true, the topmost sectioning unit is parts, else it is chapters.  Default:
   ``False``.

   .. versionadded:: 0.3

   .. deprecated:: 1.4
      Use :confval:`latex_toplevel_sectioning`.

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

.. confval:: latex_keep_old_macro_names

   If ``True`` (default) the ``\strong``, ``\code``, ``\bfcode``, ``\email``,
   ``\tablecontinued``, ``\titleref``, ``\menuselection``, ``\accelerator``,
   ``\crossref``, ``\termref``, and ``\optional`` text styling macros are
   pre-defined by Sphinx and may be user-customized by some
   ``\renewcommand``'s inserted either via ``'preamble'`` key or :dudir:`raw
   <raw-data-pass-through>` directive. If ``False``, only ``\sphinxstrong``,
   etc... macros are defined (and may be redefined by user). Setting to
   ``False`` may help solve macro name conflicts caused by user-added latex
   packages.

   .. versionadded:: 1.4.5


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
     ``'pxunit'``
        the value of the ``px`` when used in image attributes ``width`` and
        ``height``. The default value is ``'49336sp'`` which achieves
        ``96px=1in`` (``1in = 72.27*65536 = 4736286.72sp``, and all dimensions
        in TeX are internally integer multiples of ``sp``). To obtain for
        example ``100px=1in``, one can use ``'0.01in'`` but it is more precise
        to use ``'47363sp'``. To obtain ``72px=1in``, use ``'1bp'``.

        .. versionadded:: 1.5
     ``'passoptionstopackages'``
        "PassOptionsToPackage" call, default empty.

        .. versionadded:: 1.4
     ``'geometry'``
        "geometry" package inclusion, the default definition is:

          ``'\\usepackage[margin=1in,marginparwidth=0.5in]{geometry}'``.

        .. versionadded:: 1.5
     ``'babel'``
        "babel" package inclusion, default ``'\\usepackage{babel}'``.
     ``'fontpkg'``
        Font package inclusion, default ``'\\usepackage{times}'`` (which uses
        Times and Helvetica).  You can set this to ``''`` to use the Computer
        Modern fonts.

        .. versionchanged:: 1.2
           Defaults to ``''`` when the :confval:`language` uses the Cyrillic
           script.
     ``'fncychap'``
        Inclusion of the "fncychap" package (which makes fancy chapter titles),
        default ``'\\usepackage[Bjarne]{fncychap}'`` for English documentation
        (this option is slightly customized by Sphinx),
        ``'\\usepackage[Sonny]{fncychap}'`` for internationalized docs (because
        the "Bjarne" style uses numbers spelled out in English).  Other
        "fncychap" styles you can try are "Lenny", "Glenn", "Conny", "Rejne" and
        "Bjornstrup".  You can also set this to ``''`` to disable fncychap.
     ``'preamble'``
        Additional preamble content, default empty. See :doc:`latex`.
     ``'postamble'``
        Additional postamble content (before the indices), default empty.
     ``'figure_align'``
        Latex figure float alignment, default 'htbp' (here, top, bottom, page).
        Whenever an image doesn't fit into the current page, it will be
        'floated' into the next page but may be preceded by any other text.
        If you don't like this behavior, use 'H' which will disable floating
        and position figures strictly in the order they appear in the source.

        .. versionadded:: 1.3
     ``'footer'``
        Additional footer content (before the indices), default empty.

        .. deprecated:: 1.5
           User ``'postamble'`` key instead.

   * Keys that don't need be overridden unless in special cases are:

     ``'inputenc'``
        "inputenc" package inclusion, defaults to
        ``'\\usepackage[utf8]{inputenc}'`` when using pdflatex.
        Otherwise unset.

        .. versionchanged:: 1.4.3
           Previously ``'\\usepackage[utf8]{inputenc}'`` was used for all
           compilers.
     ``'cmappkg'``
        "cmap" package inclusion, default ``'\\usepackage{cmap}'``.

        .. versionadded:: 1.2
     ``'fontenc'``
        "fontenc" package inclusion, default ``'\\usepackage[T1]{fontenc}'``.
     ``'hyperref'``
        "hyperref" package inclusion; also loads package "hypcap" and issues
        ``\urlstyle{same}``. This is done after :file:`sphinx.sty` file is
        loaded and before executing the contents of ``'preamble'`` key.

        .. attention::

           Loading of packages "hyperref" and "hypcap" is mandatory.

        .. versionadded:: 1.5
           Previously this was done from inside :file:`sphinx.sty`.
     ``'maketitle'``
        "maketitle" call, default ``'\\maketitle'`` (but it has been
        redefined by the Sphinx ``manual`` and ``howto`` classes.) Override
        if you want to
        generate a differently-styled title page.
     ``'releasename'``
        value that prefixes ``'release'`` element on title page, default
        ``'Release'``.
     ``'tableofcontents'``
        "tableofcontents" call, default ``'\\sphinxtableofcontents'`` (it is a
        wrapper of unmodified ``\tableofcontents``, which may itself be
        customized by user loaded packages.)
        Override if
        you want to generate a different table of contents or put content
        between the title page and the TOC.

        .. versionchanged:: 1.5
           Previously the meaning of ``\tableofcontents`` itself was modified
           by Sphinx. This created an incompatibility with dedicated packages
           modifying it also such as "tocloft" or "etoc".
     ``'transition'``
        Commands used to display transitions, default
        ``'\n\n\\bigskip\\hrule{}\\bigskip\n\n'``.  Override if you want to
        display transitions differently.

        .. versionadded:: 1.2
     ``'printindex'``
        "printindex" call, the last thing in the file, default
        ``'\\printindex'``.  Override if you want to generate the index
        differently or append some content after the index. For example
        ``'\\footnotesize\\raggedright\\printindex'`` is advisable when the
        index is full of long entries.

   * Keys that are set by other options and therefore should not be overridden
     are:

     ``'docclass'``
     ``'classoptions'``
     ``'title'``
     ``'date'``
     ``'release'``
     ``'author'``
     ``'logo'``
     ``'makeindex'``
     ``'shorthandoff'``

.. confval:: latex_docclass

   A dictionary mapping ``'howto'`` and ``'manual'`` to names of real document
   classes that will be used as the base for the two Sphinx classes.  Default
   is to use ``'article'`` for ``'howto'`` and ``'report'`` for ``'manual'``.

   .. versionadded:: 1.0

   .. versionchanged:: 1.5

      In Japanese docs(`language` is ``ja``), ``'jreport'`` is used for
      ``'howto'`` and ``'jsbooks'`` is used for ``'manual'`` by default.

.. confval:: latex_additional_files

   A list of file names, relative to the configuration directory, to copy to the
   build directory when building LaTeX output.  This is useful to copy files
   that Sphinx doesn't copy automatically, e.g. if they are referenced in custom
   LaTeX added in ``latex_elements``.  Image files that are referenced in source
   files (e.g. via ``.. image::``) are copied automatically.

   You have to make sure yourself that the filenames don't collide with those of
   any automatically copied files.

   .. versionadded:: 0.6

   .. versionchanged:: 1.2
      This overrides the files which is provided from Sphinx such as sphinx.sty.

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
   * *toctree_only*: Must be ``True`` or ``False``.  If true, the *startdoc*
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

.. confval:: texinfo_no_detailmenu

   If true, do not generate a ``@detailmenu`` in the "Top" node's menu
   containing entries for each sub-node in the document.  Default is ``False``.

   .. versionadded:: 1.2

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

   .. versionadded:: 1.1


Options for the linkcheck builder
---------------------------------

.. confval:: linkcheck_ignore

   A list of regular expressions that match URIs that should not be checked
   when doing a ``linkcheck`` build.  Example::

      linkcheck_ignore = [r'http://localhost:\d+/']

   .. versionadded:: 1.1

.. confval:: linkcheck_retries

   The number of times the linkcheck builder will attempt to check a URL before
   declaring it broken. Defaults to 1 attempt.

   .. versionadded:: 1.4

.. confval:: linkcheck_timeout

   A timeout value, in seconds, for the linkcheck builder.  The default is to
   use Python's global socket timeout.

   .. versionadded:: 1.1

.. confval:: linkcheck_workers

   The number of worker threads to use when checking links.  Default is 5
   threads.

   .. versionadded:: 1.1

.. confval:: linkcheck_anchors

   If true, check the validity of ``#anchor``\ s in links. Since this requires
   downloading the whole document, it's considerably slower when enabled.
   Default is ``True``.

   .. versionadded:: 1.2


Options for the XML builder
---------------------------

.. confval:: xml_pretty

   If true, pretty-print the XML.  Default is ``True``.

   .. versionadded:: 1.2


.. rubric:: Footnotes

.. [1] A note on available globbing syntax: you can use the standard shell
       constructs ``*``, ``?``, ``[...]`` and ``[!...]`` with the feature that
       these all don't match slashes.  A double star ``**`` can be used to match
       any sequence of characters *including* slashes.


.. _cpp-config:

Options for the C++ domain
--------------------------

.. confval:: cpp_index_common_prefix

   A list of prefixes that will be ignored when sorting C++ objects in the global index.
   For example ``['awesome_lib::']``.

   .. versionadded:: 1.5

.. confval:: cpp_id_attributes

   A list of strings that the parser additionally should accept as attributes.
   This can for example be used when attributes have been ``#define`` d for portability.

   .. versionadded:: 1.5

.. confval:: cpp_paren_attributes

   A list of strings that the parser additionally should accept as attributes with one argument.
   That is, if ``my_align_as`` is in the list, then ``my_align_as(X)`` is parsed as an attribute
   for all strings ``X`` that have balanced brances (``()``, ``[]``, and ``{}``).
   This can for example be used when attributes have been ``#define`` d for portability.

   .. versionadded:: 1.5

example of configuration file
=============================

.. literalinclude:: _static/conf.py.txt
   :language: python
