.. highlight:: python

.. _build-config:

=============
Configuration
=============

.. module:: conf
   :synopsis: Build configuration file.

The :term:`configuration directory` must contain a file named :file:`conf.py`.
This file (containing Python code) is called the "build configuration file"
and contains (almost) all configuration needed to customize Sphinx input
and output behavior.

An optional file `docutils.conf`_ can be added to the configuration
directory to adjust `Docutils`_ configuration if not otherwise overridden or
set by Sphinx.

.. _`docutils`: https://docutils.sourceforge.io/
.. _`docutils.conf`: https://docutils.sourceforge.io/docs/user/config.html

The configuration file is executed as Python code at build time (using
:func:`importlib.import_module`, and with the current directory set to its
containing directory), and therefore can execute arbitrarily complex code.
Sphinx then reads simple names from the file's namespace as its configuration.

Important points to note:

* If not otherwise documented, values must be strings, and their default is the
  empty string.

* The term "fully-qualified name" refers to a string that names an importable
  Python object inside a module; for example, the FQN
  ``"sphinx.builders.Builder"`` means the ``Builder`` class in the
  ``sphinx.builders`` module.

* Remember that document names use ``/`` as the path separator and don't
  contain the file name extension.

* Since :file:`conf.py` is read as a Python file, the usual rules apply for
  encodings and Unicode support.

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


Project information
-------------------

.. confval:: project

   The documented project's name.

.. confval:: author

   The author name(s) of the document.  The default value is ``'unknown'``.

.. confval:: copyright

   A copyright statement in the style ``'2008, Author Name'``.

   .. versionchanged:: 7.1
      The value may now be a sequence of copyright statements in the above form,
      which will be displayed each to their own line.

.. confval:: project_copyright

   An alias of :confval:`copyright`.

   .. versionadded:: 3.5

.. confval:: version

   The major project version, used as the replacement for ``|version|``.  For
   example, for the Python documentation, this may be something like ``2.6``.

.. confval:: release

   The full project version, used as the replacement for ``|release|`` and
   e.g. in the HTML templates.  For example, for the Python documentation, this
   may be something like ``2.6.0rc1``.

   If you don't need the separation provided between :confval:`version` and
   :confval:`release`, just set them both to the same value.


General configuration
---------------------

.. confval:: extensions

   A list of strings that are module names of :doc:`extensions
   <extensions/index>`. These can be extensions coming with Sphinx (named
   ``sphinx.ext.*``) or custom ones.

   Note that you can extend :data:`sys.path` within the conf file if your
   extensions live in another directory -- but make sure you use absolute paths.
   If your extension path is relative to the :term:`configuration directory`,
   use :func:`os.path.abspath` like so::

      import sys, os

      sys.path.append(os.path.abspath('sphinxext'))

      extensions = ['extname']

   That way, you can load an extension called ``extname`` from the subdirectory
   ``sphinxext``.

   The configuration file itself can be an extension; for that, you only need
   to provide a :func:`setup` function in it.

.. confval:: source_suffix

   The file extensions of source files.  Sphinx considers the files with this
   suffix as sources.  The value can be a dictionary mapping file extensions
   to file types.  For example::

      source_suffix = {
          '.rst': 'restructuredtext',
          '.txt': 'restructuredtext',
          '.md': 'markdown',
      }

   By default, Sphinx only supports ``'restructuredtext'`` file type.  You can
   add a new file type using source parser extensions.  Please read a document
   of the extension to know which file type the extension supports.

   The value may also be a list of file extensions: then Sphinx will consider
   that they all map to the ``'restructuredtext'`` file type.

   Default is ``{'.rst': 'restructuredtext'}``.

   .. note:: file extensions have to start with a dot (e.g. ``.rst``).

   .. versionchanged:: 1.3
      Can now be a list of extensions.

   .. versionchanged:: 1.8
      Support file type mapping

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

      source_parsers = {'.md': 'recommonmark.parser.CommonMarkParser'}

   .. note::

      Refer to :doc:`/usage/markdown` for more information on using Markdown
      with Sphinx.

   .. versionadded:: 1.3

   .. deprecated:: 1.8
      Now Sphinx provides an API :meth:`.Sphinx.add_source_parser` to register
      a source parser.  Please use it instead.

.. confval:: master_doc

   Same as :confval:`root_doc`.

   .. versionchanged:: 4.0
      Renamed ``master_doc`` to ``root_doc``.

.. confval:: root_doc

   The document name of the "root" document, that is, the document that
   contains the root :rst:dir:`toctree` directive.  Default is ``'index'``.

   .. versionchanged:: 2.0
      The default is changed to ``'index'`` from ``'contents'``.
   .. versionchanged:: 4.0
      Renamed ``root_doc`` from ``master_doc``.

.. confval:: exclude_patterns

   A list of glob-style patterns [1]_ that should be excluded when looking for
   source files. They are matched against the source file names relative
   to the source directory, using slashes as directory separators on all
   platforms.

   Example patterns:

   - ``'library/xml.rst'`` -- ignores the ``library/xml.rst`` file
   - ``'library/xml'`` -- ignores the ``library/xml`` directory
   - ``'library/xml*'`` -- ignores all files and directories starting with
     ``library/xml``
   - ``'**/.svn'`` -- ignores all ``.svn`` directories

   :confval:`exclude_patterns` is also consulted when looking for static files
   in :confval:`html_static_path` and :confval:`html_extra_path`.

   .. versionadded:: 1.0

.. confval:: include_patterns

   A list of glob-style patterns [1]_ that are used to find source files. They
   are matched against the source file names relative to the source directory,
   using slashes as directory separators on all platforms. The default is ``**``,
   meaning that all files are recursively included from the source directory.
   :confval:`exclude_patterns` has priority over :confval:`include_patterns`.

   Example patterns:

   - ``'**'`` -- all files in the source directory and subdirectories, recursively
   - ``'library/xml'`` -- just the ``library/xml`` directory
   - ``'library/xml*'`` -- all files and directories starting with ``library/xml``
   - ``'**/doc'`` -- all ``doc`` directories (this might be useful if
     documentation is co-located with source files)

   .. versionadded:: 5.1

.. confval:: templates_path

   A list of paths that contain extra templates (or templates that overwrite
   builtin/theme-specific templates).  Relative paths are taken as relative to
   the configuration directory.

   .. versionchanged:: 1.3
      As these files are not meant to be built, they are automatically added to
      :confval:`exclude_patterns`.

.. confval:: template_bridge

   A string with the fully-qualified name of a callable (or simply a class)
   that returns an instance of :class:`~sphinx.application.TemplateBridge`.
   This instance is then used to render HTML documents, and possibly the output
   of other builders (currently the changes builder).  (Note that the template
   bridge must be made theme-aware if HTML themes are to be used.)

.. confval:: rst_epilog

   .. index:: pair: global; substitutions

   A string of reStructuredText that will be included at the end of every source
   file that is read.  This is a possible place to add substitutions that should
   be available in every file (another being :confval:`rst_prolog`).  An
   example::

      rst_epilog = """
      .. |psf| replace:: Python Software Foundation
      """

   .. versionadded:: 0.6

.. confval:: rst_prolog

   .. index:: pair: global; substitutions

   A string of reStructuredText that will be included at the beginning of every
   source file that is read.  This is a possible place to add substitutions that
   should be available in every file (another being :confval:`rst_epilog`).  An
   example::

      rst_prolog = """
      .. |psf| replace:: Python Software Foundation
      """

   .. versionadded:: 1.0

.. confval:: primary_domain

   .. index:: default; domain
              primary; domain

   The name of the default :doc:`domain </usage/domains/index>`.
   Can also be ``None`` to disable a default domain.  The default is ``'py'``.
   Those objects in other domains (whether the domain name is given explicitly,
   or selected by a :rst:dir:`default-domain` directive) will have the domain
   name explicitly prepended when named (e.g., when the default domain is C,
   Python functions will be named "Python function", not just "function").

   .. versionadded:: 1.0

.. confval:: default_role

   .. index:: default; role

   The name of a reST role (builtin or Sphinx extension) to use as the default
   role, that is, for text marked up ```like this```.  This can be set to
   ``'py:obj'`` to make ```filter``` a cross-reference to the Python function
   "filter".  The default is ``None``, which doesn't reassign the default role.

   The default role can always be set within individual documents using the
   standard reST :dudir:`default-role` directive.

   .. versionadded:: 0.4

.. confval:: keep_warnings

   If true, keep warnings as "system message" paragraphs in the built
   documents.  Regardless of this setting, warnings are always written to the
   standard error stream when ``sphinx-build`` is run.

   The default is ``False``, the pre-0.5 behavior was to always keep them.

   .. versionadded:: 0.5

.. confval:: show_warning_types

   If ``True``, the type of each warning is added as a suffix to the warning message,
   e.g., ``WARNING: [...] [index]`` or ``WARNING: [...] [toc.circular]``.
   The default is ``False``.

   .. versionadded:: 7.3.0

.. confval:: suppress_warnings

   A list of warning types to suppress arbitrary warning messages.

   Sphinx core supports following warning types:

   * ``app.add_node``
   * ``app.add_directive``
   * ``app.add_role``
   * ``app.add_generic_role``
   * ``app.add_source_parser``
   * ``config.cache``
   * ``download.not_readable``
   * ``epub.unknown_project_files``
   * ``epub.duplicated_toc_entry``
   * ``i18n.inconsistent_references``
   * ``index``
   * ``image.not_readable``
   * ``ref.term``
   * ``ref.ref``
   * ``ref.numref``
   * ``ref.keyword``
   * ``ref.option``
   * ``ref.citation``
   * ``ref.footnote``
   * ``ref.doc``
   * ``ref.python``
   * ``misc.highlighting_failure``
   * ``toc.circular``
   * ``toc.excluded``
   * ``toc.not_readable``
   * ``toc.secnum``

   Extensions can also define their own warning types.
   Those defined by the first-party ``sphinx.ext`` extensions are:

   * ``autodoc``
   * ``autodoc.import_object``
   * ``autosectionlabel.<document name>``
   * ``autosummary``
   * ``intersphinx.external``

   You can choose from these types.  You can also give only the first
   component to exclude all warnings attached to it.

   .. versionadded:: 1.4

   .. versionchanged:: 1.5

      Added ``misc.highlighting_failure``

   .. versionchanged:: 1.5.1

      Added ``epub.unknown_project_files``

   .. versionchanged:: 1.6

      Added ``ref.footnote``

   .. versionchanged:: 2.1

      Added ``autosectionlabel.<document name>``

   .. versionchanged:: 3.3.0

      Added ``epub.duplicated_toc_entry``

   .. versionchanged:: 4.3

      Added ``toc.excluded`` and ``toc.not_readable``

   .. versionadded:: 4.5

      Added ``i18n.inconsistent_references``

   .. versionadded:: 7.1

      Added ``index`` warning type.

   .. versionadded:: 7.3

      Added ``config.cache`` warning type.

.. confval:: needs_sphinx

   If set to a ``major.minor`` version string like ``'1.1'``, Sphinx will
   compare it with its version and refuse to build if it is too old.  Default
   is no requirement.

   .. versionadded:: 1.0

   .. versionchanged:: 1.4
      also accepts micro version string

.. confval:: needs_extensions

   This value can be a dictionary specifying version requirements for
   extensions in :confval:`extensions`, e.g. ``needs_extensions =
   {'sphinxcontrib.something': '1.5'}``.  The version strings should be in the
   form ``major.minor``.  Requirements do not have to be specified for all
   extensions, only for those you want to check.

   This requires that the extension specifies its version to Sphinx (see
   :ref:`dev-extensions` for how to do that).

   .. versionadded:: 1.3

.. confval:: manpages_url

   A URL to cross-reference :rst:role:`manpage` roles. If this is
   defined to ``https://manpages.debian.org/{path}``, the
   :literal:`:manpage:`man(1)`` role will link to
   <https://manpages.debian.org/man(1)>. The patterns available are:

   * ``page`` - the manual page (``man``)
   * ``section`` - the manual section (``1``)
   * ``path`` - the original manual page and section specified (``man(1)``)

   This also supports manpages specified as ``man.1``.

   .. note:: This currently affects only HTML writers but could be
             expanded in the future.

   .. versionadded:: 1.7

.. confval:: nitpicky

   If true, Sphinx will warn about *all* references where the target cannot be
   found.  Default is ``False``.  You can activate this mode temporarily using
   the :option:`-n <sphinx-build -n>` command-line switch.

   .. versionadded:: 1.0

.. confval:: nitpick_ignore

   A set or list of ``(type, target)`` tuples (by default empty) that should be
   ignored when generating warnings in "nitpicky mode".  Note that ``type``
   should include the domain name if present.  Example entries would be
   ``('py:func', 'int')`` or ``('envvar', 'LD_LIBRARY_PATH')``.

   .. versionadded:: 1.1
   .. versionchanged:: 6.2
      Changed allowable container types to a set, list, or tuple

.. confval:: nitpick_ignore_regex

   An extended version of :confval:`nitpick_ignore`, which instead interprets
   the ``type`` and ``target`` strings as regular expressions. Note, that the
   regular expression must match the whole string (as if the ``^`` and ``$``
   markers were inserted).

   For example, ``(r'py:.*', r'foo.*bar\.B.*')`` will ignore nitpicky warnings
   for all python entities that start with ``'foo'`` and have ``'bar.B'`` in
   them, such as ``('py:const', 'foo_package.bar.BAZ_VALUE')`` or
   ``('py:class', 'food.bar.Barman')``.

   .. versionadded:: 4.1
   .. versionchanged:: 6.2
      Changed allowable container types to a set, list, or tuple

.. confval:: numfig

   If true, figures, tables and code-blocks are automatically numbered if they
   have a caption.  The :rst:role:`numref` role is enabled.
   Obeyed so far only by HTML and LaTeX builders. Default is ``False``.

   .. note::

      The LaTeX builder always assigns numbers whether this option is enabled
      or not.

   .. versionadded:: 1.3

.. confval:: numfig_format

   A dictionary mapping ``'figure'``, ``'table'``, ``'code-block'`` and
   ``'section'`` to strings that are used for format of figure numbers.
   As a special character, ``%s`` will be replaced to figure number.

   Default is to use ``'Fig. %s'`` for ``'figure'``, ``'Table %s'`` for
   ``'table'``, ``'Listing %s'`` for ``'code-block'`` and ``'Section %s'`` for
   ``'section'``.

   .. versionadded:: 1.3

.. confval:: numfig_secnum_depth

   - if set to ``0``, figures, tables and code-blocks are continuously numbered
     starting at ``1``.
   - if ``1`` (default) numbers will be ``x.1``, ``x.2``, ... with ``x``
     the section number (top level sectioning; no ``x.`` if no section).
     This naturally applies only if section numbering has been activated via
     the ``:numbered:`` option of the :rst:dir:`toctree` directive.
   - ``2`` means that numbers will be ``x.y.1``, ``x.y.2``, ... if located in
     a sub-section (but still ``x.1``, ``x.2``, ... if located directly under a
     section and ``1``, ``2``, ... if not in any top level section.)
   - etc...

   .. versionadded:: 1.3

   .. versionchanged:: 1.7
      The LaTeX builder obeys this setting (if :confval:`numfig` is set to
      ``True``).

.. confval:: smartquotes

   If true, the `Docutils Smart Quotes transform`__, originally based on
   `SmartyPants`__ (limited to English) and currently applying to many
   languages, will be used to convert quotes and dashes to typographically
   correct entities.  Default: ``True``.

   __ https://docutils.sourceforge.io/docs/user/smartquotes.html
   __ https://daringfireball.net/projects/smartypants/

   .. versionadded:: 1.6.6
      It replaces deprecated :confval:`html_use_smartypants`.
      It applies by default to all builders except ``man`` and ``text``
      (see :confval:`smartquotes_excludes`.)

   A `docutils.conf`__ file located in the configuration directory (or a
   global :file:`~/.docutils` file) is obeyed unconditionally if it
   *deactivates* smart quotes via the corresponding `Docutils option`__.  But
   if it *activates* them, then :confval:`smartquotes` does prevail.

   __ https://docutils.sourceforge.io/docs/user/config.html
   __ https://docutils.sourceforge.io/docs/user/config.html#smart-quotes

.. confval:: smartquotes_action

   This string customizes the Smart Quotes transform.  See the file
   :file:`smartquotes.py` at the `Docutils repository`__ for details.  The
   default ``'qDe'`` educates normal **q**\ uote characters ``"``, ``'``,
   em- and en-**D**\ ashes ``---``, ``--``, and **e**\ llipses ``...``.

   .. versionadded:: 1.6.6

   __ https://sourceforge.net/p/docutils/code/HEAD/tree/trunk/docutils/

.. confval:: smartquotes_excludes

   This is a ``dict`` whose default is::

     {'languages': ['ja'], 'builders': ['man', 'text']}

   Each entry gives a sufficient condition to ignore the
   :confval:`smartquotes` setting and deactivate the Smart Quotes transform.
   Accepted keys are as above ``'builders'`` or ``'languages'``.
   The values are lists.

   .. note:: Currently, in case of invocation of :program:`make` with multiple
      targets, the first target name is the only one which is tested against
      the ``'builders'`` entry and it decides for all.  Also, a ``make text``
      following ``make html`` needs to be issued in the form ``make text
      O="-E"`` to force re-parsing of source files, as the cached ones are
      already transformed.  On the other hand the issue does not arise with
      direct usage of :program:`sphinx-build` as it caches
      (in its default usage) the parsed source files in per builder locations.

   .. hint:: An alternative way to effectively deactivate (or customize) the
      smart quotes for a given builder, for example ``latex``, is to use
      ``make`` this way:

      .. code-block:: console

         make latex O="-D smartquotes_action="

      This can follow some ``make html`` with no problem, in contrast to the
      situation from the prior note.

   .. versionadded:: 1.6.6

.. confval:: user_agent

   A User-Agent of Sphinx.  It is used for a header on HTTP access (ex.
   linkcheck, intersphinx and so on).  Default is ``"Sphinx/X.Y.Z
   requests/X.Y.Z python/X.Y.Z"``.

   .. versionadded:: 2.3

.. confval:: tls_verify

   If true, Sphinx verifies server certifications.  Default is ``True``.

   .. versionadded:: 1.5

.. confval:: tls_cacerts

   A path to a certification file of CA or a path to directory which
   contains the certificates.  This also allows a dictionary mapping
   hostname to the path to certificate file.
   The certificates are used to verify server certifications.

   .. versionadded:: 1.5

   .. tip:: Sphinx uses requests_ as a HTTP library internally.
            Therefore, Sphinx refers a certification file on the
            directory pointed ``REQUESTS_CA_BUNDLE`` environment
            variable if ``tls_cacerts`` not set.

            .. _requests: https://requests.readthedocs.io/en/master/

.. confval:: today
             today_fmt

   These values determine how to format the current date, used as the
   replacement for ``|today|``.

   * If you set :confval:`today` to a non-empty value, it is used.
   * Otherwise, the current time is formatted using :func:`time.strftime` and
     the format given in :confval:`today_fmt`.

   The default is now :confval:`today` and a :confval:`today_fmt` of ``'%b %d,
   %Y'`` (or, if translation is enabled with :confval:`language`, an equivalent
   format for the selected locale).

.. confval:: highlight_language

   The default language to highlight source code in.  The default is
   ``'default'``.  It is similar to ``'python3'``; it is mostly a superset of
   ``'python'`` but it fallbacks to ``'none'`` without warning if failed.
   ``'python3'`` and other languages will emit warning if failed.

   The value should be a valid Pygments lexer name, see
   :ref:`code-examples` for more details.

   .. versionadded:: 0.5

   .. versionchanged:: 1.4
      The default is now ``'default'``.  If you prefer Python 2 only
      highlighting, you can set it back to ``'python'``.

.. confval:: highlight_options

   A dictionary that maps language names to options for the lexer modules of
   Pygments.  These are lexer-specific; for the options understood by each,
   see the `Pygments documentation <https://pygments.org/docs/lexers>`_.

   Example::

     highlight_options = {
       'default': {'stripall': True},
       'php': {'startinline': True},
     }

   A single dictionary of options are also allowed.  Then it is recognized
   as options to the lexer specified by :confval:`highlight_language`::

     # configuration for the ``highlight_language``
     highlight_options = {'stripall': True}

   .. versionadded:: 1.3
   .. versionchanged:: 3.5

      Allow to configure highlight options for multiple languages

.. confval:: pygments_style

   The style name to use for Pygments highlighting of source code.  If not set,
   either the theme's default style or ``'sphinx'`` is selected for HTML
   output.

   .. versionchanged:: 0.3
      If the value is a fully-qualified name of a custom Pygments style class,
      this is then used as custom style.

.. confval:: maximum_signature_line_length

   If a signature's length in characters exceeds the number set, each
   parameter within the signature will be displayed on an individual logical
   line.

   When ``None`` (the default), there is no maximum length and the entire
   signature will be displayed on a single logical line.

   A 'logical line' is similar to a hard line break---builders or themes may
   choose to 'soft wrap' a single logical line, and this setting does not affect
   that behaviour.

   Domains may provide options to suppress any hard wrapping on an individual
   object directive, such as seen in the C, C++, and Python domains (e.g.
   :rst:dir:`py:function:single-line-parameter-list`).

   .. versionadded:: 7.1

.. confval:: add_function_parentheses

   A boolean that decides whether parentheses are appended to function and
   method role text (e.g. the content of ``:func:`input```) to signify that the
   name is callable.  Default is ``True``.

.. confval:: add_module_names

   A boolean that decides whether module names are prepended to all
   :term:`object` names (for object types where a "module" of some kind is
   defined), e.g. for :rst:dir:`py:function` directives.  Default is ``True``.

.. confval:: toc_object_entries

  Create table of contents entries for domain objects (e.g. functions, classes,
  attributes, etc.). Default is ``True``.

.. confval:: toc_object_entries_show_parents

   A string that determines how domain objects (e.g. functions, classes,
   attributes, etc.) are displayed in their table of contents entry.

   Use ``domain`` to allow the domain to determine the appropriate number of
   parents to show. For example, the Python domain would show ``Class.method()``
   and ``function()``, leaving out the ``module.`` level of parents.
   This is the default setting.

   Use ``hide`` to only show the name of the element without any parents
   (i.e. ``method()``).

   Use ``all`` to show the fully-qualified name for the object
   (i.e. ``module.Class.method()``),  displaying all parents.

   .. versionadded:: 5.2

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

   Trim spaces before footnote references that are necessary for the reST
   parser to recognize the footnote, but do not look too nice in the output.

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

.. confval:: strip_signature_backslash

   Default is ``False``.
   When backslash stripping is enabled then every occurrence of ``\\`` in a
   domain directive will be changed to ``\``, even within string literals.
   This was the behaviour before version 3.0, and setting this variable to
   ``True`` will reinstate that behaviour.

   .. versionadded:: 3.0

.. confval:: option_emphasise_placeholders

   Default is ``False``.
   When enabled, emphasise placeholders in :rst:dir:`option` directives.
   To display literal braces, escape with a backslash (``\{``). For example,
   ``option_emphasise_placeholders=True`` and ``.. option:: -foption={TYPE}`` would
   render with ``TYPE`` emphasised.

   .. versionadded:: 5.1

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
   language-specific figures named by :confval:`figure_language_filename`
   (e.g. the German version of ``myfigure.png`` will be ``myfigure.de.png``
   by default setting) and substitute them for original figures.  In the LaTeX
   builder, a suitable language will be selected as an option for the *Babel*
   package.  Default is ``'en'``.

   .. versionadded:: 0.5

   .. versionchanged:: 1.4

      Support figure substitution

   .. versionchanged:: 5.0

   Currently supported languages by Sphinx are:

   * ``ar`` -- Arabic
   * ``bg`` -- Bulgarian
   * ``bn`` -- Bengali
   * ``ca`` -- Catalan
   * ``cak`` -- Kaqchikel
   * ``cs`` -- Czech
   * ``cy`` -- Welsh
   * ``da`` -- Danish
   * ``de`` -- German
   * ``el`` -- Greek
   * ``en`` -- English (default)
   * ``eo`` -- Esperanto
   * ``es`` -- Spanish
   * ``et`` -- Estonian
   * ``eu`` -- Basque
   * ``fa`` -- Iranian
   * ``fi`` -- Finnish
   * ``fr`` -- French
   * ``he`` -- Hebrew
   * ``hi`` -- Hindi
   * ``hi_IN`` -- Hindi (India)
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
   * ``pt`` -- Portuguese
   * ``pt_BR`` -- Brazilian Portuguese
   * ``pt_PT`` -- European Portuguese
   * ``ro`` -- Romanian
   * ``ru`` -- Russian
   * ``si`` -- Sinhala
   * ``sk`` -- Slovak
   * ``sl`` -- Slovenian
   * ``sq`` -- Albanian
   * ``sr`` -- Serbian
   * ``sr@latin`` -- Serbian (Latin)
   * ``sr_RS`` -- Serbian (Cyrillic)
   * ``sv`` -- Swedish
   * ``ta`` -- Tamil
   * ``te`` -- Telugu
   * ``tr`` -- Turkish
   * ``uk_UA`` -- Ukrainian
   * ``ur`` -- Urdu
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

   .. note:: The :option:`-v option for sphinx-build command <sphinx-build -v>`
             is useful to check the locale_dirs config works as expected.  It
             emits debug messages if message catalog directory not found.

   .. versionchanged:: 1.5
      Use ``locales`` directory as a default value

.. confval:: gettext_allow_fuzzy_translations

   If true, "fuzzy" messages in the message catalogs are used for translation.
   The default is ``False``.

   .. versionadded:: 4.3

.. confval:: gettext_compact

   .. versionadded:: 1.1

   If true, a document's text domain is its docname if it is a top-level
   project file and its very base directory otherwise.

   If set to string, all document's text domain is this string, making all
   documents use single text domain.

   By default, the document ``markup/code.rst`` ends up in the ``markup`` text
   domain.  With this option set to ``False``, it is ``markup/code``.

   .. versionchanged:: 3.3
      The string value is now accepted.

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
   :literal-block: literal blocks (``::`` annotation and ``code-block`` directive)
   :doctest-block: doctest block
   :raw: raw content
   :image: image/figure uri

   For example: ``gettext_additional_targets = ['literal-block', 'image']``.

   The default is ``[]``.

   .. versionadded:: 1.3
   .. versionchanged:: 4.0

      The alt text for image is translated by default.

.. confval:: figure_language_filename

   The filename format for language-specific figures.  The default value is
   ``{root}.{language}{ext}``.  It will be expanded to
   ``dirname/filename.en.png`` from ``.. image:: dirname/filename.png``.
   The available format tokens are:

   * ``{root}`` - the filename, including any path component, without the file
     extension, e.g. ``dirname/filename``
   * ``{path}`` - the directory path component of the filename, with a trailing
     slash if non-empty, e.g. ``dirname/``
   * ``{docpath}`` - the directory path component for the current document, with
     a trailing slash if non-empty.
   * ``{basename}`` - the filename without the directory path or file extension
     components, e.g. ``filename``
   * ``{ext}`` - the file extension, e.g. ``.png``
   * ``{language}`` - the translation language, e.g. ``en``

   For example, setting this to ``{path}{language}/{basename}{ext}`` will
   expand to ``dirname/en/filename.png`` instead.

   .. versionadded:: 1.4

   .. versionchanged:: 1.5
      Added ``{path}`` and ``{basename}`` tokens.

   .. versionchanged:: 3.2
      Added ``{docpath}`` token.

.. confval:: translation_progress_classes

   Control which, if any, classes are added to indicate translation progress.
   This setting would likely only be used by translators of documentation,
   in order to quickly indicate translated and untranslated content.

   * ``True``: add ``translated`` and ``untranslated`` classes
     to all nodes with translatable content.
   * ``translated``: only add the ``translated`` class.
   * ``untranslated``: only add the ``untranslated`` class.
   * ``False``: do not add any classes to indicate translation progress.

   Defaults to ``False``.

   .. versionadded:: 7.1

.. _math-options:

Options for Math
----------------

These options influence Math notations.

.. confval:: math_number_all

   Set this option to ``True`` if you want all displayed math to be numbered.
   The default is ``False``.

.. confval:: math_eqref_format

   A string used for formatting the labels of references to equations.
   The ``{number}`` place-holder stands for the equation number.

   Example: ``'Eq.{number}'`` gets rendered as, for example, ``Eq.10``.

.. confval:: math_numfig

   If ``True``, displayed math equations are numbered across pages when
   :confval:`numfig` is enabled.  The :confval:`numfig_secnum_depth` setting
   is respected.  The :rst:role:`eq`, not :rst:role:`numref`, role
   must be used to reference equation numbers.  Default is ``True``.

   .. versionadded:: 1.7


.. _html-options:

Options for HTML output
-----------------------

These options influence HTML as well as HTML Help output, and other builders
that use Sphinx's HTMLWriter class.

.. confval:: html_theme

   The "theme" that the HTML output should use.  See the :doc:`section about
   theming </usage/theming>`.  The default is ``'alabaster'``.

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

   The style sheet to use for HTML pages.  A file of that name must exist
   either in Sphinx's :file:`static/` path, or in one of the custom paths given
   in :confval:`html_static_path`.  Default is the stylesheet given by the
   selected theme.  If you only want to add or override a few things compared
   to the theme's stylesheet, use CSS ``@import`` to import the theme's
   stylesheet.

.. confval:: html_title

   The "title" for HTML documentation generated with Sphinx's own templates.
   This is appended to the ``<title>`` tag of individual pages, and used in the
   navigation bar as the "topmost" element.  It defaults to :samp:`'{<project>}
   v{<revision>} documentation'`.

.. confval:: html_short_title

   A shorter "title" for the HTML docs.  This is used for links in the
   header and in the HTML Help docs.  If not given, it defaults to the value of
   :confval:`html_title`.

   .. versionadded:: 0.4

.. confval:: html_baseurl

   The base URL which points to the root of the HTML documentation.  It is used
   to indicate the location of document using `The Canonical Link Relation`_.
   Default: ``''``.

   .. _The Canonical Link Relation: https://datatracker.ietf.org/doc/html/rfc6596

   .. versionadded:: 1.8

.. confval:: html_codeblock_linenos_style

   The style of line numbers for code-blocks.

   * ``'table'`` -- display line numbers using ``<table>`` tag
   * ``'inline'`` -- display line numbers using ``<span>`` tag (default)

   .. versionadded:: 3.2
   .. versionchanged:: 4.0

      It defaults to ``'inline'``.

   .. deprecated:: 4.0

.. confval:: html_context

   A dictionary of values to pass into the template engine's context for all
   pages.  Single values can also be put in this dictionary using the
   :option:`-A <sphinx-build -A>` command-line option of ``sphinx-build``.

   .. versionadded:: 0.5

.. confval:: html_logo

   If given, this must be the name of an image file (path relative to the
   :term:`configuration directory`) that is the logo of the docs, or URL that
   points an image file for the logo.  It is placed at the top of the sidebar;
   its width should therefore not exceed 200 pixels.  Default: ``None``.

   .. versionadded:: 0.4.1
      The image file will be copied to the ``_static`` directory of the output
      HTML, but only if the file does not already exist there.

   .. versionchanged:: 4.0
      Also accepts the URL for the logo file.

.. confval:: html_favicon

   If given, this must be the name of an image file (path relative to the
   :term:`configuration directory`) that is the favicon of the docs, or URL that
   points an image file for the favicon.  Modern browsers use this as the icon
   for tabs, windows and bookmarks.  It should be a Windows-style icon file
   (``.ico``), which is 16x16 or 32x32 pixels large.  Default: ``None``.

   .. versionadded:: 0.4
      The image file will be copied to the ``_static`` directory of the output
      HTML, but only if the file does not already exist there.

   .. versionchanged:: 4.0
      Also accepts the URL for the favicon.

.. confval:: html_css_files

   A list of CSS files.  The entry must be a *filename* string or a tuple
   containing the *filename* string and the *attributes* dictionary.  The
   *filename* must be relative to the :confval:`html_static_path`, or a full URI
   with scheme like ``https://example.org/style.css``.  The *attributes* is used
   for attributes of ``<link>`` tag.  It defaults to an empty list.

   Example::

       html_css_files = ['custom.css',
                         'https://example.com/css/custom.css',
                         ('print.css', {'media': 'print'})]

   As a special attribute, *priority* can be set as an integer to load the CSS
   file at an earlier or lazier step.  For more information, refer
   :meth:`.Sphinx.add_css_file()`.

   .. versionadded:: 1.8
   .. versionchanged:: 3.5

      Support priority attribute

.. confval:: html_js_files

   A list of JavaScript *filename*.  The entry must be a *filename* string or a
   tuple containing the *filename* string and the *attributes* dictionary.  The
   *filename* must be relative to the :confval:`html_static_path`, or a full
   URI with scheme like ``https://example.org/script.js``.  The *attributes* is
   used for attributes of ``<script>`` tag.  It defaults to an empty list.

   Example::

       html_js_files = ['script.js',
                        'https://example.com/scripts/custom.js',
                        ('custom.js', {'async': 'async'})]

   As a special attribute, *priority* can be set as an integer to load the
   JavaScript file at an earlier or lazier step.  For more information, refer
   :meth:`.Sphinx.add_js_file()`.

   .. versionadded:: 1.8
   .. versionchanged:: 3.5

      Support priority attribute

.. confval:: html_static_path

   A list of paths that contain custom static files (such as style
   sheets or script files).  Relative paths are taken as relative to
   the configuration directory.  They are copied to the output's
   :file:`_static` directory after the theme's static files, so a file
   named :file:`default.css` will overwrite the theme's
   :file:`default.css`.

   As these files are not meant to be built, they are automatically excluded
   from source files.

   .. note::

      For security reasons, dotfiles under ``html_static_path`` will
      not be copied.  If you would like to copy them intentionally, please
      add each filepath to this setting::

          html_static_path = ['_static', '_static/.htaccess']

      Another way to do that, you can also use
      :confval:`html_extra_path`.  It allows to copy dotfiles under
      the directories.

   .. versionchanged:: 0.4
      The paths in :confval:`html_static_path` can now contain subdirectories.

   .. versionchanged:: 1.0
      The entries in :confval:`html_static_path` can now be single files.

   .. versionchanged:: 1.8
      The files under :confval:`html_static_path` are excluded from source
      files.

.. confval:: html_extra_path

   A list of paths that contain extra files not directly related to
   the documentation, such as :file:`robots.txt` or :file:`.htaccess`.
   Relative paths are taken as relative to the configuration
   directory.  They are copied to the output directory.  They will
   overwrite any existing file of the same name.

   As these files are not meant to be built, they are automatically excluded
   from source files.

   .. versionadded:: 1.2

   .. versionchanged:: 1.4
      The dotfiles in the extra directory will be copied to the output
      directory.  And it refers :confval:`exclude_patterns` on copying extra
      files and directories, and ignores if path matches to patterns.

.. confval:: html_last_updated_fmt

   If this is not None, a 'Last updated on:' timestamp is inserted
   at every page bottom, using the given :func:`~time.strftime` format.
   The empty string is equivalent to ``'%b %d, %Y'`` (or a
   locale-dependent equivalent).

.. confval:: html_use_smartypants

   If true, quotes and dashes are converted to typographically correct
   entities.  Default: ``True``.

   .. deprecated:: 1.6
      To disable smart quotes, use rather :confval:`smartquotes`.

.. confval:: html_permalinks

   Add link anchors for each heading and description environment.
   Default: ``True``.

   .. versionadded:: 3.5

.. confval:: html_permalinks_icon

   Text for link anchors for each heading and description environment.
   HTML entities and Unicode are allowed.  Default: a paragraph sign; ``¶``

   .. versionadded:: 3.5

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

     The default sidebars (for documents that don't match any pattern) are
     defined by theme itself.  Builtin themes are using these templates by
     default: ``['localtoc.html', 'relations.html', 'sourcelink.html',
     'searchbox.html']``.

   * If a value is a single string, it specifies a custom sidebar to be added
     between the ``'sourcelink.html'`` and ``'searchbox.html'`` entries.  This
     is for compatibility with Sphinx versions before 1.0.

   .. deprecated:: 1.7

      a single string value for ``html_sidebars`` will be removed in 2.0

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

.. confval:: html_show_sourcelink

   If true (and :confval:`html_copy_source` is true as well), links to the
   reST sources will be added to the sidebar.  The default is ``True``.

   .. versionadded:: 0.6

.. confval:: html_sourcelink_suffix

   Suffix to be appended to source links (see :confval:`html_show_sourcelink`),
   unless they have this suffix already.  Default is ``'.txt'``.

   .. versionadded:: 1.5

.. confval:: html_use_opensearch

   If nonempty, an `OpenSearch <https://github.com/dewitt/opensearch>`_
   description file will be output, and all pages will contain a ``<link>``
   tag referring to it.  Since OpenSearch doesn't support relative URLs for
   its search page location, the value of this option must be the base URL
   from which these documents are served (without trailing slash), e.g.
   ``"https://docs.python.org"``.  The default is ``''``.

.. confval:: html_file_suffix

   This is the file name suffix for generated HTML files, if set to a :obj:`str`
   value.  If left to the default ``None``, the suffix will be ``".html"``.

   .. versionadded:: 0.4

.. confval:: html_link_suffix

   Suffix for generated links to HTML files.  The default is whatever
   :confval:`html_file_suffix` is set to; it can be set differently (e.g. to
   support different web server setups).

   .. versionadded:: 0.6

.. confval:: html_show_copyright

   If true, "(C) Copyright ..." is shown in the HTML footer. Default is
   ``True``.

   .. versionadded:: 1.0

.. confval:: html_show_search_summary

   If true, the text around the keyword is shown as summary of each search result.
   Default is ``True``.

   .. versionadded:: 4.5

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

   If true, a list all whose items consist of a single paragraph and/or a
   sub-list all whose items etc... (recursive definition) will not use the
   ``<p>`` element for any of its items. This is standard docutils behavior.
   Default: ``True``.

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

      * `PorterStemmer <https://pypi.org/project/PorterStemmer/>`_ (``en``)
      * `PyStemmer <https://pypi.org/project/PyStemmer/>`_ (all languages)

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
      _`type` is dotted module path string to specify Splitter implementation
      which should be derived from :class:`!sphinx.search.ja.BaseSplitter`.  If
      not specified or ``None`` is specified,
      ``'sphinx.search.ja.DefaultSplitter'`` will be used.

      You can choose from these modules:

      :'sphinx.search.ja.DefaultSplitter':
         TinySegmenter algorithm. This is default splitter.
      :'sphinx.search.ja.MecabSplitter':
         MeCab binding. To use this splitter, 'mecab' python binding or dynamic
         link library ('libmecab.so' for linux, 'libmecab.dll' for windows) is
         required.
      :'sphinx.search.ja.JanomeSplitter':
         Janome binding. To use this splitter,
         `Janome <https://pypi.org/project/Janome/>`_ is required.

      .. deprecated:: 1.6
         ``'mecab'``, ``'janome'`` and ``'default'`` is deprecated.
         To keep compatibility, ``'mecab'``, ``'janome'`` and ``'default'`` are
         also acceptable.

   Other option values depend on splitter value which you choose.

   Options for ``'mecab'``:
      :dic_enc:
         _`dic_enc option` is the encoding for the MeCab algorithm.
      :dict:
         _`dict option` is the dictionary to use for the MeCab algorithm.
      :lib:
         _`lib option` is the library name for finding the MeCab library via
         ctypes if the Python binding is not installed.

      For example::

          html_search_options = {
              'type': 'mecab',
              'dic_enc': 'utf-8',
              'dict': '/path/to/mecab.dic',
              'lib': '/path/to/libmecab.so',
          }

   Options for ``'janome'``:
      :user_dic:
         _`user_dic option` is the user dictionary file path for Janome.
      :user_dic_enc:
         _`user_dic_enc option` is the encoding for the user dictionary file
         specified by ``user_dic`` option. Default is 'utf8'.

   .. versionadded:: 1.1

   .. versionchanged:: 1.4
      html_search_options for Japanese is re-organized and any custom splitter
      can be used by `type`_ settings.

   The Chinese support has these options:

   * ``dict``  -- the ``jieba`` dictionary path if want to use
     custom dictionary.

.. confval:: html_search_scorer

   The name of a JavaScript file (relative to the configuration directory) that
   implements a search results scorer.  If empty, the default will be used.

   The scorer must implement the following interface,
   and may optionally define the ``score()`` function for more granular control.

   .. code-block:: javascript

      const Scorer = {
          // Implement the following function to further tweak the score for each result
          score: result => {
            const [docName, title, anchor, descr, score, filename] = result

            // ... calculate a new score ...
            return score
          },

          // query matches the full name of an object
          objNameMatch: 11,
          // or matches in the last dotted part of the object name
          objPartialMatch: 6,
          // Additive scores depending on the priority of the object
          objPrio: {
            0: 15, // used to be importantResults
            1: 5, // used to be objectResults
            2: -5, // used to be unimportantResults
          },
          //  Used when the priority is not in the mapping.
          objPrioDefault: 0,

          // query found in title
          title: 15,
          partialTitle: 7,

          // query found in terms
          term: 5,
          partialTerm: 2,
      };

   .. versionadded:: 1.2

.. confval:: html_scaled_image_link

   If true, image itself links to the original image if it doesn't have
   'target' option or scale related options: 'scale', 'width', 'height'.
   The default is ``True``.

   Document authors can disable this feature manually with giving
   ``no-scaled-link`` class to the image:

   .. code-block:: rst

      .. image:: sphinx.png
         :scale: 50%
         :class: no-scaled-link

   .. versionadded:: 1.3

   .. versionchanged:: 3.0

      It is disabled for images having ``no-scaled-link`` class

.. confval:: html_math_renderer

   The name of math_renderer extension for HTML output.  The default is
   ``'mathjax'``.

   .. versionadded:: 1.8

.. confval:: html_experimental_html5_writer

   Output is processed with HTML5 writer.  Default is ``False``.

   .. versionadded:: 1.6

   .. deprecated:: 2.0

.. confval:: html4_writer

   Output is processed with HTML4 writer.  Default is ``False``.

Options for Single HTML output
-------------------------------

.. confval:: singlehtml_sidebars

   Custom sidebar templates, must be a dictionary that maps document names to
   template names.  And it only allows a key named ``'index'``.  All other keys
   are ignored.  For more information, refer to :confval:`html_sidebars`.  By
   default, it is same as :confval:`html_sidebars`.


.. _htmlhelp-options:

Options for HTML help output
-----------------------------

.. confval:: htmlhelp_basename

   Output file base name for HTML help builder.  Default is ``'pydoc'``.

.. confval:: htmlhelp_file_suffix

   This is the file name suffix for generated HTML help files.  The
   default is ``".html"``.

   .. versionadded:: 2.0

.. confval:: htmlhelp_link_suffix

   Suffix for generated links to HTML files.  The default is ``".html"``.

   .. versionadded:: 2.0


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

   The help bundle icon file, or ``None`` for no icon.  According to Apple's
   documentation, this should be a 16-by-16 pixel version of the application's
   icon with a transparent background, saved as a PNG file.

.. confval:: applehelp_kb_product

   The product tag for use with :confval:`applehelp_kb_url`.  Defaults to
   :samp:`'{<project>}-{<release>}'`.

.. confval:: applehelp_kb_url

   The URL for your knowledgebase server,
   e.g. ``https://example.com/kbsearch.py?p='product'&q='query'&l='lang'``.
   Help Viewer will replace the values ``'product'``, ``'query'`` and
   ``'lang'`` at runtime with the contents of :confval:`applehelp_kb_product`,
   the text entered by the user in the search box and the user's system
   language respectively.

   Defaults to ``None`` for no remote search.

.. confval:: applehelp_remote_url

   The URL for remote content.  You can place a copy of your Help Book's
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

   Defaults to :confval:`language`, or if that is not set, to ``'en'``.

.. confval:: applehelp_locale

   Specifies the locale to generate help for.  This is used to determine
   the name of the ``.lproj`` folder inside the Help Book’s ``Resources``, and
   is passed to the help indexer.

   Defaults to :confval:`language`, or if that is not set, to ``'en'``.

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
the `Dublin Core metadata <https://dublincore.org/>`_.

.. confval:: epub_basename

   The basename for the epub file.  It defaults to the :confval:`project` name.

.. confval:: epub_theme

   The HTML theme for the epub output.  Since the default themes are not
   optimized for small screen space, using the same theme for HTML and epub
   output is usually not wise.  This defaults to ``'epub'``, a theme designed
   to save visual space.

.. confval:: epub_theme_options

   A dictionary of options that influence the look and feel of the selected
   theme.  These are theme-specific.  For the options understood by the builtin
   themes, see :ref:`this section <builtin-themes>`.

   .. versionadded:: 1.2

.. confval:: epub_title

   The title of the document.  It defaults to the :confval:`html_title` option
   but can be set independently for epub creation.  It defaults to the
   :confval:`project` option.

   .. versionchanged:: 2.0
      It defaults to the ``project`` option.

.. confval:: epub_description

   The description of the document. The default value is ``'unknown'``.

   .. versionadded:: 1.4

   .. versionchanged:: 1.5
      Renamed from ``epub3_description``

.. confval:: epub_author

   The author of the document.  This is put in the Dublin Core metadata.  It
   defaults to the :confval:`author` option.

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

   The publisher of the document.  This is put in the Dublin Core metadata.
   You may use any sensible string, e.g. the project homepage.  The defaults to
   the :confval:`author` option.

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
   metadata.  You may use a
   `XML's Name format <https://www.w3.org/TR/REC-xml/#NT-NameStartChar>`_
   string.  You can't use hyphen, period, numbers as a first character.  The
   default value is ``'unknown'``.

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

.. confval:: epub_css_files

   A list of CSS files.  The entry must be a *filename* string or a tuple
   containing the *filename* string and the *attributes* dictionary.  For more
   information, see :confval:`html_css_files`.

   .. versionadded:: 1.8

.. confval:: epub_guide

   Meta data for the guide element of :file:`content.opf`. This is a
   sequence of tuples containing the *type*, the *uri* and the *title* of
   the optional guide information. See the OPF documentation
   at `<https://idpf.org/epub>`_ for details. If possible, default entries
   for the *cover* and *toc* types are automatically inserted. However,
   the types can be explicitly overwritten if the default entries are not
   appropriate. Example::

      epub_guide = (('cover', 'cover.html', 'Cover Page'),)

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

.. confval:: epub_tocscope

   This setting control the scope of the epub table of contents.  The setting
   can have the following values:

   * ``'default'`` -- include all toc entries that are not hidden (default)
   * ``'includehidden'`` -- include all toc entries

   .. versionadded:: 1.2

.. confval:: epub_fix_images

   This flag determines if sphinx should try to fix image formats that are not
   supported by some epub readers.  At the moment palette images with a small
   color table are upgraded.  You need Pillow, the Python Image Library,
   installed to use this option.  The default value is ``False`` because the
   automatic conversion may lose information.

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


.. _latex-options:

Options for LaTeX output
------------------------

These options influence LaTeX output.

.. confval:: latex_engine

   The LaTeX engine to build the docs.  The setting can have the following
   values:

   * ``'pdflatex'`` -- PDFLaTeX (default)
   * ``'xelatex'`` -- XeLaTeX
   * ``'lualatex'`` -- LuaLaTeX
   * ``'platex'`` -- pLaTeX
   * ``'uplatex'`` -- upLaTeX (default if :confval:`language` is ``'ja'``)

   ``'pdflatex'``\ 's support for Unicode characters is limited.

   .. note::

      2.0 adds to ``'pdflatex'`` support in Latin language document of
      occasional Cyrillic or Greek letters or words.  This is not automatic,
      see the discussion of the :confval:`latex_elements` ``'fontenc'`` key.

   If your project uses Unicode characters, setting the engine to
   ``'xelatex'`` or ``'lualatex'`` and making sure to use an OpenType font
   with wide-enough glyph coverage is often easier than trying to make
   ``'pdflatex'`` work with the extra Unicode characters.  Since Sphinx 2.0
   the default is the GNU FreeFont which covers well Latin, Cyrillic and
   Greek.

   .. versionchanged:: 2.1.0

      Use ``xelatex`` (and LaTeX package ``xeCJK``) by default for Chinese
      documents.

   .. versionchanged:: 2.2.1

      Use ``xelatex`` by default for Greek documents.

   .. versionchanged:: 2.3

      Add ``uplatex`` support.

   .. versionchanged:: 4.0

      ``uplatex`` becomes the default setting of Japanese documents.

   Contrarily to :ref:`MathJaX math rendering in HTML output <math-support>`,
   LaTeX requires some extra configuration to support Unicode literals in
   :rst:dir:`math`: the only comprehensive solution (as far as we know) is to
   use ``'xelatex'`` or ``'lualatex'`` *and* to add
   ``r'\usepackage{unicode-math}'`` (e.g. via the :confval:`latex_elements`
   ``'preamble'`` key).  You may prefer
   ``r'\usepackage[math-style=literal]{unicode-math}'`` to keep a Unicode
   literal such as ``α`` (U+03B1) for example as is in output, rather than
   being rendered as :math:`\alpha`.

.. confval:: latex_documents

   This value determines how to group the document tree into LaTeX source files.
   It must be a list of tuples ``(startdocname, targetname, title, author,
   theme, toctree_only)``, where the items are:

   *startdocname*
     String that specifies the :term:`document name` of the LaTeX file's master
     document.  All documents referenced by the *startdoc* document in TOC trees
     will be included in the LaTeX file.  (If you want to use the default root
     document for your LaTeX build, provide your :confval:`root_doc` here.)

   *targetname*
     File name of the LaTeX file in the output directory.

   *title*
     LaTeX document title.  Can be empty to use the title of the *startdoc*
     document.  This is inserted as LaTeX markup, so special characters like a
     backslash or ampersand must be represented by the proper LaTeX commands if
     they are to be inserted literally.

   *author*
     Author for the LaTeX document.  The same LaTeX markup caveat as for *title*
     applies.  Use ``\\and`` to separate multiple authors, as in:
     ``'John \\and Sarah'`` (backslashes must be Python-escaped to reach LaTeX).

   *theme*
     LaTeX theme.  See :confval:`latex_theme`.

   *toctree_only*
     Must be ``True`` or ``False``.  If true, the *startdoc* document itself is
     not included in the output, only the documents referenced by it via TOC
     trees.  With this option, you can put extra stuff in the master document
     that shows up in the HTML, but not the LaTeX output.

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
   ``'part'``, ``'chapter'`` or ``'section'``. The default is ``None``;
   the topmost
   sectioning unit is switched by documentclass: ``section`` is used if
   documentclass will be ``howto``, otherwise ``chapter`` will be used.

   Note that if LaTeX uses ``\part`` command, then the numbering of sectioning
   units one level deep gets off-sync with HTML numbering, because LaTeX
   numbers continuously ``\chapter`` (or ``\section`` for ``howto``.)

   .. versionadded:: 1.4

.. confval:: latex_appendices

   A list of document names to append as an appendix to all manuals.

.. confval:: latex_domain_indices

   If true, generate domain-specific indices in addition to the general index.
   For e.g. the Python domain, this is the global module index.  Default is
   ``True``.

   This value can be a bool or a list of index names that should be generated,
   like for :confval:`html_domain_indices`.

   .. versionadded:: 1.0

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

.. confval:: latex_use_latex_multicolumn

   The default is ``False``: it means that Sphinx's own macros are used for
   merged cells from grid tables. They allow general contents (literal blocks,
   lists, blockquotes, ...) but may have problems if the
   :rst:dir:`tabularcolumns` directive was used to inject LaTeX mark-up of the
   type ``>{..}``, ``<{..}``, ``@{..}`` as column specification.

   Setting to ``True`` means to use LaTeX's standard ``\multicolumn``; this is
   incompatible with literal blocks in the horizontally merged cell, and also
   with multiple paragraphs in such cell if the table is rendered using
   ``tabulary``.

   .. versionadded:: 1.6

.. confval:: latex_table_style

   A list of styling classes (strings).  Currently supported:

   - ``'booktabs'``: no vertical lines, and only 2 or 3 horizontal lines (the
     latter if there is a header), using the booktabs_ package.

   - ``'borderless'``: no lines whatsoever.

   - ``'colorrows'``: the table rows are rendered with alternating background
     colours.  The interface to customize them is via :ref:`dedicated keys
     <tablecolors>` of :ref:`latexsphinxsetup`.

     .. important::

        With the ``'colorrows'`` style, the ``\rowcolors`` LaTeX command
        becomes a no-op (this command has limitations and has never correctly
        supported all types of tables Sphinx produces in LaTeX).  Please
        update your project to use instead
        the :ref:`latex table color configuration <tablecolors>` keys.

   Default: ``['booktabs', 'colorrows']``

   .. versionadded:: 5.3.0

   .. versionchanged:: 6.0.0

      Modify default from ``[]`` to ``['booktabs', 'colorrows']``.

   Each table can override the global style via ``:class:`` option, or
   ``.. rst-class::`` for no-directive tables (cf.  :ref:`table-directives`).
   Currently recognized classes are ``booktabs``, ``borderless``,
   ``standard``, ``colorrows``, ``nocolorrows``.  The latter two can be
   combined with any of the first three.  The ``standard`` class produces
   tables with both horizontal and vertical lines (as has been the default so
   far with Sphinx).

   A single-row multi-column merged cell will obey the row colour, if it is
   set.  See also ``TableMergeColor{Header,Odd,Even}`` in the
   :ref:`latexsphinxsetup` section.

   .. note::

      - It is hard-coded in LaTeX that a single cell will obey the row colour
        even if there is a column colour set via ``\columncolor`` from a
        column specification (see :rst:dir:`tabularcolumns`).  Sphinx provides
        ``\sphinxnorowcolor`` which can be used like this:

        .. code-block:: latex

           >{\columncolor{blue}\sphinxnorowcolor}

        in a table column specification.

      - Sphinx also provides ``\sphinxcolorblend`` which however requires the
        xcolor_ package.  Here is an example:

        .. code-block:: latex

           >{\sphinxcolorblend{!95!red}}

        It means that in this column, the row colours will be slightly tinted
        by red; refer to xcolor_ documentation for more on the syntax of its
        ``\blendcolors`` command (a ``\blendcolors`` in place of
        ``\sphinxcolorblend`` would modify colours of the cell *contents*, not
        of the cell *background colour panel*...).  You can find an example of
        usage in the :ref:`dev-deprecated-apis` section of this document in
        PDF format.

        .. hint::

           If you want to use a special colour for the *contents* of the
           cells of a given column use ``>{\noindent\color{<color>}}``,
           possibly in addition to the above.

      - Multi-row merged cells, whether single column or multi-column
        currently ignore any set column, row, or cell colour.

      - It is possible for a simple cell to set a custom colour via the
        :dudir:`raw` directive and the ``\cellcolor`` LaTeX command used
        anywhere in the cell contents.  This currently is without effect
        in a merged cell, whatever its kind.

   .. hint::

      In a document not using ``'booktabs'`` globally, it is possible to style
      an individual table via the ``booktabs`` class, but it will be necessary
      to add ``r'\usepackage{booktabs}'`` to the LaTeX preamble.

      On the other hand one can use ``colorrows`` class for individual tables
      with no extra package (as Sphinx since 5.3.0 always loads colortbl_).

   .. _booktabs: https://ctan.org/pkg/booktabs
   .. _colortbl: https://ctan.org/pkg/colortbl
   .. _xcolor: https://ctan.org/pkg/xcolor

.. confval:: latex_use_xindy

   If ``True``, the PDF build from the LaTeX files created by Sphinx
   will use :program:`xindy` (doc__) rather than :program:`makeindex`
   for preparing the index of general terms (from :rst:dir:`index`
   usage).  This means that words with UTF-8 characters will get
   ordered correctly for the :confval:`language`.

   __ https://xindy.sourceforge.net/

   - This option is ignored if :confval:`latex_engine` is ``'platex'``
     (Japanese documents; :program:`mendex` replaces :program:`makeindex`
     then).

   - The default is ``True`` for ``'xelatex'`` or ``'lualatex'`` as
     :program:`makeindex`, if any indexed term starts with a non-ascii
     character, creates ``.ind`` files containing invalid bytes for
     UTF-8 encoding. With ``'lualatex'`` this then breaks the PDF
     build.

   - The default is ``False`` for ``'pdflatex'`` but ``True`` is
     recommended for non-English documents as soon as some indexed
     terms use non-ascii characters from the language script.

   Sphinx adds to :program:`xindy` base distribution some dedicated support
   for using ``'pdflatex'`` engine with Cyrillic scripts.  And whether with
   ``'pdflatex'`` or Unicode engines, Cyrillic documents handle correctly the
   indexing of Latin names, even with diacritics.

   .. versionadded:: 1.8

.. confval:: latex_elements

   .. versionadded:: 0.5

   Its :ref:`documentation <latex_elements_confval>` has moved to :doc:`/latex`.

.. confval:: latex_docclass

   A dictionary mapping ``'howto'`` and ``'manual'`` to names of real document
   classes that will be used as the base for the two Sphinx classes.  Default
   is to use ``'article'`` for ``'howto'`` and ``'report'`` for ``'manual'``.

   .. versionadded:: 1.0

   .. versionchanged:: 1.5

      In Japanese docs (:confval:`language` is ``'ja'``), by default
      ``'jreport'`` is used for ``'howto'`` and ``'jsbook'`` for ``'manual'``.

.. confval:: latex_additional_files

   A list of file names, relative to the configuration directory, to copy to
   the build directory when building LaTeX output.  This is useful to copy
   files that Sphinx doesn't copy automatically, e.g. if they are referenced in
   custom LaTeX added in ``latex_elements``.  Image files that are referenced
   in source files (e.g. via ``.. image::``) are copied automatically.

   You have to make sure yourself that the filenames don't collide with those
   of any automatically copied files.

   .. attention::

      Filenames with extension ``.tex`` will automatically be handed over to
      the PDF build process triggered by :option:`sphinx-build -M`
      ``latexpdf`` or by :program:`make latexpdf`.  If the file was added only
      to be ``\input{}`` from a modified preamble, you must add a further
      suffix such as ``.txt`` to the filename and adjust accordingly the
      ``\input{}`` command added to the LaTeX document preamble.

   .. versionadded:: 0.6

   .. versionchanged:: 1.2
      This overrides the files which is provided from Sphinx such as
      ``sphinx.sty``.

.. confval:: latex_theme

   The "theme" that the LaTeX output should use.  It is a collection of settings
   for LaTeX output (ex. document class, top level sectioning unit and so on).

   As a built-in LaTeX themes, ``manual`` and ``howto`` are bundled.

   ``manual``
     A LaTeX theme for writing a manual.  It imports the ``report`` document
     class (Japanese documents use ``jsbook``).

   ``howto``
     A LaTeX theme for writing an article.  It imports the ``article`` document
     class (Japanese documents use ``jreport`` rather).  :confval:`latex_appendices`
     is available only for this theme.

   It defaults to ``'manual'``.

   .. versionadded:: 3.0

.. confval:: latex_theme_options

   A dictionary of options that influence the look and feel of the selected
   theme.

   .. versionadded:: 3.1

.. confval:: latex_theme_path

   A list of paths that contain custom LaTeX themes as subdirectories.  Relative
   paths are taken as relative to the configuration directory.

   .. versionadded:: 3.0


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

.. confval:: text_add_secnumbers

   A boolean that decides whether section numbers are included in text output.
   Default is ``True``.

   .. versionadded:: 1.7

.. confval:: text_secnumber_suffix

   Suffix for section numbers in text output.  Default: ``". "``. Set to
   ``" "`` to suppress the final dot on section numbers.

   .. versionadded:: 1.7


.. _man-options:

Options for manual page output
------------------------------

These options influence manual page output.

.. confval:: man_pages

   This value determines how to group the document tree into manual pages.  It
   must be a list of tuples ``(startdocname, name, description, authors,
   section)``, where the items are:

   *startdocname*
     String that specifies the :term:`document name` of the manual page's master
     document. All documents referenced by the *startdoc* document in TOC trees
     will be included in the manual file.  (If you want to use the default
     root document for your manual pages build, use your :confval:`root_doc`
     here.)

   *name*
     Name of the manual page.  This should be a short string without spaces or
     special characters.  It is used to determine the file name as well as the
     name of the manual page (in the NAME section).

   *description*
     Description of the manual page.  This is used in the NAME section.
     Can be an empty string if you do not want to automatically generate
     the NAME section.

   *authors*
     A list of strings with authors, or a single string.  Can be an empty
     string or list if you do not want to automatically generate an AUTHORS
     section in the manual page.

   *section*
     The manual page section.  Used for the output file name as well as in the
     manual page header.

   .. versionadded:: 1.0

.. confval:: man_show_urls

   If true, add URL addresses after links.  Default is ``False``.

   .. versionadded:: 1.1

.. confval:: man_make_section_directory

   If true, make a section directory on build man page.  Default is True.

   .. versionadded:: 3.3
   .. versionchanged:: 4.0

      The default is changed to ``False`` from ``True``.

   .. versionchanged:: 4.0.2

      The default is changed to ``True`` from ``False`` again.

.. _texinfo-options:

Options for Texinfo output
--------------------------

These options influence Texinfo output.

.. confval:: texinfo_documents

   This value determines how to group the document tree into Texinfo source
   files.  It must be a list of tuples ``(startdocname, targetname, title,
   author, dir_entry, description, category, toctree_only)``, where the items
   are:

   *startdocname*
     String that specifies the :term:`document name` of the the Texinfo file's
     master document.  All documents referenced by the *startdoc* document in
     TOC trees will be included in the Texinfo file.  (If you want to use the
     default master document for your Texinfo build, provide your
     :confval:`root_doc` here.)

   *targetname*
     File name (no extension) of the Texinfo file in the output directory.

   *title*
     Texinfo document title.  Can be empty to use the title of the *startdoc*
     document.  Inserted as Texinfo markup, so special characters like ``@`` and
     ``{}`` will need to be escaped to be inserted literally.

   *author*
     Author for the Texinfo document.  Inserted as Texinfo markup.  Use ``@*``
     to separate multiple authors, as in: ``'John@*Sarah'``.

   *dir_entry*
     The name that will appear in the top-level ``DIR`` menu file.

   *description*
     Descriptive text to appear in the top-level ``DIR`` menu file.

   *category*
     Specifies the section which this entry will appear in the top-level
     ``DIR`` menu file.

   *toctree_only*
     Must be ``True`` or ``False``.  If true, the *startdoc* document itself is
     not included in the output, only the documents referenced by it via TOC
     trees.  With this option, you can put extra stuff in the master document
     that shows up in the HTML, but not the Texinfo output.

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

.. confval:: texinfo_cross_references

  If false, do not generate inline references in a document.  That makes
  an info file more readable with stand-alone reader (``info``).
  Default is ``True``.

  .. versionadded:: 4.4

.. _qthelp-options:

Options for QtHelp output
--------------------------

These options influence qthelp output.  As this builder derives from the HTML
builder, the HTML options also apply where appropriate.

.. confval:: qthelp_basename

   The basename for the qthelp file.  It defaults to the :confval:`project`
   name.

.. confval:: qthelp_namespace

   The namespace for the qthelp file.  It defaults to
   ``org.sphinx.<project_name>.<project_version>``.

.. confval:: qthelp_theme

   The HTML theme for the qthelp output.
   This defaults to ``'nonav'``.

.. confval:: qthelp_theme_options

   A dictionary of options that influence the look and feel of the selected
   theme.  These are theme-specific.  For the options understood by the builtin
   themes, see :ref:`this section <builtin-themes>`.


Options for the linkcheck builder
---------------------------------

.. confval:: linkcheck_ignore

   A list of regular expressions that match URIs that should not be checked
   when doing a ``linkcheck`` build.  Example::

      linkcheck_ignore = [r'https://localhost:\d+/']

   .. versionadded:: 1.1

.. confval:: linkcheck_allowed_redirects

   A dictionary that maps a pattern of the source URI to a pattern of the canonical
   URI. The linkcheck builder treats the redirected link as "working" when:

   - the link in the document matches the source URI pattern, and
   - the redirect location matches the canonical URI pattern.

   Example:

   .. code-block:: python

      linkcheck_allowed_redirects = {
          # All HTTP redirections from the source URI to the canonical URI will be treated as "working".
          r'https://sphinx-doc\.org/.*': r'https://sphinx-doc\.org/en/master/.*'
      }

   If set, linkcheck builder will emit a warning when disallowed redirection
   found.  It's useful to detect unexpected redirects under :option:`the
   warn-is-error mode <sphinx-build -W>`.

   .. versionadded:: 4.1

.. confval:: linkcheck_request_headers

   A dictionary that maps baseurls to HTTP request headers.

   The key is a URL base string like ``"https://www.sphinx-doc.org/"``.  To specify
   headers for other hosts, ``"*"`` can be used.  It matches all hosts only when
   the URL does not match other settings.

   The value is a dictionary that maps header name to its value.

   Example:

   .. code-block:: python

      linkcheck_request_headers = {
          "https://www.sphinx-doc.org/": {
              "Accept": "text/html",
              "Accept-Encoding": "utf-8",
          },
          "*": {
              "Accept": "text/html,application/xhtml+xml",
          }
      }

   .. versionadded:: 3.1

.. confval:: linkcheck_retries

   The number of times the linkcheck builder will attempt to check a URL before
   declaring it broken. Defaults to 1 attempt.

   .. versionadded:: 1.4

.. confval:: linkcheck_timeout

   The duration, in seconds, that the linkcheck builder will wait for a
   response after each hyperlink request.  Defaults to 30 seconds.

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

.. confval:: linkcheck_anchors_ignore

   A list of regular expressions that match anchors Sphinx should skip when
   checking the validity of anchors in links. This allows skipping anchors that
   a website's JavaScript adds to control dynamic pages or when triggering an
   internal REST request. Default is ``["^!"]``.

   .. tip::

      Use :confval:`linkcheck_anchors_ignore_for_url` to check a URL,
      but skip verifying that the anchors exist.

   .. note::

      If you want to ignore anchors of a specific page or of pages that match a
      specific pattern (but still check occurrences of the same page(s) that
      don't have anchors), use :confval:`linkcheck_ignore` instead, for example
      as follows::

         linkcheck_ignore = [
            'https://www.sphinx-doc.org/en/1.7/intro.html#',
         ]

   .. versionadded:: 1.5

.. confval:: linkcheck_anchors_ignore_for_url

   A list or tuple of regular expressions matching URLs
   for which Sphinx should not check the validity of anchors.
   This allows skipping anchor checks on a per-page basis
   while still checking the validity of the page itself.
   Default is an empty tuple ``()``.

   .. versionadded:: 7.1

.. confval:: linkcheck_auth

   Pass authentication information when doing a ``linkcheck`` build.

   A list of ``(regex_pattern, auth_info)`` tuples where the items are:

   *regex_pattern*
     A regular expression that matches a URI.
   *auth_info*
     Authentication information to use for that URI. The value can be anything
     that is understood by the ``requests`` library (see :ref:`requests
     Authentication <requests:authentication>` for details).

   The ``linkcheck`` builder will use the first matching ``auth_info`` value
   it can find in the :confval:`linkcheck_auth` list, so values earlier in the
   list have higher priority.

   Example::

      linkcheck_auth = [
        ('https://foo\.yourcompany\.com/.+', ('johndoe', 'secret')),
        ('https://.+\.yourcompany\.com/.+', HTTPDigestAuth(...)),
      ]

   .. versionadded:: 2.3

.. confval:: linkcheck_rate_limit_timeout

   The ``linkcheck`` builder may issue a large number of requests to the same
   site over a short period of time. This setting controls the builder behavior
   when servers indicate that requests are rate-limited.

   If a server indicates when to retry (using the `Retry-After`_ header),
   ``linkcheck`` always follows the server indication.

   Otherwise, ``linkcheck`` waits for a minute before to retry and keeps
   doubling the wait time between attempts until it succeeds or exceeds the
   ``linkcheck_rate_limit_timeout``. By default, the timeout is 300 seconds
   and custom timeouts should be given in seconds.

   .. _Retry-After: https://datatracker.ietf.org/doc/html/rfc7231#section-7.1.3

   .. versionadded:: 3.4

.. confval:: linkcheck_exclude_documents

   A list of regular expressions that match documents in which Sphinx should
   not check the validity of links. This can be used for permitting link decay
   in legacy or historical sections of the documentation.

   Example::

      # ignore all links in documents located in a subfolder named 'legacy'
      linkcheck_exclude_documents = [r'.*/legacy/.*']

   .. versionadded:: 4.4

.. confval:: linkcheck_allow_unauthorized

   When a webserver responds with an HTTP 401 (unauthorized) response, the
   current default behaviour of Sphinx is to treat the link as "working".  To
   change that behaviour, set this option to ``False``.

   The default value for this option will be changed in Sphinx 8.0; from that
   version onwards, HTTP 401 responses to checked hyperlinks will be treated
   as "broken" by default.

   .. versionadded:: 7.3

.. confval:: linkcheck_report_timeouts_as_broken

   When an HTTP response is not received from a webserver before the configured
   :confval:`linkcheck_timeout` expires,
   the current default behaviour of Sphinx is to treat the link as 'broken'.
   To report timeouts using a distinct report code of ``timeout``,
   set :confval:`linkcheck_report_timeouts_as_broken` to ``False``.

   From Sphinx 8.0 onwards, timeouts that occur while checking hyperlinks
   will be reported using the new 'timeout' status code.

   .. xref RemovedInSphinx80Warning

   .. versionadded:: 7.3


Options for the XML builder
---------------------------

.. confval:: xml_pretty

   If true, pretty-print the XML.  Default is ``True``.

   .. versionadded:: 1.2


.. rubric:: Footnotes

.. [1] A note on available globbing syntax: you can use the standard shell
       constructs ``*``, ``?``, ``[...]`` and ``[!...]`` with the feature that
       these all don't match slashes.  A double star ``**`` can be used to
       match any sequence of characters *including* slashes.


.. _c-config:

Options for the C domain
------------------------

.. confval:: c_id_attributes

   A list of strings that the parser additionally should accept as attributes.
   This can for example be used when attributes have been ``#define`` d for
   portability.

   .. versionadded:: 3.0

.. confval:: c_paren_attributes

   A list of strings that the parser additionally should accept as attributes
   with one argument.  That is, if ``my_align_as`` is in the list, then
   ``my_align_as(X)`` is parsed as an attribute for all strings ``X`` that have
   balanced braces (``()``, ``[]``, and ``{}``).  This can for example be used
   when attributes have been ``#define`` d for portability.

   .. versionadded:: 3.0

.. confval:: c_extra_keywords

  A list of identifiers to be recognized as keywords by the C parser.
  It defaults to ``['alignas', 'alignof', 'bool', 'complex', 'imaginary',
  'noreturn', 'static_assert', 'thread_local']``.

  .. versionadded:: 4.0.3

.. confval:: c_maximum_signature_line_length

   If a signature's length in characters exceeds the number set, each
   parameter will be displayed on an individual logical line. This is a
   domain-specific setting, overriding :confval:`maximum_signature_line_length`.

   .. versionadded:: 7.1

.. _cpp-config:

Options for the C++ domain
--------------------------

.. confval:: cpp_index_common_prefix

   A list of prefixes that will be ignored when sorting C++ objects in the
   global index.  For example ``['awesome_lib::']``.

   .. versionadded:: 1.5

.. confval:: cpp_id_attributes

   A list of strings that the parser additionally should accept as attributes.
   This can for example be used when attributes have been ``#define`` d for
   portability.

   .. versionadded:: 1.5

.. confval:: cpp_paren_attributes

   A list of strings that the parser additionally should accept as attributes
   with one argument.  That is, if ``my_align_as`` is in the list, then
   ``my_align_as(X)`` is parsed as an attribute for all strings ``X`` that have
   balanced braces (``()``, ``[]``, and ``{}``).  This can for example be used
   when attributes have been ``#define`` d for portability.

   .. versionadded:: 1.5

.. confval:: cpp_maximum_signature_line_length

   If a signature's length in characters exceeds the number set, each
   parameter will be displayed on an individual logical line. This is a
   domain-specific setting, overriding :confval:`maximum_signature_line_length`.

   .. versionadded:: 7.1

Options for the Python domain
-----------------------------

.. confval:: python_display_short_literal_types

   This value controls how :py:data:`~typing.Literal` types are displayed.
   The setting is a boolean, default ``False``.

   Examples
   ~~~~~~~~

   The examples below use the following :rst:dir:`py:function` directive:

   .. code:: reStructuredText

      .. py:function:: serve_food(item: Literal["egg", "spam", "lobster thermidor"]) -> None

   When ``False``, :py:data:`~typing.Literal` types display as per standard
   Python syntax, i.e.:

      .. code:: python

         serve_food(item: Literal["egg", "spam", "lobster thermidor"]) -> None

   When ``True``, :py:data:`~typing.Literal` types display with a short,
   :PEP:`604`-inspired syntax, i.e.:

      .. code:: python

         serve_food(item: "egg" | "spam" | "lobster thermidor") -> None

   .. versionadded:: 6.2

.. confval:: python_use_unqualified_type_names

   If true, suppress the module name of the python reference if it can be
   resolved.  The default is ``False``.

   .. versionadded:: 4.0

   .. note:: This configuration is still in experimental

.. confval:: python_maximum_signature_line_length

   If a signature's length in characters exceeds the number set,
   each argument or type parameter will be displayed on an individual logical line.
   This is a domain-specific setting,
   overriding :confval:`maximum_signature_line_length`.

   For the Python domain, the signature length depends on whether
   the type parameters or the list of arguments are being formatted.
   For the former, the signature length ignores the length of the arguments list;
   for the latter, the signature length ignores the length of
   the type parameters list.

   For instance, with ``python_maximum_signature_line_length = 20``,
   only the list of type parameters will be wrapped
   while the arguments list will be rendered on a single line

   .. code:: rst

      .. py:function:: add[T: VERY_LONG_SUPER_TYPE, U: VERY_LONG_SUPER_TYPE](a: T, b: U)

   .. versionadded:: 7.1

Options for the Javascript domain
---------------------------------

.. confval:: javascript_maximum_signature_line_length

   If a signature's length in characters exceeds the number set, each
   parameter will be displayed on an individual logical line. This is a
   domain-specific setting, overriding :confval:`maximum_signature_line_length`.

   .. versionadded:: 7.1

Example of configuration file
-----------------------------

.. literalinclude:: /_static/conf.py.txt
   :language: python
