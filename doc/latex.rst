.. highlightlang:: python

.. _latex:

LaTeX customization
===================

.. module:: latex
   :synopsis: LaTeX specifics.

The *latex* target does not benefit from pre-prepared themes like the
*html* target does (see :doc:`theming`).

.. raw:: latex

   \begingroup
   \sphinxsetup{%
         verbatimwithframe=false,
         VerbatimColor={named}{OldLace},
         TitleColor={named}{DarkGoldenrod},
         hintBorderColor={named}{LightCoral},
         attentionborder=3pt,
         attentionBorderColor={named}{Crimson},
         attentionBgColor={named}{FloralWhite},
         noteborder=2pt,
         noteBorderColor={named}{Olive},
         cautionborder=3pt,
         cautionBorderColor={named}{Cyan},
         cautionBgColor={named}{LightCyan}}
   \relax


Basic customization
-------------------

It is achieved via usage of the
:ref:`latex-options` as described in :doc:`config`. For example::

   # inside conf.py
   latex_engine = 'xelatex'
   latex_elements = {
       'fontpkg': r'''
   \setmainfont{DejaVu Serif}
   \setsansfont{DejaVu Sans}
   \setmonofont{DejaVu Sans Mono}
   ''',
       'preamble': r'''
   \usepackage[titles]{tocloft}
   \cftsetpnumwidth {1.25cm}\cftsetrmarg{1.5cm}
   \setlength{\cftchapnumwidth}{0.75cm}
   \setlength{\cftsecindent}{\cftchapnumwidth}
   \setlength{\cftsecnumwidth}{1.25cm}
   ''',
       'fncychap': r'\usepackage[Bjornstrup]{fncychap}',
       'printindex': r'\footnotesize\raggedright\printindex',
   }
   latex_show_urls = 'footnote'

.. the above was tested on Sphinx's own 1.5a2 documentation with good effect!

.. highlight:: latex

If the size of the ``'preamble'`` contents become inconvenient, one may put
all needed macros into some file :file:`mystyle.tex` of the project source
repertory, and get LaTeX to import it at run time::

   'preamble': r'\input{mystyle.tex}',
   # or, if the \ProvidesPackage LaTeX macro is used in a file mystyle.sty
   'preamble': r'\usepackage{mystyle}',

It is needed to set appropriately :confval:`latex_additional_files`, for
example::

   latex_additional_files = ["mystyle.tex"]

.. _latexsphinxsetup:

The LaTeX style file options
----------------------------

The sphinxsetup interface
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``'sphinxsetup'`` key of :confval:`latex_elements` provides a convenient
interface to the package options of the Sphinx style file::

   latex_elements = {
       'sphinxsetup': 'key1=value1, key2=value2, ...',
   }

- some values may be LaTeX macros, then the backslashes must be
  Python-escaped, or the whole must be a Python raw string,
- LaTeX boolean keys require *lowercase* ``true`` or ``false`` values,
- spaces around the commas and equal signs are ignored, spaces inside LaTeX
  macros may be significant.

If non-empty, it will be passed as argument to the ``\sphinxsetup`` macro
inside the document preamble, like this::

   \usepackage{sphinx}
   \sphinxsetup{key1=value1, key2=value2,...}

.. versionadded:: 1.5

It is possible to insert further uses of the ``\sphinxsetup`` LaTeX macro
directly into the body of the document, via the help of the :rst:dir:`raw`
directive. This is what is done for this documentation, for local styling
of this chapter in the PDF output::

   .. raw:: latex

      \begingroup
      \sphinxsetup{%
            verbatimwithframe=false,
            VerbatimColor={named}{OldLace},
            TitleColor={named}{DarkGoldenrod},
            hintBorderColor={named}{LightCoral},
            attentionborder=3pt,
            attentionBorderColor={named}{Crimson},
            attentionBgColor={named}{FloralWhite},
            noteborder=2pt,
            noteBorderColor={named}{Olive},
            cautionborder=3pt,
            cautionBorderColor={named}{Cyan},
            cautionBgColor={named}{LightCyan}}

at the start of the chapter and::

    .. raw:: latex

       \endgroup

at its end.

.. note::

   The colors above are made available via the ``svgnames`` option of
   the "xcolor" package::

      latex_elements = {
          'passoptionstopackages': r'\PassOptionsToPackage{svgnames}{xcolor}',
      }


The available styling options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. _latexsphinxsetuphmargin:

``hmargin, vmargin``
    The dimensions of the horizontal (resp. vertical) margins, passed as
    ``hmargin`` (resp. ``vmargin``) option to
    the ``geometry`` package. The default is ``1in``, which is equivalent to
    ``{1in,1in}``. Example::

      'sphinxsetup': 'hmargin={2in,1.5in}, vmargin={1.5in,2in}, marginpar=1in',

    Japanese documents currently accept only the one-dimension format for
    these parameters. The ``geometry`` package is then passed suitable options
    to get the text width set to an exact multiple of the *zenkaku* width, and
    the text height set to an integer multiple of the baselineskip, with the
    closest fit for the margins.

    .. hint::

       For Japanese ``'manual'`` docclass with pointsize ``11pt`` or ``12pt``,
       use the ``nomag`` extra document class option (cf.
       ``'extraclassoptions'`` key of :confval:`latex_elements`) or so-called
       TeX "true" units:

         'sphinxsetup': 'hmargin=1.5truein, vmargin=1.5truein, marginpar=5zw',

    .. versionadded:: 1.5.3

``marginpar``
    The ``\marginparwidth`` LaTeX dimension, defaults to ``0.5in``. For Japanese
    documents, the value is modified to be the closest integer multiple of the
    *zenkaku* width.

    .. versionadded:: 1.5.3

``verbatimwithframe``
    default ``true``. Boolean to specify if :rst:dir:`code-block`\ s and literal
    includes are framed. Setting it to ``false`` does not deactivate use of
    package "framed", because it is still in use for the optional background
    colour.

``verbatimwrapslines``
    default ``true``. Tells whether long lines in :rst:dir:`code-block`\ 's
    contents should wrap.

``parsedliteralwraps``
    default ``true``. Tells whether long lines in :dudir:`parsed-literal`\ 's
    contents should wrap.

    .. versionadded:: 1.5.2
       set this option value to ``false`` to recover former behaviour.

``inlineliteralwraps``
    default ``true``. Allows linebreaks inside inline literals: but extra
    potential break-points (additionally to those allowed by LaTeX at spaces
    or for hyphenation) are currently inserted only after the characters
    ``. , ; ? ! /``. Due to TeX internals, white space in the line will be
    stretched (or shrunk) in order to accomodate the linebreak.

    .. versionadded:: 1.5
       set this option value to ``false`` to recover former behaviour.

``verbatimvisiblespace``
    default ``\textcolor{red}{\textvisiblespace}``. When a long code line is
    split, the last space character from the source code line right before the
    linebreak location is typeset using this.

``verbatimcontinued``
    A LaTeX macro inserted at start of continuation code lines. Its
    (complicated...) default typesets a small red hook pointing to the right::

      \makebox[2\fontcharwd\font`\x][r]{\textcolor{red}{\tiny$\hookrightarrow$}}

    .. versionchanged:: 1.5
       The breaking of long code lines was added at 1.4.2. The default
       definition of the continuation symbol was changed at 1.5 to accomodate
       various font sizes (e.g. code-blocks can be in footnotes).

``TitleColor``
    default ``{rgb}{0.126,0.263,0.361}``. The colour for titles (as configured
    via use of package "titlesec".) It must obey the syntax of the
    ``\definecolor`` command. Check the documentation of packages ``color`` or
    ``xcolor``.

``InnerLinkColor``
    default ``{rgb}{0.208,0.374,0.486}``. A colour passed to ``hyperref`` as
    value of ``linkcolor``  and ``citecolor``.

``OuterLinkColor``
    default ``{rgb}{0.216,0.439,0.388}``. A colour passed to ``hyperref`` as
    value of ``filecolor``, ``menucolor``, and ``urlcolor``.

``VerbatimColor``
    default ``{rgb}{1,1,1}``. The background colour for
    :rst:dir:`code-block`\ s. The default is white.

``VerbatimBorderColor``
    default ``{rgb}{0,0,0}``. The frame color, defaults to black.

``verbatimsep``
    default ``\fboxsep``. The separation between code lines and the frame.

``verbatimborder``
    default ``\fboxrule``. The width of the frame around
    :rst:dir:`code-block`\ s.

``shadowsep``
    default ``5pt``. The separation between contents and frame for
    :dudir:`contents` and :dudir:`topic` boxes.

``shadowsize``
    default ``4pt``. The width of the lateral "shadow" to the right.

``shadowrule``
    default ``\fboxrule``. The width of the frame around :dudir:`topic` boxes.

``noteBorderColor``
    default ``{rgb}{0,0,0}``. The colour for the two horizontal rules used by
    Sphinx in LaTeX for styling a
    :dudir:`note` admonition. Defaults to black.

    .. note::

       The actual name of the colour as declared to "color" or "xcolor" is
       ``sphinxnoteBorderColor``. The same "sphinx" prefix applies to all
       colours for notices and admonitions.

``hintBorderColor``
    default ``{rgb}{0,0,0}``. id.

``importantBorderColor``
    default ``{rgb}{0,0,0}``. id.

``tipBorderColor``
    default ``{rgb}{0,0,0}``. id.

``noteborder``
    default ``0.5pt``. The width of the two horizontal rules.

``hintborder``
    default ``0.5pt``. id.

``importantborder``
    default ``0.5pt``. id.

``tipborder``
    default ``0.5pt``. id.

``warningBorderColor``
    default ``{rgb}{0,0,0}``. The colour of the frame for :dudir:`warning` type
    admonitions. Defaults to black.

``cautionBorderColor``
    default ``{rgb}{0,0,0}``. id.

``attentionBorderColor``
    default ``{rgb}{0,0,0}``. id.

``dangerBorderColor``
    default ``{rgb}{0,0,0}``. id.

``errorBorderColor``
    default ``{rgb}{0,0,0}``. id.

``warningBgColor``
    default ``{rgb}{1,1,1}``. The background colour for :dudir:`warning` type
    admonition, defaults to white.

``cautionBgColor``
    default ``{rgb}{1,1,1}``. id.

``attentionBgColor``
    default ``{rgb}{1,1,1}``. id.

``dangerBgColor``
    default ``{rgb}{1,1,1}``. id.

``errorBgColor``
    default ``{rgb}{1,1,1}``. id.

``warningborder``
    default ``1pt``. The width of the frame.

``cautionborder``
    default ``1pt``. id.

``attentionborder``
    default ``1pt``. id.

``dangerborder``
    default ``1pt``. id.

``errorborder``
    default ``1pt``. id.

``AtStartFootnote``
    default ``\mbox{ }``. LaTeX macros inserted at the start of the footnote
    text at bottom of page, after the footnote number.

``BeforeFootnote``
    default ``\leavevmode\unskip``. LaTeX macros inserted before the footnote
    mark. The default removes possible space before it (else, TeX could insert
    a linebreak there).

    .. versionadded:: 1.5

``HeaderFamily``
    default ``\sffamily\bfseries``. Sets the font used by headings.

LaTeX macros and environments
-----------------------------

Here are some macros from the package file :file:`sphinx.sty` and class files
:file:`sphinxhowto.cls`, :file:`sphinxmanual.cls`, which have public names
thus allowing redefinitions. Check the respective files for the defaults.

Macros
~~~~~~

- text styling commands ``\sphinx<foo>`` with ``<foo>`` being one of
  ``strong``, ``bfcode``, ``email``, ``tablecontinued``, ``titleref``,
  ``menuselection``, ``accelerator``, ``crossref``, ``termref``, ``optional``.
  The non-prefixed macros will still be defined if option
  :confval:`latex_keep_old_macro_names` has been set to ``True`` (default is
  ``False``), in which case the prefixed macros expand to the non-prefixed
  ones.

  .. versionadded:: 1.4.5
     Use of ``\sphinx`` prefixed macro names to limit possibilities of conflict
     with LaTeX packages.
  .. versionchanged:: 1.6
     The default value of :confval:`latex_keep_old_macro_names` changes to
     ``False``, and even if set to ``True``, if a non-prefixed macro
     already exists at ``sphinx.sty`` loading time, only the ``\sphinx``
     prefixed one will be defined. The setting will be removed at 1.7.

- more text styling: ``\sphinxstyle<bar>`` with ``<bar>`` one of
  ``indexentry``, ``indexextra``, ``indexpageref``, ``topictitle``,
  ``sidebartitle``, ``othertitle``, ``sidebarsubtitle``, ``thead``,
  ``theadfamily``, ``emphasis``, ``literalemphasis``, ``strong``,
  ``literalstrong``, ``abbreviation``, ``literalintitle``.

  .. versionadded:: 1.5
     these macros were formerly hard-coded as non customizable ``\texttt``,
     ``\emph``, etc...
  .. versionadded:: 1.6
     ``\sphinxstyletheadfamily`` which defaults to ``\sffamily`` and allows
     multiple paragraphs in header cells of tables.
  .. deprecated:: 1.6
     macro ``\sphinxstylethead`` is deprecated at 1.6 and will be removed at 1.7.
- by default the Sphinx style file ``sphinx.sty`` executes the command
  ``\fvset{fontsize=\small}`` as part of its configuration of
  ``fancyvrb.sty``. This may be overriden for example via
  ``\fvset{fontsize=auto}`` which will let code listings use the ambient font
  size. Refer to ``fancyvrb.sty``'s documentation for further keys.

  .. versionadded:: 1.5
- the table of contents is typeset via ``\sphinxtableofcontents`` which is a
  wrapper (whose definition can be found in :file:`sphinxhowto.cls` or in
  :file:`sphinxmanual.cls`) of standard ``\tableofcontents``.

  .. versionchanged:: 1.5
     formerly, the meaning of ``\tableofcontents`` was modified by Sphinx.
- the ``\maketitle`` command is redefined by the class files
  :file:`sphinxmanual.cls` and :file:`sphinxhowto.cls`.

Environments
~~~~~~~~~~~~

- a :dudir:`figure` may have an optional legend with arbitrary body
  elements: they are rendered in a ``sphinxlegend`` environment. The default
  definition issues ``\small``, and ends with ``\par``.

  .. versionadded:: 1.5.6
     formerly, the ``\small`` was hardcoded in LaTeX writer and the ending
     ``\par`` was lacking.
- for each admonition type ``<foo>``, the
  used environment is named ``sphinx<foo>``. They may be ``\renewenvironment``
  'd individually, and must then be defined with one argument (it is the heading
  of the notice, for example ``Warning:`` for :dudir:`warning` directive, if
  English is the document language). Their default definitions use either the
  *sphinxheavybox* (for the first listed directives) or the *sphinxlightbox*
  environments, configured to use the parameters (colours, border thickness)
  specific to each type, which can be set via ``'sphinxsetup'`` string.

  .. versionchanged:: 1.5
     use of public environment names, separate customizability of the
     parameters, such as ``noteBorderColor``, ``noteborder``,
     ``warningBgColor``, ``warningBorderColor``, ``warningborder``, ...
- the :dudir:`contents` directive (with ``:local:`` option) and the
  :dudir:`topic` directive are implemented by environment ``sphinxShadowBox``.

  .. versionadded:: 1.4.2
     former code refactored into an environment allowing page breaks.
  .. versionchanged:: 1.5
     options ``shadowsep``, ``shadowsize``,  ``shadowrule``.
- the literal blocks (via ``::`` or :rst:dir:`code-block`), are
  implemented using ``sphinxVerbatim`` environment which is a wrapper of
  ``Verbatim`` environment from package ``fancyvrb.sty``. It adds the handling
  of the top caption and the wrapping of long lines, and a frame which allows
  pagebreaks. Inside tables the used
  environment is ``sphinxVerbatimintable`` (it does not draw a frame, but
  allows a caption).

  .. versionchanged:: 1.5
     ``Verbatim`` keeps exact same meaning as in ``fancyvrb.sty`` (also
     under the name ``OriginalVerbatim``); ``sphinxVerbatimintable`` is used
     inside tables.
  .. versionadded:: 1.5
     options ``verbatimwithframe``, ``verbatimwrapslines``,
     ``verbatimsep``, ``verbatimborder``.
- the bibliography and Python Module index are typeset respectively within
  environments ``sphinxthebibliography`` and ``sphinxtheindex``, which are
  simple wrappers of the non-modified ``thebibliography`` and ``theindex``
  environments.

  .. versionchanged:: 1.5
     formerly, the original environments were modified by Sphinx.

Miscellany
~~~~~~~~~~

- the section, subsection, ...  headings are set using  *titlesec*'s
  ``\titleformat`` command.
- for the ``'manual'`` docclass, the chapter headings can be customized using
  *fncychap*'s commands ``\ChNameVar``, ``\ChNumVar``, ``\ChTitleVar``. File
  :file:`sphinx.sty` has custom re-definitions in case of *fncychap*
  option ``Bjarne``.

  .. versionchanged:: 1.5
     formerly, use of *fncychap* with other styles than ``Bjarne`` was
     dysfunctional.
- check file :file:`sphinx.sty` for more...

.. hint::

   As an experimental feature, Sphinx can use user-defined template file for
   LaTeX source if you have a file named ``_templates/latex.tex_t`` in your
   project.

   .. versionadded:: 1.5
      currently all template variables are unstable and undocumented.

   Additional files ``longtable.tex_t``, ``tabulary.tex_t`` and
   ``tabular.tex_t`` can be added to ``_templates/`` to configure some aspects
   of table rendering (such as the caption position).

   .. versionadded:: 1.6
      currently all template variables are unstable and undocumented.

.. raw:: latex

   \endgroup
