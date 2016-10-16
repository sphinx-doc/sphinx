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
file :file:`mycustomizedmacros.tex` and then use::

    'preamble': '\\makeatletter\\input{mycustomizedmacros.tex}\\makeatother',

More advanced LaTeX users will set up a style file
:file:`mycustomizedmacros.sty`, which can then be loaded via::

    'preamble': '\\usepackage{mycustomizedmacros}',

The :ref:`build configuration file <build-config>` file for the project needs
to have its variable :confval:`latex_additional_files` appropriately
configured, for example::

    latex_additional_files = ["mycustomizedmacros.sty"]

Such *LaTeX Sphinx theme* files could possibly be contributed in the
future by advanced users for wider use.

Let us list here some examples of macros, lengths, colors, which are inherited
from package file :file:`sphinx.sty` and class file :file:`sphinxhowto.cls` or
:file:`sphinxmanual.cls`, and can be customized.

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
     ``\emph``, ... The default definitions can be found near the end of
     :file:`sphinx.sty`.
- parameters for paragraph level environments: with ``<foo>`` one of
  :dudir:`warning`, :dudir:`caution`, :dudir:`attention`,
  :dudir:`danger`, :dudir:`error`, the colours
  *sphinx<foo>bordercolor* and *sphinx<foo>bgcolor* can be
  re-defined using ``\definecolor`` command. The
  ``\sphinx<foo>border`` is a command (not a LaTeX length) which
  specifies the thickness of the frame (default ``1pt``) and can be
  ``\renewcommand`` 'd. The same applies with ``<foo>`` one of
  :dudir:`note`, :dudir:`hint`, :dudir:`important`, :dudir:`tip`, but
  the background colour is not implemented by the default environments
  and the top and bottom rule thickness default is ``0.5pt``.

  .. versionchanged:: 1.5
     customizability of the parameters for each type of admonition.
- paragraph level environments: for each admonition as in the previous item, the
  used environment is named ``sphinx<foo>``. They may be ``\renewenvironment``
  'd individually, and must then be defined with one argument (it is the heading
  of the notice, for example ``Warning:`` for :dudir:`warning` directive, if
  English is the document language). Their default definitions use either the
  *sphinxheavybox* (for the first listed directives) or the *sphinxlightbox*
  environments, configured to use the parameters (colours, border thickness)
  specific to each type, as mentioned in the previous item.

  .. versionchanged:: 1.5
     use of public environment names, separate customizability of the parameters.
- the :dudir:`contents` directive (with ``:local:`` option) and the
  :dudir:`topic` directive are implemented by environment ``sphinxShadowBox``.
  Its default definition obeys three LaTeX lengths (not commands) as parameters:
  ``\sphinxshadowsep`` (distance from contents), ``\sphinxshadowsize`` (width of
  lateral shadow), ``\sphinxshadowrule`` (thickness of the frame).

  .. versionchanged:: 1.5
     use of public names for the three lengths. The environment itself was
     redefined to allow page breaks at release 1.4.2.
- the literal blocks (:rst:dir:`code-block` directives, etc ...), are
  implemented using ``sphinxVerbatim`` environment which is a wrapper of
  ``Verbatim`` environment from package ``fancyvrb.sty``. It adds the handling
  of the top caption and the wrapping of long lines, and a frame which allows
  pagebreaks. The LaTeX lengths (not commands) ``\sphinxverbatimsep`` and
  ``\sphinxverbatimborder`` customize the framing. Inside tables the used
  environment is ``sphinxVerbatimintable`` (it does not draw a frame, but
  allows a caption).

  .. versionchanged:: 1.5
     ``Verbatim`` keeps exact same meaning as in ``fancyvrb.sty`` (meaning
     which is the one of ``OriginalVerbatim`` too), and custom one is called
     ``sphinxVerbatim``. Also, earlier version of Sphinx used
     ``OriginalVerbatim`` inside tables (captions were lost, long code lines
     were not wrapped), they now use ``sphinxVerbatimintable``.
  .. versionadded:: 1.5
     the two customizable lengths, the ``sphinxVerbatimintable``.
- by default the Sphinx style file ``sphinx.sty`` includes the command
  ``\fvset{fontsize=\small}`` as part of its configuration of
  ``fancyvrb.sty``. The user may override this for example via
  ``\fvset{fontsize=auto}`` which will use for listings the ambient
  font size. Refer to ``fancyvrb.sty``'s documentation for further keys.

  .. versionadded:: 1.5
     formerly, the use of ``\small`` for code listings was not customizable.
- miscellaneous colours: *InnerLinkColor*, *OuterLinkColor* (used in
  ``hyperref`` options), *TitleColor* (used for titles via  ``titlesec``),
  *VerbatimColor* (background colour) and *VerbatimBorderColor* (used for
  displaying source code examples).
- the ``\sphinxAtStartFootnote`` is inserted between footnote numbers and their
  texts, by default it does ``\mbox{ }``.
- the ``\sphinxBeforeFootnote`` command is executed before each footnote, its
  default definition is::

    \newcommand*{\sphinxBeforeFootnote}{\leavevmode\unskip}

  You can ``\renewcommand`` it to do nothing in order to recover the earlier
  behaviour of Sphinx, or alternatively add a ``\nobreak\space`` or a
  ``\thinspace`` after the ``\unskip`` in the definition to insert some
  (non-breakable) space.

  .. versionadded:: 1.5
     formerly, footnotes from explicit mark-up were preceded by a space
     allowing a linebreak, but automatically generated footnotes had no such
     space.
- use ``\sphinxSetHeaderFamily`` to set the font used by headings
  (default is ``\sffamily\bfseries``).

  .. versionadded:: 1.5
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
