.. highlight:: python

.. _latex:

LaTeX customization
===================

.. module:: latex
   :synopsis: LaTeX specifics.

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

The *latex* target does not benefit from prepared themes.

The :ref:`latex-options`, and particularly among them the
:ref:`latex_elements <latex_elements_confval>` variable
provides much of the interface for customization.

For some details of the LaTeX/PDF builder command line
invocation, refer to :py:class:`~sphinx.builders.latex.LaTeXBuilder`.

.. _latex-basic:

Example
-------

Keep in mind that backslashes must be doubled in Python string literals to
avoid interpretation as escape sequences, or use raw strings (as is done here).

::

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

.. highlight:: latex

.. _latex_elements_confval:

The latex_elements configuration setting
----------------------------------------

A dictionary that contains LaTeX snippets overriding those Sphinx usually puts
into the generated ``.tex`` files.  Its ``'sphinxsetup'`` key is described
:ref:`separately <latexsphinxsetup>`.

* Keys that you may want to override include:

  ``'papersize'``
     Paper size option of the document class (``'a4paper'`` or
     ``'letterpaper'``), default ``'letterpaper'``.

  ``'pointsize'``
     Point size option of the document class (``'10pt'``, ``'11pt'`` or
     ``'12pt'``), default ``'10pt'``.

  ``'pxunit'``
     the value of the ``px`` when used in image attributes ``width`` and
     ``height``. The default value is ``'0.75bp'`` which achieves
     ``96px=1in`` (in TeX ``1in = 72bp = 72.27pt``.) To obtain for
     example ``100px=1in`` use ``'0.01in'`` or ``'0.7227pt'`` (the latter
     leads to TeX computing a more precise value, due to the smaller unit
     used in the specification); for ``72px=1in``, simply use ``'1bp'``; for
     ``90px=1in``, use ``'0.8bp'`` or ``'0.803pt'``.

     .. versionadded:: 1.5

  ``'passoptionstopackages'``
     A string which will be positioned early in the preamble, designed to
     contain ``\\PassOptionsToPackage{options}{foo}`` commands. Default empty.

     .. versionadded:: 1.4

  ``'babel'``
     "babel" package inclusion, default ``'\\usepackage{babel}'`` (the
     suitable document language string is passed as class option, and
     ``english`` is used if no language.) For Japanese documents, the
     default is the empty string.

     With XeLaTeX and LuaLaTeX, Sphinx configures the LaTeX document to use
     `polyglossia`_, but one should be aware that current `babel`_ has
     improved its support for Unicode engines in recent years and for some
     languages it may make sense to prefer ``babel`` over ``polyglossia``.

     .. hint::

        After modifiying a core LaTeX key like this one, clean up the LaTeX
        build repertory before next PDF build, else left-over auxiliary
        files are likely to break the build.

     .. _`polyglossia`: https://ctan.org/pkg/polyglossia
     .. _`babel`: https://ctan.org/pkg/babel

     .. versionchanged:: 1.5
        For :confval:`latex_engine` set to ``'xelatex'``, the default
        is ``'\\usepackage{polyglossia}\n\\setmainlanguage{<language>}'``.
     .. versionchanged:: 1.6
        ``'lualatex'`` uses same default setting as ``'xelatex'``
     .. versionchanged:: 1.7.6
        For French, ``xelatex`` and ``lualatex`` default to using
        ``babel``, not ``polyglossia``.

  ``'fontpkg'``
     Font package inclusion, the default is ``'\\usepackage{times}'`` which
     uses Times for text, Helvetica for sans serif and Courier for monospace.

     .. versionchanged:: 1.2
        Defaults to ``''`` when the :confval:`language` uses the Cyrillic
        script.
     .. versionchanged:: 2.0
        Support for individual Greek and Cyrillic letters:

        - In order to support occasional Cyrillic (физика частиц)
          or Greek letters (Σωματιδιακή φυσική) in
          a document whose language is English or a  Latin European
          one, the default set-up is enhanced (only for ``'pdflatex'``
          engine) to do:

          .. code-block:: latex

             \substitutefont{LGR}{\rmdefault}{cmr}
             \substitutefont{LGR}{\sfdefault}{cmss}
             \substitutefont{LGR}{\ttdefault}{cmtt}
             \substitutefont{X2}{\rmdefault}{cmr}
             \substitutefont{X2}{\sfdefault}{cmss}
             \substitutefont{X2}{\ttdefault}{cmtt}

          but this is activated only under the condition that the
          ``'fontenc'`` key is configured to load the ``LGR`` (Greek)
          and/or ``X2`` (Cyrillic) pdflatex-font encodings (if the
          :confval:`language` is set to a Cyrillic language, this
          ``'fontpkg'`` key must be used as "times" package has no direct
          support for it; then keep only ``LGR`` lines from the above,
          if support is needed for Greek in the text).

          The ``\substitutefont`` command is from the eponymous LaTeX
          package, which is loaded by Sphinx if needed (on Ubuntu xenial it
          is part of ``texlive-latex-extra`` which is a Sphinx
          requirement).

          Only if the document actually does contain Unicode Greek letters
          (in text) or Cyrillic letters, will the above default set-up
          cause additional requirements for the PDF build.  On Ubuntu
          xenial, ``texlive-lang-greek``, ``texlive-lang-cyrillic``, and
          (with the above choice of fonts) the ``cm-super`` (or
          ``cm-super-minimal``) package.

        - For ``'xelatex'`` and ``'lualatex'``, the default is to
          use the FreeFont family:  this OpenType font family
          supports both Cyrillic and Greek scripts and is available as
          separate Ubuntu xenial package ``fonts-freefont-otf``, it is not
          needed to install the big package ``texlive-fonts-extra``.

        - ``'platex'`` (Japanese documents) engine supports individual
          Cyrillic and Greek letters with no need of extra user set-up.

  ``'fncychap'``
     Inclusion of the "fncychap" package (which makes fancy chapter titles),
     default ``'\\usepackage[Bjarne]{fncychap}'`` for English documentation
     (this option is slightly customized by Sphinx),
     ``'\\usepackage[Sonny]{fncychap}'`` for internationalized docs (because
     the "Bjarne" style uses numbers spelled out in English).  Other
     "fncychap" styles you can try are "Lenny", "Glenn", "Conny", "Rejne" and
     "Bjornstrup".  You can also set this to ``''`` to disable fncychap.

     The default is ``''`` for Japanese documents.

  ``'preamble'``
     Additional preamble content, default empty.  One may move all needed
     macros into some file :file:`mystyle.tex.txt` of the project source
     repertory, and get LaTeX to import it at run time::

       'preamble': r'\input{mystyle.tex.txt}',
       # or, if the \ProvidesPackage LaTeX macro is used in a file mystyle.sty
       'preamble': r'\usepackage{mystyle}',

     It is then needed to set appropriately
     :confval:`latex_additional_files`, for example::

        latex_additional_files = ["mystyle.sty"]


  ``'figure_align'``
     Latex figure float alignment, default 'htbp' (here, top, bottom, page).
     Whenever an image doesn't fit into the current page, it will be
     'floated' into the next page but may be preceded by any other text.
     If you don't like this behavior, use 'H' which will disable floating
     and position figures strictly in the order they appear in the source.

     .. versionadded:: 1.3

  ``'atendofbody'``
     Additional document content (right before the indices), default empty.

     .. versionadded:: 1.5

  ``'footer'``
     Additional footer content (before the indices), default empty.

     .. deprecated:: 1.5
        Use ``'atendofbody'`` key instead.

* Keys that don't need to be overridden unless in special cases are:

  ``'extraclassoptions'``
     The default is the empty string. Example: ``'extraclassoptions':
     'openany'`` will allow chapters (for documents of the ``'manual'``
     type) to start on any page.

     .. versionadded:: 1.2
     .. versionchanged:: 1.6
        Added this documentation.

  ``'maxlistdepth'``
     LaTeX allows by default at most 6 levels for nesting list and
     quote-like environments, with at most 4 enumerated lists, and 4 bullet
     lists. Setting this key for example to ``'10'`` (as a string) will
     allow up to 10 nested levels (of all sorts). Leaving it to the empty
     string means to obey the LaTeX default.

     .. warning::

        - Using this key may prove incompatible with some LaTeX packages
          or special document classes which do their own list customization.

        - The key setting is silently *ignored* if ``\usepackage{enumitem}``
          is executed inside the document preamble. Use then rather the
          dedicated commands of this LaTeX package.

     .. versionadded:: 1.5

  ``'inputenc'``
     "inputenc" package inclusion, defaults to
     ``'\\usepackage[utf8]{inputenc}'`` when using pdflatex.
     Otherwise empty.

     .. versionchanged:: 1.4.3
        Previously ``'\\usepackage[utf8]{inputenc}'`` was used for all
        compilers.

  ``'cmappkg'``
     "cmap" package inclusion, default ``'\\usepackage{cmap}'``.

     .. versionadded:: 1.2

  ``'fontenc'``
     "fontenc" package inclusion, defaults to
     ``'\\usepackage[T1]{fontenc}'``.

     If ``'pdflatex'`` is the :confval:`latex_engine`, one can add ``LGR``
     for support of Greek letters in the document, and also ``X2`` (or
     ``T2A``) for Cyrillic letters, like this:

     .. code-block:: latex

        r'\usepackage[LGR,X2,T1]{fontenc}'

     .. attention::

        Prior to 2.0, Unicode Greek letters were escaped to use LaTeX math
        mark-up.  This is not the case anymore, and the above must be used
        (only in case of ``'pdflatex'`` engine) if the source contains such
        Unicode Greek.

        On Ubuntu xenial, packages ``texlive-lang-greek`` and ``cm-super``
        (for the latter, only if the ``'fontpkg'`` setting is left to its
        default) are needed for ``LGR`` to work.  In place of ``cm-super``
        one can install smaller ``cm-super-minimal``, but it requires the
        LaTeX document to execute ``\usepackage[10pt]{type1ec}`` before
        loading ``fontenc``.  Thus, use this key with this extra at its
        start if needed.

     .. versionchanged:: 1.5
        Defaults to ``'\\usepackage{fontspec}'`` when
        :confval:`latex_engine` is ``'xelatex'``.
     .. versionchanged:: 1.6
        ``'lualatex'`` uses ``fontspec`` per default like ``'xelatex'``.
     .. versionchanged:: 2.0
        ``'lualatex'`` executes
        ``\defaultfontfeatures[\rmfamily,\sffamily]{}`` to disable TeX
        ligatures.
     .. versionchanged:: 2.0
        Detection of ``LGR``, ``T2A``, ``X2`` to trigger support of
        occasional Greek or Cyrillic (``'pdflatex'`` only, as this support
        is provided natively by ``'platex'`` and only requires suitable
        font with ``'xelatex'/'lualatex'``).

  ``'textgreek'``
     The default (``'pdflatex'`` only) is
     ``'\\usepackage{textalpha}'``, but only if ``'fontenc'`` was
     modified by user to include ``LGR`` option.  If not, the key
     value will be forced to be the empty string.

     This is needed for ``pdfLaTeX`` to support Unicode input of Greek
     letters such as φύσις.  Expert users may want to load the ``textalpha``
     package with its option ``normalize-symbols``.

     .. hint::

        Unicode Greek (but no further Unicode symbols) in :rst:dir:`math`
        can be supported by ``'pdflatex'`` from setting this key to
        ``r'\usepackage{textalpha,alphabeta}'``.  Then ``:math:`α``` (U+03B1)
        will render as :math:`\alpha`.  For wider Unicode support in math
        input, see the discussion of :confval:`latex_engine`.

     With ``'platex'`` (Japanese),  ``'xelatex'`` or ``'lualatex'``, this
     key is ignored.

     .. versionadded:: 2.0
  ``'geometry'``
     "geometry" package inclusion, the default definition is:

       ``'\\usepackage{geometry}'``

     with an additional ``[dvipdfm]`` for Japanese documents.
     The Sphinx LaTeX style file executes:

       ``\PassOptionsToPackage{hmargin=1in,vmargin=1in,marginpar=0.5in}{geometry}``

     which can be customized via corresponding :ref:`'sphinxsetup' options
     <latexsphinxsetup>`.

     .. versionadded:: 1.5

     .. versionchanged:: 1.5.2
        ``dvipdfm`` option if :confval:`latex_engine` is ``'platex'``.

     .. versionadded:: 1.5.3
        The :ref:`'sphinxsetup' keys for the margins
        <latexsphinxsetuphmargin>`.

     .. versionchanged:: 1.5.3
        The location in the LaTeX file has been moved to after
        ``\usepackage{sphinx}`` and ``\sphinxsetup{..}``, hence also after
        insertion of ``'fontpkg'`` key. This is in order to handle the paper
        layout options in a special way for Japanese documents: the text
        width will be set to an integer multiple of the *zenkaku* width, and
        the text height to an integer multiple of the baseline. See the
        :ref:`hmargin <latexsphinxsetuphmargin>` documentation for more.

  ``'hyperref'``
     "hyperref" package inclusion; also loads package "hypcap" and issues
     ``\urlstyle{same}``. This is done after :file:`sphinx.sty` file is
     loaded and before executing the contents of ``'preamble'`` key.

     .. attention::

        Loading of packages "hyperref" and "hypcap" is mandatory.

     .. versionadded:: 1.5
        Previously this was done from inside :file:`sphinx.sty`.

  ``'maketitle'``
     "maketitle" call, default ``'\\sphinxmaketitle'``. Override
     if you want to generate a differently styled title page.

     .. hint::

        If the key value is set to
        ``r'\newcommand\sphinxbackoftitlepage{<Extra
        material>}\sphinxmaketitle'``, then ``<Extra material>`` will be
        typeset on back of title page (``'manual'`` docclass only).

     .. versionchanged:: 1.8.3
        Original ``\maketitle`` from document class is not overwritten,
        hence is re-usable as part of some custom setting for this key.
     .. versionadded:: 1.8.3
        ``\sphinxbackoftitlepage`` optional macro.  It can also be defined
        inside ``'preamble'`` key rather than this one.

  ``'releasename'``
     value that prefixes ``'release'`` element on title page, default
     ``'Release'``. As for *title* and *author* used in the tuples of
     :confval:`latex_documents`, it is inserted as LaTeX markup.

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
     ``'\n\n\\bigskip\\hrule\\bigskip\n\n'``.  Override if you want to
     display transitions differently.

     .. versionadded:: 1.2
     .. versionchanged:: 1.6
        Remove unneeded ``{}`` after ``\\hrule``.

  ``'printindex'``
     "printindex" call, the last thing in the file, default
     ``'\\printindex'``.  Override if you want to generate the index
     differently or append some content after the index. For example
     ``'\\footnotesize\\raggedright\\printindex'`` is advisable when the
     index is full of long entries.

  ``'fvset'``
     Customization of ``fancyvrb`` LaTeX package.  Sphinx does by default
     ``'fvset': '\\fvset{fontsize=\\small}'``, to adjust for the large
     character width of the monospace font, used in code-blocks.
     You may need to modify this if you use custom fonts.

     .. versionadded:: 1.8
     .. versionchanged:: 2.0
        Due to new default font choice for ``'xelatex'`` and ``'lualatex'``
        (FreeFont), Sphinx does ``\\fvset{fontsize=\\small}`` also with these
        engines (and not ``\\fvset{fontsize=auto}``).

* Keys that are set by other options and therefore should not be overridden
  are:

  ``'docclass'``
  ``'classoptions'``
  ``'title'``
  ``'release'``
  ``'author'``
  ``'makeindex'``


.. _latexsphinxsetup:

\\'sphinxsetup\\' key
---------------------

The ``'sphinxsetup'`` key of :ref:`latex_elements <latex_elements_confval>`
provides a LaTeX-type customization interface::

   latex_elements = {
       'sphinxsetup': 'key1=value1, key2=value2, ...',
   }

It defaults to empty.  If non-empty, it will be passed as argument to the
``\sphinxsetup`` macro inside the document preamble, like this::

   \usepackage{sphinx}
   \sphinxsetup{key1=value1, key2=value2,...}

.. versionadded:: 1.5

.. hint::

   It is possible to insert further uses of the ``\sphinxsetup`` LaTeX macro
   directly into the body of the document, via the help of the :rst:dir:`raw`
   directive.  Here is how this present chapter is styled in the PDF output::

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


LaTeX boolean keys require *lowercase* ``true`` or ``false`` values.
Spaces around the commas and equal signs are ignored, spaces inside LaTeX
macros may be significant.

``latexlistlabels``
    Defaults to ``false``.  It means that enumerated list items will follow
    the format (alphabetical or numerical) from the source.

    Setting to ``true`` means to let LaTeX decide itself (depending on the
    document class and language, and/or packages) the style of labels (this
    was Sphinx behaviour prior to release 1.8.0).  This may be useful in
    conjunction with some dedicated LaTeX package such as ``enumitem`` to
    configure how enumerated lists are labeled, depending on nesting level.

    .. versionadded:: 2.1.3

.. _latexsphinxsetuphmargin:

``hmargin``, ``vmargin``
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
    default ``r``. Horizontal position relative to the framed contents:
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

.. |warningborders| replace:: ``warningborder``, ``cautionborder``,
                              ``attentionborder``, ``dangerborder``,
                              ``errorborder``

LaTeX macros and environments
-----------------------------

Here are some macros from the package file :file:`sphinx.sty` and class files
:file:`sphinxhowto.cls`, :file:`sphinxmanual.cls`, which have public names
thus allowing redefinitions. Check the respective files for the defaults.

.. _latex-macros:

Macros
~~~~~~

- text styling commands:

  - ``\sphinxstrong``,
  - ``\sphinxbfcode``,
  - ``\sphinxemail``,
  - ``\sphinxtablecontinued``,
  - ``\sphinxtitleref``,
  - ``\sphinxmenuselection``,
  - ``\sphinxaccelerator``,
  - ``\sphinxcrossref``,
  - ``\sphinxtermref``,
  - ``\sphinxoptional``.
 
  .. versionadded:: 1.4.5
     Use of ``\sphinx`` prefixed macro names to limit possibilities of conflict
     with LaTeX packages.
- more text styling:

  - ``\sphinxstyleindexentry``,
  - ``\sphinxstyleindexextra``,
  - ``\sphinxstyleindexpageref``,
  - ``\sphinxstyletopictitle``,
  - ``\sphinxstylesidebartitle``,
  - ``\sphinxstyleothertitle``,
  - ``\sphinxstylesidebarsubtitle``,
  - ``\sphinxstyletheadfamily``,
  - ``\sphinxstyleemphasis``,
  - ``\sphinxstyleliteralemphasis``,
  - ``\sphinxstylestrong``,
  - ``\sphinxstyleliteralstrong``,
  - ``\sphinxstyleabbreviation``,
  - ``\sphinxstyleliteralintitle``,
  - ``\sphinxstylecodecontinued``,
  - ``\sphinxstylecodecontinues``.
 
  .. versionadded:: 1.5
     these macros were formerly hard-coded as non customizable ``\texttt``,
     ``\emph``, etc...
  .. versionadded:: 1.6
     ``\sphinxstyletheadfamily`` which defaults to ``\sffamily`` and allows
     multiple paragraphs in header cells of tables.
  .. versionadded:: 1.6.3
     ``\sphinxstylecodecontinued`` and ``\sphinxstylecodecontinues``.
- ``\sphinxtableofcontents``: it is a
  wrapper (defined differently in :file:`sphinxhowto.cls` and in
  :file:`sphinxmanual.cls`) of standard ``\tableofcontents``.  The macro
  ``\sphinxtableofcontentshook`` is executed during its expansion right before
  ``\tableofcontents`` itself.

  .. versionchanged:: 1.5
     formerly, the meaning of ``\tableofcontents`` was modified by Sphinx.
  .. versionchanged:: 2.0
     hard-coded redefinitions of ``\l@section`` and ``\l@subsection`` formerly
     done during loading of ``'manual'`` docclass are now executed later via
     ``\sphinxtableofcontentshook``.  This macro is also executed by the
     ``'howto'`` docclass, but defaults to empty with it.
- ``\sphinxmaketitle``: it is defined in the class files
  :file:`sphinxmanual.cls` and :file:`sphinxhowto.cls` and is used as
  default setting of ``'maketitle'`` :confval:`latex_elements` key.

  .. versionchanged:: 1.8.3
     formerly, ``\maketitle`` from LaTeX document class was modified by
     Sphinx.
- ``\sphinxbackoftitlepage``: for ``'manual'`` docclass, and if it is
  defined, it gets executed at end of ``\sphinxmaketitle``, before the final
  ``\clearpage``.  Use either the ``'maketitle'`` key or the ``'preamble'`` key
  of :confval:`latex_elements` to add a custom definition of
  ``\sphinxbackoftitlepage``.

  .. versionadded:: 1.8.3
- ``\sphinxcite``: it is a wrapper of standard ``\cite`` for citation
  references.

Environments
~~~~~~~~~~~~

- a :dudir:`figure` may have an optional legend with arbitrary body
  elements: they are rendered in a ``sphinxlegend`` environment. The default
  definition issues ``\small``, and ends with ``\par``.

  .. versionadded:: 1.5.6
     formerly, the ``\small`` was hardcoded in LaTeX writer and the ending
     ``\par`` was lacking.
- environments associated with admonitions:

  - ``sphinxnote``,
  - ``sphinxhint``,
  - ``sphinximportant``,
  - ``sphinxtip``,
  - ``sphinxwarning``,
  - ``sphinxcaution``,
  - ``sphinxattention``,
  - ``sphinxdanger``,
  - ``sphinxerror``.

  They may be ``\renewenvironment``
  'd individually, and must then be defined with one argument (it is the heading
  of the notice, for example ``Warning:`` for :dudir:`warning` directive, if
  English is the document language). Their default definitions use either the
  *sphinxheavybox* (for the last 5 ones) or the *sphinxlightbox*
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
