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

It is available from ``conf.py`` via usage of the
:ref:`latex-options` as described in :doc:`config` (backslashes must be doubled
in Python string literals to reach latex.) For example::

    # inside conf.py
    latex_engine = 'xelatex'
    latex_elements = {
        'fontenc': '\\usepackage{fontspec}',
        'fontpkg': '''\
    \\setmainfont{DejaVu Serif}
    \\setsansfont{DejaVu Sans}
    \\setmonofont{DejaVu Sans Mono}''',
        'geometry': '\\usepackage[vmargin=2.5cm, hmargin=3cm]{geometry}',
        'preamble': '''\
    \\usepackage[titles]{tocloft}
    \\cftsetpnumwidth {1.25cm}\\cftsetrmarg{1.5cm}
    \\setlength{\\cftchapnumwidth}{0.75cm}
    \\setlength{\\cftsecindent}{\\cftchapnumwidth}
    \\setlength{\\cftsecnumwidth}{1.25cm}''',
        'fncychap': '\\usepackage[Bjornstrup]{fncychap}',
        'printindex': '\\footnotesize\\raggedright\\printindex',
    }
    latex_show_urls = 'footnote'

.. the above was tested on Sphinx's own 1.5a2 documentation with good effect !

.. highlight:: latex

More advanced customization will be obtained via insertion into the LaTeX
preamble of relevant ``\renewcommand``, ``\renewenvironment``, ``\setlength``,
or ``\definecolor`` commands. The ``'preamble'`` key of
:confval:`latex_elements` will serve for inserting these commands. If they are
numerous, it may prove more convenient to assemble them into a specialized
file :file:`mystyle.tex` and then use::

    'preamble': r'\makeatletter\input{mystyle.tex}\makeatother',

or, better, to set up a style file
:file:`mystyle.sty` which can then be loaded via::

    'preamble': r'\usepackage{mystyle}',

The :ref:`build configuration file <build-config>` file for the project needs
to have its variable :confval:`latex_additional_files` appropriately
configured, for example::

    latex_additional_files = ["mystyle.sty"]

.. _latexsphinxsetup:

The Sphinx LaTeX style package options
--------------------------------------

The ``'sphinxsetup'`` key to :confval:`latex_elements` provides a
more convenient interface to various style parameters. It is a comma separated
string of ``key=value`` instructions::

    key1=value1,key2=value2, ...

- if a key is repeated, it is its last occurence which counts,
- spaces around the commas and equal signs are ignored.

If non-empty, it will be passed as argument to the ``\sphinxsetup`` command::

    \usepackage{sphinx}
    \sphinxsetup{key1=value1,key2=value2,...}

.. versionadded:: 1.5

.. note::

   - Most options described next could also have been positioned as
     :file:`sphinx.sty` package options. But for those where the key value
     contains some LaTeX code the use of ``\sphinxsetup`` is mandatory. Hence
     the whole ``'sphinxsetup'`` string is passed as argument to
     ``\sphinxsetup``.

   - As an alternative to the ``'sphinxsetup'`` key, it is possibly
     to insert explicitely the ``\\sphinxsetup{key=value,..}`` inside the
     ``'preamble'`` key. It is even possible to use the ``\sphinxsetup`` in
     the body of the document, via the :rst:dir:`raw` directive, to modify
     dynamically the option values: this is actually what we did for the
     duration of this chapter for the PDF output, which is styled using::

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

     and with the ``svgnames`` option having been passed to "xcolor" package::

         latex_elements = {
             'passoptionstopackages': r'\PassOptionsToPackage{svgnames}{xcolor}',
         }


Here are the currently available options together with their default values.

.. caution::

   These options correspond to what has been so far the default LaTeX
   rendering by Sphinx; if in future Sphinx offers various *themes* for LaTeX,
   the interface may change.

.. attention::

   LaTeX requires for keys with Boolean values to use **lowercase** ``true`` or
   ``false``.

.. _latexsphinxsetuphmargin:

``hmargin``
    The dimensions of the horizontal margins. Legacy Sphinx default value is
    ``1in`` (which stands for ``{1in,1in}``.) It is passed over as ``hmargin``
    option to ``geometry`` package.

    Here is an example for non-Japanese documents of use of this key::

      'sphinxsetup': 'hmargin={2in,1.5in}, vmargin={1.5in,2in}, marginpar=1in',

    Japanese documents currently accept only the form with only one dimension.
    This option is handled then in a special manner in order for ``geometry``
    package to set the text width to an exact multiple of the *zenkaku* width
    of the base document font.

    .. hint::

       For a ``'manual'`` type document with :confval:`language` set to
       ``'ja'``, which by default uses the ``jsbook`` LaTeX document class, the
       dimension units, when the pointsize isn't ``10pt``, must be so-called TeX
       "true" units::

         'sphinxsetup': 'hmargin=1.5truein, vmargin=1.5truein, marginpar=5zw',

       This is due to the way the LaTeX class ``jsbook`` handles the
       pointsize.

       Or, one uses regular units but with ``nomag`` as document class option.
       This can be achieved for example via::

         'pointsize': 'nomag,12pt',

       in the :confval:`latex_elements` configuration variable.

    .. versionadded:: 1.5.3

``vmargin``
    The dimension of the vertical margins. Legacy Sphinx default value is
    ``1in`` (or ``{1in,1in}``.) Passed over as ``vmargin`` option to
    ``geometry``.

    Japanese documents will arrange for the text height to be an integer
    multiple of the baselineskip, taking the closest match suitable for the
    asked-for vertical margin. It can then be only one dimension. See notice
    above.

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
    colour (see below).

``verbatimwrapslines``
    default ``true``. Tells whether long lines in :rst:dir:`code-block`\ 's
    contents should wrap.

    .. (comment) It is theoretically possible to customize this even
       more and decide at which characters a line-break can occur and whether
       before or after, but this is accessible currently only by re-defining some
       macros with complicated LaTeX syntax from :file:`sphinx.sty`.

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
    stretched
    (or shrinked) in order to accomodate the linebreak.

    .. versionadded:: 1.5
       set this option value to ``false`` to recover former behaviour.

``verbatimvisiblespace``
    default ``\textcolor{red}{\textvisiblespace}``. When a long code line is
    split, space characters located at end of the line before the break are
    displayed using this code.

``verbatimcontinued``
    The default is::

      \makebox[2\fontcharwd\font`\x][r]{\textcolor{red}{\tiny$\hookrightarrow$}}

    It is printed at start of continuation lines. This rather formidable
    expression reserves twice the width of a typical character in the current
    (monospaced) font and puts there a small red hook pointing to the right.

    .. versionchanged:: 1.5
       The breaking of long code lines was introduced at 1.4.2. The space
       reserved to the continuation symbol was changed at 1.5 to obey the
       current font characteristics (this was needed as Sphinx 1.5 LaTeX
       allows code-blocks in footnotes which use a smaller font size).

       .. hint::

          This specification gives the same spacing as before 1.5::

            \normalfont\normalsize\makebox[3ex][r]{\textcolor{red}{\tiny$\hookrightarrow$}

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
    mark. The default removes possible space before it.

    It can be set to empty (``BeforeFootnote={},``) to recover the earlier
    behaviour of Sphinx, or alternatively contain a ``\nobreak\space`` or a
    ``\thinspace`` after the ``\unskip`` to insert some chosen
    (non-breakable) space.

    .. versionadded:: 1.5
       formerly, footnotes from explicit mark-up (but not automatically
       generated ones) were preceded by a space in the output ``.tex`` file
       hence a linebreak in PDF was possible. To avoid insertion of this space
       one could use ``foo\ [#f1]`` mark-up, but this impacts all builders.

``HeaderFamily``
    default ``\sffamily\bfseries``. Sets the font used by headings.

As seen above, key values may even be used for LaTeX commands. But don't
forget to double the backslashes if not using "raw" Python strings.

The LaTeX environments defined by Sphinx
----------------------------------------

Let us now list some macros from the package file
:file:`sphinx.sty` and class file :file:`sphinxhowto.cls` or
:file:`sphinxmanual.cls`, which can be entirely redefined, if desired.

- text styling commands (they have one argument): ``\sphinx<foo>`` with
  ``<foo>`` being one of ``strong``, ``bfcode``, ``email``, ``tablecontinued``,
  ``titleref``, ``menuselection``, ``accelerator``, ``crossref``, ``termref``,
  ``optional``. By default and for backwards compatibility the ``\sphinx<foo>``
  expands to ``\<foo>`` hence the user can choose to customize rather the latter
  (the non-prefixed macros will be left undefined if option
  :confval:`latex_keep_old_macro_names` is set to ``False`` in :file:`conf.py`.)

  .. versionchanged:: 1.4.5
     use of ``\sphinx`` prefixed macro names to limit possibilities of conflict
     with user added packages: if
     :confval:`latex_keep_old_macro_names` is set to ``False`` in
     :file:`conf.py` only the prefixed names are defined.
- more text styling commands: ``\sphinxstyle<bar>`` with ``<bar>`` one of
  ``indexentry``, ``indexextra``, ``indexpageref``, ``topictitle``,
  ``sidebartitle``, ``othertitle``, ``sidebarsubtitle``, ``thead``,
  ``emphasis``, ``literalemphasis``, ``strong``, ``literalstrong``,
  ``abbreviation``, ``literalintitle``.

  .. versionadded:: 1.5
     the new macros are wrappers of the formerly hard-coded ``\texttt``,
     ``\emph``, ... The default definitions can be found in
     :file:`sphinx.sty`.
- paragraph level environments: for each admonition type ``<foo>``, the
  used environment is named ``sphinx<foo>``. They may be ``\renewenvironment``
  'd individually, and must then be defined with one argument (it is the heading
  of the notice, for example ``Warning:`` for :dudir:`warning` directive, if
  English is the document language). Their default definitions use either the
  *sphinxheavybox* (for the first listed directives) or the *sphinxlightbox*
  environments, configured to use the parameters (colours, border thickness)
  specific to each type, which can be set via ``'sphinxsetup'`` string.

  .. versionchanged:: 1.5
     use of public environment names, separate customizability of the parameters.
- the :dudir:`contents` directive (with ``:local:`` option) and the
  :dudir:`topic` directive are implemented by environment ``sphinxShadowBox``.
  See above for the three dimensions associated with it.

  .. versionchanged:: 1.5
     use of public names for the three lengths. The environment itself was
     redefined to allow page breaks at release 1.4.2.
- the literal blocks (:rst:dir:`code-block` directives, etc ...), are
  implemented using ``sphinxVerbatim`` environment which is a wrapper of
  ``Verbatim`` environment from package ``fancyvrb.sty``. It adds the handling
  of the top caption and the wrapping of long lines, and a frame which allows
  pagebreaks. Inside tables the used
  environment is ``sphinxVerbatimintable`` (it does not draw a frame, but
  allows a caption).

  .. versionchanged:: 1.5
     ``Verbatim`` keeps exact same meaning as in ``fancyvrb.sty`` (meaning
     which is the one of ``OriginalVerbatim`` too), and custom one is called
     ``sphinxVerbatim``. Also, earlier version of Sphinx used
     ``OriginalVerbatim`` inside tables (captions were lost, long code lines
     were not wrapped), it now uses there ``sphinxVerbatimintable``.
  .. versionadded:: 1.5
     the two customizable lengths, the ``sphinxVerbatimintable``, the boolean
     toggles described above.
- by default the Sphinx style file ``sphinx.sty`` includes the command
  ``\fvset{fontsize=\small}`` as part of its configuration of
  ``fancyvrb.sty``. The user may override this for example via
  ``\fvset{fontsize=auto}`` which will use for listings the ambient
  font size. Refer to ``fancyvrb.sty``'s documentation for further keys.

  .. versionadded:: 1.5
     formerly, the use of ``\small`` for code listings was not customizable.
- the section, subsection, ...  headings are set using  *titlesec*'s
  ``\titleformat`` command. Check :file:`sphinx.sty` for the definitions.
- for the ``'sphinxmanual'`` class (corresponding to the fifth element of
  :confval:`latex_documents` being set to ``'manual'``), the chapter headings
  can be customized using *fncychap*'s commands ``\ChNameVar``, ``\ChNumVar``,
  ``\ChTitleVar``. Check :file:`sphinx.sty` for the default definitions. They
  are applied only if *fncychap* is loaded with option ``Bjarne``. It is also
  possible to use an empty ``'fncychap'`` key, and use the *titlesec*
  ``\titleformat`` command to style the chapter titles.

  .. versionchanged:: 1.5
     formerly, use of *fncychap* with other styles than ``Bjarne`` was
     dysfunctional.
- the table of contents is typeset via ``\sphinxtableofcontents`` which is a
  wrapper (whose definition can be found in :file:`sphinxhowto.cls` or in
  :file:`sphinxmanual.cls`) of standard ``\tableofcontents``.

  .. versionchanged:: 1.5
     formerly, the meaning of ``\tableofcontents`` was modified by Sphinx.
- the bibliography and Python Module index are typeset respectively within
  environments ``sphinxthebibliography`` and ``sphinxtheindex``, which are
  simple wrappers of the non-modified ``thebibliography`` and ``theindex``
  environments.

  .. versionchanged:: 1.5
     formerly, the original environments were modified by Sphinx.

- the list is not exhaustive: refer to :file:`sphinx.sty` for more.

.. hint::

   As an experimental feature, Sphinx can use user-defined template file for
   LaTeX source if you have a file named ``_templates/latex.tex_t`` on your
   project.  Now all template variables are unstable and undocumented.  They
   will be changed in future version.

   .. versionadded:: 1.5

.. raw:: latex

   \endgroup
