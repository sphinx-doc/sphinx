.. highlightlang:: python

.. _latex:

LaTeX customization
===================

.. module:: latex
   :synopsis: LaTeX specifics.

For details of the LaTeX/PDF builder command line invocation, refer to
:py:class:`~sphinx.builders.latex.LaTeXBuilder`.

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

.. _latex-basic:

Basic customization
-------------------

The *latex* target does not benefit from prepared themes.

Basic customization is obtained via usage of the :ref:`latex-options`. For
example::

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

If the size of the ``'preamble'`` contents becomes inconvenient, one may move
all needed macros into some file :file:`mystyle.tex.txt` of the project source
repertory, and get LaTeX to import it at run time::

   'preamble': r'\input{mystyle.tex.txt}',
   # or, if the \ProvidesPackage LaTeX macro is used in a file mystyle.sty
   'preamble': r'\usepackage{mystyle}',

It is then needed to set appropriately :confval:`latex_additional_files`, for
example::

   latex_additional_files = ["mystyle.sty"]

.. _latexsphinxsetup:

The LaTeX style file options
----------------------------

Additional customization is possible via LaTeX options of the Sphinx style
file.

The sphinxsetup interface
~~~~~~~~~~~~~~~~~~~~~~~~~

The ``'sphinxsetup'`` key of :confval:`latex_elements` provides a convenient
interface::

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

.. hint::

   It is possible to insert further uses of the ``\sphinxsetup`` LaTeX macro
   directly into the body of the document, via the help of the :rst:dir:`raw`
   directive.  Here is how this present chapter in PDF is styled::

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

   The colors used in the above are provided by the ``svgnames`` option of the
   "xcolor" package::

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
       TeX "true" units::

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

``literalblockcappos``
    default ``t`` for "top". Decides the caption position. Alternative is
    ``b`` ("bottom").

    .. versionadded:: 1.7

``verbatimhintsturnover``
    default ``true``. If ``true``, code-blocks display "continued on next
    page", "continued from previous page" hints in case of pagebreaks.

    .. versionadded:: 1.6.3
    .. versionchanged:: 1.7
       the default changed from ``false`` to ``true``.

``verbatimcontinuedalign``, ``verbatimcontinuesalign``
    default ``c``. Horizontal position relative to the framed contents:
    either ``l`` (left aligned), ``r`` (right aligned) or ``c`` (centered).

    .. versionadded:: 1.7

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
    via use of package "titlesec".)

.. warning::

   Colours set via ``'sphinxsetup'``  must obey the syntax of the
   argument of the ``color/xcolor`` packages ``\definecolor`` command.

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

``VerbatimHighlightColor``
    default ``{rgb}{0.878,1,1}``. The color for highlighted lines.

    .. versionadded:: 1.6.6

.. note::

   Starting with this colour key, and for all others coming next, the actual
   names declared to "color" or "xcolor" are prefixed with "sphinx".

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

|notebdcolors|
    default ``{rgb}{0,0,0}`` (black). The colour for the two horizontal rules
    used by Sphinx in LaTeX for styling a :dudir:`note` type admonition.

``noteborder``, ``hintborder``, ``importantborder``, ``tipborder``
    default ``0.5pt``. The width of the two horizontal rules.

.. only:: not latex

   |warningbdcolors|
       default ``{rgb}{0,0,0}`` (black). The colour for the admonition frame.

.. only:: latex

   |wgbdcolorslatex|
       default ``{rgb}{0,0,0}`` (black). The colour for the admonition frame.

|warningbgcolors|
    default ``{rgb}{1,1,1}`` (white). The background colours for the respective
    admonitions.

|warningborders|
    default ``1pt``. The width of the frame.

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


.. |notebdcolors| replace:: ``noteBorderColor``, ``hintBorderColor``,
                            ``importantBorderColor``, ``tipBorderColor``

.. |warningbdcolors| replace:: ``warningBorderColor``, ``cautionBorderColor``,
                               ``attentionBorderColor``, ``dangerBorderColor``,
                               ``errorBorderColor``

.. |wgbdcolorslatex| replace:: ``warningBorderColor``, ``cautionBorderColor``,
                               ``attentionB..C..``, ``dangerB..C..``,
                               ``errorB..C..``

.. else latex goes into right margin, as it does not hyphenate the names

.. |warningbgcolors| replace:: ``warningBgColor``, ``cautionBgColor``,
                               ``attentionBgColor``, ``dangerBgColor``,
                               ``errorBgColor``

.. |warningborders| replace:: ``warningBorder``, ``cautionBorder``,
                              ``attentionBorder``, ``dangerBorder``,
                              ``errorBorder``

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

  .. versionadded:: 1.4.5
     Use of ``\sphinx`` prefixed macro names to limit possibilities of conflict
     with LaTeX packages.
- more text styling: ``\sphinxstyle<bar>`` with ``<bar>`` one of
  ``indexentry``, ``indexextra``, ``indexpageref``, ``topictitle``,
  ``sidebartitle``, ``othertitle``, ``sidebarsubtitle``, ``theadfamily``,
  ``emphasis``, ``literalemphasis``, ``strong``, ``literalstrong``,
  ``abbreviation``, ``literalintitle``, ``codecontinued``, ``codecontinues``

  .. versionadded:: 1.5
     these macros were formerly hard-coded as non customizable ``\texttt``,
     ``\emph``, etc...
  .. versionadded:: 1.6
     ``\sphinxstyletheadfamily`` which defaults to ``\sffamily`` and allows
     multiple paragraphs in header cells of tables.
  .. versionadded:: 1.6.3
     ``\sphinxstylecodecontinued`` and ``\sphinxstylecodecontinues``.
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
  .. versionadded:: 1.6.6
     support for ``:emphasize-lines:`` option
  .. versionadded:: 1.6.6
     easier customizability of the formatting via exposed to user LaTeX macros
     such as ``\sphinxVerbatimHighlightLine``.
- the bibliography uses ``sphinxthebibliography`` and the Python Module index
  as well as the general index both use ``sphinxtheindex``; these environments
  are wrappers of the ``thebibliography`` and respectively ``theindex``
  environments as provided by the document class (or packages).

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
