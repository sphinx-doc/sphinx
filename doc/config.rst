.. highlightlang:: python

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
   contains the root :dir:`toctree` directive.  Default is ``'contents'``.

.. confval:: unused_docs

   A list of document names that are present, but not currently included in the
   toctree.  Use this setting to suppress the warning that is normally emitted
   in that case.

.. confval:: exclude_trees

   A list of directory paths, relative to the source directory, that are to be
   recursively excluded from the search for source files, that is, their
   subdirectories won't be searched too.  The default is ``[]``.

   .. versionadded:: 0.4

.. confval:: exclude_dirnames

   A list of directory names that are to be excluded from any recursive
   operation Sphinx performs (e.g. searching for source files or copying static
   files).  This is useful, for example, to exclude version-control-specific
   directories like ``'CVS'``.  The default is ``[]``.

   .. versionadded:: 0.5

.. confval:: exclude_dirs

   A list of directory names, relative to the source directory, that are to be
   excluded from the search for source files.

   .. deprecated:: 0.5
      This does not take subdirs of the excluded directories into account.  Use
      :confval:`exclude_trees` or :confval:`exclude_dirnames`, which match the
      expectations.

.. confval:: locale_dirs

   .. versionadded:: 0.5

   Directories in which to search for additional Sphinx message catalogs (see
   :confval:`language`), relative to the source directory.  The directories on
   this path are searched by the standard :mod:`gettext` module for a domain of
   ``sphinx``; so if you add the directory :file:`./locale` to this settting,
   the message catalogs (compiled from ``.po`` format using :program:`msgfmt`)
   must be in :file:`./locale/{language}/LC_MESSAGES/sphinx.mo`.

   The default is ``[]``.

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

.. confval:: default_role

   .. index:: default; role

   The name of a reST role (builtin or Sphinx extension) to use as the default
   role, that is, for text marked up ```like this```.  This can be set to
   ``'obj'`` to make ```filter``` a cross-reference to the function "filter".
   The default is ``None``, which doesn't reassign the default role.

   The default role can always be set within individual documents using the
   standard reST :dir:`default-role` directive.

   .. versionadded:: 0.4

.. confval:: keep_warnings

   If true, keep warnings as "system message" paragraphs in the built documents.
   Regardless of this setting, warnings are always written to the standard error
   stream when ``sphinx-build`` is run.

   The default is ``False``, the pre-0.5 behavior was to always keep them.

   .. versionadded:: 0.5


.. confval:: modindex_common_prefix

   A list of prefixes that are ignored for sorting the module index (e.g.,
   if this is set to ``['foo.']``, then ``foo.bar`` is shown under ``B``, not
   ``F``). This can be handy if you document a project that consists of a single
   package.  Works only for the HTML builder currently.   Default is ``[]``.

   .. versionadded:: 0.6


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

.. confval:: language

   The code for the language the docs are written in.  Any text automatically
   generated by Sphinx will be in that language.  Also, in the LaTeX builder, a
   suitable language will be selected as an option for the *Babel* package.
   Default is ``None``, which means that no translation will be done.

   .. versionadded:: 0.5

   Currently supported languages are:

   * ``cs`` -- Czech
   * ``de`` -- German
   * ``en`` -- English
   * ``es`` -- Spanish
   * ``fi`` -- Finnish
   * ``fr`` -- French
   * ``it`` -- Italian
   * ``nl`` -- Dutch
   * ``pl`` -- Polish
   * ``pt_BR`` -- Brazilian Portuguese
   * ``ru`` -- Russian
   * ``sl`` -- Slovenian
   * ``uk_UA`` -- Ukrainian
   * ``zh_TW`` -- Traditional Chinese

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
   :term:`description unit` titles, e.g. for :dir:`function` directives.
   Default is ``True``.

.. confval:: show_authors

   A boolean that decides whether :dir:`moduleauthor` and :dir:`sectionauthor`
   directives produce any output in the built files.

.. confval:: trim_footnote_reference_space

   Trim spaces before footnote references that are necessary for the reST parser
   to recognize the footnote, but do not look too nice in the output.

   .. versionadded:: 0.6


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

.. confval:: html_last_updated_fmt

   If this is not the empty string, a 'Last updated on:' timestamp is inserted
   at every page bottom, using the given :func:`strftime` format.  Default is
   ``'%b %d, %Y'`` (or a locale-dependent equivalent).

.. confval:: html_use_smartypants

   If true, *SmartyPants* will be used to convert quotes and dashes to
   typographically correct entities.  Default: ``True``.

.. confval:: html_add_permalinks

   If true, Sphinx will add "permalinks" for each heading and description
   environment as paragraph signs that become visible when the mouse hovers over
   them.  Default: ``True``.

   .. versionadded:: 0.6
      Previously, this was always activated.

.. confval:: html_sidebars

   Custom sidebar templates, must be a dictionary that maps document names to
   template names.  Example::

      html_sidebars = {
         'using/windows': 'windowssidebar.html'
      }

   This will render the template ``windowssidebar.html`` within the sidebar of
   the given document.

.. confval:: html_additional_pages

   Additional templates that should be rendered to HTML pages, must be a
   dictionary that maps document names to template names.

   Example::

      html_additional_pages = {
          'download': 'customdownload.html',
      }

   This will render the template ``customdownload.html`` as the page
   ``download.html``.

   .. note::

      Earlier versions of Sphinx had a value called :confval:`html_index` which
      was a clumsy way of controlling the content of the "index" document.  If
      you used this feature, migrate it by adding an ``'index'`` key to this
      setting, with your custom template as the value, and in your custom
      template, use ::

         {% extend "defindex.html" %}
         {% block tables %}
         ... old template content ...
         {% endblock %}

.. confval:: html_use_modindex

   If true, add a module index to the HTML documents.   Default is ``True``.

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

   If nonempty, this is the file name suffix for generated HTML files.  The
   default is ``".html"``.

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

.. confval:: html_show_sphinx

   If true, "Created using Sphinx" is shown in the HTML footer.  Default is
   ``True``.

   .. versionadded:: 0.4

.. confval:: htmlhelp_basename

   Output file base name for HTML help builder.  Default is ``'pydoc'``.


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
   * *documentclass*: Must be one of ``'manual'`` or ``'howto'``.  Only "manual"
     documents will get appendices.  Also, howtos will have a simpler title
     page.
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

.. confval:: latex_use_modindex

   If true, add a module index to LaTeX documents.   Default is ``True``.

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
     ``'makemodindex'``
     ``'shorthandoff'``
     ``'printmodindex'``

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
