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

Unlike :ref:`the HTML builders <html-themes>`, the ``latex`` builder does not
benefit from prepared themes. The :ref:`latex-options`, and particularly the
:ref:`latex_elements <latex_elements_confval>` variable, provides much of the
interface for customization. For example:

.. code-block:: python

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

.. note::

   Keep in mind that backslashes must be doubled in Python string literals to
   avoid interpretation as escape sequences. Alternatively, you may use raw
   strings as is done above.

.. _latex_elements_confval:

The ``latex_elements`` configuration setting
--------------------------------------------

A dictionary that contains LaTeX snippets overriding those Sphinx usually puts
into the generated ``.tex`` files.  Its ``'sphinxsetup'`` key is described
:ref:`separately <latexsphinxsetup>`.

Keys that you may want to override include:

``'papersize'``
   Paper size option of the document class (``'a4paper'`` or
   ``'letterpaper'``)

   Default: ``'letterpaper'``

``'pointsize'``
   Point size option of the document class (``'10pt'``, ``'11pt'`` or
   ``'12pt'``)

   Default: ``'10pt'``

``'pxunit'``
   The value of the ``px`` when used in image attributes ``width`` and
   ``height``. The default value is ``'0.75bp'`` which achieves
   ``96px=1in`` (in TeX ``1in = 72bp = 72.27pt``.) To obtain for
   example ``100px=1in`` use ``'0.01in'`` or ``'0.7227pt'`` (the latter
   leads to TeX computing a more precise value, due to the smaller unit
   used in the specification); for ``72px=1in``, simply use ``'1bp'``; for
   ``90px=1in``, use ``'0.8bp'`` or ``'0.803pt'``.

   Default: ``'0.75bp'``

   .. versionadded:: 1.5

``'passoptionstopackages'``
   A string which will be positioned early in the preamble, designed to
   contain ``\\PassOptionsToPackage{options}{foo}`` commands.

   Default: ``''``

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

   .. _`polyglossia`: https://ctan.org/pkg/polyglossia
   .. _`babel`: https://ctan.org/pkg/babel

   .. hint::

      After modifiying a core LaTeX key like this one, clean up the LaTeX
      build repertory before next PDF build, else left-over auxiliary
      files are likely to break the build.

   Default:  ``'\\usepackage{babel}'`` (``''`` for Japanese documents)

   .. versionchanged:: 1.5
      For :confval:`latex_engine` set to ``'xelatex'``, the default
      is ``'\\usepackage{polyglossia}\n\\setmainlanguage{<language>}'``.

   .. versionchanged:: 1.6
      ``'lualatex'`` uses same default setting as ``'xelatex'``

   .. versionchanged:: 1.7.6
      For French, ``xelatex`` and ``lualatex`` default to using
      ``babel``, not ``polyglossia``.

``'fontpkg'``
   Font package inclusion. The default of ``'\\usepackage{times}'`` uses Times
   for text, Helvetica for sans serif and Courier for monospace.

   In order to support occasional Cyrillic (физика частиц) or Greek
   letters (Σωματιδιακή φυσική) in a document whose language is
   English or a Latin European one, the default set-up is enhanced (only for
   ``'pdflatex'`` engine) to do:

   .. code-block:: latex

      \substitutefont{LGR}{\rmdefault}{cmr}
      \substitutefont{LGR}{\sfdefault}{cmss}
      \substitutefont{LGR}{\ttdefault}{cmtt}
      \substitutefont{X2}{\rmdefault}{cmr}
      \substitutefont{X2}{\sfdefault}{cmss}
      \substitutefont{X2}{\ttdefault}{cmtt}

   This is activated only under the condition that the ``'fontenc'`` key is
   configured to load the ``LGR`` (Greek) and/or ``X2`` (Cyrillic)
   pdflatex-font encodings (if the :confval:`language` is set to a Cyrillic
   language, this ``'fontpkg'`` key must be used as "times" package has no
   direct support for it; then keep only ``LGR`` lines from the above, if
   support is needed for Greek in the text).

   The ``\substitutefont`` command is from the eponymous LaTeX package, which
   is loaded by Sphinx if needed (on Ubuntu Xenial it is part of
   ``texlive-latex-extra`` which is a Sphinx requirement).

   Only if the document actually does contain Unicode Greek letters (in text)
   or Cyrillic letters, will the above default set-up cause additional
   requirements for the PDF build. On Ubuntu Xenial, these are the
   ``texlive-lang-greek``, ``texlive-lang-cyrillic``, and (with the above
   choice of fonts) the ``cm-super`` (or ``cm-super-minimal``) packages.

   For ``'xelatex'`` and ``'lualatex'``, the default is to use the FreeFont
   family: this OpenType font family supports both Cyrillic and Greek scripts
   and is available as separate Ubuntu Xenial package ``fonts-freefont-otf``.
   It is not necessary to install the much larger ``texlive-fonts-extra``
   package.

   ``'platex'`` (Japanese documents) engine supports individual Cyrillic and
   Greek letters with no need of extra user set-up.

   Default: ``'\\usepackage{times}'`` (or ``''`` when using a Cyrillic script)

   .. versionchanged:: 1.2
      Defaults to ``''`` when the :confval:`language` uses the Cyrillic
      script.

   .. versionchanged:: 2.0
      Added support for individual Greek and Cyrillic letters:

``'fncychap'``
   Inclusion of the "fncychap" package (which makes fancy chapter titles),
   default ``'\\usepackage[Bjarne]{fncychap}'`` for English documentation
   (this option is slightly customized by Sphinx),
   ``'\\usepackage[Sonny]{fncychap}'`` for internationalized docs (because
   the "Bjarne" style uses numbers spelled out in English).  Other
   "fncychap" styles you can try are "Lenny", "Glenn", "Conny", "Rejne" and
   "Bjornstrup".  You can also set this to ``''`` to disable fncychap.

   Default: ``'\\usepackage[Bjarne]{fncychap}'`` for English documents,
       ``'\\usepackage[Sonny]{fncychap}'`` for internationalized documents, and
       ``''`` for Japanese documents.

``'preamble'``
   Additional preamble content.  One may move all needed macros into some file
   :file:`mystyle.tex.txt` of the project source repertory, and get LaTeX to
   import it at run time::

     'preamble': r'\input{mystyle.tex.txt}',
     # or, if the \ProvidesPackage LaTeX macro is used in a file mystyle.sty
     'preamble': r'\usepackage{mystyle}',

   It is then needed to set appropriately :confval:`latex_additional_files`,
   for example:

   .. code-block:: python

      latex_additional_files = ["mystyle.sty"]

   Default: ``''``

``'figure_align'``
   Latex figure float alignment. Whenever an image doesn't fit into the current
   page, it will be 'floated' into the next page but may be preceded by any
   other text.  If you don't like this behavior, use 'H' which will disable
   floating and position figures strictly in the order they appear in the
   source.

   Default: ``'htbp'`` (here, top, bottom, page)

   .. versionadded:: 1.3

``'atendofbody'``
   Additional document content (right before the indices).

   Default: ``''``

   .. versionadded:: 1.5

``'extrapackages'``
   Additional LaTeX packages.  For example:

   .. code-block:: python

       latex_elements = {
           'packages': r'\usepackage{isodate}'
       }

   The specified LaTeX packages will be loaded before
   hyperref package and packages loaded from Sphinx extensions.

   .. hint::
      If you'd like to load additional LaTeX packages after hyperref, use
      ``'preamble'`` key instead.

   Default: ``''``

   .. versionadded:: 2.3

``'footer'``
   Additional footer content (before the indices).

   Default: ``''``

   .. deprecated:: 1.5
      Use ``'atendofbody'`` key instead.

Keys that don't need to be overridden unless in special cases are:

``'extraclassoptions'``
   The default is the empty string. Example: ``'extraclassoptions':
   'openany'`` will allow chapters (for documents of the ``'manual'``
   type) to start on any page.

   Default: ``''``

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

   Default: ``6``

   .. versionadded:: 1.5

``'inputenc'``
   "inputenc" package inclusion.

   Default: ``'\\usepackage[utf8]{inputenc}'`` when using pdflatex, else
       ``''``

   .. versionchanged:: 1.4.3
      Previously ``'\\usepackage[utf8]{inputenc}'`` was used for all
      compilers.

``'cmappkg'``
   "cmap" package inclusion.

   Default: ``'\\usepackage{cmap}'``

   .. versionadded:: 1.2

``'fontenc'``
   "fontenc" package inclusion.

   If ``'pdflatex'`` is the :confval:`latex_engine`, one can add ``LGR``
   for support of Greek letters in the document, and also ``X2`` (or
   ``T2A``) for Cyrillic letters, like this:

   .. code-block:: latex

      r'\usepackage[LGR,X2,T1]{fontenc}'

   .. attention::

      If Greek is main language, do not use this key.  Since Sphinx 2.2.1,
      ``xelatex`` will be used automatically as :confval:`latex_engine`.
      Formerly, Sphinx did not support producing PDF via LaTeX with Greek as
      main language.

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

   Default: ``'\\usepackage[T1]{fontenc}'``

   .. versionchanged:: 1.5
      Defaults to ``'\\usepackage{fontspec}'`` when
      :confval:`latex_engine` is ``'xelatex'``.

   .. versionchanged:: 1.6
      ``'lualatex'`` uses ``fontspec`` per default like ``'xelatex'``.

   .. versionchanged:: 2.0
      ``'lualatex'`` executes
      ``\defaultfontfeatures[\rmfamily,\sffamily]{}`` to disable TeX
      ligatures transforming `<<` and `>>` as escaping working with
      ``pdflatex/xelatex`` failed with ``lualatex``.

   .. versionchanged:: 2.0
      Detection of ``LGR``, ``T2A``, ``X2`` to trigger support of
      occasional Greek or Cyrillic (``'pdflatex'`` only, as this support
      is provided natively by ``'platex'`` and only requires suitable
      font with ``'xelatex'/'lualatex'``).

   .. versionchanged:: 2.3.0
      ``'xelatex'`` also executes
      ``\defaultfontfeatures[\rmfamily,\sffamily]{}`` in order to avoid
      contractions of ``--`` into en-dash or transforms of straight quotes
      into curly ones in PDF (in non-literal text paragraphs) despite
      :confval:`smartquotes` being set to ``False``.

``'textgreek'``
   This is needed for ``pdflatex`` to support Unicode input of Greek
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

   Default: ``'\\usepackage{textalpha}'`` or ``''`` if ``fontenc`` does not
       include the ``LGR`` option.

   .. versionadded:: 2.0

``'geometry'``
   "geometry" package inclusion, the default definition is:

     ``'\\usepackage{geometry}'``

   with an additional ``[dvipdfm]`` for Japanese documents.
   The Sphinx LaTeX style file executes:

     ``\PassOptionsToPackage{hmargin=1in,vmargin=1in,marginpar=0.5in}{geometry}``

   which can be customized via corresponding :ref:`'sphinxsetup' options
   <latexsphinxsetup>`.

   Default: ``'\\usepackage{geometry}'`` (or
       ``'\\usepackage[dvipdfm]{geometry}'`` for Japanese documents)

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
   "maketitle" call. Override if you want to generate a differently styled
   title page.

   .. hint::

      If the key value is set to
      ``r'\newcommand\sphinxbackoftitlepage{<Extra
      material>}\sphinxmaketitle'``, then ``<Extra material>`` will be
      typeset on back of title page (``'manual'`` docclass only).

   Default: ``'\\sphinxmaketitle'``

   .. versionchanged:: 1.8.3
      Original ``\maketitle`` from document class is not overwritten,
      hence is re-usable as part of some custom setting for this key.

   .. versionadded:: 1.8.3
      ``\sphinxbackoftitlepage`` optional macro.  It can also be defined
      inside ``'preamble'`` key rather than this one.

``'releasename'``
   Value that prefixes ``'release'`` element on title page.  As for *title* and
   *author* used in the tuples of :confval:`latex_documents`, it is inserted as
   LaTeX markup.

   Default: ``'Release'``

``'tableofcontents'``
   "tableofcontents" call. The default of ``'\\sphinxtableofcontents'`` is a
   wrapper of unmodified ``\tableofcontents``, which may itself be customized
   by user loaded packages. Override if you want to generate a different table
   of contents or put content between the title page and the TOC.

   Default: ``'\\sphinxtableofcontents'``

   .. versionchanged:: 1.5
      Previously the meaning of ``\tableofcontents`` itself was modified
      by Sphinx. This created an incompatibility with dedicated packages
      modifying it also such as "tocloft" or "etoc".

``'transition'``
   Commands used to display transitions. Override if you want to display
   transitions differently.

   Default: ``'\n\n\\bigskip\\hrule\\bigskip\n\n'``

   .. versionadded:: 1.2

   .. versionchanged:: 1.6
      Remove unneeded ``{}`` after ``\\hrule``.

``'printindex'``
   "printindex" call, the last thing in the file. Override if you want to
   generate the index differently or append some content after the index. For
   example ``'\\footnotesize\\raggedright\\printindex'`` is advisable when the
   index is full of long entries.

   Default: ``'\\printindex'``

``'fvset'``
   Customization of ``fancyvrb`` LaTeX package. The default value of
   ``'\\fvset{fontsize=\\small}'`` is used to adjust for the large character
   width of the monospace font, used in code-blocks.  You may need to modify
   this if you use custom fonts.

   Default: ``'\\fvset{fontsize=\\small}'``

   .. versionadded:: 1.8

   .. versionchanged:: 2.0
      Due to new default font choice for ``'xelatex'`` and ``'lualatex'``
      (FreeFont), Sphinx does ``\\fvset{fontsize=\\small}`` also with these
      engines (and not ``\\fvset{fontsize=auto}``).

Keys that are set by other options and therefore should not be overridden are:

``'docclass'``
``'classoptions'``
``'title'``
``'release'``
``'author'``
``'makeindex'``


.. _latexsphinxsetup:

The ``sphinxsetup`` configuration setting
-----------------------------------------

.. versionadded:: 1.5

The ``'sphinxsetup'`` key of :ref:`latex_elements <latex_elements_confval>`
provides a LaTeX-type customization interface::

   latex_elements = {
       'sphinxsetup': 'key1=value1, key2=value2, ...',
   }

It defaults to empty.  If non-empty, it will be passed as argument to the
``\sphinxsetup`` macro inside the document preamble, like this::

   \usepackage{sphinx}
   \sphinxsetup{key1=value1, key2=value2,...}

The colors used in the above are provided by the ``svgnames`` option of the
"xcolor" package::

   latex_elements = {
       'passoptionstopackages': r'\PassOptionsToPackage{svgnames}{xcolor}',
   }

It is possible to insert further uses of the ``\sphinxsetup`` LaTeX macro
directly into the body of the document, via the help of the :rst:dir:`raw`
directive. This chapter is styled in the PDF output using the following at the
start of the chaper::

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

The below is included at the end of the chapter::

  .. raw:: latex

     \endgroup

LaTeX boolean keys require *lowercase* ``true`` or ``false`` values.
Spaces around the commas and equal signs are ignored, spaces inside LaTeX
macros may be significant.

.. _latexsphinxsetuphmargin:

``hmargin, vmargin``
    The dimensions of the horizontal (resp. vertical) margins, passed as
    ``hmargin`` (resp. ``vmargin``) option to the ``geometry`` package.
    Example::

      'sphinxsetup': 'hmargin={2in,1.5in}, vmargin={1.5in,2in}, marginpar=1in',

    Japanese documents currently accept only the one-dimension format for
    these parameters. The ``geometry`` package is then passed suitable options
    to get the text width set to an exact multiple of the *zenkaku* width, and
    the text height set to an integer multiple of the baselineskip, with the
    closest fit for the margins.

    Default: ``1in`` (equivalent to ``{1in,1in}``)

    .. hint::

       For Japanese ``'manual'`` docclass with pointsize ``11pt`` or ``12pt``,
       use the ``nomag`` extra document class option (cf.
       ``'extraclassoptions'`` key of :confval:`latex_elements`) or so-called
       TeX "true" units::

         'sphinxsetup': 'hmargin=1.5truein, vmargin=1.5truein, marginpar=5zw',

    .. versionadded:: 1.5.3

``marginpar``
    The ``\marginparwidth`` LaTeX dimension. For Japanese documents, the value
    is modified to be the closest integer multiple of the *zenkaku* width.

    Default: ``0.5in``

    .. versionadded:: 1.5.3

``verbatimwithframe``
    Boolean to specify if :rst:dir:`code-block`\ s and literal includes are
    framed. Setting it to ``false`` does not deactivate use of package
    "framed", because it is still in use for the optional background colour.

    Default: ``true``.

``verbatimwrapslines``
    Boolean to specify if long lines in :rst:dir:`code-block`\ 's contents are
    wrapped.

    Default: ``true``

``literalblockcappos``
    Decides the caption position: either ``b`` ("bottom") or ``t`` ("top").

    Default: ``t``

    .. versionadded:: 1.7

``verbatimhintsturnover``
    Boolean to specify if code-blocks display "continued on next page" and
    "continued from previous page" hints in case of pagebreaks.

    Default: ``true``

    .. versionadded:: 1.6.3
    .. versionchanged:: 1.7
       the default changed from ``false`` to ``true``.

``verbatimcontinuedalign``, ``verbatimcontinuesalign``
    Horizontal position relative to the framed contents: either ``l`` (left
    aligned), ``r`` (right aligned) or ``c`` (centered).

    Default: ``r``

    .. versionadded:: 1.7

``parsedliteralwraps``
    Boolean to specify if long lines in :dudir:`parsed-literal`\ 's contents
    should wrap.

    Default: ``true``

    .. versionadded:: 1.5.2
       set this option value to ``false`` to recover former behaviour.

``inlineliteralwraps``
    Boolean to specify if line breaks are allowed inside inline literals: but
    extra potential break-points (additionally to those allowed by LaTeX at
    spaces or for hyphenation) are currently inserted only after the characters
    ``. , ; ? ! /`` and ``\``. Due to TeX internals, white space in the line
    will be stretched (or shrunk) in order to accommodate the linebreak.

    Default: ``true``

    .. versionadded:: 1.5
       set this option value to ``false`` to recover former behaviour.

    .. versionchanged:: 2.3.0
       added potential breakpoint at ``\`` characters.

``verbatimvisiblespace``
    When a long code line is split, the last space character from the source
    code line right before the linebreak location is typeset using this.

    Default: ``\textcolor{red}{\textvisiblespace}``

``verbatimcontinued``
    A LaTeX macro inserted at start of continuation code lines. Its
    (complicated...) default typesets a small red hook pointing to the right::

      \makebox[2\fontcharwd\font`\x][r]{\textcolor{red}{\tiny$\hookrightarrow$}}

    .. versionchanged:: 1.5
       The breaking of long code lines was added at 1.4.2. The default
       definition of the continuation symbol was changed at 1.5 to accomodate
       various font sizes (e.g. code-blocks can be in footnotes).

``TitleColor``
    The colour for titles (as configured via use of package "titlesec".)

    Default: ``{rgb}{0.126,0.263,0.361}``

.. warning::

   Colours set via ``'sphinxsetup'``  must obey the syntax of the
   argument of the ``color/xcolor`` packages ``\definecolor`` command.

``InnerLinkColor``
    A colour passed to ``hyperref`` as value of ``linkcolor``  and
    ``citecolor``.

    Default: ``{rgb}{0.208,0.374,0.486}``.

``OuterLinkColor``
    A colour passed to ``hyperref`` as value of ``filecolor``, ``menucolor``,
    and ``urlcolor``.

    Default: ``{rgb}{0.216,0.439,0.388}``

``VerbatimColor``
    The background colour for :rst:dir:`code-block`\ s.

    Default: ``{rgb}{1,1,1}`` (white)

``VerbatimBorderColor``
    The frame color.

    Default: ``{rgb}{0,0,0}`` (black)

``VerbatimHighlightColor``
    The color for highlighted lines.

    Default: ``{rgb}{0.878,1,1}``

    .. versionadded:: 1.6.6

.. note::

   Starting with this colour key, and for all others coming next, the actual
   names declared to "color" or "xcolor" are prefixed with "sphinx".

``verbatimsep``
    The separation between code lines and the frame.

    Default: ``\fboxsep``

``verbatimborder``
    The width of the frame around :rst:dir:`code-block`\ s.

    Default: ``\fboxrule``

``shadowsep``
    The separation between contents and frame for :dudir:`contents` and
    :dudir:`topic` boxes.

    Default: ``5pt``

``shadowsize``
    The width of the lateral "shadow" to the right.

    Default: ``4pt``

``shadowrule``
    The width of the frame around :dudir:`topic` boxes.

    Default: ``\fboxrule``

|notebdcolors|
    The colour for the two horizontal rules used by Sphinx in LaTeX for styling
    a :dudir:`note` type admonition.

    Default: ``{rgb}{0,0,0}`` (black)

``noteborder``, ``hintborder``, ``importantborder``, ``tipborder``
    The width of the two horizontal rules.

    Default: ``0.5pt``

.. only:: not latex

   |warningbdcolors|
       The colour for the admonition frame.

       Default: ``{rgb}{0,0,0}`` (black)

.. only:: latex

   |wgbdcolorslatex|
       The colour for the admonition frame.

       Default: ``{rgb}{0,0,0}`` (black)

|warningbgcolors|
    The background colours for the respective admonitions.

    Default: ``{rgb}{1,1,1}`` (white)

|warningborders|
    The width of the frame.

    Default: ``1pt``

``AtStartFootnote``
    LaTeX macros inserted at the start of the footnote text at bottom of page,
    after the footnote number.

    Default: ``\mbox{ }``

``BeforeFootnote``
    LaTeX macros inserted before the footnote mark. The default removes
    possible space before it (else, TeX could insert a line break there).

    Default: ``\leavevmode\unskip``

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

- Text styling commands:

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

- More text styling:

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
     These macros were formerly hard-coded as non customizable ``\texttt``,
     ``\emph``, etc...

  .. versionadded:: 1.6
     ``\sphinxstyletheadfamily`` which defaults to ``\sffamily`` and allows
     multiple paragraphs in header cells of tables.

  .. versionadded:: 1.6.3
     ``\sphinxstylecodecontinued`` and ``\sphinxstylecodecontinues``.

  .. versionadded:: 3.0
     ``\sphinxkeyboard``

- ``\sphinxtableofcontents``: A wrapper (defined differently in
  :file:`sphinxhowto.cls` and in :file:`sphinxmanual.cls`) of standard
  ``\tableofcontents``.  The macro ``\sphinxtableofcontentshook`` is executed
  during its expansion right before ``\tableofcontents`` itself.

  .. versionchanged:: 1.5
     Formerly, the meaning of ``\tableofcontents`` was modified by Sphinx.

  .. versionchanged:: 2.0
     Hard-coded redefinitions of ``\l@section`` and ``\l@subsection`` formerly
     done during loading of ``'manual'`` docclass are now executed later via
     ``\sphinxtableofcontentshook``.  This macro is also executed by the
     ``'howto'`` docclass, but defaults to empty with it.

- ``\sphinxmaketitle``: Used as the default setting of the ``'maketitle'``
  :confval:`latex_elements` key.
  Defined in the class files :file:`sphinxmanual.cls` and
  :file:`sphinxhowto.cls`.

  .. versionchanged:: 1.8.3
     Formerly, ``\maketitle`` from LaTeX document class was modified by
     Sphinx.

- ``\sphinxbackoftitlepage``: For ``'manual'`` docclass, and if it is
  defined, it gets executed at end of ``\sphinxmaketitle``, before the final
  ``\clearpage``.  Use either the ``'maketitle'`` key or the ``'preamble'`` key
  of :confval:`latex_elements` to add a custom definition of
  ``\sphinxbackoftitlepage``.

  .. versionadded:: 1.8.3

- ``\sphinxcite``: A wrapper of standard ``\cite`` for citation references.

Environments
~~~~~~~~~~~~

- A :dudir:`figure` may have an optional legend with arbitrary body
  elements: they are rendered in a ``sphinxlegend`` environment. The default
  definition issues ``\small``, and ends with ``\par``.

  .. versionadded:: 1.5.6
     Formerly, the ``\small`` was hardcoded in LaTeX writer and the ending
     ``\par`` was lacking.

- Environments associated with admonitions:

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
     Use of public environment names, separate customizability of the
     parameters, such as ``noteBorderColor``, ``noteborder``,
     ``warningBgColor``, ``warningBorderColor``, ``warningborder``, ...

- The :dudir:`contents` directive (with ``:local:`` option) and the
  :dudir:`topic` directive are implemented by environment ``sphinxShadowBox``.

  .. versionadded:: 1.4.2
     Former code refactored into an environment allowing page breaks.

  .. versionchanged:: 1.5
     Options ``shadowsep``, ``shadowsize``,  ``shadowrule``.

- The literal blocks (via ``::`` or :rst:dir:`code-block`), are
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
     Options ``verbatimwithframe``, ``verbatimwrapslines``,
     ``verbatimsep``, ``verbatimborder``.

  .. versionadded:: 1.6.6
     Support for ``:emphasize-lines:`` option

  .. versionadded:: 1.6.6
     Easier customizability of the formatting via exposed to user LaTeX macros
     such as ``\sphinxVerbatimHighlightLine``.

- The bibliography uses ``sphinxthebibliography`` and the Python Module index
  as well as the general index both use ``sphinxtheindex``; these environments
  are wrappers of the ``thebibliography`` and respectively ``theindex``
  environments as provided by the document class (or packages).

  .. versionchanged:: 1.5
     Formerly, the original environments were modified by Sphinx.

Miscellany
~~~~~~~~~~

- The section, subsection, ... headings are set using  *titlesec*'s
  ``\titleformat`` command.

- For the ``'manual'`` docclass, the chapter headings can be customized using
  *fncychap*'s commands ``\ChNameVar``, ``\ChNumVar``, ``\ChTitleVar``. File
  :file:`sphinx.sty` has custom re-definitions in case of *fncychap*
  option ``Bjarne``.

  .. versionchanged:: 1.5
     Formerly, use of *fncychap* with other styles than ``Bjarne`` was
     dysfunctional.

.. hint::

   As an experimental feature, Sphinx can use user-defined template file for
   LaTeX source if you have a file named ``_templates/latex.tex_t`` in your
   project.

   Additional files ``longtable.tex_t``, ``tabulary.tex_t`` and
   ``tabular.tex_t`` can be added to ``_templates/`` to configure some aspects
   of table rendering (such as the caption position).

   .. versionadded:: 1.6
      currently all template variables are unstable and undocumented.

.. raw:: latex

   \endgroup
