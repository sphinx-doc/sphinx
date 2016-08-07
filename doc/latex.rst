.. highlightlang:: python

.. _latex:

LaTeX customization
===================

.. module:: latex
   :synopsis: LaTeX specifics.

The *latex* target does not (yet) benefit from pre-prepared themes like the
*html* target does (see :doc:`theming`).

There are two principal means of setting up customization:

#. usage of the :ref:`latex-options` as described in :doc:`config`, particularly the
   various keys of :confval:`latex_elements`, to modify the loaded packages,
   for example::

        'fontpkg':  '\\usepackage{times}',            # can load other font
        'fncychap': '\\usepackage[Bjarne]{fncychap}', # can use other option

   .. tip::

      It is not mandatory to load *fncychap*. Naturally, without it and in
      absence of further customizations, the chapter headings will revert to
      LaTeX's default for the *report* class.

#. usage of LaTeX ``\renewcommand``, ``\renewenvironment``, ``\setlength``,
   ``\definecolor`` to modify the defaults from package file :file:`sphinx.sty`
   and class files :file:`sphinxhowto.cls` and :file:`sphinxmanual.cls`. If such
   definitions are few, they can be located inside the ``'preamble'`` key of
   :confval:`latex_elements`. In case of many it may prove more convenient to
   assemble them into a specialized file :file:`customizedmacros.tex` and use::

       'preamble': '\\makeatletter\\input{customizedmacros.tex}\\makeatother',

   More advanced LaTeX users will set up a style file
   :file:`customizedmacros.sty`, which can then be loaded via::

       'preamble': '\\usepackage{customizedmacros}',

   The :ref:`build configuration file <build-config>` file will then have its variable
   :confval:`latex_additional_files` appropriately configured, for example::

       latex_additional_files = ["customizedmacros.sty"]

   Such *LaTeX Sphinx theme* files could possibly be contributed in the
   future by advanced users for wider use.

Let us illustrate here what can be modified by the second method.

- text styling commands (they have one argument): ``\sphinx<foo>`` with
  ``<foo>`` being one of ``strong``, ``bfcode``, ``email``, ``tablecontinued``,
  ``titleref``, ``menuselection``, ``accelerator``, ``crossref``, ``termref``,
  ``optional``. By default and for backwards compatibility the ``\sphinx<foo>``
  expands to ``\<foo>`` hence the user can choose to customize rather the latter
  (the non-prefixed macros will be left undefined if option
  :confval:`latex_keep_old_macro_names` is set to ``False`` in :file:`conf.py`.)

  .. versionchanged:: 1.4.5
     use of ``\sphinx`` prefixed macro names to limit possibilities of conflict
     with user added packages. The LaTeX writer uses always the prefixed names.
- more text styling commands: ``\sphinxstyle<bar>`` with ``<bar>`` one of
  ``indexentry``, ``indexextra``, ``indexpageref``, ``topictitle``,
  ``sidebartitle``, ``othertitle``, ``sidebarsubtitle``, ``thead``,
  ``emphasis``, ``literalemphasis``, ``strong``, ``literalstrong``,
  ``abbreviation``, ``literalintitle``.

  .. versionadded:: 1.5
     earlier, the LaTeX writer used hard-coded ``\texttt``, ``\emph``, etc...
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
- miscellaneous colours: *TitleColor*, *InnerLinkColor*, *OuterLinkColor*,
  *VerbatimColor* (this is a background colour), *VerbatimBorderColor*.
- the ``\sphinxAtStartFootnote`` is inserted between footnote numbers and their
  texts, by default it does ``\mbox{ }``.
- use ``\sphinxSetHeaderFamily`` to set the font used by headings
  (default is ``\sffamily\bfseries``).

  .. versionadded:: 1.5
- the section, subsection, ...  headings are set using  *titlesec*'s
  ``\titleformat`` command.
- for the ``'manual'`` class, the chapter headings can be customized using
  *fncychap*'s commands ``\ChNameVar``, ``\ChNumVar``, ``\ChTitleVar``. Or, if
  the loading of this package has been removed from ``'fncychap'`` key, one can
  use the *titlesec* ``\titleformat`` command.

.. note::

   It is impossible to revert or prevent the loading of a package that results
   from a ``\usepackage`` executed from inside the :file:`sphinx.sty` style
   file. Sphinx aims at loading as few packages as are really needed for its
   default design.
