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

Release 7.3.7 (released Apr 19, 2024)
=====================================

Bugs fixed
----------

* #12299: Defer loading themes defined via entry points until
  their explicit use by the user or a child theme.
  Patch by Adam Turner.
* #12305: Return the default value for ``theme.get_config()`` with
  an unsupported theme configuration section.
  Patch by Adam Turner.

Release 7.3.6 (released Apr 17, 2024)
=====================================

Bugs fixed
----------

* #12295: Re-export all AST types in the C and C++ domains.
  Patch by Adam Turner.
* #12295: Re-export various objects from ``sphinx.domains.python._annotations``
  in ``sphinx.domains.python``.
  Patch by Jacob Chesslo and Adam Turner.

Release 7.3.5 (released Apr 17, 2024)
=====================================

Bugs fixed
----------

* #12295: Re-export various objects from ``sphinx.domains.python._object``
  in ``sphinx.domains.python``.
  Patch by Jacob Chesslo and Adam Turner.

Release 7.3.4 (released Apr 17, 2024)
=====================================

Bugs fixed
----------

* Handle cases when ``Any`` is not an instance of ``type``.
  Patch by Adam Turner.

Release 7.3.3 (released Apr 17, 2024)
=====================================

Bugs fixed
----------

* #12290: Fix a false-positive warning when setting a configuration value
  with ``Any`` as the valid type to a type other than the value's default.
  Patch by Adam Turner.

Release 7.3.2 (released Apr 17, 2024)
=====================================

Bugs fixed
----------

* Preload all themes defined via entry points.
  Patch by Adam Turner.
* Fix a bad interaction between the ``'Furo'`` theme and the new-style for
  configuration values.
  Patch by Adam Turner.

Release 7.3.1 (released Apr 17, 2024)
=====================================

Dependencies
------------

* Require ``tomli`` on Python 3.10 and earlier.
  Patch by Adam Turner.

Release 7.3.0 (released Apr 16, 2024)
=====================================

Dependencies
------------

* #11858: Increase the minimum supported version of Alabaster to 0.7.14.
  Patch by Adam Turner.
* #11411: Support `Docutils 0.21`_. Patch by Adam Turner.

  .. _Docutils 0.21: https://docutils.sourceforge.io/RELEASE-NOTES.html#release-0-21-2024-04-09
* #12012: Use ``types-docutils`` instead of ``docutils-stubs``.

Deprecated
----------

* #11693: Support for old-style :file:`Makefile` and :file:`make.bat` output
  in :program:`sphinx-quickstart`, and the associated options :option:`!-M`,
  :option:`!-m`, :option:`!--no-use-make-mode`, and :option:`!--use-make-mode`.
* #11285: Direct access to :attr:`!sphinx.testing.util.SphinxTestApp._status`
  or :attr:`!sphinx.testing.util.SphinxTestApp._warning` is deprecated. Use
  the public properties :attr:`!sphinx.testing.util.SphinxTestApp.status`
  and :attr:`!sphinx.testing.util.SphinxTestApp.warning` instead.
  Patch by Bénédikt Tran.
* tests: :func:`!sphinx.testing.util.strip_escseq` is deprecated in favour of
  :func:`!sphinx.util.console.strip_colors`.
  Patch by Bénédikt Tran.

Features added
--------------

* #12265: Support theme configuration via ``theme.toml``.
* #11701: HTML Search: Adopt the new `\<search\>`_ element.
  Patch by Bénédikt Tran.

  .. _`\<search\>`: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/search
* #11776: Add long option names to ``sphinx-build``.
  Patch by Hugo van Kemenade, Adam Turner, Bénédikt Tran, and Ezio Melotti.
* Organise the ``sphinx-build`` options into groups.
  Patch by Adam Turner.
* #11855: Defer computation of configuration values.
  Patch by Adam Turner.
* Add ``:no-search:`` as an alias of the ``:nosearch:`` metadata field.
  Patch by Adam Turner.
* #11803: autodoc: Use an overridden ``__repr__()`` function in an enum,
  if defined. Patch by Shengyu Zhang.
* #11825: Allow custom targets in the manpage role.
  Patch by Nicolas Peugnet.
* #11892: Improved performance when resolving cross references in the C++ domain.
  Patch by Rouslan Korneychuk.
* #11905: Add a :rst:dir:`versionremoved` directive.
  Patch by Hugo van Kemenade, Adam Turner, and C.A.M. Gerlach.
* #11981: Improve rendering of signatures using ``slice`` syntax,
  e.g., ``def foo(arg: np.float64[:,:]) -> None: ...``.
* The manpage builder now adds `OSC 8`_ anchors to hyperlinks, using
  the `groff`_ device control command.

  .. _OSC 8: https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
  .. _groff: https://lists.gnu.org/archive/html/groff/2021-10/msg00000.html
* #11015: Change the text of the :rst:dir:`versionadded` directive from
  ``New in [...]`` to ``Added in [...]``.
  Patch by Bénédikt Tran.
* #12131: Added :confval:`show_warning_types` configuration option.
  Patch by Chris Sewell.
* #12193: Improve ``external`` warnings for unknown roles.
  In particular, suggest related role names if an object type is mistakenly used.
  Patch by Chris Sewell.
* Add public type alias :class:`sphinx.util.typing.ExtensionMetadata`.
  This can be used by extension developers
  to annotate the return type of their ``setup`` function.
  Patch by Chris Sewell.

Bugs fixed
----------

* #11668: Raise a useful error when ``theme.conf`` is missing.
  Patch by Vinay Sajip.
* #11622: Ensure that the order of keys in ``searchindex.js`` is deterministic.
  Patch by Pietro Albini.
* #11617: ANSI control sequences are stripped from the output when writing to
  a warnings file with :option:`-w <sphinx-build -w>`.
  Patch by Bénédikt Tran.
* #11666: Skip all hidden directories in ``CatalogRepository.pofiles``.
  Patch by Aryaz Eghbali.
* #9686: html builder: Fix MathJax lazy loading when equations appear in titles.
  Patch by Bénédikt Tran.
* #11483: singlehtml builder: Fix MathJax lazy loading when the index does not
  contain any math equations.
  Patch by Bénédikt Tran.
* #11697: HTML Search: add 'noindex' meta robots tag.
  Patch by James Addison.
* #11678: Fix a possible ``ZeroDivisionError`` in ``sphinx.ext.coverage``.
  Patch by Stephen Finucane.
* #11756: LaTeX: build error with recent TeXLive due to missing ``substitutefont``
  package (triggered if using ``fontenc`` with ``T2A`` option and document
  language is not a Cyrillic one).
  Patch by Jean-François B.
* #11675: Fix rendering of progression bars in environments that do not support
  ANSI control sequences.
  Patch by Bénédikt Tran.
* #11861: Whitelist more types with an incorrect ``__module__`` attribute.
  Patch by Adam Turner.
* #11715: Apply ``tls_verify`` and ``tls_cacerts`` config to
  ``ImageDownloader``.
  Patch by Nick Touran.
* Allow hyphens in group names for :rst:dir:`productionlist` cross-references.
  Patch by Adam Turner.
* #11433: Added the :confval:`linkcheck_allow_unauthorized` configuration option.
  Set this option to ``False`` to report HTTP 401 (unauthorized) server
  responses as broken.
  Patch by James Addison.
* #11868: linkcheck: added a distinct ``timeout`` reporting status code.
  This can be enabled by setting :confval:`linkcheck_report_timeouts_as_broken`
  to ``False``.
  Patch by James Addison.
* #11869: Refresh the documentation for the ``linkcheck_timeout`` setting.
  Patch by James Addison.
* #11874: Configure a default 30-second value for ``linkcheck_timeout``.
  Patch by James Addison.
* #11886: Print the Jinja2 template path chain in ``TemplateNotFound`` exceptions.
  Patch by Colin Marquardt.
* #11598: Do not use query components in URLs for assets in EPUB rendering.
  Patch by David Runge.
* #11904: Support unary subtraction when parsing annotations.
  Patch by James Addison.
* #11925: Blacklist the ``sphinxprettysearchresults`` extension; the functionality
  it provides was merged into Sphinx v2.0.0.
  Patch by James Addison.
* #11917: Fix rendering of annotated inherited members for Python 3.9.
  Patch by Janet Carson.
* #11935: C Domain: Fix namespace-pop context.
  Patch by Frank Dana.
* #11923: Avoid zombie processes when parallel builds fail.
  Patch by Felix von Drigalski.
* #11353: Support enumeration classes inheriting from mixin or data types.
  Patch by Bénédikt Tran.
* #11962: Fix target resolution when using ``:paramtype:`` fields.
  Patch by Bénédikt Tran.
* #11944: Use anchor in search preview.
  Patch by Will Lachance.
* #12008: Fix case-sensitive lookup of ``std:label`` names in intersphinx inventory.
  Patch by Michael Goerz.
* #11958: HTML Search: Fix partial matches overwriting full matches.
  Patch by William Lachance.
* #11959: Fix multiple term matching when word appears in both title and document.
  Patch by Will Lachance.
* #11474: Fix doctrees caching causing files not be rebuilt in some cases,
  e.g., when :confval:`numfig` is ``True``.
  Patch by Bénédikt Tran.
* #11278: autodoc: Fix rendering of :class:`functools.singledispatchmethod`
  combined with :func:`@classmethod <classmethod>`.
  Patch by Bénédikt Tran.
* #11894: Do not add checksums to css files if building using the htmlhelp builder.
  Patch by reduerK akiM.
* #12052: Remove ``<script>`` and ``<style>`` tags from the content of search result
  summary snippets.
  Patch by James Addison.
* #11578: HTML Search: Order non-main index entries after other results.
  Patch by Brad King.
* #12147: autosummary: Fix a bug whereby the wrong file extension
  may be used,
  when multiple suffixes are specified in :confval:`source_suffix`.
  Patch by Sutou Kouhei.
* #10786: improve the error message when a file to be copied (e.g., an asset)
  is removed during Sphinx execution.
  Patch by Bénédikt Tran.
* #12040: HTML Search: Ensure that document titles that are partially-matched by
  the user search query are included in search results.
  Patch by James Addison.
* #11970: singlehtml builder: make target URIs to be same-document references in
  the sense of :rfc:`RFC 3986, §4.4 <3986#section-4.4>`, e.g., ``index.html#foo``
  becomes ``#foo``. Patch by Eric Norige.
* #12271: Partially revert Docutils' r9562__ to fix EPUB files.
  Patch by Adam Turner.

  __ https://sourceforge.net/p/docutils/code/9562/
* #12253: Escape reserved path characters in the remote images post-transform
  download cache.
  Patch by James Addison and Adam Turner.

Testing
-------

* Reorganise tests into directories.
  Patch by Adam Turner.
* Clean up global state in ``SphinxTestApp``.
  Patch by Adam Turner.
* #11285: :func:`!pytest.mark.sphinx` and :class:`!sphinx.testing.util.SphinxTestApp`
  accept *warningiserror*, *keep_going* and *verbosity* as keyword arguments.
  Patch by Bénédikt Tran.
* #11285: :class:`!sphinx.testing.util.SphinxTestApp` *status* and *warning*
  arguments are checked to be :class:`io.StringIO` objects (the public API
  incorrectly assumed this without checking it).
  Patch by Bénédikt Tran.
* Report the result of ``test_run_epubcheck`` as ``skipped`` instead of
  ``success`` when either Java or ``epubcheck`` are not available.
* Use dynamic allocation of unused port numbers for the test HTTP(S) servers.
  As a side-effect, this removes the need for test server lockfiles,
  meaning that any remaining ``tests/test-server.lock`` files can safely be
  deleted.
