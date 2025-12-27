.. _build-config:

=============
Configuration
=============

.. module:: conf
   :synopsis: Build configuration file.

.. role:: code-c(code)
   :language: C
.. role:: code-cpp(code)
   :language: C++
.. role:: code-js(code)
   :language: JavaScript
.. role:: code-py(code)
   :language: Python
.. role:: code-rst(code)
   :language: reStructuredText
.. role:: code-tex(code)
   :language: LaTeX

The :term:`configuration directory` must contain a file named :file:`conf.py`.
This file (containing Python code) is called the "build configuration file"
and contains (almost) all configuration needed to customise Sphinx input
and output behaviour.

An optional file `docutils.conf`_ can be added to the configuration
directory to adjust `Docutils`_ configuration if not otherwise overridden or
set by Sphinx.

.. _`docutils`: https://docutils.sourceforge.io/
.. _`docutils.conf`: https://docutils.sourceforge.io/docs/user/config.html

Important points to note:

* If not otherwise documented, values must be strings,
  and their default is the empty string.

* The term "fully-qualified name" (FQN) refers to a string that names an importable
  Python object inside a module; for example, the fully-qualified name
  :code-py:`"sphinx.builders.Builder"` means the :code-py:`Builder` class in the
  :code-py:`sphinx.builders` module.

* Document names use ``/`` as the path separator
  and do not contain the file name extension.

.. _glob-style patterns:

* Where glob-style patterns are permitted,
  you can use the standard shell constructs
  (``*``, ``?``, ``[...]``, and ``[!...]``)
  with the feature that none of these will match slashes (``/``).
  A double star ``**`` can be used to match any sequence of characters
  *including* slashes.

.. tip::

   The configuration file is executed as Python code at build time
   (using :func:`importlib.import_module`, with the current directory set
   to the :term:`configuration directory`),
   and therefore can execute arbitrarily complex code.

   Sphinx then reads simple names from the file's namespace as its configuration.
   In general, configuration values should be simple strings, numbers, or
   lists or dictionaries of simple values.

   The contents of the config namespace are pickled (so that Sphinx can find out
   when configuration changes), so it may not contain unpickleable values --
   delete them from the namespace with ``del`` if appropriate.
   Modules are removed automatically, so deleting imported modules is not needed.


.. _conf-tags:

Project tags
============

There is a special object named ``tags`` available in the config file,
which exposes the :ref:`project tags <tags>`.
Tags are defined either via the
:option:`--tag <sphinx-build --tag>` command-line option
or :code-py:`tags.add('tag')`.
Note that the builder's name and format tags are not available in :file:`conf.py`.

It can be used to query and change the defined tags as follows:

* To query whether a tag is set, use :code-py:`'tag' in tags`.
* To add a tag, use :code-py:`tags.add('tag')`.
* To remove a tag, use :code-py:`tags.remove('tag')`.

Project information
===================

.. confval:: project
   :type: :code-py:`str`
   :default: :code-py:`'Project name not set'`

   The documented project's name.
   Example:

   .. code-block:: python

      project = 'Thermidor'

.. confval:: author
   :type: :code-py:`str`
   :default: :code-py:`'Author name not set'`

   The project's author(s).
   Example:

   .. code-block:: python

      author = 'Joe Bloggs'

.. _config-copyright:

.. confval:: copyright
             project_copyright
   :type: :code-py:`str | Sequence[str]`
   :default: :code-py:`''`

   A copyright statement.
   Permitted styles are as follows, where 'YYYY' represents a four-digit year.

   * :code-py:`copyright = 'YYYY'`
   * :code-py:`copyright = 'YYYY, Author Name'`
   * :code-py:`copyright = 'YYYY Author Name'`
   * :code-py:`copyright = 'YYYY-YYYY, Author Name'`
   * :code-py:`copyright = 'YYYY-YYYY Author Name'`

   If the string :code-py:`'%Y'` appears in a copyright line,
   it will be replaced with the current four-digit year.
   For example:

   * :code-py:`copyright = '%Y'`
   * :code-py:`copyright = '%Y, Author Name'`
   * :code-py:`copyright = 'YYYY-%Y, Author Name'`

   .. versionadded:: 3.5
      The :code-py:`project_copyright` alias.

   .. versionchanged:: 7.1
      The value may now be a sequence of copyright statements in the above form,
      which will be displayed each to their own line.

   .. versionchanged:: 8.1
      Copyright statements support the :code-py:`'%Y'` placeholder.

.. confval:: version
   :type: :code-py:`str`
   :default: :code-py:`''`

   The major project version, used as the replacement for the :code-rst:`|version|`
   :ref:`default substitution <default-substitutions>`.

   This may be something like :code-py:`version = '4.2'`.
   The full project version is defined in :confval:`release`.

   If your project does not draw a meaningful distinction between
   between a 'full' and 'major' version,
   set both :code-py:`version` and :code-py:`release` to the same value.

.. confval:: release
   :type: :code-py:`str`
   :default: :code-py:`''`

   The full project version, used as the replacement for the :code-rst:`|release|`
   :ref:`default substitution <default-substitutions>`, and
   e.g. in the HTML templates.

   This may be something like :code-py:`release = '4.2.1b0'`.
   The major (short) project version is defined in :confval:`version`.

   If your project does not draw a meaningful distinction between
   between a 'full' and 'major' version,
   set both :code-py:`version` and :code-py:`release` to the same value.


General configuration
=====================

.. confval:: needs_sphinx
   :type: :code-py:`str`
   :default: :code-py:`''`

   Set a minimum supported version of Sphinx required to build the project.
   The format should be a ``'major.minor'`` version string like ``'1.1'``
   Sphinx will compare it with its version and refuse to build the project
   if the running version of Sphinx is too old.
   By default, there is no minimum version.

   .. versionadded:: 1.0

   .. versionchanged:: 1.4
      Allow a ``'major.minor.micro'`` version string.

.. confval:: extensions
   :type: :code-py:`list[str]`
   :default: :code-py:`[]`

   A list of strings that are module names of
   :doc:`Sphinx extensions <extensions/index>`.
   These can be extensions bundled with Sphinx (named ``sphinx.ext.*``)
   or custom first-party or third-party extensions.

   To use a third-party extension, you must ensure that it is installed
   and include it in the :code-py:`extensions` list, like so:

   .. code-block:: python

      extensions = [
          ...
          'numpydoc',
      ]

   There are two options for first-party extensions.
   The configuration file itself can be an extension;
   for that, you only need to provide a :func:`setup` function in it.
   Otherwise, you must ensure that your custom extension is importable,
   and located in a directory that is in the Python path.

   Ensure that absolute paths are used when modifying :data:`sys.path`.
   If your custom extensions live in a directory that is relative to the
   :term:`configuration directory`, use :meth:`pathlib.Path.resolve` like so:

   .. code-block:: python

      import sys
      from pathlib import Path

      sys.path.append(str(Path('sphinxext').resolve()))

      extensions = [
         ...
         'extname',
      ]

   The directory structure illustrated above would look like this:

   .. code-block:: none

      <project directory>/
      ├── conf.py
      └── sphinxext/
          └── extname.py


.. confval:: needs_extensions
   :type: :code-py:`dict[str, str]`
   :default: :code-py:`{}`

   If set, this value must be a dictionary specifying version requirements
   for extensions in :confval:`extensions`.
   The version strings should be in the ``'major.minor'`` form.
   Requirements do not have to be specified for all extensions,
   only for those you want to check.
   Example:

   .. code-block:: python

      needs_extensions = {
          'sphinxcontrib.something': '1.5',
      }

   This requires that the extension declares its version
   in the :code-py:`setup()` function. See :ref:`dev-extensions` for further details.

   .. versionadded:: 1.3

.. confval:: manpages_url
   :type: :code-py:`str`
   :default: :code-py:`''`

   A URL to cross-reference :rst:role:`manpage` roles.
   If this is defined to ``https://manpages.debian.org/{path}``,
   the :literal:`:manpage:`man(1)`` role will link to
   <https://manpages.debian.org/man(1)>.
   The patterns available are:

   ``page``
      The manual page (``man``)
   ``section``
      The manual section (``1``)
   ``path``
      The original manual page and section specified (``man(1)``)

   This also supports manpages specified as ``man.1``.

   .. code-block:: python

      # To use manpages.debian.org:
      manpages_url = 'https://manpages.debian.org/{path}'
      # To use man7.org:
      manpages_url = 'https://man7.org/linux/man-pages/man{section}/{page}.{section}.html'
      # To use linux.die.net:
      manpages_url = 'https://linux.die.net/man/{section}/{page}'
      # To use helpmanual.io:
      manpages_url = 'https://helpmanual.io/man{section}/{page}'

   .. versionadded:: 1.7

.. confval:: today
             today_fmt

   These values determine how to format the current date,
   used as the replacement for the :code-rst:`|today|`
   :ref:`default substitution <default-substitutions>`.

   * If you set :confval:`today` to a non-empty value, it is used.
   * Otherwise, the current time is formatted using :func:`time.strftime` and
     the format given in :confval:`today_fmt`.

   The default for :confval:`today` is :code-py:`''`,
   and the default for :confval:`today_fmt` is :code-py:`'%b %d, %Y'`
   (or, if translation is enabled with :confval:`language`,
   an equivalent format for the selected locale).


Options for figure numbering
----------------------------

.. confval:: numfig
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If :code-py:`True`, figures, tables and code-blocks are automatically numbered
   if they have a caption.
   The :rst:role:`numref` role is enabled.
   Obeyed so far only by HTML and LaTeX builders.

   .. note::

      The LaTeX builder always assigns numbers whether this option is enabled
      or not.

   .. versionadded:: 1.3

.. confval:: numfig_format
   :type: :code-py:`dict[str, str]`
   :default: :code-py:`{}`

   A dictionary mapping :code-py:`'figure'`, :code-py:`'table'`,
   :code-py:`'code-block'` and :code-py:`'section'` to strings
   that are used for format of figure numbers.
   The marker ``%s`` will be replaced with the figure number.

   The defaults are:

   .. code-block:: python

      numfig_format = {
          'code-block': 'Listing %s',
          'figure': 'Fig. %s',
          'section': 'Section',
          'table': 'Table %s',
      }

   .. versionadded:: 1.3

.. confval:: numfig_secnum_depth
   :type: :code-py:`int`
   :default: :code-py:`1`

   * If set to :code-py:`0`, figures, tables, and code-blocks
     are continuously numbered starting at ``1``.
   * If :code-py:`1`, the numbering will be ``x.1``, ``x.2``, ...
     with ``x`` representing the section number.
     (If there is no top-level section, the prefix will not be added ).
     This naturally applies only if section numbering has been activated via
     the ``:numbered:`` option of the :rst:dir:`toctree` directive.
   * If :code-py:`2`, the numbering will be ``x.y.1``, ``x.y.2``, ...
     with ``x`` representing the section number and ``y`` the sub-section number.
     If located directly under a section, there will be no ``y.`` prefix,
     and if there is no top-level section, the prefix will not be added.
   * Any other positive integer can be used, following the rules above.

   .. versionadded:: 1.3

   .. versionchanged:: 1.7
      The LaTeX builder obeys this setting
      if :confval:`numfig` is set to :code-py:`True`.


Options for highlighting
------------------------

.. confval:: highlight_language
   :type: :code-py:`str`
   :default: :code-py:`'default'`

   The default language to highlight source code in.
   The default is :code-py:`'default'`,
   which suppresses warnings if highlighting as Python code fails.

   The value should be a valid Pygments lexer name, see
   :ref:`code-examples` for more details.

   .. versionadded:: 0.5

   .. versionchanged:: 1.4
      The default is now :code-py:`'default'`.

.. confval:: highlight_options
   :type: :code-py:`dict[str, dict[str, Any]]`
   :default: :code-py:`{}`

   A dictionary that maps Pygments lexer names to their options.
   These are lexer-specific; for the options understood by each,
   see the `Pygments documentation <https://pygments.org/docs/lexers>`_.

   Example:

   .. code-block:: python

     highlight_options = {
       'default': {'stripall': True},
       'php': {'startinline': True},
     }

   .. versionadded:: 1.3
   .. versionchanged:: 3.5

      Allow configuring highlight options for multiple lexers.

.. confval:: pygments_style
   :type: :code-py:`str`
   :default: :code-py:`'sphinx'`

   The style name to use for Pygments highlighting of source code.
   If not set, either the theme's default style
   or :code-py:`'sphinx'` is selected for HTML output.

   .. versionchanged:: 0.3
      If the value is a fully-qualified name of a custom Pygments style class,
      this is then used as custom style.


Options for HTTP requests
-------------------------

.. confval:: tls_verify
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If True, Sphinx verifies server certificates.

   .. versionadded:: 1.5

.. confval:: tls_cacerts
   :type: :code-py:`str | dict[str, str]`
   :default: :code-py:`''`

   A path to a certification file of CA or
   a path to directory which contains the certificates.
   This also allows a dictionary mapping
   hostnames to the certificate file path.
   The certificates are used to verify server certifications.

   .. versionadded:: 1.5

   .. tip::

      Sphinx uses requests_ as a HTTP library internally.
      If :confval:`!tls_cacerts` is not set,
      Sphinx falls back to requests' default behaviour.
      See :ref:`requests:verification` for further details.

      .. _requests: https://requests.readthedocs.io/

.. confval:: user_agent
   :type: :code-py:`str`
   :default: :code-py:`'Mozilla/5.0 (X11; Linux x86_64; rv:100.0) Gecko/20100101 \
                        Firefox/100.0 Sphinx/X.Y.Z'`

   Set the User-Agent used by Sphinx for HTTP requests.

   .. versionadded:: 2.3


.. _intl-options:

Options for internationalisation
--------------------------------

These options influence Sphinx's *Native Language Support*.
See the documentation on :ref:`intl` for details.

.. confval:: language
   :type: :code-py:`str`
   :default: :code-py:`'en'`

   The code for the language the documents are written in.
   Any text automatically generated by Sphinx will be in that language.
   Also, Sphinx will try to substitute individual paragraphs
   from your documents with the translation sets obtained
   from :confval:`locale_dirs`.
   Sphinx will search language-specific figures named by
   :confval:`figure_language_filename`
   (e.g. the German version of ``myfigure.png`` will be ``myfigure.de.png``
   by default setting)
   and substitute them for original figures.
   In the LaTeX builder, a suitable language will be selected
   as an option for the *Babel* package.

   .. versionadded:: 0.5

   .. versionchanged:: 1.4
      Support figure substitution

   .. versionchanged:: 5.0
      The default is now :code-py:`'en'` (previously :code-py:`None`).

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
   :type: :code-py:`list[str]`
   :default: :code-py:`['locales']`

   Directories in which to search for additional message catalogs
   (see :confval:`language`), relative to the source directory.
   The directories on this path are searched by the :mod:`gettext` module.

   Internal messages are fetched from a text domain of ``sphinx``;
   so if you add the directory :file:`./locales` to this setting,
   the message catalogs
   (compiled from ``.po`` format using :program:`msgfmt`)
   must be in :file:`./locales/{language}/LC_MESSAGES/sphinx.mo`.
   The text domain of individual documents
   depends on :confval:`gettext_compact`.

   .. note::
      The :option:`-v option to sphinx-build <sphinx-build -v>`
      is useful to check the :confval:`!locale_dirs` setting is working as expected.
      If the message catalog directory not found, debug messages are emitted.

   .. versionadded:: 0.5

   .. versionchanged:: 1.5
      Use ``locales`` directory as a default value

.. confval:: gettext_allow_fuzzy_translations
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If True, "fuzzy" messages in the message catalogs are used for translation.

   .. versionadded:: 4.3

.. confval:: gettext_compact
   :type: :code-py:`bool | str`
   :default: :code-py:`True`

   * If :code-py:`True`, a document's text domain is
     its docname if it is a top-level project file
     and its very base directory otherwise.
   * If :code-py:`False`, a document's text domain is
     the docname, in full.
   * If set to a string, every document's text domain is
     set to this string, making all documents use single text domain.

   With :code-py:`gettext_compact = True`, the document
   :file:`markup/code.rst` ends up in the ``markup`` text domain.
   With this option set to :code-py:`False`, it is ``markup/code``.
   With this option set to :code-py:`'sample'`, it is ``sample``.

   .. versionadded:: 1.1

   .. versionchanged:: 3.3
      Allow string values.

.. confval:: gettext_uuid
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If :code-py:`True`, Sphinx generates UUID information
   for version tracking in message catalogs.
   It is used to:

   * Add a UUID line for each *msgid* in ``.pot`` files.
   * Calculate similarity between new msgids and previously saved old msgids.
     (This calculation can take a long time.)

   .. tip::
      If you want to accelerate the calculation,
      you can use a third-party package (Levenshtein_) by running
      :command:`pip install levenshtein`.

      .. _Levenshtein: https://pypi.org/project/Levenshtein/

   .. versionadded:: 1.3

.. confval:: gettext_location
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If :code-py:`True`, Sphinx generates location information
   for messages in message catalogs.

   .. versionadded:: 1.3

.. confval:: gettext_auto_build
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If :code-py:`True`, Sphinx builds a ``.mo`` file
   for each translation catalog file.

   .. versionadded:: 1.3

.. confval:: gettext_additional_targets
   :type: :code-py:`set[str] | Sequence[str]`
   :default: :code-py:`[]`

   Enable ``gettext`` translation for certain element types.
   Example:

   .. code-block:: python

      gettext_additional_targets = {'literal-block', 'image'}

   The following element types are supported:

   * :code-py:`'index'` -- index terms
   * :code-py:`'literal-block'` -- literal blocks
     (``::`` annotation and ``code-block`` directive)
   * :code-py:`'doctest-block'` -- doctest block
   * :code-py:`'raw'` -- raw content
   * :code-py:`'image'` -- image/figure uri

   .. versionadded:: 1.3
   .. versionchanged:: 4.0
      The alt text for images is translated by default.
   .. versionchanged:: 7.4
      Permit and prefer a set type.

.. confval:: figure_language_filename
   :type: :code-py:`str`
   :default: :code-py:`'{root}.{language}{ext}'`

   The filename format for language-specific figures.
   The available format tokens are:

   * ``{root}``: the filename, including any path component,
     without the file extension.
     For example: ``images/filename``.
   * ``{path}``: the directory path component of the filename,
     with a trailing slash if non-empty.
     For example: ``images/``.
   * ``{basename}``: the filename without the directory path
     or file extension components.
     For example: ``filename``.
   * ``{ext}``: the file extension.
     For example: ``.png``.
   * ``{language}``: the translation language.
     For example: ``en``.
   * ``{docpath}``: the directory path component for the current document,
     with a trailing slash if non-empty.
     For example: ``dirname/``.

   By default, an image directive :code-rst:`.. image:: images/filename.png`,
   using an image at :file:`images/filename.png`,
   will use the language-specific figure filename
   :file:`images/filename.en.png`.

   If :confval:`!figure_language_filename` is set as below,
   the language-specific figure filename will be
   :file:`images/en/filename.png` instead.

   .. code-block:: python

      figure_language_filename = '{path}{language}/{basename}{ext}'

   .. versionadded:: 1.4

   .. versionchanged:: 1.5
      Added ``{path}`` and ``{basename}`` tokens.

   .. versionchanged:: 3.2
      Added ``{docpath}`` token.

.. confval:: translation_progress_classes
   :type: :code-py:`bool | 'translated' | 'untranslated'`
   :default: :code-py:`False`

   Control which, if any, classes are added to indicate translation progress.
   This setting would likely only be used by translators of documentation,
   in order to quickly indicate translated and untranslated content.

   :code-py:`True`
      Add ``translated`` and ``untranslated`` classes
      to all nodes with translatable content.
   :code-py:`'translated'`
      Only add the ``translated`` class.
   :code-py:`'untranslated'`
      Only add the ``untranslated`` class.
   :code-py:`False`
      Do not add any classes to indicate translation progress.

   .. versionadded:: 7.1


Options for markup
------------------

.. confval:: default_role
   :type: :code-py:`str`
   :default: :code-py:`None`

   .. index:: default; role

   The name of a reStructuredText role (builtin or Sphinx extension)
   to use as the default role, that is, for text marked up ```like this```.
   This can be set to :code-py:`'py:obj'` to make ```filter```
   a cross-reference to the Python function "filter".

   The default role can always be set within individual documents using
   the standard reStructuredText :dudir:`default-role` directive.

   .. versionadded:: 0.4

.. confval:: keep_warnings
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Keep warnings as "system message" paragraphs in the rendered documents.
   Warnings are always written to the standard error stream
   when :program:`sphinx-build` is run, regardless of this setting.

   .. versionadded:: 0.5

.. confval:: option_emphasise_placeholders
   :type: :code-py:`bool`
   :default: :code-py:`False`

   When enabled, emphasise placeholders in :rst:dir:`option` directives.
   To display literal braces, escape with a backslash (``\{``).
   For example, ``option_emphasise_placeholders=True``
   and ``.. option:: -foption={TYPE}`` would render with ``TYPE`` emphasised.

   .. versionadded:: 5.1

.. confval:: primary_domain
   :type: :code-py:`str`
   :default: :code-py:`'py'`

   .. index:: pair: default; domain

   The name of the default :doc:`domain </usage/domains/index>`.
   Can also be :code-py:`None` to disable a default domain.
   The default is :code-py:`'py'`, for the Python domain.

   Those objects in other domain
   (whether the domain name is given explicitly,
   or selected by a :rst:dir:`default-domain` directive)
   will have the domain name explicitly prepended when named
   (e.g., when the default domain is C,
   Python functions will be named "Python function", not just "function").
   Example:

   .. code-block:: python

      primary_domain = 'cpp'

   .. versionadded:: 1.0

.. confval:: rst_epilog
   :type: :code-py:`str`
   :default: :code-py:`''`

   .. index:: pair: global; substitutions

   A string of reStructuredText that will be included
   at the end of every source file that is read.
   This is a possible place to add substitutions that
   should be available in every file (another being :confval:`rst_prolog`).
   Example:

   .. code-block:: python

      rst_epilog = """
      .. |psf| replace:: Python Software Foundation
      """

   .. versionadded:: 0.6

.. confval:: rst_prolog
   :type: :code-py:`str`
   :default: :code-py:`''`

   .. index:: pair: global; substitutions

   A string of reStructuredText that will be included
   at the beginning of every source file that is read.
   This is a possible place to add substitutions that
   should be available in every file (another being :confval:`rst_epilog`).
   Example:

   .. code-block:: python

      rst_prolog = """
      .. |psf| replace:: Python Software Foundation
      """

   .. versionadded:: 1.0

.. confval:: show_authors
   :type: :code-py:`bool`
   :default: :code-py:`False`

   A boolean that decides whether :rst:dir:`codeauthor` and
   :rst:dir:`sectionauthor` directives produce any output in the built files.

.. confval:: trim_footnote_reference_space
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Trim spaces before footnote references that are
   necessary for the  reStructuredText parser to recognise the footnote,
   but do not look too nice in the output.

   .. versionadded:: 0.6


.. _math-options:

Options for Maths
-----------------

These options control maths markup and notation.

.. confval:: math_eqref_format
   :type: :code-py:`str`
   :default: :code-py:`'({number})'`

   A string used for formatting the labels of references to equations.
   The ``{number}`` place-holder stands for the equation number.

   Example: ``'Eq.{number}'`` gets rendered as, for example, ``Eq.10``.

   .. versionadded:: 1.7

.. confval:: math_number_all
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Force all displayed equations to be numbered.
   Example:

   .. code-block:: python

      math_number_all = True

   .. versionadded:: 1.4

.. confval:: math_numfig
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If :code-py:`True`, displayed math equations are numbered across pages
   when :confval:`numfig` is enabled.
   The :confval:`numfig_secnum_depth` setting is respected.
   The :rst:role:`eq`, not :rst:role:`numref`, role
   must be used to reference equation numbers.

   .. versionadded:: 1.7

.. confval:: math_numsep
   :type: :code-py:`str`
   :default: :code-py:`'.'`

   A string that defines the separator between section numbers
   and the equation number when :confval:`numfig` is enabled and
   :confval:`numfig_secnum_depth` is positive.

   Example: :code-py:`'-'` gets rendered as ``1.2-3``.

   .. versionadded:: 7.4


Options for the nitpicky mode
-----------------------------

.. confval:: nitpicky
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Enables nitpicky mode if :code-py:`True`.
   In nitpicky mode, Sphinx will warn about *all* references
   where the target cannot be found.
   This is recommended for new projects as it ensures that all references
   are to valid targets.

   You can activate this mode temporarily using
   the :option:`--nitpicky <sphinx-build --nitpicky>` command-line option.
   See :confval:`nitpick_ignore` for a way to mark missing references
   as "known missing".

   .. code-block:: python

      nitpicky = True

   .. versionadded:: 1.0

.. confval:: nitpick_ignore
   :type: :code-py:`set[tuple[str, str]] | Sequence[tuple[str, str]]`
   :default: :code-py:`()`

   A set or list of :code-py:`(warning_type, target)` tuples
   that should be ignored when generating warnings
   in :confval:`"nitpicky mode" <nitpicky>`.
   Note that ``warning_type`` should include the domain name if present.
   Example:

   .. code-block:: python

      nitpick_ignore = {
          ('py:func', 'int'),
          ('envvar', 'LD_LIBRARY_PATH'),
      }

   .. versionadded:: 1.1
   .. versionchanged:: 6.2
      Changed allowable container types to a set, list, or tuple

.. confval:: nitpick_ignore_regex
   :type: :code-py:`set[tuple[str, str]] | Sequence[tuple[str, str]]`
   :default: :code-py:`()`

   An extended version of :confval:`nitpick_ignore`,
   which instead interprets the ``warning_type`` and ``target`` strings
   as regular expressions.
   Note that the regular expression must match the whole string
   (as if the ``^`` and ``$`` markers were inserted).

   For example, ``(r'py:.*', r'foo.*bar\.B.*')`` will ignore nitpicky warnings
   for all python entities that start with ``'foo'``
   and have ``'bar.B'`` in them,
   such as  :code-py:`('py:const', 'foo_package.bar.BAZ_VALUE')`
   or :code-py:`('py:class', 'food.bar.Barman')`.

   .. versionadded:: 4.1
   .. versionchanged:: 6.2
      Changed allowable container types to a set, list, or tuple


Options for object signatures
-----------------------------

.. confval:: add_function_parentheses
   :type: :code-py:`bool`
   :default: :code-py:`True`

   A boolean that decides whether parentheses are appended to function and
   method role text (e.g. the content of ``:func:`input```) to signify that the
   name is callable.

.. confval:: maximum_signature_line_length
   :type: :code-py:`int | None`
   :default: :code-py:`None`

   If a signature's length in characters exceeds the number set,
   each parameter within the signature will be displayed on
   an individual logical line.

   When :code-py:`None`, there is no maximum length and the entire
   signature will be displayed on a single logical line.

   A 'logical line' is similar to a hard line break---builders or themes
   may choose to 'soft wrap' a single logical line,
   and this setting does not affect that behaviour.

   Domains may provide options to suppress any hard wrapping
   on an individual object directive,
   such as seen in the C, C++, and Python domains
   (e.g. :rst:dir:`py:function:single-line-parameter-list`).

   .. versionadded:: 7.1

.. confval:: strip_signature_backslash
   :type: :code-py:`bool`
   :default: :code-py:`False`

   When backslash stripping is enabled then every occurrence of ``\\`` in a
   domain directive will be changed to ``\``, even within string literals.
   This was the behaviour before version 3.0, and setting this variable to
   :code-py:`True` will reinstate that behaviour.

   .. versionadded:: 3.0

.. confval:: toc_object_entries
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Create table of contents entries for domain objects
   (e.g. functions, classes, attributes, etc.).

   .. versionadded:: 5.2

.. confval:: toc_object_entries_show_parents
   :type: :code-py:`'domain' | 'hide' | 'all'`
   :default: :code-py:`'domain'`

   A string that determines how domain objects
   (functions, classes, attributes, etc.)
   are displayed in their table of contents entry.

   Use :code-py:`'domain'` to allow the domain to determine
   the appropriate number of parents to show.
   For example, the Python domain would show :code-py:`Class.method()`
   and :code-py:`function()`,
   leaving out the :code-py:`module.` level of parents.

   Use :code-py:`'hide'` to only show the name of the element
   without any parents (i.e. :code-py:`method()`).

   Use :code-py:`'all'` to show the fully-qualified name for the object
   (i.e.  :code-py:`module.Class.method()`), displaying all parents.

   .. versionadded:: 5.2


Options for source files
------------------------

.. confval:: exclude_patterns
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list of `glob-style patterns`_ that should be excluded when looking for
   source files.
   They are matched against the source file names
   relative to the source directory,
   using slashes as directory separators on all platforms.
   :confval:`exclude_patterns` has priority over :confval:`include_patterns`.

   Example patterns:

   * :code-py:`'library/xml.rst'` -- ignores the ``library/xml.rst`` file
   * :code-py:`'library/xml'` -- ignores the ``library/xml`` directory
   * :code-py:`'library/xml*'` -- ignores all files and directories starting with
     :code-py:`library/xml`
   * :code-py:`'**/.git'` -- ignores all ``.git`` directories
   * :code-py:`'Thumbs.db'` -- ignores all ``Thumbs.db`` files

   :confval:`exclude_patterns` is also consulted when looking for static files
   in :confval:`html_static_path` and :confval:`html_extra_path`.

   .. versionadded:: 1.0

.. confval:: include_patterns
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`('**',)`

   A list of `glob-style patterns`_ that are used to find source files.
   They are matched against the source file
   names relative to the source directory,
   using slashes as directory separators on all platforms.
   By default, all files are recursively included from the source directory.
   :confval:`exclude_patterns` has priority over :confval:`include_patterns`.

   Example patterns:

   * :code-py:`'**'` -- all files in the source directory and subdirectories,
     recursively
   * :code-py:`'library/xml'` -- just the ``library/xml`` directory
   * :code-py:`'library/xml*'` -- all files and directories starting with
     ``library/xml``
   * :code-py:`'**/doc'` -- all ``doc`` directories (this might be useful if
     documentation is co-located with source files)

   .. versionadded:: 5.1

.. confval:: master_doc
             root_doc
   :type: :code-py:`str`
   :default: :code-py:`'index'`

   Sphinx builds a tree of documents based on the :rst:dir:`toctree` directives
   contained within the source files.
   This sets the name of the document containing the master ``toctree`` directive,
   and hence the root of the entire tree.
   Example:

   .. code-block:: python

      master_doc = 'contents'

   .. versionchanged:: 2.0
      Default is :code-py:`'index'` (previously :code-py:`'contents'`).

   .. versionadded:: 4.0
      The :confval:`!root_doc` alias.

.. confval:: source_encoding
   :type: :code-py:`str`
   :default: :code-py:`'utf-8-sig'`

   The file encoding of all source files.
   The recommended encoding is ``'utf-8-sig'``.

   .. versionadded:: 0.5
   .. deprecated:: 9.0
      Support for source encodings other than UTF-8 is deprecated.
      Sphinx 11 will only support UTF-8 files.

.. confval:: source_suffix
   :type: :code-py:`dict[str, str] | Sequence[str] | str`
   :default: :code-py:`{'.rst': 'restructuredtext'}`

   A dictionary mapping the file extensions (suffixes)
   of source files to their file types.
   Sphinx considers all files files with suffixes in :code-py:`source_suffix`
   to be source files.
   Example:

   .. code-block:: python

      source_suffix = {
          '.rst': 'restructuredtext',
          '.txt': 'restructuredtext',
          '.md': 'markdown',
      }

   By default, Sphinx only supports the :code-py:`'restructuredtext'` file type.
   Further file types can be added with extensions that register different
   source file parsers, such as `MyST-Parser`_.
   Refer to the extension's documentation to see which file types it supports.

   .. _MyST-Parser: https://myst-parser.readthedocs.io/

   If the value is a string or sequence of strings,
   Sphinx will consider that they are all :code-py:`'restructuredtext'` files.

   .. note:: File extensions must begin with a dot (``'.'``).

   .. versionchanged:: 1.3
      Support a list of file extensions.

   .. versionchanged:: 1.8
      Change to a map of file extensions to file types.


Options for smart quotes
------------------------

.. confval:: smartquotes
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If :code-py:`True`, the `Smart Quotes transform`__
   will be used to convert quotation marks and dashes
   to typographically correct entities.

   __ https://docutils.sourceforge.io/docs/user/smartquotes.html

   .. versionadded:: 1.6.6
      Replaces the now-removed :confval:`!html_use_smartypants`.
      It applies by default to all builders except ``man`` and ``text``
      (see :confval:`smartquotes_excludes`.)

   .. note::

      A `docutils.conf`__ file located in the :term:`configuration directory`
      (or a global :file:`~/.docutils` file) is obeyed unconditionally if it
      *deactivates* smart quotes via the corresponding `Docutils option`__.
      But if it *activates* them, then :confval:`smartquotes` does prevail.

      __ https://docutils.sourceforge.io/docs/user/config.html
      __ https://docutils.sourceforge.io/docs/user/config.html#smart-quotes

.. confval:: smartquotes_action
   :type: :code-py:`str`
   :default: :code-py:`'qDe'`

   Customise the Smart Quotes transform.
   See below for the permitted codes.
   The default :code-py:`'qDe'` educates
   normal **q**\ uote characters ``"``, ``'``,
   em- and en-**D**\ ashes ``---``, ``--``,
   and **e**\ llipses ``...``..

   :code-py:`'q'`
      Convert quotation marks
   :code-py:`'b'`
      Convert backtick quotation marks
      (:literal:`\`\`double''` only)
   :code-py:`'B'`
      Convert backtick quotation marks
      (:literal:`\`\`double''` and :literal:`\`single'`)
   :code-py:`'d'`
      Convert dashes
      (convert ``--`` to em-dashes and ``---`` to en-dashes)
   :code-py:`'D'`
      Convert dashes (old school)
      (convert ``--`` to en-dashes and ``---`` to em-dashes)
   :code-py:`'i'`
      Convert dashes (inverted old school)
      (convert ``--`` to em-dashes and ``---`` to en-dashes)
   :code-py:`'e'`
      Convert ellipses ``...``
   :code-py:`'w'`
      Convert ``'&quot;'`` entities to ``'"'``

   .. versionadded:: 1.6.6

.. confval:: smartquotes_excludes
   :type: :code-py:`dict[str, list[str]]`
   :default: :code-py:`{'languages': ['ja'], 'builders': ['man', 'text']}`

   Control when the Smart Quotes transform is disabled.
   Permitted keys are :code-py:`'builders'` and :code-py:`'languages'`, and
   The values are lists of strings.

   Each entry gives a sufficient condition to ignore the
   :confval:`smartquotes` setting and deactivate the Smart Quotes transform.
   Example:

   .. code-block:: python

     smartquotes_excludes = {
         'languages': ['ja'],
         'builders': ['man', 'text'],
     }

   .. note::

      Currently, in case of invocation of :program:`make` with multiple
      targets, the first target name is the only one which is tested against
      the :code-py:`'builders'` entry and it decides for all.
      Also, a ``make text`` following ``make html`` needs to be issued
      in the form ``make text SPHINXOPTS="-E"`` to force re-parsing
      of source files, as the cached ones are already transformed.
      On the other hand the issue does not arise with
      direct usage of :program:`sphinx-build` as it caches
      (in its default usage) the parsed source files in per builder locations.

   .. hint::

      An alternative way to effectively deactivate (or customise) the
      smart quotes for a given builder, for example ``latex``,
      is to use ``make`` this way:

      .. code-block:: console

         make latex SPHINXOPTS="-D smartquotes_action="

      This can follow some ``make html`` with no problem, in contrast to the
      situation from the prior note.

   .. versionadded:: 1.6.6


Options for templating
----------------------

.. confval:: template_bridge
   :type: :code-py:`str`
   :default: :code-py:`''`

   A string with the fully-qualified name of a callable (or simply a class)
   that returns an instance of :class:`~sphinx.application.TemplateBridge`.
   This instance is then used to render HTML documents,
   and possibly the output of other builders (currently the changes builder).
   (Note that the template bridge must be made theme-aware
   if HTML themes are to be used.)
   Example:

   .. code-block:: python

      template_bridge = 'module.CustomTemplateBridge'

.. confval:: templates_path
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list of paths that contain extra templates
   (or templates that overwrite builtin/theme-specific templates).
   Relative paths are taken as relative to the :term:`configuration directory`.
   Example:

   .. code-block:: python

      templates_path = ['.templates']

   .. versionchanged:: 1.3
      As these files are not meant to be built,
      they are automatically excluded when discovering source files.


Options for warning control
---------------------------

.. confval:: show_warning_types
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Add the type of each warning as a suffix to the warning message.
   For example, ``WARNING: [...] [index]`` or ``WARNING: [...] [toc.circular]``.
   This setting can be useful for determining which warnings types to include
   in a :confval:`suppress_warnings` list.

   .. versionadded:: 7.3.0
   .. versionchanged:: 8.0.0
      The default is now :code-py:`True`.

.. confval:: suppress_warnings
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list of warning codes to suppress arbitrary warning messages.

   .. versionadded:: 1.4

   By default, Sphinx supports the following warning codes:

   * ``app.add_directive``
   * ``app.add_generic_role``
   * ``app.add_node``
   * ``app.add_role``
   * ``app.add_source_parser``
   * ``config.cache``
   * ``docutils``
   * ``download.not_readable``
   * ``duplicate_declaration.c``
   * ``duplicate_declaration.cpp``
   * ``epub.duplicated_toc_entry``
   * ``epub.unknown_project_files``
   * ``i18n.babel``
   * ``i18n.inconsistent_references``
   * ``i18n.not_readable``
   * ``i18n.not_writeable``
   * ``image.not_readable``
   * ``index``
   * ``misc.copy_overwrite``
   * ``misc.highlighting_failure``
   * ``ref.any``
   * ``ref.citation``
   * ``ref.doc``
   * ``ref.equation``
   * ``ref.footnote``
   * ``ref.keyword``
   * ``ref.numref``
   * ``ref.option``
   * ``ref.python``
   * ``ref.ref``
   * ``ref.term``
   * ``source_code_parser.c``
   * ``source_code_parser.cpp``
   * ``toc.circular``
   * ``toc.duplicate_entry``
   * ``toc.empty_glob``
   * ``toc.excluded``
   * ``toc.no_title``
   * ``toc.not_included``
   * ``toc.not_readable``
   * ``toc.secnum``

   Extensions can also define their own warning types.
   Those defined by the first-party ``sphinx.ext`` extensions are:

   * ``autodoc``
   * ``autodoc.import_object``
   * ``autodoc.mocked_object``
   * ``autosectionlabel.<document name>``
   * ``autosummary``
   * ``autosummary.import_cycle``
   * ``duration``
   * ``intersphinx.external``

   You can choose from these types.  You can also give only the first
   component to exclude all warnings attached to it.

   .. versionadded:: 1.4
      ``ref.citation``, ``ref.doc``, ``ref.keyword``,
      ``ref.numref``, ``ref.option``, ``ref.ref``, and ``ref.term``.

   .. versionadded:: 1.4.2
      ``app.add_directive``, ``app.add_generic_role``,
      ``app.add_node``, ``app.add_role``, and ``app.add_source_parser``.

   .. versionadded:: 1.5
      ``misc.highlighting_failure``.

   .. versionadded:: 1.5.1
      ``epub.unknown_project_files``.

   .. versionadded:: 1.5.2
      ``toc.secnum``.

   .. versionadded:: 1.6
      ``ref.footnote``, ``download.not_readable``, and ``image.not_readable``.

   .. versionadded:: 1.7
      ``ref.python``.

   .. versionadded:: 2.0
      ``autodoc.import_object``.

   .. versionadded:: 2.1
      ``autosectionlabel.<document name>``.

   .. versionadded:: 3.1
      ``toc.circular``.

   .. versionadded:: 3.3
      ``epub.duplicated_toc_entry``.

   .. versionadded:: 4.3
      ``toc.excluded`` and ``toc.not_readable``.

   .. versionadded:: 4.5
      ``i18n.inconsistent_references``.

   .. versionadded:: 7.1
      ``index``.

   .. versionadded:: 7.3
      ``config.cache``, ``intersphinx.external``, and ``toc.no_title``.

   .. versionadded:: 7.4
      ``docutils`` and ``autosummary.import_cycle``.

   .. versionadded:: 8.0
      ``misc.copy_overwrite``.

   .. versionadded:: 8.2
      ``autodoc.mocked_object``,
      ``duplicate_declaration.c``, ``duplicate_declaration.cpp``,
      ``i18n.babel``, ``i18n.not_readable``, ``i18n.not_writeable``,
      ``ref.any``,
      ``toc.duplicate_entry``, ``toc.empty_glob``, and ``toc.not_included``.

   .. versionadded:: 9.0
      ``duration``.


Builder options
===============


.. _html-options:

Options for HTML output
-----------------------

These options influence HTML output.
Various other builders are derived from the HTML output,
and also make use of these options.

.. confval:: html_theme
   :type: :code-py:`str`
   :default: :code-py:`'alabaster'`

   The theme for HTML output.
   See the :doc:`HTML theming section </usage/theming>`.

   .. versionadded:: 0.6
   .. versionchanged:: 1.3
      The default theme is now :code-py:`'alabaster'`.

.. confval:: html_theme_options
   :type: :code-py:`dict[str, Any]`
   :default: :code-py:`{}`

   A dictionary of options that influence the
   look and feel of the selected theme.
   These are theme-specific.
   The options understood by the :ref:`builtin themes
   <builtin-themes>` are described :ref:`here <builtin-themes>`.

   .. versionadded:: 0.6

.. confval:: html_theme_path
   :type: :code-py:`list[str]`
   :default: :code-py:`[]`

   A list of paths that contain custom themes,
   either as subdirectories or as zip files.
   Relative paths are taken as relative to the :term:`configuration directory`.

   .. versionadded:: 0.6

.. confval:: html_style
   :type: :code-py:`Sequence[str] | str`
   :default: :code-py:`()`

   Stylesheets to use for HTML pages.
   The stylesheet given by the selected theme is used by default
   A file of that name must exist either in Sphinx's :file:`static/` path
   or in one of the custom paths given in :confval:`html_static_path`.
   If you only want to add or override a few things from the theme,
   use CSS ``@import`` to import the theme's stylesheet.

   .. versionchanged:: 5.1
      The value can be a iterable of strings.

.. confval:: html_title
   :type: :code-py:`str`
   :default: :samp:`'{project} {release} documentation'`

   The "title" for HTML documentation generated with Sphinx's own templates.
   This is appended to the ``<title>`` tag of individual pages,
   and used in the navigation bar as the "topmost" element.

.. confval:: html_short_title
   :type: :code-py:`str`
   :default: The value of **html_title**

   A shorter "title" for HTML documentation.
   This is used for links in the header and in the HTML Help documentation.

   .. versionadded:: 0.4

.. confval:: html_baseurl
   :type: :code-py:`str`
   :default: :code-py:`''`

   The base URL which points to the root of the HTML documentation.
   It is used to indicate the location of document using
   :rfc:`the Canonical Link Relation <6596>`.

   .. versionadded:: 1.8

.. confval:: html_codeblock_linenos_style
   :type: :code-py:`'inline' | 'table'`
   :default: :code-py:`'inline'`

   The style of line numbers for code-blocks.

   :code-py:`'table'`
      Display line numbers using ``<table>`` tag
   :code-py:`'inline'`
      Display line numbers using ``<span>`` tag

   .. versionadded:: 3.2
   .. versionchanged:: 4.0
      It defaults to :code-py:`'inline'`.
   .. deprecated:: 4.0

.. confval:: html_context
   :type: :code-py:`dict[str, Any]`
   :default: :code-py:`{}`

   A dictionary of values to pass into
   the template engine's context for all pages.
   Single values can also be put in this dictionary using
   :program:`sphinx-build`'s :option:`--html-define
   <sphinx-build --html-define>` command-line option.

   .. versionadded:: 0.5

.. confval:: html_logo
   :type: :code-py:`str`
   :default: :code-py:`''`

   If given, this must be the name of an image file
   (path relative to the :term:`configuration directory`)
   that is the logo of the documentation,
   or a URL that points an image file for the logo.
   It is placed at the top of the sidebar;
   its width should therefore not exceed 200 pixels.

   .. versionadded:: 0.4.1
      The image file will be copied to the ``_static`` directory,
      but only if the file does not already exist there.
   .. versionchanged:: 4.0
      Also accepts a URL.

.. confval:: html_favicon
   :type: :code-py:`str`
   :default: :code-py:`''`

   If given, this must be the name of an image file
   (path relative to the :term:`configuration directory`)
   that is the favicon_ of the documentation,
   or a URL that points an image file for the favicon.
   Browsers use this as the icon for tabs, windows and bookmarks.
   It should be a 16-by-16 pixel icon in
   the PNG, SVG, GIF, or ICO file formats.

   .. _favicon: https://developer.mozilla.org/en-US/
                docs/Web/HTML/Attributes/rel#icon

   Example:

   .. code-block:: python

      html_favicon = 'static/favicon.png'

   .. versionadded:: 0.4
      The image file will be copied to the ``_static``,
      but only if the file does not already exist there.

   .. versionchanged:: 4.0
      Also accepts the URL for the favicon.

.. confval:: html_css_files
   :type: :code-py:`Sequence[str | tuple[str, dict[str, str]]]`
   :default: :code-py:`[]`

   A list of CSS files.
   The entry must be a *filename* string
   or a tuple containing the *filename* string and the *attributes* dictionary.
   The *filename* must be relative to the :confval:`html_static_path`,
   or a full URI with scheme like :code-py:`'https://example.org/style.css'`.
   The *attributes* dictionary is used for the ``<link>`` tag's attributes.

   Example:

   .. code-block:: python

      html_css_files = [
          'custom.css',
          'https://example.com/css/custom.css',
          ('print.css', {'media': 'print'}),
      ]

   The special attribute *priority* can be set as an integer
   to load the CSS file at an earlier or later step.
   For more information, refer to :meth:`.Sphinx.add_css_file`.

   .. versionadded:: 1.8
   .. versionchanged:: 3.5
      Support the *priority* attribute

.. confval:: html_js_files
   :type: :code-py:`Sequence[str | tuple[str, dict[str, str]]]`
   :default: :code-py:`[]`

   A list of JavaScript files.
   The entry must be a *filename* string
   or a tuple containing the *filename* string and the *attributes* dictionary.
   The *filename* must be relative to the :confval:`html_static_path`,
   or a full URI with scheme like :code-py:`'https://example.org/script.js'`.
   The *attributes* dictionary is used for the ``<script>`` tag's attributes.

   Example:

   .. code-block:: python

      html_js_files = [
          'script.js',
          'https://example.com/scripts/custom.js',
          ('custom.js', {'async': 'async'}),
      ]

   As a special attribute, *priority* can be set as an integer
   to load the JavaScript file at an earlier or later step.
   For more information, refer to :meth:`.Sphinx.add_js_file`.

   .. versionadded:: 1.8
   .. versionchanged:: 3.5
      Support the *priority* attribute

.. confval:: html_static_path
   :type: :code-py:`list[str]`
   :default: :code-py:`[]`

   A list of paths that contain custom static files
   (such as style sheets or script files).
   Relative paths are taken as relative to the :term:`configuration directory`.
   They are copied to the output's :file:`_static` directory
   after the theme's static files,
   so a file named :file:`default.css` will overwrite
   the theme's :file:`default.css`.

   As these files are not meant to be built,
   they are automatically excluded from source files.

   .. note::

      For security reasons, dotfiles under :confval:`!html_static_path`
      will not be copied.
      If you would like to copy them intentionally,
      explicitly add each file to this setting:

      .. code-block:: python

         html_static_path = ['_static', '_static/.htaccess']

      An alternative approach is to use :confval:`html_extra_path`,
      which allows copying dotfiles under the directories.

   .. versionchanged:: 0.4
      The paths in :confval:`html_static_path` can now contain subdirectories.

   .. versionchanged:: 1.0
      The entries in :confval:`html_static_path` can now be single files.

   .. versionchanged:: 1.8
      The files under :confval:`html_static_path` are excluded from source
      files.

.. confval:: html_extra_path
   :type: :code-py:`list[str]`
   :default: :code-py:`[]`

   A list of paths that contain extra files not directly related to
   the documentation,
   such as :file:`robots.txt` or :file:`.htaccess`.
   Relative paths are taken as relative to the :term:`configuration directory`.
   They are copied to the output directory.
   They will overwrite any existing file of the same name.

   As these files are not meant to be built,
   they are automatically excluded from source files.

   .. versionadded:: 1.2

   .. versionchanged:: 1.4
      The dotfiles in the extra directory will be copied
      to the output directory.
      And it refers :confval:`exclude_patterns` on copying extra
      files and directories, and ignores if path matches to patterns.

.. confval:: html_last_updated_fmt
   :type: :code-py:`str`
   :default: :code-py:`None`

   If set, a 'Last updated on:' timestamp is inserted into the page footer
   using the given :func:`~time.strftime` format.
   The empty string is equivalent to :code-py:`'%b %d, %Y'`
   (or a locale-dependent equivalent).

.. confval:: html_last_updated_use_utc
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Use GMT/UTC (+00:00) instead of the system's local time zone
   for the time supplied to :confval:`html_last_updated_fmt`.
   This is most useful when the format used includes the time.

.. confval:: html_permalinks
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Add link anchors for each heading and description environment.

   .. versionadded:: 3.5

.. confval:: html_permalinks_icon
   :type: :code-py:`str`
   :default: :code-py:`'¶'` (the paragraph sign)

   Text for link anchors for each heading and description environment.
   HTML entities and Unicode are allowed.

   .. versionadded:: 3.5

.. confval:: html_sidebars
   :type: :code-py:`dict[str, Sequence[str]]`
   :default: :code-py:`{}`

   A dictionary defining custom sidebar templates,
   mapping document names to template names.

   The keys can contain `glob-style patterns`_,
   in which case all matching documents will get the specified sidebars.
   (A warning is emitted when a more than one glob-style pattern
   matches for any document.)

   Each value must be a list of strings which specifies
   the complete list of sidebar templates to include.
   If all or some of the default sidebars are to be included,
   they must be put into this list as well.

   The default sidebars (for documents that don't match any pattern) are
   defined by theme itself.
   The builtin themes use these templates by default:
   :code-py:`'localtoc.html'`, :code-py:`'relations.html'`,
   :code-py:`'sourcelink.html'`, and :code-py:`'searchbox.html'`.

   The bundled first-party sidebar templates that can be rendered are:

   * **localtoc.html** -- a fine-grained table of contents of the current
     document
   * **globaltoc.html** -- a coarse-grained table of contents for the whole
     documentation set, collapsed
   * **relations.html** -- two links to the previous and next documents
   * **sourcelink.html** -- a link to the source of the current document,
     if enabled in :confval:`html_show_sourcelink`
   * **searchbox.html** -- the "quick search" box

   Example:

   .. code-block:: python

      html_sidebars = {
         '**': ['globaltoc.html', 'sourcelink.html', 'searchbox.html'],
         'using/windows': ['windows-sidebar.html', 'searchbox.html'],
      }

   This will render the custom template ``windows-sidebar.html`` and the quick
   search box within the sidebar of the given document, and render the default
   sidebars for all other pages (except that the local TOC is replaced by the
   global TOC).

   Note that this value only has no effect if
   the chosen theme does not possess a sidebar,
   like the builtin **scrolls** and **haiku** themes.

   .. versionadded:: 1.0
      The ability to use globbing keys and to specify multiple sidebars.

   .. deprecated:: 1.7
      A single string value for :confval:`!html_sidebars` will be removed.

   .. versionchanged:: 2.0
      :confval:`!html_sidebars` must be a list of strings,
      and no longer accepts a single string value.

.. confval:: html_additional_pages
   :type: :code-py:`dict[str, str]`
   :default: :code-py:`{}`

   Additional templates that should be rendered to HTML pages,
   must be a dictionary that maps document names to template names.

   Example:

   .. code-block:: python

      html_additional_pages = {
          'download': 'custom-download.html.jinja',
      }

   This will render the template :file:`custom-download.html.jinja`
   as the page :file:`download.html`.

.. confval:: html_domain_indices
   :type: :code-py:`bool | Sequence[str]`
   :default: :code-py:`True`

   If True, generate domain-specific indices in addition to the general index.
   For e.g. the Python domain, this is the global module index.

   This value can be a Boolean or a list of index names that should be generated.
   To find out the index name for a specific index, look at the HTML file name.
   For example, the Python module index has the name ``'py-modindex'``.

   Example:

   .. code-block:: python

      html_domain_indices = {
          'py-modindex',
      }

   .. versionadded:: 1.0
   .. versionchanged:: 7.4
      Permit and prefer a set type.

.. confval:: html_use_index
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Controls if an index is added to the HTML documents.

   .. versionadded:: 0.4

.. confval:: html_split_index
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Generates two versions of the index:
   once as a single page with all the entries,
   and once as one page per starting letter.

   .. versionadded:: 0.4

.. confval:: html_copy_source
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If True, the  reStructuredText sources are included in the HTML build as
   :file:`_sources/{docname}`.

.. confval:: html_show_sourcelink
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If True (and :confval:`html_copy_source` is true as well),
   links to the reStructuredText sources will be added to the sidebar.

   .. versionadded:: 0.6

.. confval:: html_sourcelink_suffix
   :type: :code-py:`str`
   :default: :code-py:`'.txt'`

   The suffix to append to source links
   (see :confval:`html_show_sourcelink`),
   unless files they have this suffix already.

   .. versionadded:: 1.5

.. confval:: html_use_opensearch
   :type: :code-py:`str`
   :default: :code-py:`''`

   If nonempty, an `OpenSearch <https://github.com/dewitt/opensearch>`_
   description file will be output,
   and all pages will contain a ``<link>`` tag referring to it.
   Since OpenSearch doesn't support relative URLs for its search page location,
   the value of this option must be the base URL
   from which these documents are served (without trailing slash),
   e.g. :code-py:`'https://docs.python.org'`.

   .. versionadded:: 0.2

.. confval:: html_file_suffix
   :type: :code-py:`str`
   :default: :code-py:`'.html'`

   The file name suffix (file extension) for generated HTML files.

   .. versionadded:: 0.4

.. confval:: html_link_suffix
   :type: :code-py:`str`
   :default: The value of **html_file_suffix**

   The suffix for generated links to HTML files.
   Intended to support more esoteric server setups.

   .. versionadded:: 0.6

.. confval:: html_show_copyright
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If True, "© Copyright ..." is shown in the HTML footer,
   with the value or values from :confval:`copyright`.

   .. versionadded:: 1.0

.. confval:: html_show_search_summary
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Show a summary of the search result, i.e., the text around the keyword.

   .. versionadded:: 4.5

.. confval:: html_show_sphinx
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Add "Created using Sphinx_" to the HTML footer.

   .. _Sphinx: https://www.sphinx-doc.org/

   .. versionadded:: 0.4

.. confval:: html_output_encoding
   :type: :code-py:`str`
   :default: :code-py:`'utf-8'`

   Encoding of HTML output files.
   This encoding name must both be a valid Python encoding name
   and a valid HTML ``charset`` value.

   .. versionadded:: 1.0

.. confval:: html_compact_lists
   :type: :code-py:`bool`
   :default: :code-py:`True`

   If True, a list all whose items consist of a single paragraph and/or a
   sub-list all whose items etc... (recursive definition) will not use the
   ``<p>`` element for any of its items. This is standard docutils behaviour.
   Default: :code-py:`True`.

   .. versionadded:: 1.0

.. confval:: html_secnumber_suffix
   :type: :code-py:`str`
   :default: :code-py:`'. '`

   Suffix for section numbers in HTML output.
   Set to :code-py:`' '` to suppress the final dot on section numbers.

   .. versionadded:: 1.0

.. confval:: html_search_language
   :type: :code-py:`str`
   :default: The value of **language**

   Language to be used for generating the HTML full-text search index.
   This defaults to the global language selected with :confval:`language`.
   English (:code-py:`'en'`) is used as a fall-back option
   if there is no support for this language.

   Support exists for the following languages:

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

   .. tip:: Accelerating build speed

      Each language (except Japanese) provides its own stemming algorithm.
      Sphinx uses a Python implementation by default.
      If you want to accelerate building the index file,
      you can use a third-party package (PyStemmer_) by running
      :command:`pip install PyStemmer`.

      .. _PyStemmer: https://pypi.org/project/PyStemmer/

   .. versionadded:: 1.1
      Support English (``en``) and Japanese (``ja``).

   .. versionchanged:: 1.3
      Added additional languages.

.. confval:: html_search_options
   :type: :code-py:`dict[str, str]`
   :default: :code-py:`{}`

   A dictionary with options for the search language support.
   The meaning of these options depends on the language selected.
   Currently, only Japanese and Chinese support options.

   :Japanese:
      ``type`` -- the type of the splitter to use.
         The other options depend on the splitter used.

         :code-py:`'sphinx.search.ja.DefaultSplitter'`
            The TinySegmenter algorithm, used by default.
         :code-py:`'sphinx.search.ja.MecabSplitter'`:
            The MeCab binding
            To use this splitter, the 'mecab' python binding
            or dynamic link library
            ('libmecab.so' for Linux, 'libmecab.dll' for Windows) is required.
         :code-py:`'sphinx.search.ja.JanomeSplitter'`:
            The Janome binding.
            To use this splitter,
            `Janome <https://pypi.org/project/Janome/>`_ is required.


         .. deprecated:: 1.6
            ``'mecab'``, ``'janome'`` and ``'default'`` is deprecated.
            To keep compatibility,
            ``'mecab'``, ``'janome'`` and ``'default'`` are also acceptable.

      Options for :code-py:`'mecab'`:
         :dic_enc:
            _`dic_enc option` is the encoding for the MeCab algorithm.
         :dict:
            _`dict option` is the dictionary to use for the MeCab algorithm.
         :lib:
            _`lib option` is the library name for finding the MeCab library
            via ``ctypes`` if the Python binding is not installed.

         For example:

         .. code-block:: python

             html_search_options = {
                 'type': 'mecab',
                 'dic_enc': 'utf-8',
                 'dict': '/path/to/mecab .dic',
                 'lib': '/path/to/libmecab.so',
             }

      Options for :code-py:`'janome'`:
         :user_dic:
            _`user_dic option` is the user dictionary file path for Janome.
         :user_dic_enc:
            _`user_dic_enc option` is the encoding for
            the user dictionary file specified by ``user_dic`` option.
            Default is 'utf8'.

   :Chinese:
      ``dict``
         The ``jieba`` dictionary path for using a custom dictionary.

   .. versionadded:: 1.1

   .. versionchanged:: 1.4
      Allow any custom splitter in the *type* setting for Japanese.

.. confval:: html_search_scorer
   :type: :code-py:`str`
   :default: :code-py:`''`

   The name of a JavaScript file
   (relative to the :term:`configuration directory`)
   that implements a search results scorer.
   If empty, the default will be used.

   The scorer must implement the following interface,
   and may optionally define the :code-js:`score()` function
   for more granular control.

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
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Link images that have been resized with a
   scale option (*scale*, *width*, or *height*)
   to their original full-resolution image.
   This will not overwrite any link given by the *target* option
   on the the :dudir:`image` directive, if present.

   .. tip::

      To disable this feature on a per-image basis,
      add the ``no-scaled-link`` class to the image directive:

      .. code-block:: rst

         .. image:: sphinx.png
            :scale: 50%
            :class: no-scaled-link

   .. versionadded:: 1.3

   .. versionchanged:: 3.0
      Images with the ``no-scaled-link`` class will not be linked.

.. confval:: html_math_renderer
   :type: :code-py:`str`
   :default: :code-py:`'mathjax'`

   The maths renderer to use for HTML output.
   The bundled renders are *mathjax* and *imgmath*.
   You must also load the relevant extension in :confval:`extensions`.

   .. versionadded:: 1.8


Options for Single HTML output
-------------------------------

These options influence Single HTML output.
This builder derives from the HTML builder,
so the HTML options also apply where appropriate.

.. confval:: singlehtml_sidebars
   :type: :code-py:`dict[str, Sequence[str]]`
   :default: The value of **html_sidebars**

   A dictionary defining custom sidebar templates,
   mapping document names to template names.

   This has the same effect as :confval:`html_sidebars`,
   but the only permitted key is :code-py:`'index'`,
   and all other keys are ignored.


.. _htmlhelp-options:

Options for HTML help output
-----------------------------

These options influence HTML help output.
This builder derives from the HTML builder,
so the HTML options also apply where appropriate.

.. confval:: htmlhelp_basename
   :type: :code-py:`str`
   :default: :code-py:`'{project}doc'`

   Output file base name for HTML help builder.
   The default is the :confval:`project name <project>`
   with spaces removed and ``doc`` appended.

.. confval:: htmlhelp_file_suffix
   :type: :code-py:`str`
   :default: :code-py:`'.html'`

   This is the file name suffix for generated HTML help files.

   .. versionadded:: 2.0

.. confval:: htmlhelp_link_suffix
   :type: :code-py:`str`
   :default: The value of **htmlhelp_file_suffix**

   Suffix for generated links to HTML files.

   .. versionadded:: 2.0


.. _applehelp-options:

Options for Apple Help output
-----------------------------

.. versionadded:: 1.3

These options influence Apple Help output.
This builder derives from the HTML builder,
so the HTML options also apply where appropriate.

.. note::

   Apple Help output will only work on Mac OS X 10.6 and higher,
   as it requires the :program:`hiutil` and :program:`codesign`
   command-line tools, neither of which are Open Source.

   You can disable the use of these tools using
   :confval:`applehelp_disable_external_tools`,
   but the result will not be a valid help book
   until the indexer is run over the ``.lproj`` directories within the bundle.

   .. TODO: Is this warning still relevant as of 2024-07?
            Needs updating by someone with a Mac.

.. confval:: applehelp_bundle_name
   :type: :code-py:`str`
   :default: The value of **project**

   The basename for the Apple Help Book.
   The default is the :confval:`project name <project>`
   with spaces removed.

.. confval:: applehelp_bundle_id
   :type: :code-py:`str`
   :default: :code-py:`None`

   The bundle ID for the help book bundle.

   .. warning::

      You *must* set this value in order to generate Apple Help.

.. confval:: applehelp_bundle_version
   :type: :code-py:`str`
   :default: :code-py:`'1'`

   The bundle version, as a string.

.. confval:: applehelp_dev_region
   :type: :code-py:`str`
   :default: :code-py:`'en-us'`

   The development region.
   Defaults to Apple’s recommended setting, :code-py:`'en-us'`.

.. confval:: applehelp_icon
   :type: :code-py:`str`
   :default: :code-py:`None`

   Path to the help bundle icon file or :code-py:`None` for no icon.
   According to Apple's documentation,
   this should be a 16-by-16 pixel version of the application's icon
   with a transparent background, saved as a PNG file.

.. confval:: applehelp_kb_product
   :type: :code-py:`str`
   :default: :samp:`'{project}-{release}'`

   The product tag for use with :confval:`applehelp_kb_url`.

.. confval:: applehelp_kb_url
   :type: :code-py:`str`
   :default: :code-py:`None`

   The URL for your knowledgebase server,
   e.g. ``https://example.com/kbsearch.py?p='product'&q='query'&l='lang'``.
   At runtime, Help Viewer will replace
   ``'product'`` with the contents of :confval:`applehelp_kb_product`,
   ``'query'`` with the text entered by the user in the search box,
   and ``'lang'`` with the user's system language.

   Set this to to :code-py:`None` to disable remote search.

.. confval:: applehelp_remote_url
   :type: :code-py:`str`
   :default: :code-py:`None`

   The URL for remote content.
   You can place a copy of your Help Book's ``Resources`` directory
   at this location and Help Viewer will attempt to use it
   to fetch updated content.

   For example, if you set it to ``https://example.com/help/Foo/``
   and Help Viewer wants a copy of ``index.html`` for
   an English speaking customer,
   it will look at ``https://example.com/help/Foo/en.lproj/index.html``.

   Set this to to :code-py:`None` for no remote content.

.. confval:: applehelp_index_anchors
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Tell the help indexer to index anchors in the generated HTML.
   This can be useful for jumping to a particular topic
   using the ``AHLookupAnchor`` function
   or the ``openHelpAnchor:inBook:`` method in your code.
   It also allows you to use ``help:anchor`` URLs;
   see the Apple documentation for more information on this topic.

.. confval:: applehelp_min_term_length
   :type: :code-py:`str`
   :default: :code-py:`None`

   Controls the minimum term length for the help indexer.
   If :code-py:`None`, use the default length.

.. confval:: applehelp_stopwords
   :type: :code-py:`str`
   :default: The value of **language**

   Either a language specification (to use the built-in stopwords),
   or the path to a stopwords plist,
   or :code-py:`None` if you do not want to use stopwords.
   The default stopwords plist can be found at
   ``/usr/share/hiutil/Stopwords.plist``
   and contains, at time of writing, stopwords for the following languages:

   * German (``de``)
   * English (``en``)
   * Spanish (``es``)
   * French (``fr``)
   * Hungarian (``hu``)
   * Italian (``it``)
   * Swedish (``sv``)

.. confval:: applehelp_locale
   :type: :code-py:`str`
   :default: The value of **language**

   Specifies the locale to generate help for.
   This is used to determine the name of the ``.lproj`` directory
   inside the Help Book’s ``Resources``,
   and is passed to the help indexer.

.. confval:: applehelp_title
   :type: :code-py:`str`
   :default: :samp:`'{project} Help'`

   Specifies the help book title.

.. confval:: applehelp_codesign_identity
   :type: :code-py:`str`
   :default: The value of **CODE_SIGN_IDENTITY**

   Specifies the identity to use for code signing.
   Use :code-py:`None` if code signing is not to be performed.

   Defaults to the value of the :envvar:`!CODE_SIGN_IDENTITY`
   environment variable, which is set by Xcode for script build phases,
   or :code-py:`None` if that variable is not set.

.. confval:: applehelp_codesign_flags
   :type: :code-py:`list[str]`
   :default: The value of **OTHER_CODE_SIGN_FLAGS**

   A *list* of additional arguments to pass to :program:`codesign` when
   signing the help book.

   Defaults to a list based on the value of the :envvar:`!OTHER_CODE_SIGN_FLAGS`
   environment variable, which is set by Xcode for script build phases,
   or the empty list if that variable is not set.

.. confval:: applehelp_codesign_path
   :type: :code-py:`str`
   :default: :code-py:`'/usr/bin/codesign'`

   The path to the :program:`codesign` program.

.. confval:: applehelp_indexer_path
   :type: :code-py:`str`
   :default: :code-py:`'/usr/bin/hiutil'`

   The path to the :program:`hiutil` program.

.. confval:: applehelp_disable_external_tools
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Do not run the indexer or the code signing tool,
   no matter what other settings are specified.

   This is mainly useful for testing,
   or where you want to run the Sphinx build on a non-macOS platform
   and then complete the final steps on a Mac for some reason.


.. _epub-options:

Options for EPUB output
-----------------------

These options influence EPUB output.
This builder derives from the HTML builder,
so the HTML options also apply where appropriate.

.. note::
   The actual value for some of these options is not important,
   but they are required for the `Dublin Core metadata`_.

   .. _Dublin Core metadata: https://dublincore.org/

.. confval:: epub_basename
   :type: :code-py:`str`
   :default: The value of **project**

   The basename for the EPUB file.

.. confval:: epub_theme
   :type: :code-py:`str`
   :default: :code-py:`'epub'`

   The HTML theme for the EPUB output.  Since the default themes are not
   optimised for small screen space, using the same theme for HTML and EPUB
   output is usually not wise.
   This defaults to :code-py:`'epub'`,
   a theme designed to save visual space.

.. confval:: epub_theme_options
   :type: :code-py:`dict[str, Any]`
   :default: :code-py:`{}`

   A dictionary of options that influence the
   look and feel of the selected theme.
   These are theme-specific.
   The options understood by the :ref:`builtin themes
   <builtin-themes>` are described :ref:`here <builtin-themes>`.

   .. versionadded:: 1.2

.. confval:: epub_title
   :type: :code-py:`str`
   :default: The value of **project**

   The title of the document.

   .. versionchanged:: 2.0
      It defaults to the :confval:`!project` option
      (previously :confval:`!html_title`).

.. confval:: epub_description
   :type: :code-py:`str`
   :default: :code-py:`'unknown'`

   The description of the document.

   .. versionadded:: 1.4

   .. versionchanged:: 1.5
      Renamed from :confval:`!epub3_description`

.. confval:: epub_author
   :type: :code-py:`str`
   :default: The value of **author**

   The author of the document.
   This is put in the Dublin Core metadata.

.. confval:: epub_contributor
   :type: :code-py:`str`
   :default: :code-py:`'unknown'`

   The name of a person, organisation, etc. that played a secondary role
   in the creation of the content of an EPUB Publication.

   .. versionadded:: 1.4

   .. versionchanged:: 1.5
      Renamed from :confval:`!epub3_contributor`

.. confval:: epub_language
   :type: :code-py:`str`
   :default: The value of **language**

   The language of the document.
   This is put in the Dublin Core metadata.

.. confval:: epub_publisher
   :type: :code-py:`str`
   :default: The value of **author**

   The publisher of the document.
   This is put in the Dublin Core metadata.
   You may use any sensible string, e.g. the project homepage.

.. confval:: epub_copyright
   :type: :code-py:`str`
   :default: The value of **copyright**

   The copyright of the document.
   See :confval:`copyright` for permitted formats.

.. confval:: epub_identifier
   :type: :code-py:`str`
   :default: :code-py:`'unknown'`

   An identifier for the document.
   This is put in the Dublin Core metadata.
   For published documents this is the ISBN number,
   but you can also use an alternative scheme, e.g. the project homepage.

.. confval:: epub_scheme
   :type: :code-py:`str`
   :default: :code-py:`'unknown'`

   The publication scheme for the :confval:`epub_identifier`.
   This is put in the Dublin Core metadata.
   For published books the scheme is ``'ISBN'``.
   If you use the project homepage, ``'URL'`` seems reasonable.

.. confval:: epub_uid
   :type: :code-py:`str`
   :default: :code-py:`'unknown'`

   A unique identifier for the document.
   This is put in the Dublin Core metadata.
   You may use a `XML's Name format`_ string.
   You can't use hyphen, period, numbers as a first character.

   .. _XML's Name format: https://www.w3.org/TR/REC-xml/#NT-NameStartChar

.. confval:: epub_cover
   :type: :code-py:`tuple[str, str]`
   :default: :code-py:`()`

   The cover page information.
   This is a tuple containing the filenames of the cover image
   and the html template.
   The rendered html cover page is inserted as the first item
   in the spine in :file:`content.opf`.
   If the template filename is empty, no html cover page is created.
   No cover at all is created if the tuple is empty.

   Examples:

   .. code-block:: python

      epub_cover = ('_static/cover.png', 'epub-cover.html')
      epub_cover = ('_static/cover.png', '')
      epub_cover = ()

   .. versionadded:: 1.1

.. confval:: epub_css_files
   :type: :code-py:`Sequence[str | tuple[str, dict[str, str]]]`
   :default: :code-py:`[]`

   A list of CSS files.
   The entry must be a *filename* string
   or a tuple containing the *filename* string and the *attributes* dictionary.
   The *filename* must be relative to the :confval:`html_static_path`,
   or a full URI with scheme like :code-py:`'https://example.org/style.css'`.
   The *attributes* dictionary is used for the ``<link>`` tag's attributes.
   For more information, see :confval:`html_css_files`.

   .. versionadded:: 1.8

.. confval:: epub_guide
   :type: :code-py:`Sequence[tuple[str, str, str]]`
   :default: :code-py:`()`

   Meta data for the guide element of :file:`content.opf`.
   This is a sequence of tuples containing
   the *type*, the *uri* and the *title* of the optional guide information.
   See `the OPF documentation <https://idpf.org/epub>`_ for details.
   If possible, default entries for the *cover* and *toc* types
   are automatically inserted.
   However, the types can be explicitly overwritten
   if the default entries are not appropriate.

   Example:

   .. code-block:: python

      epub_guide = (
          ('cover', 'cover.html', 'Cover Page'),
      )

   The default value is :code-py:`()`.

.. confval:: epub_pre_files
   :type: :code-py:`Sequence[tuple[str, str]]`
   :default: :code-py:`()`

   Additional files that should be inserted before the text generated by Sphinx.
   It is a list of tuples containing the file name and the title.
   If the title is empty, no entry is added to :file:`toc.ncx`.

   Example:

   .. code-block:: python

      epub_pre_files = [
          ('index.html', 'Welcome'),
      ]

.. confval:: epub_post_files
   :type: :code-py:`Sequence[tuple[str, str]]`
   :default: :code-py:`()`

   Additional files that should be inserted after the text generated by Sphinx.
   It is a list of tuples containing the file name and the title.
   This option  can be used to add an appendix.
   If the title is empty, no entry is added to :file:`toc.ncx`.

   Example:

   .. code-block:: python

      epub_post_files = [
          ('appendix.xhtml', 'Appendix'),
      ]

.. confval:: epub_exclude_files
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`[]`

   A sequence of files that are generated/copied in the build directory
   but should not be included in the EPUB file.

.. confval:: epub_tocdepth
   :type: :code-py:`int`
   :default: :code-py:`3`

   The depth of the table of contents in the file :file:`toc.ncx`.
   It should be an integer greater than zero.

   .. tip::
      A deeply nested table of contents may be difficult to navigate.

.. confval:: epub_tocdup
   :type: :code-py:`bool`
   :default: :code-py:`True`

   This flag determines if a ToC entry is inserted again
   at the beginning of its nested ToC listing.
   This allows easier navigation to the top of a chapter,
   but can be confusing because it mixes entries of different depth in one list.

.. confval:: epub_tocscope
   :type: :code-py:`'default' | 'includehidden'`
   :default: :code-py:`'default'`

   This setting control the scope of the EPUB table of contents.
   The setting can have the following values:

   :code-py:`'default'`
      Include all ToC entries that are not hidden
   :code-py:`'includehidden'`
      Include all ToC entries

   .. versionadded:: 1.2

.. confval:: epub_fix_images
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Try and fix image formats that are not supported by some EPUB readers.
   At the moment palette images with a small colour table are upgraded.
   This is disabled by default because the
   automatic conversion may lose information.
   You need the Python Image Library (Pillow_) installed to use this option.

   .. _Pillow: https://pypi.org/project/Pillow/

   .. versionadded:: 1.2

.. confval:: epub_max_image_width
   :type: :code-py:`int`
   :default: :code-py:`0`

   This option specifies the maximum width of images.
   If it is set to a valuevgreater than zero,
   images with a width larger than the given value are scaled accordingly.
   If it is zero, no scaling is performed.
   You need the Python Image Library (Pillow_) installed to use this option.

   .. _Pillow: https://pypi.org/project/Pillow/

   .. versionadded:: 1.2

.. confval:: epub_show_urls
   :type: :code-py:`'footnote' | 'no' | 'inline'`
   :default: :code-py:`'footnote'`

   Control how to display URL addresses.
   This is very useful for readers that have no other means
   to display the linked URL.
   The setting can have the following values:

   :code-py:`'inline'`
      Display URLs inline in parentheses.
   :code-py:`'footnote'`
      Display URLs in footnotes.
   :code-py:`'no'`
      Do not display URLs.

   The display of inline URLs can be customised by adding CSS rules
   for the class ``link-target``.

   .. versionadded:: 1.2

.. confval:: epub_use_index
   :type: :code-py:`bool`
   :default: The value of **html_use_index**

   Add an index to the EPUB document.

   .. versionadded:: 1.2

.. confval:: epub_writing_mode
   :type: :code-py:`'horizontal' | 'vertical'`
   :default: :code-py:`'horizontal'`

   It specifies writing direction.
   It can accept :code-py:`'horizontal'` and :code-py:`'vertical'`

   .. list-table::
      :align: left
      :header-rows: 1
      :stub-columns: 1

      * - ``epub_writing_mode``
        - ``'horizontal'``
        - ``'vertical'``
      * - writing-mode_
        - ``horizontal-tb``
        - ``vertical-rl``
      * - page progression
        - left to right
        - right to left
      * - iBook's Scroll Theme support
        - scroll-axis is vertical.
        - scroll-axis is horizontal.

   .. _writing-mode: https://developer.mozilla.org/en-US/docs/Web/CSS/writing-mode


.. _latex-options:

Options for LaTeX output
------------------------

These options influence LaTeX output.

.. confval:: latex_engine
   :type: :code-py:`'pdflatex' | 'xelatex' | 'lualatex' | 'platex' | 'uplatex'`
   :default: :code-py:`'pdflatex'`

   The LaTeX engine to build the documentation.
   The setting can have the following values:

   * :code-py:`'pdflatex'` -- PDFLaTeX (default)
   * :code-py:`'xelatex'` -- XeLaTeX
     (default if :confval:`language` is one of ``el``, ``zh_CN``, or ``zh_TW``)
   * :code-py:`'lualatex'` -- LuaLaTeX
   * :code-py:`'platex'` -- pLaTeX
   * :code-py:`'uplatex'` -- upLaTeX
     (default if :confval:`language` is :code-py:`'ja'`)

   .. important::

      ``'pdflatex'``\ 's support for Unicode characters is limited.
      If your project uses Unicode characters,
      setting the engine to ``'xelatex'`` or ``'lualatex'``
      and making sure to use an OpenType font with wide-enough glyph coverage
      is often easier than trying to make ``'pdflatex'`` work
      with the extra Unicode characters.
      Since Sphinx 2.0, the default typeface is GNU FreeFont,
      which has good coverage of Latin, Cyrillic, and Greek glyphs.

   .. note::

      Sphinx 2.0 adds support for occasional Cyrillic and Greek letters or
      words in documents using a Latin language and ``'pdflatex'``.  To enable
      this, the :ref:`fontenc` key of :ref:`latex_elements
      <latex_elements_confval>` must be used appropriately.

   .. note::

      Contrarily to :ref:`MathJaX math rendering in HTML output <math-support>`,
      LaTeX requires some extra configuration to support Unicode literals in
      :rst:dir:`math`:
      the only comprehensive solution (as far as we know) is to
      use ``'xelatex'`` or ``'lualatex'`` *and* to add
      ``r'\usepackage{unicode-math}'``
      (e.g. via the :ref:`preamble` key of :ref:`latex_elements
      <latex_elements_confval>`).
      You may prefer ``r'\usepackage[math-style=literal]{unicode-math}'``
      to keep a Unicode literal such as ``α`` (U+03B1) as-is in output,
      rather than being rendered as :math:`\alpha`.

   .. versionchanged:: 2.1.0
      Use ``'xelatex'`` (and LaTeX package ``xeCJK``)
      by default for Chinese documents.

   .. versionchanged:: 2.2.1
      Use ``'xelatex'`` by default for Greek documents.

   .. versionchanged:: 2.3
      Add ``'uplatex'`` support.

   .. versionchanged:: 4.0
      Use ``'uplatex'`` by default for Japanese documents.

.. confval:: latex_documents
   :type: :code-py:`Sequence[tuple[str, str, str, str, str, bool]]`
   :default: The default LaTeX documents

   This value determines how to group the document tree
   into LaTeX source files.
   It must be a list of tuples ``(startdocname, targetname, title, author,
   theme, toctree_only)``,
   where the items are:

   *startdocname*
      String that specifies the :term:`document name` of
      the LaTeX file's master document.
      All documents referenced by the *startdoc* document in
      ToC trees will be included in the LaTeX file.
      (If you want to use the default master document for your LaTeX build,
      provide your :confval:`master_doc` here.)

   *targetname*
      File name of the LaTeX file in the output directory.

   *title*
      LaTeX document title.
      Can be empty to use the title of the *startdoc* document.
      This is inserted as LaTeX markup,
      so special characters like a backslash or ampersand
      must be represented by the proper LaTeX commands
      if they are to be inserted literally.

   *author*
      Author for the LaTeX document.
      The same LaTeX markup caveat as for *title* applies.
      Use ``\\and`` to separate multiple authors,  as in: ``'John \\and Sarah'``
      (backslashes must be Python-escaped to reach LaTeX).

   *theme*
      LaTeX theme.
      See :confval:`latex_theme`.

   *toctree_only*
      Must be :code-py:`True` or :code-py:`False`.
      If True, the *startdoc* document itself is not included in the output,
      only the documents referenced by it via ToC trees.
      With this option, you can put extra stuff in the master document
      that shows up in the HTML, but not the LaTeX output.

   .. versionadded:: 0.3
      The 6th item ``toctree_only``.
      Tuples with 5 items are still accepted.

   .. versionadded:: 1.2
      In the past including your own document class required you to prepend the
      document class name with the string "sphinx".
      This is not necessary anymore.

.. confval:: latex_logo
   :type: :code-py:`str`
   :default: :code-py:`''`

   If given, this must be the name of an image file
   (path relative to the :term:`configuration directory`)
   that is the logo of the documentation.
   It is placed at the top of the title page.

.. confval:: latex_toplevel_sectioning
   :type: :code-py:`'part' | 'chapter' | 'section'`
   :default: :code-py:`None`

   This value determines the topmost sectioning unit.  The default setting is
   ``'section'`` if :confval:`latex_theme` is ``'howto'``, and ``'chapter'``
   if it is ``'manual'``.  The alternative in both cases is to specify
   ``'part'``, which means that LaTeX document will use the :code-tex:`\\part`
   command.

   In that case the numbering of sectioning units one level deep gets off-sync
   with HTML numbering, as by default LaTeX does not reset
   :code-tex:`\\chapter` numbering (or :code-tex:`\\section` for ``'howto'``
   theme) when encountering :code-tex:`\\part` command.

   .. versionadded:: 1.4

.. confval:: latex_appendices
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list of document names to append as an appendix to all manuals.
   This is ignored if :confval:`latex_theme` is set to :code-py:`'howto'`.

.. confval:: latex_domain_indices
   :type: :code-py:`bool | Sequence[str]`
   :default: :code-py:`True`

   If True, generate domain-specific indices in addition to the general index.
   For e.g. the Python domain, this is the global module index.

   This value can be a Boolean or a list of index names that should be generated.
   To find out the index name for a specific index, look at the HTML file name.
   For example, the Python module index has the name ``'py-modindex'``.

   Example:

   .. code-block:: python

      latex_domain_indices = {
          'py-modindex',
      }

   .. versionadded:: 1.0
   .. versionchanged:: 7.4
      Permit and prefer a set type.

.. confval:: latex_show_pagerefs
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Add page references after internal references.
   This is very useful for printed copies of the manual.

   .. versionadded:: 1.0

.. confval:: latex_show_urls
   :type: :code-py:`'no' | 'footnote' | 'inline'`
   :default: :code-py:`'no'`

   Control how to display URL addresses.
   This is very useful for printed copies of the manual.
   The setting can have the following values:

   :code-py:`'no'`
      Do not display URLs
   :code-py:`'footnote'`
      Display URLs in footnotes
   :code-py:`'inline'`
      Display URLs inline in parentheses

   .. versionadded:: 1.0
   .. versionchanged:: 1.1
      This value is now a string; previously it was a boolean value,
      and a true value selected the :code-py:`'inline'` display.
      For backwards compatibility, :code-py:`True` is still accepted.

.. confval:: latex_use_latex_multicolumn
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Use standard LaTeX's :code-tex:`\\multicolumn` for merged cells in tables.

   :code-py:`False`
      Sphinx's own macros are used for merged cells from grid tables.
      They allow general contents (literal blocks, lists, blockquotes, ...)
      but may have problems if the :rst:dir:`tabularcolumns` directive
      was used to inject LaTeX mark-up of the type
      ``>{..}``, ``<{..}``, ``@{..}`` as column specification.
   :code-py:`True`
      Use LaTeX's standard :code-tex:`\\multicolumn`;
      this is incompatible with literal blocks in horizontally merged cells,
      and also with multiple paragraphs in such cells
      if the table is rendered using ``tabulary``.

   .. versionadded:: 1.6

.. confval:: latex_table_style
   :type: :code-py:`list[str]`
   :default: :code-py:`['booktabs', 'colorrows']`

   A list of styling classes (strings).
   Currently supported:

   :code-py:`'booktabs'`
      No vertical lines, and only 2 or 3 horizontal lines
      (the latter if there is a header),
      using the booktabs_ package.

   :code-py:`'borderless'`
      No lines whatsoever.

   :code-py:`'colorrows'`
      The table rows are rendered with alternating background colours.
      The interface to customise them is via
      :ref:`dedicated keys <tablecolors>` of :ref:`latexsphinxsetup`.

      .. important::

         With the :code-py:`'colorrows'` style,
         the :code-tex:`\\rowcolors` LaTeX command becomes a no-op
         (this command has limitations and has never correctly
         supported all types of tables Sphinx produces in LaTeX).
         Please use the
         :ref:`latex table color configuration <tablecolors>` keys instead.

   To customise the styles for a table,
   use the ``:class:`` option if the table is defined using a directive,
   or otherwise insert a :ref:`rst-class <rstclass>` directive before the table
   (cf. :ref:`table-directives`).

   Currently recognised classes are ``booktabs``, ``borderless``,
   ``standard``, ``colorrows``, ``nocolorrows``.
   The latter two can be combined with any of the first three.
   The ``standard`` class produces tables with
   both horizontal and vertical lines
   (as had been the default prior to Sphinx 6.0.0).

   A single-row multi-column merged cell will obey the row colour,
   if it is set.
   See also ``TableMergeColor{Header,Odd,Even}``
   in the :ref:`latexsphinxsetup` section.

   .. note::

      * It is hard-coded in LaTeX that a single cell will obey the row colour
        even if there is a column colour set via :code-tex:`\\columncolor`
        from a column specification (see :rst:dir:`tabularcolumns`).
        Sphinx provides :code-tex:`\\sphinxnorowcolor` which can be used
        in a table column specification like this:

        .. code-block:: latex

           >{\columncolor{blue}\sphinxnorowcolor}

      * Sphinx also provides :code-tex:`\\sphinxcolorblend`,
        which however requires the xcolor_ package.
        Here is an example:

        .. code-block:: latex

           >{\sphinxcolorblend{!95!red}}

        It means that in this column,
        the row colours will be slightly tinted by red;
        refer to xcolor_ documentation for more on the syntax of its
        :code-tex:`\\blendcolors` command
        (a :code-tex:`\\blendcolors` in place of :code-tex:`\\sphinxcolorblend`
        would modify colours of the cell *contents*,
        not of the cell *background colour panel*...).
        You can find an example of usage in the :ref:`dev-deprecated-apis`
        section of this document in PDF format.

        .. hint::

           If you want to use a special colour for the *contents* of the
           cells of a given column use ``>{\noindent\color{<color>}}``,
           possibly in addition to the above.

      * Multi-row merged cells, whether single column or multi-column
        currently ignore any set column, row, or cell colour.

      * It is possible for a simple cell to set a custom colour via the
        :dudir:`raw` directive and
        the :code-tex:`\\cellcolor` LaTeX command used
        anywhere in the cell contents.
        This currently is without effect in a merged cell, whatever its kind.

   .. hint::

      In a document not using ``'booktabs'`` globally,
      it is possible to style an individual table via the ``booktabs`` class,
      but it will be necessary to add ``r'\usepackage{booktabs}'``
      to the LaTeX preamble.

      On the other hand one can use ``colorrows`` class for individual tables
      with no extra package (as Sphinx since 5.3.0 always loads colortbl_).

   .. _booktabs: https://ctan.org/pkg/booktabs
   .. _colortbl: https://ctan.org/pkg/colortbl
   .. _xcolor: https://ctan.org/pkg/xcolor

   .. versionadded:: 5.3.0

   .. versionchanged:: 6.0.0

      Modify default from :code-py:`[]` to :code-py:`['booktabs', 'colorrows']`.

.. confval:: latex_use_xindy
   :type: :code-py:`bool`
   :default: :code-py:`True if latex_engine in {'xelatex', 'lualatex'} else False`

   Use Xindy_ to prepare the index of general terms.
   By default, the LaTeX builder uses :program:`makeindex`
   for preparing the index of general terms .
   Using Xindy_ means that words with UTF-8 characters will be
   ordered correctly for the :confval:`language`.

   .. _Xindy: https://xindy.sourceforge.net/

   * This option is ignored if :confval:`latex_engine` is :code-py:`'platex'`
     (Japanese documents;
     :program:`mendex` replaces :program:`makeindex` then).

   * The default is :code-py:`True`
     for :code-py:`'xelatex'` or :code-py:`'lualatex'` as
     :program:`makeindex` creates ``.ind`` files containing invalid bytes
     for the UTF-8 encoding if any indexed term starts with
     a non-ASCII character.
     With :code-py:`'lualatex'` this then breaks the PDF build.

   * The default is :code-py:`False` for :code-py:`'pdflatex'`,
     but :code-py:`True` is recommended for non-English documents as soon
     as some indexed terms use non-ASCII characters from the language script.
     Attempting to index a term whose first character is non-ASCII
     will break the build, if :confval:`latex_use_xindy` is left to its
     default :code-py:`False`.

   Sphinx adds some dedicated support to the :program:`xindy` base distribution
   for using :code-py:`'pdflatex'` engine with Cyrillic scripts.
   With both :code-py:`'pdflatex'` and Unicode engines,
   Cyrillic documents handle the indexing of Latin names correctly,
   even those having diacritics.

   .. versionadded:: 1.8

.. confval:: latex_elements
   :type: :code-py:`dict[str, str]`
   :default: :code-py:`{}`

   .. versionadded:: 0.5

   :ref:`See the full documentation for latex_elements  <latex_elements_confval>`.

.. confval:: latex_docclass
   :type: :code-py:`dict[str, str]`
   :default: :code-py:`{}`

   A dictionary mapping :code-py:`'howto'` and :code-py:`'manual'`
   to names of real document classes that will be used as the base
   for the two Sphinx classes.
   Default is to use :code-py:`'article'` for :code-py:`'howto'`
   and :code-py:`'report'` for :code-py:`'manual'`.

   .. versionadded:: 1.0

   .. versionchanged:: 1.5
      In Japanese documentation (:confval:`language` is :code-py:`'ja'`),
      by default :code-py:`'jreport'` is used for :code-py:`'howto'`
      and :code-py:`'jsbook'` for :code-py:`'manual'`.

.. confval:: latex_additional_files
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list of file names, relative to the :term:`configuration directory`,
   to copy to the build directory when building LaTeX output.
   This is useful to copy files that Sphinx doesn't copy automatically,
   or to overwrite Sphinx LaTeX support files with custom versions.
   Image files that are referenced in source files (e.g. via ``.. image::``)
   are copied automatically and should not be listed there.

   .. attention::
      Filenames with the ``.tex`` extension will be automatically
      handed over to the PDF build process triggered by
      :option:`sphinx-build -M latexpdf <sphinx-build -M>`
      or by :program:`make latexpdf`.
      If the file was added only to be :code-tex:`\\input{}`
      from a modified preamble,
      you must add a further suffix such as ``.txt`` to the filename
      and adjust the :code-tex:`\\input{}` macro accordingly.

   .. versionadded:: 0.6

   .. versionchanged:: 1.2
      This overrides the files provided from Sphinx such as ``sphinx.sty``.

.. confval:: latex_theme
   :type: :code-py:`str`
   :default: :code-py:`'manual'`

   The "theme" that the LaTeX output should use.
   It is a collection of settings for LaTeX output
   (e.g. document class, top level sectioning unit and so on).

   The bundled first-party LaTeX themes are *manual* and *howto*:

   ``manual``
      A LaTeX theme for writing a manual.
      It imports the ``report`` document class
      (Japanese documents use ``jsbook``).

   ``howto``
      A LaTeX theme for writing an article.
      It imports the ``article`` document class
      (Japanese documents use ``jreport``).
      :confval:`latex_appendices` is only available for this theme.

   .. versionadded:: 3.0

.. confval:: latex_theme_options
   :type: :code-py:`dict[str, Any]`
   :default: :code-py:`{}`

   A dictionary of options that influence the
   look and feel of the selected theme.
   These are theme-specific.

   .. versionadded:: 3.1

.. confval:: latex_theme_path
   :type: :code-py:`list[str]`
   :default: :code-py:`[]`

   A list of paths that contain custom LaTeX themes as subdirectories.
   Relative paths are taken as relative to the :term:`configuration directory`.

   .. versionadded:: 3.0


.. _text-options:

Options for text output
-----------------------

These options influence text output.

.. confval:: text_add_secnumbers
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Include section numbers in text output.

   .. versionadded:: 1.7

.. confval:: text_newlines
   :type: :code-py:`'unix' | 'windows' | 'native'`
   :default: :code-py:`'unix'`

   Determines which end-of-line character(s) are used in text output.

   :code-py:`'unix'`
      Use Unix-style line endings (``\n``).
   :code-py:`'windows'`
      Use Windows-style line endings (``\r\n``).
   :code-py:`'native'`
      Use the line ending style of the platform the documentation is built on.

   .. versionadded:: 1.1

.. confval:: text_secnumber_suffix
   :type: :code-py:`str`
   :default: :code-py:`'. '`

   Suffix for section numbers in text output.
   Set to :code-py:`' '` to suppress the final dot on section numbers.

   .. versionadded:: 1.7

.. confval:: text_sectionchars
   :type: :code-py:`str`
   :default: :code-py:`'*=-~"+\`'`

   A string of 7 characters that should be used for underlining sections.
   The first character is used for first-level headings,
   the second for second-level headings and so on.

   .. versionadded:: 1.1


.. _man-options:

Options for manual page output
------------------------------

These options influence manual page output.

.. confval:: man_pages
   :type: :code-py:`Sequence[tuple[str, str, str, str, str]]`
   :default: The default manual pages

   This value determines how to group the document tree
   into manual pages.
   It must be a list of tuples
   ``(startdocname, name, description, authors, section)``,
   where the items are:

   *startdocname*
     String that specifies the :term:`document name` of
     the manual page's master document.
     All documents referenced by the *startdoc* document in
     ToC trees will be included in the manual page.
     (If you want to use the default master document for your manual pages build,
     provide your :confval:`master_doc` here.)

   *name*
     Name of the manual page.
     This should be a short string without spaces or special characters.
     It is used to determine the file name as well as the
     name of the manual page (in the NAME section).

   *description*
     Description of the manual page.
     This is used in the NAME section.
     Can be an empty string if you do not want to
     automatically generate the NAME section.

   *authors*
     A list of strings with authors, or a single string.
     Can be an empty string or list if you do not want to
     automatically generate an AUTHORS section in the manual page.

   *section*
     The manual page section.
     Used for the output file name as well as in the manual page header.

   .. versionadded:: 1.0

.. confval:: man_show_urls
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Add URL addresses after links.

   .. versionadded:: 1.1

.. confval:: man_make_section_directory
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Make a section directory on build man page.

   .. versionadded:: 3.3

   .. versionchanged:: 4.0
      The default is now :code-py:`False` (previously :code-py:`True`).

   .. versionchanged:: 4.0.2
      Revert the change in the default.


.. _texinfo-options:

Options for Texinfo output
--------------------------

These options influence Texinfo output.

.. confval:: texinfo_documents
   :type: :code-py:`Sequence[tuple[str, str, str, str, str, str, str, bool]]`
   :default: The default Texinfo documents

   This value determines how to group the document tree
   into Texinfo source files.
   It must be a list of tuples ``(startdocname, targetname, title, author,
   dir_entry, description, category, toctree_only)``,
   where the items are:

   *startdocname*
      String that specifies the :term:`document name` of
      the Texinfo file's master document.
      All documents referenced by the *startdoc* document in
      ToC trees will be included in the Texinfo file.
      (If you want to use the default master document for your Texinfo build,
      provide your :confval:`master_doc` here.)

   *targetname*
      File name (no extension) of the Texinfo file in the output directory.

   *title*
      Texinfo document title.
      Can be empty to use the title of the *startdoc*
      document.  Inserted as Texinfo markup,
      so special characters like ``@`` and ``{}`` will need to
      be escaped to be inserted literally.

   *author*
      Author for the Texinfo document.
      Inserted as Texinfo markup.
      Use ``@*`` to separate multiple authors, as in: ``'John@*Sarah'``.

   *dir_entry*
      The name that will appear in the top-level ``DIR`` menu file.

   *description*
      Descriptive text to appear in the top-level ``DIR`` menu file.

   *category*
      Specifies the section which this entry will appear in the top-level
      ``DIR`` menu file.

   *toctree_only*
      Must be :code-py:`True` or :code-py:`False`.
      If True, the *startdoc* document itself is not included in the output,
      only the documents referenced by it via ToC trees.
      With this option, you can put extra stuff in the master document
      that shows up in the HTML, but not the Texinfo output.

   .. versionadded:: 1.1

.. confval:: texinfo_appendices
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`[]`

   A list of document names to append as an appendix to all manuals.

   .. versionadded:: 1.1

.. confval:: texinfo_cross_references
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Generate inline references in a document.
   Disabling inline references can make an info file more readable
   with a stand-alone reader (``info``).

   .. versionadded:: 4.4

.. confval:: texinfo_domain_indices
   :type: :code-py:`bool | Sequence[str]`
   :default: :code-py:`True`

   If True, generate domain-specific indices in addition to the general index.
   For e.g. the Python domain, this is the global module index.

   This value can be a Boolean or a list of index names that should be generated.
   To find out the index name for a specific index, look at the HTML file name.
   For example, the Python module index has the name ``'py-modindex'``.

   Example:

   .. code-block:: python

      texinfo_domain_indices = {
          'py-modindex',
      }

   .. versionadded:: 1.1
   .. versionchanged:: 7.4
      Permit and prefer a set type.

.. confval:: texinfo_elements
   :type: :code-py:`dict[str, Any]`
   :default: :code-py:`{}`

   A dictionary that contains Texinfo snippets that override those that
   Sphinx usually puts into the generated ``.texi`` files.

   * Keys that you may want to override include:

     ``'paragraphindent'``
        Number of spaces to indent the first line of each paragraph,
        default ``2``.
        Specify ``0`` for no indentation.

     ``'exampleindent'``
        Number of spaces to indent the lines for examples or literal blocks,
        default ``4``.
        Specify ``0`` for no indentation.

     ``'preamble'``
        Texinfo markup inserted near the beginning of the file.

     ``'copying'``
        Texinfo markup inserted within the ``@copying`` block
        and displayed after the title.
        The default value consists of a simple title page identifying the project.

   * Keys that are set by other options
     and therefore should not be overridden are
     ``'author'``, ``'body'``, ``'date'``, ``'direntry'``
     ``'filename'``, ``'project'``, ``'release'``, and ``'title'``.

   .. versionadded:: 1.1

.. confval:: texinfo_no_detailmenu
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Do not generate a ``@detailmenu`` in the "Top" node's menu
   containing entries for each sub-node in the document.

   .. versionadded:: 1.2

.. confval:: texinfo_show_urls
   :type: :code-py:`'footnote' | 'no' | 'inline'`
   :default: :code-py:`'footnote'`

   Control how to display URL addresses.
   The setting can have the following values:

   :code-py:`'footnote'`
      Display URLs in footnotes.
   :code-py:`'no'`
      Do not display URLs.
   :code-py:`'inline'`
      Display URLs inline in parentheses.

   .. versionadded:: 1.1


.. _qthelp-options:

Options for QtHelp output
--------------------------

These options influence qthelp output.
This builder derives from the HTML builder,
so the HTML options also apply where appropriate.

.. confval:: qthelp_basename
   :type: :code-py:`str`
   :default: The value of **project**

   The basename for the qthelp file.

.. confval:: qthelp_namespace
   :type: :code-py:`str`
   :default: :code-py:`'org.sphinx.{project_name}.{project_version}'`

   The namespace for the qthelp file.

.. confval:: qthelp_theme
   :type: :code-py:`str`
   :default: :code-py:`'nonav'`

   The HTML theme for the qthelp output.

.. confval:: qthelp_theme_options
   :type: :code-py:`dict[str, Any]`
   :default: :code-py:`{}`

   A dictionary of options that influence the
   look and feel of the selected theme.
   These are theme-specific.
   The options understood by the :ref:`builtin themes
   <builtin-themes>` are described :ref:`here <builtin-themes>`.


Options for XML output
----------------------

.. confval:: xml_pretty
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Pretty-print the XML.

   .. versionadded:: 1.2


Options for the linkcheck builder
---------------------------------

Filtering
~~~~~~~~~

These options control which links the *linkcheck* builder checks,
and which failures and redirects it ignores.

.. confval:: linkcheck_allowed_redirects
   :type: :code-py:`dict[str, str]`

   A dictionary that maps a pattern of the source URI
   to a pattern of the canonical URI.
   The *linkcheck* builder treats the redirected link as "working" when:

   * the link in the document matches the source URI pattern, and
   * the redirect location matches the canonical URI pattern.

   The *linkcheck* builder will emit a warning when
   it finds redirected links that don't meet the rules above.
   It can be useful to detect unexpected redirects when using
   :option:`the fail-on-warnings mode <sphinx-build --fail-on-warning>`.

   Example:

   .. code-block:: python

      linkcheck_allowed_redirects = {
          # All HTTP redirections from the source URI to
          # the canonical URI will be treated as "working".
          r'https://sphinx-doc\.org/.*': r'https://sphinx-doc\.org/en/master/.*'
      }

   .. versionadded:: 4.1

   .. versionchanged:: 9.0
      Setting :confval:`!linkcheck_allowed_redirects` to an empty dictionary
      may now be used to warn on all redirects encountered
      by the *linkcheck* builder.

.. confval:: linkcheck_anchors
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Check the validity of ``#anchor``\ s in links.
   Since this requires downloading the whole document,
   it is considerably slower when enabled.

   .. versionadded:: 1.2

.. confval:: linkcheck_anchors_ignore
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`["^!"]`

   A list of regular expressions that match anchors that the *linkcheck* builder
   should skip when checking the validity of anchors in links.
   For example, this allows skipping anchors added by a website's JavaScript.

   .. tip::
      Use :confval:`linkcheck_anchors_ignore_for_url` to check a URL,
      but skip verifying that the anchors exist.

   .. note::
      If you want to ignore anchors of a specific page or
      of pages that match a specific pattern
      (but still check occurrences of the same page(s) that don't have anchors),
      use :confval:`linkcheck_ignore` instead,
      for example as follows:

      .. code-block:: python

         linkcheck_ignore = [
            'https://www.sphinx-doc.org/en/1.7/intro.html#',
         ]

   .. versionadded:: 1.5

.. confval:: linkcheck_anchors_ignore_for_url
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list or tuple of regular expressions matching URLs
   for which the *linkcheck* builder should not check the validity of anchors.
   This allows skipping anchor checks on a per-page basis
   while still checking the validity of the page itself.

   .. versionadded:: 7.1

.. confval:: linkcheck_exclude_documents
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list of regular expressions that match documents in which
   the *linkcheck* builder should not check the validity of links.
   This can be used for permitting link decay
   in legacy or historical sections of the documentation.

   Example:

   .. code-block:: python

      # ignore all links in documents located in a subdirectory named 'legacy'
      linkcheck_exclude_documents = [r'.*/legacy/.*']

   .. versionadded:: 4.4

.. confval:: linkcheck_ignore
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list of regular expressions that match URIs that should not be checked
   when doing a ``linkcheck`` build.

   Server-issued redirects that match :confval:`ignored URIs <linkcheck_ignore>`
   will not be followed.

   Example:

   .. code-block:: python

      linkcheck_ignore = [r'https://localhost:\d+/']

   .. versionadded:: 1.1

HTTP Requests
~~~~~~~~~~~~~

These options control how the *linkcheck* builder makes HTTP requests,
including how it handles redirects and authentication,
and the number of workers to use.

.. confval:: linkcheck_auth
   :type: :code-py:`Sequence[tuple[str, Any]]`
   :default: :code-py:`[]`

   Pass authentication information when doing a ``linkcheck`` build.

   A list of :code-py:`(regex_pattern, auth_info)` tuples where the items are:

   *regex_pattern*
     A regular expression that matches a URI.
   *auth_info*
     Authentication information to use for that URI.
     The value can be anything that is understood by the ``requests`` library
     (see :ref:`requests authentication <requests:authentication>` for details).

   The *linkcheck* builder will use the first matching ``auth_info`` value
   it can find in the :confval:`!linkcheck_auth` list,
   so values earlier in the list have higher priority.

   Example:

   .. code-block:: python

      linkcheck_auth = [
        ('https://foo\.yourcompany\.com/.+', ('johndoe', 'secret')),
        ('https://.+\.yourcompany\.com/.+', HTTPDigestAuth(...)),
      ]

   .. versionadded:: 2.3

.. confval:: linkcheck_allow_unauthorized
   :type: :code-py:`bool`
   :default: :code-py:`False`

   When a webserver responds with an HTTP 401 (unauthorised) response,
   the current default behaviour of the *linkcheck* builder is
   to treat the link as "broken".
   To change that behaviour, set this option to :code-py:`True`.

   .. versionchanged:: 8.0
      The default value for this option changed to :code-py:`False`,
      meaning HTTP 401 responses to checked hyperlinks
      are treated as "broken" by default.

   .. versionadded:: 7.3

.. confval:: linkcheck_case_insensitive_urls
   :type: :code-py:`Set[str] | Sequence[str]`
   :default: :code-py:`()`

   A collection of regular expressions that match URLs for which the *linkcheck*
   builder should perform case-insensitive comparisons. This is useful for
   links to websites that are case-insensitive or normalise URL casing.

   By default, *linkcheck* requires the destination URL to match the
   documented URL case-sensitively.
   For example, a link to ``http://example.org/PATH`` that redirects to
   ``http://example.org/path`` will be reported as ``redirected``.

   If the URL matches a pattern contained in
   :confval:`!linkcheck_case_insensitive_urls`,
   it would instead be reported as ``working``.

   For example, to treat all GitHub URLs as case-insensitive:

   .. code-block:: python

      linkcheck_case_insensitive_urls = [
          r'https://github\.com/.*',
      ]

   Or, to treat all URLs as case-insensitive:

   .. code-block:: python

      linkcheck_case_insensitive_urls = ['.*']

   .. note:: URI fragments (HTML anchors) are not affected by this option.
             They are always checked with case-sensitive comparisons.

   .. versionadded:: 9.0

.. confval:: linkcheck_rate_limit_timeout
   :type: :code-py:`int`
   :default: :code-py:`300`

   The *linkcheck* builder may issue a large number of requests to the same
   site over a short period of time.
   This setting controls the builder behaviour
   when servers indicate that requests are rate-limited,
   by setting the maximum duration (in seconds) that the builder will
   wait for between each attempt before recording a failure.

   The *linkcheck* builder always respects a server's direction
   of when to retry (using the `Retry-After`_ header).
   Otherwise, ``linkcheck`` waits for a minute before to retry and keeps
   doubling the wait time between attempts until it succeeds or exceeds the
   :confval:`!linkcheck_rate_limit_timeout` (in seconds).
   Custom timeouts should be given as a number of seconds.

   .. _Retry-After: https://datatracker.ietf.org/doc/html/rfc7231#section-7.1.3

   .. versionadded:: 3.4

.. confval:: linkcheck_report_timeouts_as_broken
   :type: :code-py:`bool`
   :default: :code-py:`False`

   If :confval:`linkcheck_timeout` expires while waiting for a response from
   a hyperlink, the *linkcheck* builder will report the link as a ``timeout``
   by default.  To report timeouts as ``broken`` instead, you can
   set :confval:`linkcheck_report_timeouts_as_broken` to :code-py:`True`.

   .. versionchanged:: 8.0
      The default value for this option changed to :code-py:`False`,
      meaning timeouts that occur while checking hyperlinks
      will be reported using the new 'timeout' status code.

   .. versionadded:: 7.3

.. confval:: linkcheck_request_headers
   :type: :code-py:`dict[str, dict[str, str]]`
   :default: :code-py:`{}`

   A dictionary that maps URL (without paths) to HTTP request headers.

   The key is a URL base string like :code-py:`'https://www.sphinx-doc.org/'`.
   To specify headers for other hosts, :code-py:`"*"` can be used.
   It matches all hosts only when the URL does not match other settings.

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
   :type: :code-py:`int`
   :default: :code-py:`1`

   The number of times the *linkcheck* builder
   will attempt to check a URL before declaring it broken.

   .. versionadded:: 1.4

.. confval:: linkcheck_timeout
   :type: :code-py:`int`
   :default: :code-py:`30`

   The duration, in seconds, that the *linkcheck* builder
   will wait for a response after each hyperlink request.

   .. versionadded:: 1.1

.. confval:: linkcheck_workers
   :type: :code-py:`int`
   :default: :code-py:`5`

   The number of worker threads to use when checking links.

   .. versionadded:: 1.1


Domain options
==============


.. _c-config:

Options for the C domain
------------------------

.. confval:: c_extra_keywords
   :type: :code-py:`Set[str] | Sequence[str]`
   :default: :code-py:`['alignas', 'alignof', 'bool',
                       'complex', 'imaginary', 'noreturn',
                       'static_assert', 'thread_local']`

   A list of identifiers to be recognised as keywords by the C parser.

   .. versionadded:: 4.0.3
   .. versionchanged:: 7.4
      :confval:`!c_extra_keywords` can now be a set.

.. confval:: c_id_attributes
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A sequence of strings that the parser should additionally accept
   as attributes.
   For example, this can be used when  :code-c:`#define`
   has been used for attributes, for portability.

   Example:

   .. code-block:: python

      c_id_attributes = [
          'my_id_attribute',
      ]

   .. versionadded:: 3.0
   .. versionchanged:: 7.4
      :confval:`!c_id_attributes` can now be a tuple.

.. confval:: c_maximum_signature_line_length
   :type: :code-py:`int | None`
   :default: :code-py:`None`

   If a signature's length in characters exceeds the number set,
   each parameter within the signature will be displayed on
   an individual logical line.

   When :code-py:`None`, there is no maximum length and the entire
   signature will be displayed on a single logical line.

   This is a domain-specific setting,
   overriding :confval:`maximum_signature_line_length`.

   .. versionadded:: 7.1

.. confval:: c_paren_attributes
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A sequence of strings that the parser should additionally accept
   as attributes with one argument.
   That is, if ``my_align_as`` is in the list,
   then :code-c:`my_align_as(X)` is parsed as an attribute
   for all strings ``X`` that have balanced braces
   (:code-c:`()`, :code-c:`[]`, and :code-c:`{}`).
   For example, this can be used when  :code-c:`#define`
   has been used for attributes, for portability.

   Example:

   .. code-block:: python

      c_paren_attributes = [
          'my_align_as',
      ]

   .. versionadded:: 3.0
   .. versionchanged:: 7.4
      :confval:`!c_paren_attributes` can now be a tuple.


.. _cpp-config:

Options for the C++ domain
--------------------------

.. confval:: cpp_id_attributes
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A sequence of strings that the parser should additionally accept
   as attributes.
   For example, this can be used when  :code-cpp:`#define`
   has been used for attributes, for portability.

   Example:

   .. code-block:: python

      cpp_id_attributes = [
          'my_id_attribute',
      ]

   .. versionadded:: 1.5
   .. versionchanged:: 7.4
      :confval:`!cpp_id_attributes` can now be a tuple.

.. confval:: cpp_index_common_prefix
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A list of prefixes that will be ignored
   when sorting C++ objects in the global index.

   Example:

   .. code-block:: python

      cpp_index_common_prefix = [
          'awesome_lib::',
      ]

   .. versionadded:: 1.5

.. confval:: cpp_maximum_signature_line_length
   :type: :code-py:`int | None`
   :default: :code-py:`None`

   If a signature's length in characters exceeds the number set,
   each parameter within the signature will be displayed on
   an individual logical line.

   When :code-py:`None`, there is no maximum length and the entire
   signature will be displayed on a single logical line.

   This is a domain-specific setting,
   overriding :confval:`maximum_signature_line_length`.

   .. versionadded:: 7.1

.. confval:: cpp_paren_attributes
   :type: :code-py:`Sequence[str]`
   :default: :code-py:`()`

   A sequence of strings that the parser should additionally accept
   as attributes with one argument.
   That is, if ``my_align_as`` is in the list,
   then :code-cpp:`my_align_as(X)` is parsed as an attribute
   for all strings ``X`` that have balanced braces
   (:code-cpp:`()`, :code-cpp:`[]`, and :code-cpp:`{}`).
   For example, this can be used when  :code-cpp:`#define`
   has been used for attributes, for portability.

   Example:

   .. code-block:: python

      cpp_paren_attributes = [
          'my_align_as',
      ]

   .. versionadded:: 1.5
   .. versionchanged:: 7.4
      :confval:`!cpp_paren_attributes` can now be a tuple.


Options for the Javascript domain
---------------------------------

.. confval:: javascript_maximum_signature_line_length
   :type: :code-py:`int | None`
   :default: :code-py:`None`

   If a signature's length in characters exceeds the number set,
   each parameter within the signature will be displayed on
   an individual logical line.

   When :code-py:`None`, there is no maximum length and the entire
   signature will be displayed on a single logical line.

   This is a domain-specific setting,
   overriding :confval:`maximum_signature_line_length`.

   .. versionadded:: 7.1

.. confval:: javascript_trailing_comma_in_multi_line_signatures
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Use a trailing comma in parameter lists spanning multiple lines, if true.

   .. versionadded:: 8.2


Options for the Python domain
-----------------------------

.. confval:: add_module_names
   :type: :code-py:`bool`
   :default: :code-py:`True`

   A boolean that decides whether module names are prepended
   to all :term:`object` names
   (for object types where a "module" of some kind is defined),
   e.g. for :rst:dir:`py:function` directives.

.. confval:: modindex_common_prefix
   :type: :code-py:`list[str]`
   :default: :code-py:`[]`

   A list of prefixes that are ignored for sorting the Python module index
   (e.g., if this is set to :code-py:`['foo.']`,
   then ``foo.bar`` is shown under ``B``, not ``F``).
   This can be handy if you document a project that consists of a
   single package.

   .. caution::
      Works only for the HTML builder currently.

   .. versionadded:: 0.6

.. confval:: python_display_short_literal_types
   :type: :code-py:`bool`
   :default: :code-py:`False`

   This value controls how :py:data:`~typing.Literal` types are displayed.

   Examples
   ~~~~~~~~

   The examples below use the following :rst:dir:`py:function` directive:

   .. code-block:: rst

      .. py:function:: serve_food(item: Literal["egg", "spam", "lobster thermidor"]) -> None

   When :code-py:`False`, :py:data:`~typing.Literal` types display as per standard
   Python syntax, i.e.:

   .. code-block:: python

      serve_food(item: Literal["egg", "spam", "lobster thermidor"]) -> None

   When :code-py:`True`, :py:data:`~typing.Literal` types display with a short,
   :PEP:`604`-inspired syntax, i.e.:

   .. code-block:: python

      serve_food(item: "egg" | "spam" | "lobster thermidor") -> None

   .. versionadded:: 6.2

.. confval:: python_maximum_signature_line_length
   :type: :code-py:`int | None`
   :default: :code-py:`None`

   If a signature's length in characters exceeds the number set,
   each parameter within the signature will be displayed on
   an individual logical line.

   When :code-py:`None`, there is no maximum length and the entire
   signature will be displayed on a single logical line.

   This is a domain-specific setting,
   overriding :confval:`maximum_signature_line_length`.

   For the Python domain, the signature length depends on whether
   the type parameters or the list of arguments are being formatted.
   For the former, the signature length ignores the length of the arguments list;
   for the latter, the signature length ignores the length of
   the type parameters list.

   For instance, with :code-py:`python_maximum_signature_line_length = 20`,
   only the list of type parameters will be wrapped
   while the arguments list will be rendered on a single line

   .. code-block:: rst

      .. py:function:: add[T: VERY_LONG_SUPER_TYPE, U: VERY_LONG_SUPER_TYPE](a: T, b: U)

   .. versionadded:: 7.1

.. confval:: python_trailing_comma_in_multi_line_signatures
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Use a trailing comma in parameter lists spanning multiple lines, if true.

   .. versionadded:: 8.2

.. confval:: python_use_unqualified_type_names
   :type: :code-py:`bool`
   :default: :code-py:`False`

   Suppress the module name of the python reference if it can be resolved.

   .. versionadded:: 4.0

   .. caution::
      This feature is experimental.

.. confval:: trim_doctest_flags
   :type: :code-py:`bool`
   :default: :code-py:`True`

   Remove doctest flags (comments looking like :code-py:`# doctest: FLAG, ...`)
   at the ends of lines and ``<BLANKLINE>`` markers for all code
   blocks showing interactive Python sessions (i.e. doctests).
   See the extension :mod:`~sphinx.ext.doctest` for more
   possibilities of including doctests.

   .. versionadded:: 1.0
   .. versionchanged:: 1.1
      Now also removes ``<BLANKLINE>``.


Extension options
=================

Extensions frequently have their own configuration options.
Those for Sphinx's first-party extensions are documented
in each :doc:`extension's page </usage/extensions/index>`.


Example configuration file
==========================

.. code-block:: python

   # -- Project information -----------------------------------------------------
   # https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

   project = 'Test Project'
   copyright = '2000-2042, The Test Project Authors'
   author = 'The Authors'
   version = release = '4.16'

   # -- General configuration ------------------------------------------------
   # https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

   exclude_patterns = [
       '_build',
       'Thumbs.db',
       '.DS_Store',
   ]
   extensions = []
   language = 'en'
   master_doc = 'index'
   pygments_style = 'sphinx'
   source_suffix = '.rst'
   templates_path = ['_templates']

   # -- Options for HTML output ----------------------------------------------
   # https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

   html_theme = 'alabaster'
   html_static_path = ['_static']
