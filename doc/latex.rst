LaTeX customization
===================

.. module:: latex
   :synopsis: LaTeX specifics.

.. _contents: https://docutils.sourceforge.io/docs/ref/rst/directives.html#table-of-contents

.. raw:: latex

   \begingroup
   \sphinxsetup{%
         TitleColor=DarkGoldenrod,
         pre_border-width=2pt,
         pre_border-right-width=8pt,
         pre_padding=5pt,
         pre_border-radius=5pt,
         pre_background-TeXcolor=OldLace,
         pre_border-TeXcolor=Gold!90,
         pre_box-shadow=6pt 6pt,
         pre_box-shadow-TeXcolor=gray!20,
         %
         div.warning_border-width=3pt,
         div.warning_padding=6pt,
         div.warning_padding-right=18pt,
         div.warning_padding-bottom=18pt,
         div.warning_border-TeXcolor=DarkCyan,
         div.warning_background-TeXcolor=LightCyan,
         div.warning_box-shadow=-12pt -12pt inset,
         div.warning_box-shadow-TeXcolor=Cyan,
         %
         attentionborder=3pt,
         attentionBorderColor=Crimson,
         attentionBgColor=FloralWhite,
         %
         noteborder=1pt,
         noteBorderColor=Olive,
         noteBgColor=Olive!10,
         div.note_border-top-width=0pt,
         div.note_border-bottom-width=0pt,
         hintBorderColor=LightCoral,
   }
   \relax

Unlike :ref:`the HTML builders <html-themes>`, the ``latex`` builder does not
benefit from prepared themes. The :ref:`latex-options`, and particularly the
:ref:`latex_elements <latex_elements_confval>` variable, provides much of the
interface for customization. For example:

.. code-block:: latex

   # inside conf.py
   latex_engine = 'xelatex'
   latex_elements = {
       'passoptionstopackages': r'''
   \PassOptionsToPackage{svgnames}{xcolor}
   ''',
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
       'sphinxsetup': 'TitleColor=DarkGoldenrod',
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
:ref:`separately <latexsphinxsetup>`.  It allows also local configurations
inserted in generated files, via :dudir:`raw` directives.  For example, in
the PDF documentation this chapter is styled especially, as will be described
later.

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

   .. hint::

      It may be also used for loading LaTeX packages very early in the
      preamble.  For example package ``fancybox`` is incompatible with
      being loaded via the ``'preamble'`` key, it must be loaded earlier.

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

      After modifying a core LaTeX key like this one, clean up the LaTeX
      build repertory before next PDF build, else left-over auxiliary
      files are likely to break the build.

   Default:  ``'\\usepackage{babel}'`` (for Japanese documents)

   .. versionchanged:: 1.5
      For :confval:`latex_engine` set to ``'xelatex'``, the default
      is ``'\\usepackage{polyglossia}\n\\setmainlanguage{<language>}'``.

   .. versionchanged:: 1.6
      ``'lualatex'`` uses same default setting as ``'xelatex'``

   .. versionchanged:: 1.7.6
      For French with ``'xelatex'`` (not ``'lualatex'``) the default is to
      use ``babel``, not ``polyglossia``.

   .. versionchanged:: 7.4.0
      For French with ``'lualatex'`` the default is to use ``babel``.

``'fontpkg'``
   Font package inclusion. The default is::

      r"""\usepackage{tgtermes}
      \usepackage{tgheros}
      \renewcommand\ttdefault{txtt}
      """

   For ``'xelatex'`` and ``'lualatex'`` however the default is to use
   the GNU FreeFont.

   .. versionchanged:: 1.2
      Defaults to ``''`` when the :confval:`language` uses the Cyrillic
      script.

   .. versionchanged:: 2.0
      Incorporates some font substitution commands to help support occasional
      Greek or Cyrillic in a document using ``'pdflatex'`` engine.

   .. versionchanged:: 4.0.0

      - The font substitution commands added at ``2.0`` have been moved
        to the ``'fontsubstitution'`` key, as their presence here made
        it complicated for user to customize the value of ``'fontpkg'``.
      - The default font setting has changed: it still uses Times and
        Helvetica clones for serif and sans serif, but via better, more
        complete TeX fonts and associated LaTeX packages.  The
        monospace font has been changed to better match the Times clone.

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

   Do not use ``.tex`` as suffix, else the file is submitted itself to the PDF
   build process, use ``.tex.txt`` or ``.sty`` as in the examples above.

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

   .. code-block:: latex

       latex_elements = {
           'extrapackages': r'\usepackage{isodate}'
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
   ``''``.

   .. note::

      If using ``utf8x`` in place of ``utf8`` it is mandatory to extend the
      LaTeX preamble with suitable ``\PreloadUnicodePage{<number>}`` commands,
      as per the ``utf8x`` documentation (``texdoc ucs`` on a TeXLive based
      TeX installation).  Else, unexpected and possibly hard-to-spot problems
      (i.e. not causing a build crash) may arise in the PDF, in particular
      regarding hyperlinks.

      Even if these precautions are taken, PDF build via ``pdflatex`` engine
      may crash due to upstream LaTeX not being fully compatible with
      ``utf8x``.  For example, in certain circumstances related to
      code-blocks, or attempting to include images whose filenames contain
      Unicode characters.  Indeed, starting in 2015, upstream LaTeX with
      ``pdflatex`` engine has somewhat enhanced native support for Unicode and
      is becoming more and more incompatible with ``utf8x``.  In particular,
      since the October 2019 LaTeX release, filenames can use Unicode
      characters, and even spaces.  At Sphinx level this means e.g. that the
      :dudir:`image` and :dudir:`figure` directives are now compatible with
      such filenames for PDF via LaTeX output.  But this is broken if
      ``utf8x`` is in use.

   .. versionchanged:: 1.4.3
      Previously ``'\\usepackage[utf8]{inputenc}'`` was used for all
      compilers.

``'cmappkg'``
   "cmap" package inclusion.

   Default: ``'\\usepackage{cmap}'``

   .. versionadded:: 1.2

``'fontenc'``
   Customize this from its default ``'\\usepackage[T1]{fontenc}'`` to:

   - ``'\\usepackage[X2,T1]{fontenc}'`` if you need occasional
     Cyrillic letters (физика частиц),

   - ``'\\usepackage[LGR,T1]{fontenc}'`` if you need occasional
     Greek letters (Σωματιδιακή φυσική).

   Use ``[LGR,X2,T1]`` rather if both are needed.

   .. attention::

      - Do not use this key for a :confval:`latex_engine` other than
        ``'pdflatex'``.

      - If Greek is main language, do not use this key.  Since Sphinx 2.2.1,
        ``xelatex`` will be used automatically as :confval:`latex_engine`.

      - The TeX installation may need some extra packages. For example,
        on Ubuntu xenial, packages ``texlive-lang-greek`` and ``cm-super``
        are needed for ``LGR`` to work. And ``texlive-lang-cyrillic`` and
        ``cm-super`` are needed for support of Cyrillic.

   .. versionchanged:: 1.5
      Defaults to ``'\\usepackage{fontspec}'`` when
      :confval:`latex_engine` is ``'xelatex'``.

   .. versionchanged:: 1.6
      ``'lualatex'`` uses ``fontspec`` per default like ``'xelatex'``.

   .. versionchanged:: 2.0
      ``'lualatex'`` executes
      ``\defaultfontfeatures[\rmfamily,\sffamily]{}`` to disable TeX
      ligatures transforming ``<<`` and ``>>`` as escaping working with
      ``pdflatex/xelatex`` failed with ``lualatex``.

   .. versionchanged:: 2.0
      Detection of ``LGR``, ``T2A``, ``X2`` to trigger support of
      occasional Greek or Cyrillic letters (``'pdflatex'``).

   .. versionchanged:: 2.3.0
      ``'xelatex'`` executes
      ``\defaultfontfeatures[\rmfamily,\sffamily]{}`` in order to avoid
      contractions of ``--`` into en-dash or transforms of straight quotes
      into curly ones in PDF (in non-literal text paragraphs) despite
      :confval:`smartquotes` being set to ``False``.

``'fontsubstitution'``
   Ignored if ``'fontenc'`` was not configured to use ``LGR`` or ``X2`` (or
   ``T2A``).  In case ``'fontpkg'`` key is configured for usage with some
   TeX fonts known to be available in the ``LGR`` or ``X2`` encodings, set
   this one to be the empty string.  Else leave to its default.

   Ignored with :confval:`latex_engine` other than ``'pdflatex'``.

   .. versionadded:: 4.0.0

``'textgreek'``
   For the support of occasional Greek letters.

   It is ignored with ``'platex'``, ``'xelatex'`` or ``'lualatex'`` as
   :confval:`latex_engine` and defaults to either the empty string or
   to ``'\\usepackage{textalpha}'`` for ``'pdflatex'`` depending on
   whether the ``'fontenc'`` key was used with ``LGR`` or not.  Only
   expert LaTeX users may want to customize this key.

   It can also be used as ``r'\usepackage{textalpha,alphabeta}'`` to let
   ``'pdflatex'`` support Greek Unicode input in :rst:dir:`math` context.
   For example ``:math:`α``` (U+03B1) will render as :math:`\alpha`.

   Default: ``'\\usepackage{textalpha}'`` or ``''`` if ``fontenc`` does not
   include the ``LGR`` option.

   .. versionadded:: 2.0

``'geometry'``
   "geometry" package inclusion, the default definition is:

   .. code-block:: latex

      '\\usepackage{geometry}'

   with an additional ``[dvipdfm]`` for Japanese documents.
   The Sphinx LaTeX style file executes:

   .. code-block:: latex

      \PassOptionsToPackage{hmargin=1in,vmargin=1in,marginpar=0.5in}{geometry}

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
      hence is reusable as part of some custom setting for this key.

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

``'makeindex'``
   "makeindex" call, the last thing before ``\begin{document}``. With
   ``'\\usepackage[columns=1]{idxlayout}\\makeindex'`` the index will use
   only one column. You may have to install ``idxlayout`` LaTeX package.

   Default: ``'\\makeindex'``

``'printindex'``
   "printindex" call, the last thing in the file. Override if you want to
   generate the index differently, append some content after the index, or
   change the font. As LaTeX uses two-column mode for the index it is
   often advisable to set this key to
   ``'\\footnotesize\\raggedright\\printindex'``. Or, to obtain a one-column
   index, use ``'\\def\\twocolumn[#1]{#1}\\printindex'`` (this trick may fail
   if using a custom document class; then try the ``idxlayout`` approach
   described in the documentation of the ``'makeindex'`` key).

   Default: ``'\\printindex'``

``'fvset'``
   Customization of ``fancyvrb`` LaTeX package.

   The default value is ``'\\fvset{fontsize=auto}'`` which means that the
   font size will adjust correctly if a code-block ends up in a footnote.
   You may need to modify this if you use custom fonts:
   ``'\\fvset{fontsize=\\small}'`` if the monospace font is Courier-like.

   Default: ``'\\fvset{fontsize=auto}'``

   .. versionadded:: 1.8

   .. versionchanged:: 2.0
      For ``'xelatex'`` and ``'lualatex'`` defaults to
      ``'\\fvset{fontsize=\\small}'`` as this
      is adapted to the relative widths of the FreeFont family.

   .. versionchanged:: 4.0.0
      Changed default for ``'pdflatex'``. Previously it was using
      ``'\\fvset{fontsize=\\small}'``.

   .. versionchanged:: 4.1.0
      Changed default for Chinese documents to
      ``'\\fvset{fontsize=\\small,formatcom=\\xeCJKVerbAddon}'``

Keys that are set by other options and therefore should not be overridden are:

``'docclass'``
``'classoptions'``
``'title'``
``'release'``
``'author'``


.. _latexsphinxsetup:

The ``sphinxsetup`` configuration setting
-----------------------------------------

.. versionadded:: 1.5

The ``'sphinxsetup'`` key of :ref:`latex_elements <latex_elements_confval>`
provides a LaTeX-type customization interface::

   latex_elements = {
       'sphinxsetup': 'key1=value1, key2=value2, ...',
   }

LaTeX syntax for boolean keys requires *lowercase* ``true`` or ``false``
e.g ``'sphinxsetup': "verbatimwrapslines=false"``.  If setting a
boolean key to ``true``, ``=true`` is optional.
Spaces around the commas and equal signs are ignored, spaces inside LaTeX
macros may be significant.
Do not use ticks/quotes to enclose string or numerical values.

The ``'sphinxsetup'`` defaults to empty.
If non-empty, it will be passed as argument to the
``\sphinxsetup`` macro inside the document preamble, like this::

   \usepackage{sphinx}
   \sphinxsetup{key1=value1, key2=value2,...}

It is possible to insert uses of the ``\sphinxsetup`` LaTeX macro directly
into the body of the document, via the ``raw`` directive:

.. code-block:: latex

   .. raw:: latex

      \begingroup
      \sphinxsetup{%
         TitleColor=DarkGoldenrod,
         ... more comma separated key=value using LaTeX syntax ...
      }

   All elements here will be under the influence of the raw ``\sphinxsetup``
   settings.

   .. raw:: latex

      \endgroup

   From here on, the raw ``\sphinxsetup`` has no effect anymore.

This is the technique which has been used to style especially the present part
of the documentation for the PDF output.  The actually used options will be
found at top of :file:`doc/latex.rst` at the `development repository`_.

.. _development repository: https://github.com/sphinx-doc/sphinx

The color used in the above example is available from having passed the
``svgnames`` option to the "xcolor" package::

   latex_elements = {
       'passoptionstopackages': r'\PassOptionsToPackage{svgnames}{xcolor}',
   }

``bookmarksdepth``
    Controls the depth of the collapsible bookmarks panel in the PDF.
    May be either a number (e.g. ``3``) or a LaTeX sectioning name (e.g.
    ``subsubsection``, i.e. without backslash).
    For details, refer to the ``hyperref`` LaTeX docs.

    Default: ``5``

    .. versionadded:: 4.0.0

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

``mathnumsep``
    This defaults to the string (without quotes!) as set by
    :confval:`math_numsep` (which itself defaults to ``'.'``).  Use it if
    a different setting is needed for LaTeX output.

    .. versionadded:: 8.1.0

``verbatimwithframe``
    Boolean to specify if :rst:dir:`code-block`\ s and literal includes are
    framed. Setting it to ``false`` does not deactivate use of package
    "framed", because it is still in use for the optional background color.

    Default: ``true``.

``verbatimwrapslines``
    Boolean to specify if long lines in :rst:dir:`code-block`\ 's contents are
    wrapped.

    If ``true``, line breaks may happen at spaces (the last space before the
    line break will be rendered using a special symbol), and at ASCII
    punctuation characters (i.e. not at letters or digits). Whenever a long
    string has no break points, it is moved to next line. If its length is
    longer than the line width it will overflow.

    Default: ``true``

.. _latexsphinxsetupforcewraps:

``verbatimforcewraps``
    Boolean to specify if long lines in :rst:dir:`code-block`\ 's contents
    should be forcefully wrapped to never overflow due to long strings.

    .. note::

       It is assumed that the Pygments_ LaTeXFormatter has not been used with
       its ``texcomments`` or similar options which allow additional
       (arbitrary) LaTeX mark-up.

       Also, in case of :confval:`latex_engine` set to ``'pdflatex'``, only
       the default LaTeX handling of Unicode code points, i.e. ``utf8`` not
       ``utf8x`` is allowed.

    .. _Pygments: https://pygments.org/

    Default: ``false``

    .. versionadded:: 3.5.0

``verbatimmaxoverfull``
    A number. If an unbreakable long string has length larger than the total
    linewidth plus this number of characters, and if ``verbatimforcewraps``
    mode is on, the input line will be reset using the forceful algorithm
    which applies breakpoints at each character.

    Default: ``3``

    .. versionadded:: 3.5.0

``verbatimmaxunderfull``
    A number. If ``verbatimforcewraps`` mode applies, and if after applying
    the line wrapping at spaces and punctuation, the first part of the split
    line is lacking at least that number of characters to fill the available
    width, then the input line will be reset using the forceful algorithm.

    As the default is set to a high value, the forceful algorithm is triggered
    only in overfull case, i.e. in presence of a string longer than full
    linewidth. Set this to ``0`` to force all input lines to be hard wrapped
    at the current available linewidth::

      latex_elements = {
          'sphinxsetup': "verbatimforcewraps, verbatimmaxunderfull=0",
      }

    This can be done locally for a given code-block via the use of raw latex
    directives to insert suitable ``\sphinxsetup`` (before and after) into the
    latex file.

    Default: ``100``

    .. versionadded:: 3.5.0

``verbatimhintsturnover``
    Boolean to specify if code-blocks display "continued on next page" and
    "continued from previous page" hints in case of page breaks.

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
       set this option value to ``false`` to recover former behavior.

``inlineliteralwraps``
    Boolean to specify if line breaks are allowed inside inline literals: but
    extra potential break-points (additionally to those allowed by LaTeX at
    spaces or for hyphenation) are currently inserted only after the characters
    ``. , ; ? ! /`` and ``\``. Due to TeX internals, white space in the line
    will be stretched (or shrunk) in order to accommodate the linebreak.

    Default: ``true``

    .. versionadded:: 1.5
       set this option value to ``false`` to recover former behavior.

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
       definition of the continuation symbol was changed at 1.5 to accommodate
       various font sizes (e.g. code-blocks can be in footnotes).

.. note::

   Values for color keys must either:

   - obey the syntax of the ``\definecolor`` LaTeX command, e.g. something
     such as ``VerbatimColor={rgb}{0.2,0.3,0.5}`` or ``{RGB}{37,23,255}`` or
     ``{gray}{0.75}`` or ``{HTML}{808080}`` or
     ...

   - or obey the syntax of the ``\colorlet`` command from package ``xcolor``
     e.g. ``VerbatimColor=red!10`` or ``red!50!green`` or ``-red!75`` or
     ``MyPreviouslyDefinedColor`` or... Refer to xcolor_ documentation for
     this syntax.

   .. _xcolor: https://ctan.org/pkg/xcolor

   .. versionchanged:: 5.3.0
      Formerly only the ``\definecolor`` syntax was accepted.

``TitleColor``
    The color for titles (as configured via use of package "titlesec".)

    Default: ``{rgb}{0.126,0.263,0.361}``

``InnerLinkColor``
    A color passed to ``hyperref`` as value of ``linkcolor``  and
    ``citecolor``.

    Default: ``{rgb}{0.208,0.374,0.486}``.

``OuterLinkColor``
    A color passed to ``hyperref`` as value of ``filecolor``, ``menucolor``,
    and ``urlcolor``.

    Default: ``{rgb}{0.216,0.439,0.388}``

``VerbatimColor``
    The background color for :rst:dir:`code-block`\ s.

    Default: ``{RGB}{242,242,242}`` (same as ``{gray}{0.95}``).

    .. versionchanged:: 6.0.0

       Formerly, it was ``{rgb}{1,1,1}`` (white).

``VerbatimBorderColor``
    The frame color.

    Default: ``{RGB}{32,32,32}``

    .. versionchanged:: 6.0.0

       Formerly it was ``{rgb}{0,0,0}`` (black).

``VerbatimHighlightColor``
    The color for highlighted lines.

    Default: ``{rgb}{0.878,1,1}``

    .. versionadded:: 1.6.6

.. _tablecolors:

``TableRowColorHeader``
    Sets the background color for (all) the header rows of tables.

    It will have an effect only if either the :confval:`latex_table_style`
    contains ``'colorrows'`` or if the table is assigned the ``colorrows``
    class.  It is ignored for tables with ``nocolorrows`` class.

    As for the other ``'sphinxsetup'`` keys, it can also be set or modified
    from a ``\sphinxsetup{...}`` LaTeX command inserted via the :dudir:`raw`
    directive, or also from a LaTeX environment associated to a `container
    class <latexcontainer_>`_ and using such ``\sphinxsetup{...}``.

    Default: ``{gray}{0.86}``

    There is also ``TableMergeColorHeader``.  If used, sets a specific color
    for merged single-row cells in the header.

    .. versionadded:: 5.3.0

``TableRowColorOdd``
    Sets the background color for odd rows in tables (the row count starts at
    ``1`` at the first non-header row).  Has an effect only if the
    :confval:`latex_table_style` contains ``'colorrows'`` or for specific
    tables assigned the ``colorrows`` class.

    Default: ``{gray}{0.92}``

    There is also ``TableMergeColorOdd``.

    .. versionadded:: 5.3.0

``TableRowColorEven``
    Sets the background color for even rows in tables.

    Default ``{gray}{0.98}``

    There is also ``TableMergeColorEven``.

    .. versionadded:: 5.3.0

``verbatimsep``
    The separation between code lines and the frame.

    See :ref:`additionalcss` for its alias  ``pre_padding`` and
    additional keys.

    Default: ``\fboxsep``

``verbatimborder``
    The width of the frame around :rst:dir:`code-block`\ s.  See also
    :ref:`additionalcss` for ``pre_border-width``.

    Default: ``\fboxrule``

``shadowsep``
    The separation between contents and frame for contents_ and
    :dudir:`topic` boxes.

    See :ref:`additionalcss` for the alias ``div.topic_padding``.

    Default: ``5pt``

``shadowsize``
    The width of the lateral "shadow" to the right and bottom.

    See :ref:`additionalcss` for ``div.topic_box-shadow`` which allows to
    configure separately the widths of the vertical and horizontal shadows.

    Default: ``4pt``

    .. versionchanged:: 6.1.2
       Fixed a regression introduced at ``5.1.0`` which modified unintentionally
       the width of topic boxes and worse had made usage of this key break PDF
       builds.

``shadowrule``
    The width of the frame around :dudir:`topic` boxes.  See also
    :ref:`additionalcss` for ``div.topic_border-width``.

    Default: ``\fboxrule``

.. important::

   At 7.4.0 all admonitions (not only danger-type) use the possibilities
   which were added at 5.1.0 and 6.2.0.  All defaults have changed.

``iconpackage``

    The name of the LaTeX package used for icons in the admonition titles.  It
    defaults to ``fontawesome5`` or to fall-back ``fontawesome``.  In case
    neither one is available the option value will automatically default to
    ``none``, which means that no attempt at loading a package is done.
    Independently of this setting, arbitrary LaTeX code can be associated to
    each admonition type via ``div.<type>_icon-title`` keys which are
    described in the :ref:`additionalcss` section.  If these keys are not
    used, Sphinx will either apply its default choices of icons (if
    ``fontawesome{5,}`` is available) or not draw the icon at all.  Notice that
    if fall-back ``fontawesome`` is used the common icon for :dudir:`caution`
    and :dudir:`danger` will default to "bolt" not "radiation", which is only
    found in ``fontawesome5``.

    .. versionadded:: 7.4.0

|notebdcolors|
    The color for the admonition border.

    Default: ``{RGB}{134,152,155}``.

    .. versionchanged:: 7.4.0

|notebgcolors|
    The color for the admonition background.

    Default: ``{RGB}{247,247,247}``.

    .. versionadded:: 6.2.0

    .. versionchanged:: 7.4.0

|notetextcolors|
    The color for the admonition contents.

    Default: unset (contents text uses ambient text color, a priori black)

    .. versionadded:: 6.2.0

       To be considered experimental until 7.0.0.  These options have aliases
       ``div.note_TeXcolor`` (etc) described in :ref:`additionalcss`.  Using
       the latter will let Sphinx switch to a more complex LaTeX code,
       which supports the customizability described in :ref:`additionalcss`.

|notetexextras|
    Some extra LaTeX code (such as ``\bfseries``  or ``\footnotesize``)
    to be executed at start of the contents.

    Default: empty

    .. versionadded:: 6.2.0

       To be considered experimental until 7.0.0.  These options have aliases
       ``div.note_TeXextras`` (etc) described in :ref:`additionalcss`.

``noteborder``, ``hintborder``, ``importantborder``, ``tipborder``
    The width of the border.   See
    :ref:`additionalcss` for keys allowing to configure separately each
    border width.

    Default: ``0.5pt``

.. only:: not latex

   |warningbdcolors|
       The color for the admonition border.

       Default: ``{RGB}{148,0,0}`` except for ``error`` which uses ``red``.

       .. versionchanged:: 7.4.0

.. only:: latex

   |wgbdcolorslatex|
       The color for the admonition border.

       Default: ``{RGB}{148,0,0}`` except for ``error`` which uses ``red``.

       .. versionchanged:: 7.4.0

|warningbgcolors|
    The background color for the admonition background.

    Default: ``{RGB}{247,247,247}``.

    .. versionchanged:: 7.4.0

|warningborders|
    The width of the admonition frame.  See
    :ref:`additionalcss` for keys allowing to configure separately each
    border width.

    Default: ``1pt`` except for ``error`` which uses ``1.25pt``.

    .. versionchanged:: 7.4.0

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

.. |notebgcolors| replace:: ``noteBgColor``, ``hintBgColor``,
                            ``importantBgColor``, ``tipBgColor``

.. |notetextcolors| replace:: ``noteTextColor``, ``hintTextColor``,
                              ``importantTextColor``, ``tipTextColor``

.. |notetexextras| replace:: ``noteTeXextras``, ``hintTeXextras``,
                             ``importantTeXextras``, ``tipTeXextras``

.. |warningbdcolors| replace:: ``warningBorderColor``, ``cautionBorderColor``,
                               ``attentionBorderColor``, ``dangerBorderColor``,
                               ``errorBorderColor``

.. |wgbdcolorslatex| replace:: ``warningBorderColor``, and
                               ``(caution|attention|danger|error)BorderColor``

.. else latex goes into right margin, as it does not hyphenate the names

.. |warningbgcolors| replace:: ``warningBgColor``, ``cautionBgColor``,
                               ``attentionBgColor``, ``dangerBgColor``,
                               ``errorBgColor``

.. |warningborders| replace:: ``warningborder``, ``cautionborder``,
                              ``attentionborder``, ``dangerborder``,
                              ``errorborder``

.. _additionalcss:

Additional  CSS-like ``'sphinxsetup'`` keys
-------------------------------------------

.. versionadded:: 5.1.0

   For :rst:dir:`code-block`, :dudir:`topic` and contents_ directive,
   and strong-type admonitions (:dudir:`warning`, :dudir:`error`, ...).

.. versionadded:: 6.2.0

   Also the :dudir:`note`, :dudir:`hint`, :dudir:`important` and :dudir:`tip`
   admonitions can be styled this way.  Using for them *any* of the listed
   options will trigger usage of a more complex LaTeX code than the one used
   per default (``sphinxheavybox`` vs ``sphinxlightbox``).  Setting the new
   ``noteBgColor`` (or ``hintBgColor``, ...) also triggers usage of
   ``sphinxheavybox`` for :dudir:`note` (or :dudir:`hint`, ...).

.. versionadded:: 7.4.0

   For *all* admonition types, the default configuration does set a background
   color (hence the richer ``sphinxheavybox`` is always used).

.. important::

   Further, all admonition titles are by default styled using a colored row
   and an icon, which are modeled on the current rendering of Sphinx own
   docs at https://www.sphinx-doc.org.  CSS-named alike keys are added to
   set the foreground and background colors for the title as well as the
   LaTeX code for the icon.


Perhaps in future these 5.1.0 (and 6.2.0) novel settings will be optionally
imported from some genuine CSS external file, but currently they have to be used
via the ``'sphinxsetup'`` interface (or the ``\sphinxsetup`` LaTeX command
inserted via the :dudir:`raw` directive) and the CSS syntax is only imitated.

.. important:: Low-level LaTeX errors causing a build failure can happen if
   the input syntax is not respected.

   * In particular colors must be input as for the other color related options
     previously described, i.e. either in the ``\definecolor`` syntax or via the
     ``\colorlet`` syntax::

       ...<other options>
       div.warning_border-TeXcolor={rgb}{1,0,0},% \definecolor syntax
       div.error_background-TeXcolor=red!10,%     \colorlet syntax
       ...<other options>

   * A colon in place of the equal sign will break LaTeX.

   * ``...border-width`` or ``...padding`` expect a *single* dimension: they can not
     be used so far with space separated dimensions.

   * ``...top-right-radius`` et al. values may be either a single or *two* space
     separated dimensions.

   * Dimension specifications must use TeX units such as ``pt`` or ``cm`` or
     ``in``.  The ``px`` unit is recognized by ``pdflatex`` and ``lualatex``
     but not by ``xelatex`` or ``platex``.

   * It is allowed for such specifications to be so-called "dimensional
     expressions", e.g. ``\fboxsep+2pt`` or ``0.5\baselineskip`` are valid
     inputs.  The expressions will be evaluated only at the typesetting time.
     Be careful though if using as in these examples TeX control sequences to
     double the backslash or to employ a raw Python string for the value of
     the :ref:`'sphinxsetup' <latexsphinxsetup>` key.

   * As a rule, avoid inserting unneeded spaces in the key values: especially
     for the radii an input such  ``2 pt 3pt`` will break LaTeX.  Beware also
     that ``\fboxsep \fboxsep`` will not be seen as space separated in LaTeX.
     You must use something such as ``{\fboxsep} \fboxsep``.  Or use
     directly ``3pt 3pt`` which is a priori equivalent and simpler.

The options are all named in a similar pattern which depends on a ``prefix``,
which is then followed by an underscore, then the property name.

.. csv-table::
   :header: Directive, Option prefix, LaTeX environment

   :rst:dir:`code-block`, ``pre``, ``sphinxVerbatim``
   :dudir:`topic`, ``div.topic``, ``sphinxShadowBox``
   contents_, ``div.topic``, ``sphinxShadowBox``
   :dudir:`note`, ``div.note``, ``sphinxnote``
   :dudir:`warning`, ``div.warning``, ``sphinxwarning``
   further admonition types ``<type>``, ``div.<type>``,  ``sphinx<type>``
   :rst:dir:`seealso`, ``div.seealso``, ``sphinxseealso``
   :rst:dir:`todo`, ``div.todo``, ``sphinxtodo``


.. versionadded:: 7.4.0  Customizability of the :rst:dir:`seealso` and
   :rst:dir:`todo` directives.

Here are now these options as well as their common defaults.
Replace below ``<prefix>`` by the actual prefix as explained above.  Don't
forget the underscore separating the prefix from the property names.

- | ``<prefix>_border-top-width``,
  | ``<prefix>_border-right-width``,
  | ``<prefix>_border-bottom-width``,
  | ``<prefix>_border-left-width``,
  | ``<prefix>_border-width``.  The latter can (currently) be only a *single*
    dimension which then sets all four others.

  The default is that all those dimensions are equal.  They are set to:

  * ``0.4pt`` for :rst:dir:`code-block`,
  * ``0.5pt`` for :dudir:`topic` or contents_ directive,
  * ``0.5pt`` for :dudir:`note` and other "light" admonitions,
  * ``0.5pt`` for :rst:dir:`seealso` and :rst:dir:`todo` directives,
  * ``1pt`` for  :dudir:`warning` and other "strong" admonitions except
    :dudir:`error` which uses ``1.25pt``.

  .. versionchanged:: 7.4.0

     Changed defaults for :dudir:`topic` and :dudir:`error`.

- ``<prefix>_box-decoration-break`` can be set to either ``clone`` or
  ``slice`` and configures the behavior at page breaks.
  It defaults to ``slice`` for :rst:dir:`code-block` (i.e. for ``<prefix>=pre``)
  since 6.0.0.  For other directives the default is ``clone``.
- | ``<prefix>_padding-top``,
  | ``<prefix>_padding-right``,
  | ``<prefix>_padding-bottom``,
  | ``<prefix>_padding-left``,
  | ``<prefix>_padding``.  The latter can (currently) be only a *single*
    dimension which then sets all four others.

  The defaults:

  * all four ``3pt`` for :rst:dir:`code-block`,
  * ``10pt``, ``7pt``, ``12pt``, ``7pt`` for :dudir:`topic` or
    contents_ directive,
  * ``6pt``, ``7pt``, ``6pt``, ``7pt`` for all "light" admonitions as well
    as the :rst:dir:`seealso` and :rst:dir:`todo` directives.
  * ``6pt``, ``6.5pt``, ``6pt``, ``6.5pt`` for the strong admonition types
    except :dudir:`error` which uses horizontal padding of ``6.25pt``.

  .. versionchanged:: 7.4.0

     All defaults were changed, except for :rst:dir:`code-block`.  Admonitions
     are set-up so that left (or right) padding plus left (or right)
     border-width add up always to ``7.5pt``, so contents align well
     vertically across admonition types on same page in PDF.  This is only a
     property of defaults, not a constraint on possible user choices.

- | ``<prefix>_border-top-left-radius``,
  | ``<prefix>_border-top-right-radius``,
  | ``<prefix>_border-bottom-right-radius``,
  | ``<prefix>_border-bottom-left-radius``,
  | ``<prefix>_border-radius``.  This last key sets the first four to
    its assigned value.  Each key value can be either a single, or *two*,
    dimensions which are then space separated.

  The defaults:

  * ``3pt`` for :rst:dir:`code-block` (since 6.0.0) and all corners,
  * ``12pt`` for the bottom right corner of :dudir:`topic`, other corners are
    straight,
  * all radii set to ``5pt`` for :dudir:`note`, :dudir:`hint` and
    :dudir:`tip`,
  * ``0pt``, i.e. straight corners for all other directives.

  .. versionchanged:: 7.4.0

     :dudir:`topic` and :dudir:`note`\ -like admonitions acquire (at least one)
     rounded corners.

  See a remark above about traps with spaces in LaTeX.
- ``<prefix>_box-shadow`` is special in so far as it may be:

  * the ``none`` keyword,
  * or a single dimension (giving both x-offset and y-offset),
  * or two dimensions (separated by a space),
  * or two dimensions followed by the keyword ``inset``.

  The x-offset and y-offset may be negative.  The default is ``none``,
  *except* for the :dudir:`topic` or contents_ directives, for which it is
  ``4pt 4pt``, i.e. the shadow has a width of ``4pt`` and extends to the right
  and below the frame.  The lateral shadow then extends into the page right
  margin.
- | ``<prefix>_border-TeXcolor``,
  | ``<prefix>_background-TeXcolor``,
  | ``<prefix>_box-shadow-TeXcolor``,
  | ``<prefix>_TeXcolor``.
    These are colors.

  Since 6.0.0 the border and background colors of :rst:dir:`code-block`,
  default respectively to ``{RGB}{32,32,32}`` (i.e. ``{HTML}{202020}``), and
  ``{RGB}{242,242,242}`` (i.e. ``{gray}{0.95}`` or ``{HTML}{F2F2F2}``).

  At 7.4.0 other directives acquire non-black/white default border and
  background colors.  Here they are using ``xcolor`` hexadecimal notation
  (which requires always 6 hexadecimal digits):

  - ``{HTML}{F7F7F7}`` serves as background color to all.
  - ``{HTML}{86989B}`` is border color of light admonitions (inclusive of
    :rst:dir:`seealso` and :rst:dir:`todo`) as well as of :dudir:`topic` and
    contents_ directives.
  - ``{HTML}{940000}`` is border color or :dudir:`warning`-type admonitions,
    except :dudir:`error` which uses ``{HTML}{B40000}``.

  The only directives displaying a shadow per default are :dudir:`topic` and
  contents_ (handled identically at LaTeX level) and their shadow color is
  ``{HTML}{6C6C6C}``.  For all others the default shadow color is black.

  The ``<prefix>_TeXcolor`` stands for the CSS property "color", i.e. it
  influences the text color of the contents.  As for the three other options,
  the naming ``TeXcolor`` is to stress that the input syntax is the TeX one
  for colors not an HTML/CSS one.  If package ``xcolor`` is available in the
  LaTeX installation, one can use directly named colors as key values.
  Consider passing options such as ``dvipsnames``, ``svgnames`` or ``x11names``
  to ``xcolor`` via ``'passoptionstopackages'`` key of :confval:`latex_elements`.

  If ``<prefix>_TeXcolor`` is set, a ``\color`` command is inserted at
  start of the directive contents; for admonitions, this happens after the
  heading which reproduces the admonition type.

- ``<prefix>_TeXextras``: if set, its value must be some LaTeX command or
  commands, for example ``\itshape``.  These commands will be inserted at the
  start of the contents; for admonitions, this happens after the heading which
  reproduces the admonition type.

The next keys, for admonitions only, were all three added at 7.4.0.  The
default colors are the ones applying to the current HTML rendering of Sphinx
own docs at https://www.sphinx-doc.org.

- ``div.<type>_title-background-TeXcolor``: the background color for the title.

  .. important::

     The colored title-row is produced as a result of the Sphinx default
     definitions for the various ``\sphinxstyle<type>title`` commands, see
     :ref:`latex-macros`.  Custom redefinitions of these commands are
     possible, but to re-use the colors and the icon, it is needed to check in
     Sphinx LaTeX source code how the default definitions are done.

- ``div.<type>_title-foreground-TeXcolor``: the color to be used for the icon
  (it applies only to the icon, not to the title of the admonition).

- ``div.<type>_title-icon``: the LaTeX code responsible for producing the
  icon.  For example, the default for :dudir:`note` is
  ``div.note_title-icon=\faIcon{info-circle}``.  This uses a command from the
  LaTeX ``fontawesome5`` package, which is loaded automatically if available.

  If neither ``fontawesome5`` nor fall-back ``fontawesome`` (for which the
  associated command is ``\faicon``, not ``\faIcon``) are found, or if the
  ``iconpackage`` key of :ref:`'sphinxsetup' <latexsphinxsetup>` is set to
  load some other user-chosen package, or no package at all, all the
  ``title-icons`` default to empty LaTeX code.  It is up to user to employ
  this interface to inject the icon (or anything else) into the PDF output.

.. note::

   - All directives support ``box-decoration-break`` to be set to ``slice``.

     .. versionchanged:: 6.2.0

        Formerly, only :rst:dir:`code-block` did.  The default remains
        ``clone`` for all other directives, but this will probably change at
        7.0.0.

   - The corners of rounded boxes may be elliptical.

     .. versionchanged:: 6.2.0

        Formerly, only circular rounded corners were supported and a rounded
        corner forced the whole frame to use the same constant width from
        ``<prefix>_border-width``.

   - Inset shadows are incompatible with rounded corners.  In case
     both are specified the inset shadow will simply be ignored.

     .. versionchanged:: 6.2.0

        Formerly it was to the contrary the rounded corners which were ignored
        in case an inset shadow was specified.

   - ``<prefix>_TeXcolor`` and ``<prefix>_TeXextras`` are new with 6.2.0.

     Usefulness is doubtful in the case of :rst:dir:`code-block`:

     - ``pre_TeXcolor`` will influence only the few non-Pygments highlighted
       tokens; it does color the line numbers, but if one wants to color
       *only* them one has to go through the ``fancyvrb`` interface.

     - ``pre_TeXextras=\footnotesize`` for example may be replaced by usage of
       the :confval:`latex_elements` key ``'fvset'``.  For ``'lualatex'`` or
       ``'xelatex'`` Sphinx includes in the preamble already
       ``\fvset{fontsize=\small}`` and this induces ``fancyvrb`` into
       overriding a ``\footnotesize`` coming from ``pre_TeXextras``.  One has
       to use ``pre_TeXextras=\fvset{fontsize=\footnotesize}`` syntax.
       Simpler to set directly the :confval:`latex_elements` key
       ``'fvset'``...

     Consider these options experimental and that some implementation details
     may change.  For example if the ``pre_TeXextras`` LaTeX commands were put
     by Sphinx in another location it could override the ``'fvset'`` effect,
     perhaps this is what will be done in a future release.

   - Rounded boxes are done using the pict2e_ interface to some basic PDF
     graphics operations.  If this LaTeX package can not be found the build
     will proceed and render all boxes with straight corners.

   - Elliptic corners use the ellipse_ LaTeX package which extends pict2e_.
     If this LaTeX package can not be found rounded corners will be circular
     arcs (or straight if pict2e_ is not available).

.. _pict2e: https://ctan.org/pkg/pict2e
.. _ellipse: https://ctan.org/pkg/ellipse


The following legacy behavior is currently not customizable:

- For :rst:dir:`code-block`, padding and border-width and shadow (if one adds
  one) will go into the margin; the code lines remain at the same place
  independently of the values of the padding and border-width, except for
  being shifted vertically of course to not overwrite other text due to the
  width of the border or external shadow.

- For :dudir:`topic` (and contents_) the shadow (if on right) goes into the
  page margin, but the border and the extra padding are kept within the text
  area.  Same for admonitions.

- The contents_ and :dudir:`topic` directives are governed by the same options
  with ``div.topic`` prefix: the Sphinx LaTeX mark-up uses for both directives
  the same ``sphinxShadowBox`` environment which has currently no additional
  branching, contrarily to the ``sphinxadmonition`` environment which branches
  according to the admonition directive name, e.g. either to ``sphinxnote``
  or ``sphinxwarning`` etc...


LaTeX macros and environments
-----------------------------

The "LaTeX package" file :file:`sphinx.sty` loads various components
providing support macros (aka commands), and environments, which are used in
the mark-up produced on output from the ``latex`` builder, before conversion
to ``pdf`` via the LaTeX toolchain.  Also the "LaTeX class" files
:file:`sphinxhowto.cls` and :file:`sphinxmanual.cls` define or customize some
environments.  All of these files can be found in the latex build repertory.

Some of these provide facilities not available from pre-existing LaTeX
packages and work around LaTeX limitations with lists, table cells, verbatim
rendering, footnotes, etc...

Others simply define macros with public names to make overwriting their
defaults easy via user-added contents to the preamble.  We will survey most of
those public names here, but defaults have to be looked at in their respective
definition files.

.. hint::

   Sphinx LaTeX support code is split across multiple smaller-sized files.
   Rather than adding code to the preamble via
   `latex_elements <latex_elements_confval_>`_\ [``'preamble'``] it is
   also possible to replace entirely one of the component files of Sphinx
   LaTeX code with a custom version, simply by including a modified copy in
   the project source and adding the filename to the
   :confval:`latex_additional_files` list.  Check the LaTeX build repertory
   for the filenames and contents.

.. versionchanged:: 4.0.0
   split of :file:`sphinx.sty` into multiple smaller units, to facilitate
   customization of many aspects simultaneously.

.. _latex-macros:

Macros
~~~~~~

- Text styling commands:

  .. csv-table::
     :header: Name, ``maps argument #1 to:``
     :align: left
     :class: longtable
     :delim: ;

     ``\sphinxstrong``;         ``\textbf{#1}``
     ``\sphinxcode``;           ``\texttt{#1}``
     ``\sphinxbfcode``;         ``\textbf{\sphinxcode{#1}}``
     ``\sphinxemail``;          ``\textsf{#1}``
     ``\sphinxtablecontinued``; ``\textsf{#1}``
     ``\sphinxtitleref``;       ``\emph{#1}``
     ``\sphinxmenuselection``;  ``\emph{#1}``
     ``\sphinxguilabel``;       ``\emph{#1}``
     ``\sphinxkeyboard``;       ``\sphinxcode{#1}``
     ``\sphinxaccelerator``;    ``\underline{#1}``
     ``\sphinxcrossref``;       ``\emph{#1}``
     ``\sphinxtermref``;        ``\emph{#1}``
     ``\sphinxsamedocref``;     ``\emph{#1}``
     ``\sphinxparam``;          ``\emph{#1}``
     ``\sphinxtypeparam``;      ``\emph{#1}``
     ``\sphinxoptional``; ``[#1]`` with larger brackets, see source

  .. versionadded:: 1.4.5
     Use of ``\sphinx`` prefixed macro names to limit possibilities of conflict
     with LaTeX packages.

  .. versionadded:: 1.8
     ``\sphinxguilabel``

  .. versionadded:: 3.0
     ``\sphinxkeyboard``

  .. versionadded:: 6.2.0
     ``\sphinxparam``, ``\sphinxsamedocref``

  .. versionadded:: 7.1.0
     ``\sphinxparamcomma`` which defaults to a comma followed by a space and
     ``\sphinxparamcommaoneperline`` which is used for one-parameter-per-line
     signatures (see :confval:`maximum_signature_line_length`).  It defaults
     to ``\texttt{,}`` to make these end-of-line separators more distinctive.

     Signatures of Python functions are rendered as ``name<space>(parameters)``
     or ``name<space>[type parameters]<space>(parameters)`` (see :pep:`695`)
     where the length of ``<space>`` is set to ``0pt`` by default.
     This can be changed via ``\setlength{\sphinxsignaturelistskip}{1ex}``
     for instance.

- More text styling:

  .. csv-table::
     :header: Name, ``maps argument #1 to:``
     :align: left
     :class: longtable
     :delim: ;

     ``\sphinxstyleindexentry``;       ``\texttt{#1}``
     ``\sphinxstyleindexextra``;       ``(\emph{#1})`` (with a space upfront)
     ``\sphinxstyleindexpageref``;     ``, \pageref{#1}``
     ``\sphinxstyleindexpagemain``;    ``\textbf{#1}``
     ``\sphinxstyleindexlettergroup``; ``{\Large\sffamily#1}\nopagebreak\vspace{1mm}``
     ``\sphinxstyleindexlettergroupDefault``; check source, too long for here
     ``\sphinxstyletopictitle``;       ``\textbf{#1}\par\medskip``
     ``\sphinxstylesidebartitle``;     ``\textbf{#1}\par\medskip``
     ``\sphinxstyleothertitle``;       ``\textbf{#1}``
     ``\sphinxstylesidebarsubtitle``;  ``~\\\textbf{#1} \smallskip``
     ``\sphinxstyletheadfamily``;      ``\sffamily`` (*this one has no argument*)
     ``\sphinxstyleemphasis``;         ``\emph{#1}``
     ``\sphinxstyleliteralemphasis``;  ``\emph{\sphinxcode{#1}}``
     ``\sphinxstylestrong``;           ``\textbf{#1}``
     ``\sphinxstyleliteralstrong``;    ``\sphinxbfcode{#1}``
     ``\sphinxstyleabbreviation``;     ``\textsc{#1}``
     ``\sphinxstyleliteralintitle``;   ``\sphinxcode{#1}``
     ``\sphinxstylecodecontinued``;    ``{\footnotesize(#1)}}``
     ``\sphinxstylecodecontinues``;    ``{\footnotesize(#1)}}``
     ``\sphinxstylenotetitle``; ``\sphinxdotitlerowwithicon{note}{#1}``
     ``\sphinxstylehinttitle``; ``\sphinxdotitlerowwithicon{hint}{#1}``
     ``\sphinxstyleimportanttitle``;   *similar*
     ``\sphinxstyletiptitle``;         *similar*
     ``\sphinxstylewarningtitle``;     *similar*
     ``\sphinxstylecautiontitle``;     *similar*
     ``\sphinxstyleattentiontitle``;   *similar*
     ``\sphinxstyledangertitle``;      *similar*
     ``\sphinxstyleerrortitle``;       *similar*
     ``\sphinxstyleseealsotitle``;     *similar*
     ``\sphinxstyletodotitle``;        *similar*

  .. note::

     To let this table fit on the page width in PDF output we have lied a bit
     and the actual definition of ``\sphinxstylenotetitle`` is:

     .. code-block:: latex

        \newcommand\sphinxstylenotetitle[1]%
        {\sphinxdotitlerowwithicon{note}{\sphinxremovefinalcolon{#1}}}

     The same remark applies to all other similar commands associated with
     admonitions.

  .. versionadded:: 1.5
     These macros were formerly hard-coded as non customizable ``\texttt``,
     ``\emph``, etc...

  .. versionadded:: 1.6
     ``\sphinxstyletheadfamily`` which defaults to ``\sffamily`` and allows
     multiple paragraphs in header cells of tables.

  .. versionadded:: 1.6.3
     ``\sphinxstylecodecontinued`` and ``\sphinxstylecodecontinues``.

  .. versionadded:: 1.8
     ``\sphinxstyleindexlettergroup``, ``\sphinxstyleindexlettergroupDefault``.

  .. versionadded:: 6.2.0
     ``\sphinxstylenotetitle`` et al.  The ``#1`` is the localized name of the
     directive, with a final colon.  Wrap it as ``\sphinxremovefinalcolon{#1}``
     if this final colon is to be removed.

  .. versionadded:: 7.4.0 The ``\sphinxdotitlerowwithicon`` LaTeX command,
     whose first argument is the admonition type, so that it can recover
     the associated colours and icon for the title row, and the second
     argument gets typeset after the icon.

  .. todo:: The fact that we must employ ``\sphinxremovefinalcolon`` is a
            legacy artefact from old ill-designed Sphinx LaTeX writer,
            which postfixes (still today) the title with a colon automatically.

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

  .. hint::

     If adding to preamble the loading of ``tocloft`` package, also add to
     preamble ``\renewcommand\sphinxtableofcontentshook{}`` else it will reset
     ``\l@section`` and ``\l@subsection`` cancelling ``tocloft`` customization.

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


.. _sphinxbox:

The ``\sphinxbox`` command
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 6.2.0

The ``\sphinxbox[key=value,...]{inline text}`` command can be used to "box"
inline text elements with all the customizability which has been described in
:ref:`additionalcss`.  It is a LaTeX command with one optional argument, which
is a comma-separated list of key=value pairs, as for :ref:`latexsphinxsetup`.
Here is the complete list of keys.  They don't use any prefix.

- ``border-width``,
- ``border-top-width``, ``border-right-width``, ``border-bottom-width``,
  ``border-left-width``,
- ``padding``,
- ``padding-top``, ``padding-right``, ``padding-bottom``, ``padding-left``,
- ``border-radius``,
- ``border-top-left-radius``, ``border-top-right-radius``,
  ``border-bottom-right-radius``, ``border-bottom-left-radius``,
- ``box-shadow``,
- ``border-TeXcolor``, ``background-TeXcolor``, ``box-shadow-TeXcolor``,
  ``TeXcolor``,
- ``TeXextras``,
- and ``addstrut`` which is a boolean key, i.e. to be used as ``addstrut=true``,
  or ``addstrut`` alone where ``=true`` is omitted, or ``addstrut=false``.

This last key is specific to ``\sphinxbox`` and it means to add a ``\strut``
so that heights and depths are equalized across various instances on the same
line with varying contents.  The default is ``addstrut=false``.

.. important::

   Perhaps the default will turn into ``addstrut=true`` at 7.0.0 depending on
   feedback until then.

The combination ``addstrut, padding-bottom=0pt, padding-top=1pt`` is often
satisfactory.

Refer to :ref:`additionalcss` for important syntax information regarding the
other keys.  The default
configuration uses no shadow, a border-width of ``\fboxrule``, a padding of
``\fboxsep``, circular corners with radii ``\fboxsep`` and background and
border colors as for the default rendering of code-blocks.

When a ``\sphinxbox`` usage is nested within another one, it will ignore the
options of the outer one: it first resets all options to their default state
as they were prior to applying the outer box options, then it applies its own
specific ones.

One can modify these defaults via the command ``\sphinxboxsetup{key=value,...}``.
The effect is cumulative, if one uses this command multiple times.  Here the
options are a mandatory argument so are within curly braces, not square
brackets.

Here is some example of use:

.. code-block:: latex

   latex_elements = {
       'preamble': r'''
   % modify globally the defaults
   \sphinxboxsetup{border-width=2pt,%
                   border-radius=4pt,%
                   background-TeXcolor=yellow!20}
   % configure some styling element with some extra specific options:
   \protected\def\sphinxkeyboard#1{\sphinxbox[border-TeXcolor=green]{\sphinxcode{#1}}}
   ''',
   }

A utility ``\newsphinxbox`` is provided to create a new boxing macro, say
``\foo`` which will act exactly like ``\sphinxbox`` but with a given extra
configuration:

.. code-block:: latex

   % the specific options to \foo are within brackets
   \newsphinxbox[border-radius=0pt, box-shadow=2pt 2pt]{\foo}
   % then use this \foo, possibly with some extra options still:
   \protected\def\sphinxguilabel#1{\foo{#1}}
   \protected\def\sphinxmenuselection#1{\foo[box-shadow-TeXcolor=gray]{#1}}

Boxes rendered with ``\foo`` obey as the ones using directly ``\sphinxbox``
the current configuration as set possibly mid-way in document via
``\sphinxboxsetup`` (from a :dudir:`raw` LaTeX mark-up), the only difference
is that they have an initial additional set of default extras.

In the above examples, you can probably use ``\renewcommand`` syntax if you
prefer it to ``\protected\def`` (with ``[1]`` in place of ``#1`` then).


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
  environments, configured to use the parameters (colors, border thickness)
  specific to each type, which can be set via ``'sphinxsetup'`` string.

  .. versionchanged:: 1.5
     Use of public environment names, separate customizability of the
     parameters, such as ``noteBorderColor``, ``noteborder``,
     ``warningBgColor``, ``warningBorderColor``, ``warningborder``, ...

- Environment for the :rst:dir:`seealso` directive: ``sphinxseealso``.
  It takes one argument which will be the localized string ``See also``
  followed with a colon.

  .. versionadded:: 6.1.0
  .. versionchanged:: 6.2.0

     Colon made part of the mark-up rather than being inserted by the
     environment for coherence with how admonitions are handled generally.

- Environment for the :rst:dir:`todo` directive: ``sphinxtodo``.
  It takes one argument which will be the localized string ``Todo``
  followed with a colon.

  .. versionadded:: 7.4.0
- The contents_ directive (with ``:local:`` option) and the
  :dudir:`topic` directive are implemented by environment ``sphinxShadowBox``.

  .. versionadded:: 1.4.2
     Former code refactored into an environment allowing page breaks.

  .. versionchanged:: 1.5
     Options ``shadowsep``, ``shadowsize``,  ``shadowrule``.

- The literal blocks (via ``::`` or :rst:dir:`code-block`), are
  implemented using ``sphinxVerbatim`` environment which is a wrapper of
  ``Verbatim`` environment from package ``fancyvrb.sty``. It adds the handling
  of the top caption and the wrapping of long lines, and a frame which allows
  page breaks. Inside tables the used
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

- Every text paragraph in document body starts with ``\sphinxAtStartPar``.
  Currently, this is used to insert a zero width horizontal skip which
  is a trick to allow TeX hyphenation of the first word of a paragraph
  in a narrow context (like a table cell). For ``'lualatex'`` which
  does not need the trick, the ``\sphinxAtStartPar`` does nothing.

  .. versionadded:: 3.5.0

- The section, subsection, ... headings are set using  *titlesec*'s
  ``\titleformat`` command.

- For the ``'manual'`` docclass, the chapter headings can be customized using
  *fncychap*'s commands ``\ChNameVar``, ``\ChNumVar``, ``\ChTitleVar``. File
  :file:`sphinx.sty` has custom re-definitions in case of *fncychap*
  option ``Bjarne``.

  .. versionchanged:: 1.5
     Formerly, use of *fncychap* with other styles than ``Bjarne`` was
     dysfunctional.

.. _latexcontainer:

- Docutils :dudir:`container` directives are supported in LaTeX output: to
  let a container class with name ``foo`` influence the final PDF via LaTeX,
  it is only needed to define in the preamble an environment
  ``sphinxclassfoo``.  A simple example would be:

  .. code-block:: latex

     \newenvironment{sphinxclassred}{\color{red}}{}

  Currently the class names must contain only ASCII characters and avoid
  characters special to LaTeX such as ``\``.

  .. versionadded:: 4.1.0

.. hint::

   As an experimental feature, Sphinx can use user-defined template file for
   LaTeX source if you have a file named ``_templates/latex.tex.jinja`` in your
   project.

   Additional files ``longtable.tex.jinja``, ``tabulary.tex.jinja`` and
   ``tabular.tex.jinja`` can be added to ``_templates/`` to configure some
   aspects of table rendering (such as the caption position).

   .. versionadded:: 1.6
      currently all template variables are unstable and undocumented.

   .. versionchanged:: 7.4
      Added support for the ``.jinja`` file extension, which is preferred.
      The old file names remain supported.
      (``latex.tex_t``, ``longtable.tex_t``, ``tabulary.tex_t``, and ``tabular.tex_t``)

.. raw:: latex

   \endgroup
