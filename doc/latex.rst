.. highlightlang:: python

.. _latex:

LaTeX customization
===================

.. module:: latex
   :synopsis: LaTeX specifics.

The *latex* target does not benefit from pre-prepared themes like the
*html* target does (see :doc:`theming`).

Basic customization is available from ``conf.py`` via usage of the
:ref:`latex-options` as described in :doc:`config`. For example::

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

More advanced customization will be obtained via insertion into the LaTeX
preamble of relevant ``\renewcommand``, ``\renewenvironment``, ``\setlength``,
or ``\definecolor`` commands. The ``'preamble'`` key of
:confval:`latex_elements` will serve for inserting these commands. If they are
numerous, it may prove more convenient to assemble them into a specialized
file :file:`mystyle.tex` and then use::

    'preamble': '\\makeatletter\\input{mystyle.tex}\\makeatother',

or, better, to set up a style file
:file:`mystyle.sty` which can then be loaded via::

    'preamble': '\\usepackage{mystyle}',

The :ref:`build configuration file <build-config>` file for the project needs
to have its variable :confval:`latex_additional_files` appropriately
configured, for example::

    latex_additional_files = ["mystyle.sty"]

Such *LaTeX Sphinx theme* files could possibly be contributed in the
future by advanced users for wider use.

The ``'sphinxpackageoptions'`` key to :confval:`latex_elements` provides a
more convenient interface to various style parameters. It is a comma separated
string of ``key=value`` instructions::

    key1=value1,key2=value2, ...

which will be passed as the optional parameter to the Sphinx LaTeX style \file::

    \usepackage[<sphinxpackageoptions>]{sphinx}

It is possible to modify later the options (even midway in the
document using a ``.. raw:: latex`` directive) via use of the command
``\sphinxsetup{<options>}``, with the same option ``key=value`` syntax.

.. versionadded:: 1.5

Here is the current list:

``verbatimwithframe``
    default ``true``. Boolean to use or not frames around
    :rst:dir:`code-block`\ s and literal includes. Setting it to ``false``
    does not deactivate use of package "framed", because it is still in use
    for the optional background colour (see below).

    .. attention::

       LaTeX wants *lowercase* ``=true`` or  ``=false`` here.

``verbatimwrapslines``
    default ``true``. Tells whether long lines in :rst:dir:`code-block`\ s
    should be wrapped. It is theoretically possible to customize this even
    more and decide at which characters a line-break can occur and whether
    before or after, but this is accessible currently only by re-defining some
    macros with complicated LaTeX syntax from :file:`sphinx.sty`.

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

``notebordercolor``
    default ``{rgb}{0,0,0}``. The colour for the two horizontal rules used by
    Sphinx in LaTeX for styling a
    :dudir:`note` admonition. Defaults to black.

``hintbordercolor``
    default ``{rgb}{0,0,0}``. id.

``importantbordercolor``
    default ``{rgb}{0,0,0}``. id.

``tipbordercolor``
    default ``{rgb}{0,0,0}``. id.

``noteborder``
    default ``0.5pt``. The width of the two horizontal rules.

``hintborder``
    default ``0.5pt``. id.

``importantborder``
    default ``0.5pt``. id.

``tipborder``
    default ``0.5pt``. id.

``warningbordercolor``
    default ``{rgb}{0,0,0}``. The colour of the frame for :dudir:`warning` type
    admonitions. Defaults to black.

``cautionbordercolor``
    default ``{rgb}{0,0,0}``. id.

``attentionbordercolor``
    default ``{rgb}{0,0,0}``. id.

``dangerbordercolor``
    default ``{rgb}{0,0,0}``. id.

``errorbordercolor``
    default ``{rgb}{0,0,0}``. id.

``warningbgcolor``
    default ``{rgb}{1,1,1}``. The background colour for :dudir:`warning` type
    admonition, defaults to white.

``cautionbgcolor``
    default ``{rgb}{1,1,1}``. id.

``attentionbgcolor``
    default ``{rgb}{1,1,1}``. id.

``dangerbgcolor``
    default ``{rgb}{1,1,1}``. id.

``errorbgcolor``
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
    default ``\\mbox{ }``. LaTeX macros inserted at the start of the footnote
    text at bottom of page, after the footnote number.

``BeforeFootnote``
    default ``\\leavevmode\\unskip``. LaTeX macros inserted before the footnote
    mark. The default removes possible space before it.

    It can be set to empty (``BeforeFootnote={},``) to recover the earlier
    behaviour of Sphinx, or alternatively contain a ``\\nobreak\\space`` or a
    ``\\thinspace`` after the ``\\unskip`` to insert some chosen
    (non-breakable) space.

    .. versionadded:: 1.5
       formerly, footnotes from explicit mark-up were
       preceded by a space (hence a linebreak there was possible), but
       automatically generated footnotes had no such space.

``HeaderFamily``
    default ``\\sffamily\\bfseries``. Sets the font used by headings.

In the future, possibly more keys will be made available. As seen above, they
may even be used for LaTeX commands.

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
  specific to each type, which can be set via ``'sphinxpackageoptions'`` string.

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

.. note::

   It is impossible to revert or prevent the loading of a package that results
   from a ``\usepackage`` executed from inside the :file:`sphinx.sty` style
   file. Sphinx aims at loading as few packages as are really needed for its
   default design.

.. hint::

   As an experimental feature, Sphinx can use user-defined template file for
   LaTeX source if you have a file named ``_templates/latex.tex_t`` on your
   project.  Now all template variables are unstable and undocumented.  They
   will be changed in future version.

   .. versionadded:: 1.5
