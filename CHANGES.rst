Release 8.1.0 (in development)
==============================

Dependencies
------------

Incompatible changes
--------------------

Deprecated
----------

Features added
--------------

Bugs fixed
----------

Testing
-------

Release 8.0.2 (released Jul 30, 2024)
=====================================

Bugs fixed
----------

* Fix the ``pygments.Formatter.__class_getitem__`` patch.
  Patch by Adam Turner.

Release 8.0.1 (released Jul 30, 2024)
=====================================

Bugs fixed
----------

* Patch ``pygments.Formatter.__class_getitem__`` in Pygments 2.17.
  Patch by Adam Turner.

Release 8.0.0 (released Jul 29, 2024)
=====================================

Dependencies
------------

* #12633: Drop Python 3.9 support.

Incompatible changes
--------------------

.. rst-class:: compact

* Remove deprecated functions from ``sphinx.util``:

  * Removed ``sphinx.util.path_stabilize``
    (use ``sphinx.util.osutil.path_stabilize``).
  * Removed ``sphinx.util.display_chunk``
    (use ``sphinx.util.display.display_chunk``).
  * Removed ``sphinx.util.status_iterator``
    (use ``sphinx.util.display.status_iterator``).
  * Removed ``sphinx.util.SkipProgressMessage``
    (use ``sphinx.util.display.SkipProgressMessage``).
  * Removed ``sphinx.util.progress_message``
    (use ``sphinx.util.display.progress_message``).
  * Removed ``sphinx.util.epoch_to_rfc1123``
    (use ``sphinx.http_date.epoch_to_rfc1123``).
  * Removed ``sphinx.util.rfc1123_to_epoch``
    (use ``sphinx.http_date.rfc1123_to_epoch``).
  * Removed ``sphinx.util.save_traceback``
    (use ``sphinx.exceptions.save_traceback``).
  * Removed ``sphinx.util.format_exception_cut_frames``
    (use ``sphinx.exceptions.format_exception_cut_frames``).
  * Removed ``sphinx.util.xmlname_checker``
    (use ``sphinx.builders.epub3._XML_NAME_PATTERN``).

  Patch by Adam Turner.
* Removed :py:func:`!sphinx.util.osutil.cd`
  (use :py:func:`contextlib.chdir`).
  Patch by Adam Turner.
* Removed :py:func:`!sphinx.util.typing.stringify`
  (use :py:func:`!sphinx.util.typing.stringify_annotation`).
  Patch by Adam Turner.
* #12593: Raise an error for invalid :confval:`html_sidebars` values.
  Patch by Adam Turner.
* #12593: Raise an error in :py:func:`!Theme.get_config` for invalid sections.
  Patch by Adam Turner.
* #11693: Remove support for old-style :file:`Makefile` and :file:`make.bat`
  output in :program:`sphinx-quickstart`.
* #11693: Remove the :option:`!--no-use-make-mode`, :option:`!-M`,
  :option:`!--use-make-mode`, and :option:`!-m` options
  from :program:`sphinx-quickstart`.
  Patch by Adam Turner.
* Removed the tuple interface to :py:class:`!sphinx.ext.autodoc.ObjectMember`.
  Patch by Adam Turner.
* #12630: Sphinx 8 makes two changes to the ``linkcheck`` configuration defaults:

  * :confval:`linkcheck_allow_unauthorized` is now ``False`` by default.
  * :confval:`linkcheck_report_timeouts_as_broken` is now ``False`` by default.

  Patch by James Addison.
* #12597: Change the default of :confval:`show_warning_types`
  from ``False`` to ``True``.
  Patch by Chris Sewell.
* #12083: Remove support for the old (2008--2010) Sphinx 0.5 and Sphinx 0.6
  :confval:`intersphinx_mapping` format.
  Patch by Bénédikt Tran and Adam Turner.
* #12096: Do not overwrite user-supplied files when copying assets
  unless forced with ``force=True``.
  Patch by Adam Turner.
* #12646: Remove :py:func:`!sphinx.util.inspect.isNewType`.
  Use ``isinstance(obj, typing.NewType)`` instead on Python 3.10 and newer.
  Patch by Adam Turner.
* Remove the long-deprecated (since Sphinx 2) alias
  to :py:class:`!VersionChange` in
  :py:mod:`!sphinx.directives.other`
  (Deprecated since Sphinx 2).
  Use :py:class:`!sphinx.domains.changeset.VersionChange` directly.
  Patch by Adam Turner.

Deprecated
----------

* #12643: Renamed ``sphinx.ext.intersphinx.normalize_intersphinx_mapping``
  to ``sphinx.ext.intersphinx.validate_intersphinx_mapping``.
  The old name will be removed in Sphinx 10.
  Patch by Adam Turner.
* #12650, #12686, #12690: Extend the deprecation for string methods on
  :py:class:`~pathlib.Path` objects to Sphinx 9.
  Use :py:func:`os.fspath` to convert :py:class:`~pathlib.Path` objects to strings,
  or :py:class:`~pathlib.Path`'s methods to work with path objects.
  Patch by Adam Turner.

Release 7.4.7 (released Jul 20, 2024)
=====================================

Bugs fixed
----------

* #12096: Warn when files are overwritten in the build directory.
  Patch by Adam Turner and Bénédikt Tran.
* #12620: Ensure that old-style object description options are respected.
  Patch by Adam Turner.
* #12601, #12625: Support callable objects in :py:class:`~typing.Annotated` type
  metadata in the Python domain.
  Patch by Adam Turner.
* #12601, #12622: Resolve :py:class:`~typing.Annotated` warnings with
  ``sphinx.ext.autodoc``,
  especially when using :mod:`dataclasses` as type metadata.
  Patch by Adam Turner.
* #12589, #12626: autosummary: Fix warnings with :rst:role:`!autolink`.
  Patch by Adam Turner.

Release 7.4.6 (released Jul 18, 2024)
=====================================

Bugs fixed
----------

* #12589, #9743, #12609: autosummary: Do not add the package prefix when
  generating autosummary directives for modules within a package.
  Patch by Adam Turner.
* #12613: Reduce log severity for ambiguity detection during inventory loading.
  Patch by James Addison.

Release 7.4.5 (released Jul 16, 2024)
=====================================

Bugs fixed
----------

* #12593, #12600: Revert coercing the type of selected :confval:`html_sidebars`
  values to a list.
  Log an error message when string values are detected.
  Patch by Adam Turner.
* #12594: LaTeX: since 7.4.0, :rst:dir:`seealso` and other "light" admonitions
  now break PDF builds if they contain a :dudir:`figure` directive; and also
  if they are contained in a table cell (rendered by ``tabulary``).
  Patch by Jean-François B.

Release 7.4.4 (released Jul 15, 2024)
=====================================

Bugs fixed
----------

* #12585, #12586: Do not warn when an intersphinx inventory contains
  case-insensitively ambiguous duplicate items.
  Patch by James Addison.

Release 7.4.3 (released Jul 15, 2024)
=====================================

Bugs fixed
----------

* #12582: Restore support for list-styled :confval:`source_suffix` values
  with extensions that register parsers.
  Patch by Adam Turner.

Release 7.4.2 (released Jul 15, 2024)
=====================================

Bugs fixed
----------

* #12580, #12583: Resolve failures with the C domain on incremental builds
  with Sphinx 7.3.7 and earlier.
  Patch by Adam Turner.

Release 7.4.1 (released Jul 15, 2024)
=====================================

Bugs fixed
----------

* Fix invalid HTML when a rubric node with invalid ``heading-level`` is used.
  Patch by Adam Turner.
* #12579, #12581: Restore support for ``typing.ParamSpec`` in autodoc.
  Patch by Adam Turner.

Release 7.4.0 (released Jul 15, 2024)
=====================================

Dependencies
------------

* #12555: Drop Docutils 0.18.1 and Docutils 0.19 support.
  Patch by Adam Turner.
* LaTeX: the ``xcolor`` package is now required (but is for example part of
  Ubuntu ``texlive-latex-recommended`` which has always been required).
* LaTeX: the ``fontawesome5`` LaTeX package is needed for the default choices
  of icons now used in admonition titles in PDF output; but if unavailable the
  PDF build will simply silently omit rendering such icons.  Check the
  documentation of the ``iconpackage`` key of :ref:`'sphinxsetup'
  <latexsphinxsetup>` for more.

Deprecated
----------

* LaTeX: the ``sphinxlightbox`` environment is not used anymore, all types
  of admonitions use (by default) only ``sphinxheavybox``.

Features added
--------------

.. rst-class:: compact

* #11165: Support the `officially recommended`_ ``.jinja`` suffix for template
  files.
  Patch by James Addison and Adam Turner

  .. _officially recommended: https://jinja.palletsprojects.com/en/latest/templates/#template-file-extension
* #12325: Flatten ``Union[Literal[T], Literal[U], ...]`` to ``Literal[T, U, ...]``
  when turning annotations into strings.
  Patch by Adam Turner.
* #12319: ``sphinx.ext.extlinks``: Add ``extlink-{name}`` CSS class to links.
  Patch by Hugo van Kemenade.
* #12387: Improve CLI progress message, when copying assets.
  Patch by INADA Nakoi and Bénédikt Tran.
* #12361: Add :attr:`.BuildEnvironment.parser`.
  Patch by Chris Sewell.
* #12358: Add :attr:`.Sphinx.fresh_env_used`.
  Patch by Chris Sewell.
* #12329: Add detection of ambiguous ``std:label`` and ``std:term`` references during
  loading and resolution of Intersphinx targets.
  Patch by James Addison.
* #12422: Do not duplicate "navigation" in aria-label of built-in themes.
  Patch by Thomas Weißschuh
* #12421: Include project name in ``logo_alt`` of built-in themes.
  Patch by Thomas Weißschuh
* #12448: Add :option:`sphinx-apidoc --remove-old` option.
  Patch by Chris Sewell.
* #12456: Add :option:`sphinx-autogen --remove-old` option.
  Patch by Chris Sewell.
* #12479: Add warning subtype ``toc.no_title``.
  Patch by Ondřej Navrátil.
* #12492: Add helper methods for parsing reStructuredText content into nodes from
  within a directive.

  - :py:meth:`~sphinx.util.docutils.SphinxDirective.parse_content_to_nodes()`
    parses the directive's content and returns a list of Docutils nodes.
  - :py:meth:`~sphinx.util.docutils.SphinxDirective.parse_text_to_nodes()`
    parses the provided text and returns a list of Docutils nodes.
  - :py:meth:`~sphinx.util.docutils.SphinxDirective.parse_inline()`
    parses the provided text into inline elements and text nodes.

  Patch by Adam Turner.
* #12258: Support ``typing_extensions.Unpack``
  Patch by Bénédikt Tran and Adam Turner.
* #12524: Add a ``class`` option to the :rst:dir:`toctree` directive.
  Patch by Tim Hoffmann.
* #12536: Add the :rst:dir:`confval` directive.
  Patch by Adam Turner.
* #12537: :confval:`c_id_attributes`, :confval:`c_paren_attributes`,
  :confval:`cpp_id_attributes`, and :confval:`cpp_paren_attributes`
  can now be a tuple of strings.
  :confval:`c_extra_keywords`, :confval:`gettext_additional_targets`,
  :confval:`html_domain_indices`, :confval:`latex_domain_indices`,
  and :confval:`texinfo_domain_indices`,
  can now be a set of strings.
  Patch by Adam Turner.
* #12523: Added configuration option, :confval:`math_numsep`, to define the
  separator for math numbering.
  Patch by Thomas Fanning
* #11592: Add :confval:`coverage_modules` to the coverage builder
  to allow explicitly specifying which modules should be documented.
  Patch by Stephen Finucane.
* #7896, #11989: Add a :rst:dir:`py:type` directive for documenting type aliases,
  and a :rst:role:`py:type` role for linking to them.
  Patch by Ashley Whetter.
* #12549: Add optional ``description`` argument to
  :meth:`.Sphinx.add_config_value`.
  Patch by Chris Sewell.
* #6792: Prohibit module import cycles in :mod:`sphinx.ext.autosummary`.
  Patch by Trevor Bekolay.
* #12508: LaTeX: Revamped styling of all admonitions, with addition of a
  title row with icon.
  Patch by Jean-François B.
* #11773: Display :py:class:`~typing.Annotated` annotations
  with their metadata in the Python domain.
  Patch by Adam Turner and David Stansby.
* #12506: Add ``heading-level`` option to :rst:dir:`rubric` directive.
  Patch by Chris Sewell.
* #12567: Add the :event:`write-started` event.
  Patch by Chris Sewell.

Bugs fixed
----------

* #12314: Properly format ``collections.abc.Callable`` in annotations.
  Patch by Adam Turner.
* #12162: Fix a performance regression in the C domain that has
  been present since version 3.0.0.
  Patch by Donald Hunter.
* #12320: Fix removal of anchors from search summaries (regression in 7.3.0).
  Patch by Will Lachance.
* #12251: Fix ``merge_domaindata()`` in ``sphinx.ext.duration``.
  Patch by Matthias Geier.
* #12224: Properly detect WebP files.
  Patch by Benjamin Cabé.
* #12380: LaTeX: Avoid footnote markers ``Page N`` when ``N`` is already
  the current page number.
  Patch by Jean-François B.
* #12410: LaTeX: for French and ``'lualatex'`` as :confval:`latex_engine`
  use ``babel`` as with ``'xelatex'`` (and not ``polyglossia``).
  Patch by Jean-François B.
* #12520: LaTeX: let :rst:dir:`todolist` produce correct hyperlinks in PDF.
  Patch by Jean-François B.
* #12416: Ensure that configuration setting aliases are always synchronised
  when one value or the other is modified.
  Patch by Bénédikt Tran.
* #12220: Fix loading custom template translations for ``en`` locale.
  Patch by Nicolas Peugnet.
* #12459: Add valid-type arguments to the ``linkcheck_rate_limit_timeout``
  configuration setting.
  Patch by James Addison.
* #12331: Resolve data-URI-image-extraction regression from v7.3.0 affecting
  builders without native support for data-URIs in their output format.
  Patch by James Addison.
* #12494: Fix invalid genindex.html file produced with translated docs
  (regression in 7.1.0).
  Patch by Nicolas Peugnet.
* #11961: Omit anchor references from document title entries in the search index,
  removing duplication of search results.
  Patch by James Addison.
* #12425: Use Docutils' SVG processing in the HTML builder
  and remove Sphinx's custom logic.
  Patch by Tunç Başar Köse.
* #12391: Adjust scoring of matches during HTML search so that document main
  titles tend to rank higher than subsection titles. In addition, boost matches
  on the name of programming domain objects relative to title/subtitle matches.
  Patch by James Addison and Will Lachance.
* #9634: Do not add a fallback language by stripping the country code.
  Patch by Alvin Wong.
* #12352: Add domain objects to the table of contents
  in the same order as defined in the document.
  Previously, each domain used language-specific nesting rules,
  which removed control from document authors.
  Patch by Jakob Lykke Andersen and Adam Turner.
* #11041: linkcheck: Ignore URLs that respond with non-Unicode content.
  Patch by James Addison.
* #12543: Fix :pep:`695` formatting for LaTeX output.
  Patch by Bénédikt Tran.

Testing
-------

* karma: refactor HTML search tests to use fixtures generated by Sphinx.
  Patch by James Addison.
