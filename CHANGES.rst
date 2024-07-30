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

Release 7.2.6 (released Sep 13, 2023)
=====================================

Bugs fixed
----------

* #11679: Add the :envvar:`!SPHINX_AUTODOC_RELOAD_MODULES` environment variable,
  which if set reloads modules when using autodoc with ``TYPE_CHECKING = True``.
  Patch by Matt Wozniski and Adam Turner.
* #11679: Use :py:func:`importlib.reload` to reload modules in autodoc.
  Patch by Matt Wozniski and Adam Turner.

Release 7.2.5 (released Aug 30, 2023)
=====================================

Bugs fixed
----------

* #11645: Fix a regression preventing autodoc from importing modules within
  packages that make use of ``if typing.TYPE_CHECKING:`` to guard circular
  imports needed by type checkers.
  Patch by Matt Wozniski.
* #11634: Fixed inheritance diagram relative link resolution
  for sibling files in a subdirectory.
  Patch by Albert Shih.
* #11659: Allow ``?config=...`` in :confval:`mathjax_path`.
* #11654: autodoc: Fail with a more descriptive error message
  when an object claims to be an instance of ``type``,
  but is not a class.
  Patch by James Braza.
* 11620: Cease emitting :event:`source-read` events for files read via
  the :dudir:`include` directive.
* 11620: Add a new :event:`include-read` for observing and transforming
  the content of included files via the :dudir:`include` directive.
* #11627: Restore support for copyright lines of the form ``YYYY``
  when ``SOURCE_DATE_EPOCH`` is set.

Release 7.2.4 (released Aug 28, 2023)
=====================================

Bugs fixed
----------

* #11618: Fix a regression in the MoveModuleTargets transform,
  introduced in #10478 (#9662).
* #11649: linkcheck: Resolve hanging tests for timezones west of London
  and incorrect conversion from UTC to offsets from the UNIX epoch.
  Patch by Dmitry Shachnev and Adam Turner.

Release 7.2.3 (released Aug 23, 2023)
=====================================

Dependencies
------------

* #11576: Require sphinxcontrib-serializinghtml 1.1.9.

Bugs fixed
----------

* Fix regression in ``autodoc.Documenter.parse_name()``.
* Fix regression in JSON serialisation.
* #11543: autodoc: Support positional-only parameters in ``classmethod`` methods
  when ``autodoc_preserve_defaults`` is ``True``.
* Restore support string methods on path objects.
  This is deprecated and will be removed in Sphinx 8.
  Use :py:func:`os.fspath` to convert :py:class:`~pathlib.Path` objects to strings,
  or :py:class:`~pathlib.Path`'s methods to work with path objects.

Release 7.2.2 (released Aug 17, 2023)
=====================================

Bugs fixed
----------

* Fix the signature of the ``StateMachine.insert_input()`` patch,
  for when calling with keyword arguments.
* Fixed membership testing (``in``) for the :py:class:`str` interface
  of the asset classes (``_CascadingStyleSheet`` and ``_JavaScript``),
  which several extensions relied upon.
* Fixed a type error in ``SingleFileHTMLBuilder._get_local_toctree``,
  ``includehidden`` may be passed as a string or a boolean.
* Fix ``:noindex:`` for ``PyModule`` and ``JSModule``.

Release 7.2.1 (released Aug 17, 2023)
=====================================

Bugs fixed
----------

* Restored the the :py:class:`str` interface of the asset classes
  (``_CascadingStyleSheet`` and ``_JavaScript``),
  which several extensions relied upon.
  This will be removed in Sphinx 9.
* Restored calls to ``Builder.add_{css,js}_file()``,
  which several extensions relied upon.
* Restored the private API ``TocTree.get_toctree_ancestors()``,
  which several extensions relied upon.

Release 7.2.0 (released Aug 17, 2023)
=====================================

Dependencies
------------

* #11511: Drop Python 3.8 support.
* #11576: Require Pygments 2.14 or later.

Deprecated
----------

* #11512: Deprecate ``sphinx.util.md5`` and ``sphinx.util.sha1``.
  Use ``hashlib`` instead.
* #11526: Deprecate ``sphinx.testing.path``.
  Use ``os.path`` or ``pathlib`` instead.
* #11528: Deprecate ``sphinx.util.split_index_msg`` and ``sphinx.util.split_into``.
  Use ``sphinx.util.index_entries.split_index_msg`` instead.
* Deprecate ``sphinx.builders.html.Stylesheet``
  and ``sphinx.builders.html.Javascript``.
  Use ``sphinx.application.Sphinx.add_css_file()``
  and ``sphinx.application.Sphinx.add_js_file()`` instead.
* #11582: Deprecate ``sphinx.builders.html.StandaloneHTMLBuilder.css_files`` and
  ``sphinx.builders.html.StandaloneHTMLBuilder.script_files``.
  Use ``sphinx.application.Sphinx.add_css_file()``
  and ``sphinx.application.Sphinx.add_js_file()`` instead.
* #11459: Deprecate ``sphinx.ext.autodoc.preserve_defaults.get_function_def()``.
  Patch by Bénédikt Tran.

Features added
--------------

* #11526: Support ``os.PathLike`` types and ``pathlib.Path`` objects
  in many more places.
* #5474: coverage: Print summary statistics tables.
  Patch by Jorge Leitao.
* #6319: viewcode: Add :confval:`viewcode_line_numbers` to control
  whether line numbers are added to rendered source code.
  Patch by Ben Krikler.
* #9662: Add the ``:no-typesetting:`` option to suppress textual output
  and only create a linkable anchor.
  Patch by Latosha Maltba.
* #11221: C++: Support domain objects in the table of contents.
  Patch by Rouslan Korneychuk.
* #10938: doctest: Add :confval:`doctest_show_successes` option.
  Patch by Trey Hunner.
* #11533: Add ``:no-index:``, ``:no-index-entry:``, and ``:no-contents-entry:``.
* #11572: Improve ``debug`` logging of reasons why files are detected as out of
  date.
  Patch by Eric Larson.
* #10678: Emit :event:`source-read` events for files read via
  the :dudir:`include` directive.
  Patch by Halldor Fannar.
* #11570: Use short names when using :pep:`585` built-in generics.
  Patch by Riccardo Mori.
* #11300: Improve ``SigElementFallbackTransform`` fallback logic and signature
  text elements nodes. See :doc:`the documentation </extdev/nodes>` for more
  details.
  Patch by Bénédikt Tran.
* Allow running Sphinx with ``python -m sphinx build ...``.

Bugs fixed
----------

* #11077: graphviz: Fix relative links from within the graph.
  Patch by Ralf Grubenmann.
* #11529: Line Block in LaTeX builder outputs spurious empty token.
  Patch by Adrian Vollmer.
* #11196: autosummary: Summary line extraction failed with "e.g."
* #10614: Fixed a number of bugs in inheritance diagrams that resulted in
  missing or broken links.
  Patch by Albert Shih.
* #9428: Exclude substitution definitions when running the ``gettext`` builder.
  Patch by Alvin Wong.
* #10795: Raise a descriptive error if ``graphviz_dot`` is falsy.
* #11546: Translated nodes identical to their original text are now marked
  with the ``translated=True`` attribute.
* #10049: html: Change "Permalink" to "Link" for title text in link anchors.
* #4225: Relax Pygments parsing on lexing failures.
* #11246: Allow inline links in the first line of a docstring and one-line
  type comments ``#: :meta ...:`` when using :mod:`sphinx.ext.napoleon`.
  Patch by Bénédikt Tran.
* #10930: Highlight all search terms on the search results page.
  Patch by Dmitry Shachnev.
* #11473: Type annotations containing :py:data:`~typing.Literal` enumeration
  values now render correctly.
  Patch by Bénédikt Tran.
* #11591: Fix support for C coverage in ``sphinx.ext.coverage`` extension.
  Patch by Stephen Finucane.
* #11594: HTML Theme: Enhancements to horizontal scrolling on smaller
  devices in the ``agogo`` theme.
  Patch by Lukas Engelter.
* #11459: Fix support for async and lambda functions in
  ``sphinx.ext.autodoc.preserve_defaults``.
  Patch by Bénédikt Tran.

Testing
-------

* #11577: pytest: Fail tests on "XPASS".
* #11577: pytest: Use "importlib" import mode.
* #11577: pytest: Set PYTHONWARNINGS=error.
* #11577: pytest: Set strict config and strict markers.

Release 7.1.2 (released Aug 02, 2023)
=====================================

Bugs fixed
----------

* #11542: linkcheck: Properly respect :confval:`linkcheck_anchors`
  and do not spuriously report failures to validate anchors.
  Patch by James Addison.

Release 7.1.1 (released Jul 27, 2023)
=====================================

Bugs fixed
----------

* #11514: Fix ``SOURCE_DATE_EPOCH`` in multi-line copyright footer.
  Patch by Bénédikt Tran.

Release 7.1.0 (released Jul 24, 2023)
=====================================

Incompatible changes
--------------------

* Releases are no longer signed, given the `change in PyPI policy`_.

  .. _change in PyPI policy: https://blog.pypi.org/posts/2023-05-23-removing-pgp/

Deprecated
----------

* #11412: Emit warnings on using a deprecated Python-specific index entry type
  (namely, ``module``, ``keyword``, ``operator``, ``object``, ``exception``,
  ``statement``, and ``builtin``) in the :rst:dir:`index` directive, and
  set the removal version to Sphinx 9. Patch by Adam Turner.

Features added
--------------

* #11415: Add a checksum to JavaScript and CSS asset URIs included within
  generated HTML, using the CRC32 algorithm.
* :meth:`~sphinx.application.Sphinx.require_sphinx` now allows the version
  requirement to be specified as ``(major, minor)``.
* #11011: Allow configuring a line-length limit for object signatures, via
  :confval:`maximum_signature_line_length` and the domain-specific variants.
  If the length of the signature (in characters) is greater than the configured
  limit, each parameter in the signature will be split to its own logical line.
  This behaviour may also be controlled by options on object description
  directives, for example :rst:dir:`py:function:single-line-parameter-list`.
  Patch by Thomas Louf, Adam Turner, and Jean-François B.
* #10983: Support for multiline copyright statements in the footer block.
  Patch by Stefanie Molin
* ``sphinx.util.display.status_iterator`` now clears the current line
  with ANSI control codes, rather than overprinting with space characters.
* #11431: linkcheck: Treat SSL failures as broken links.
  Patch by James Addison.
* #11157: Keep the ``translated`` attribute on translated nodes.
* #11451: Improve the traceback displayed when using :option:`sphinx-build -T`
  in parallel builds. Patch by Bénédikt Tran
* #11324: linkcheck: Use session-basd HTTP requests.
* #11438: Add support for the :rst:dir:`py:class` and :rst:dir:`py:function`
  directives for PEP 695 (generic classes and functions declarations) and
  PEP 696 (default type parameters).  Multi-line support (#11011) is enabled
  for type parameters list and can be locally controlled on object description
  directives, e.g., :rst:dir:`py:function:single-line-type-parameter-list`.
  Patch by Bénédikt Tran.
* #11484: linkcheck: Allow HTML anchors to be ignored on a per-URL basis
  via :confval:`linkcheck_anchors_ignore_for_url` while
  still checking the validity of the page itself.
  Patch by Bénédikt Tran
* #1246: Add translation progress statistics and inspection support,
  via a new substitution (``|translation progress|``) and a new
  configuration variable (:confval:`translation_progress_classes`).
  These enable determining the percentage of translated elements within
  a document, and the remaining translated and untranslated elements.

Bugs fixed
----------

* Restored the ``footnote-reference`` class that has been removed in
  the latest (unreleased) version of Docutils.
* #11486: Use :rfc:`8081` font file MIME types in the EPUB builder.
  Using the correct MIME type will prevent warnings from ``epubcheck``
  and will generate a valid EPUB.
* #11435: Use microsecond-resolution timestamps for outdated file detection
  in ``BuildEnvironment.get_outdated_files``.
* #11437: Top-level headings starting with a reStructuredText role
  now render properly when :confval:`rst_prolog` is set.
  Previously, a file starting with the below would have
  improperly rendered due to where the prologue text
  was inserted into the document.

  .. code:: rst

     :mod:`lobster` -- The lobster module
     ====================================

     ...

  Patch by Bénédikt Tran.
* #11337: Fix a ``MemoryError`` in ``sphinx.ext.intersphinx`` when using ``None``
  or ``typing.*`` as inline type references. Patch by Bénédikt Tran (picnixz)

Testing
-------

* #11345: Always delete ``docutils.conf`` in test directories when running
  ``SphinxTestApp.cleanup()``.

Release 7.0.1 (released May 12, 2023)
=====================================

Dependencies
------------

* #11411: Support `Docutils 0.20`_. Patch by Adam Turner.

.. _Docutils 0.20: https://docutils.sourceforge.io/RELEASE-NOTES.html#release-0-20-2023-05-04

Bugs fixed
----------

* #11418: Clean up remaining references to ``sphinx.setup_command``
  following the removal of support for setuptools.
  Patch by Willem Mulder.

Release 7.0.0 (released Apr 29, 2023)
=====================================

Incompatible changes
--------------------

* #11359: Remove long-deprecated aliases for ``MecabSplitter`` and
  ``DefaultSplitter`` in ``sphinx.search.ja``.
* #11360: Remove deprecated ``make_old_id`` functions in domain object
  description classes.
* #11363: Remove the Setuptools integration (``build_sphinx`` hook in
  ``setup.py``).
* #11364: Remove deprecated ``sphinx.ext.napoleon.iterators`` module.
* #11365: Remove support for the ``jsdump`` format in ``sphinx.search``.
* #11366: Make ``locale`` a required argument to
  ``sphinx.util.i18n.format_date()``.
* #11370: Remove deprecated ``sphinx.util.stemmer`` module.
* #11371: Remove deprecated ``sphinx.pycode.ast.parse()`` function.
* #11372: Remove deprecated ``sphinx.io.read_doc()`` function.
* #11373: Removed deprecated ``sphinx.util.get_matching_files()`` function.
* #11378: Remove deprecated ``sphinx.util.docutils.is_html5_writer_available()``
  function.
* #11379: Make the ``env`` argument to ``Builder`` subclasses required.
* #11380: autosummary: Always emit grouped import exceptions.
* #11381: Remove deprecated ``style`` key for HTML templates.
* #11382: Remove deprecated ``sphinx.writers.latex.LaTeXTranslator.docclasses``
  attribute.
* #11383: Remove deprecated ``sphinx.builders.html.html5_ready`` and
  ``sphinx.builders.html.HTMLTranslator`` attributes.
* #11385: Remove support for HTML 4 output.

Release 6.2.1 (released Apr 25, 2023)
=====================================

Bugs fixed
----------

* #11355: Revert the default type of :confval:`nitpick_ignore` and
  :confval:`nitpick_ignore_regex` to ``list``.

Release 6.2.0 (released Apr 23, 2023)
=====================================

Dependencies
------------

* Require Docutils 0.18.1 or greater.

Incompatible changes
--------------------

* LaTeX: removal of some internal TeX ``\dimen`` registers (not previously
  publicly documented) as per 5.1.0 code comments in ``sphinx.sty``:
  ``\sphinxverbatimsep``, ``\sphinxverbatimborder``, ``\sphinxshadowsep``,
  ``\sphinxshadowsize``, and ``\sphinxshadowrule``. (refs: #11105)
* Remove ``.egg`` support from pycode ``ModuleAnalyser``; Python eggs are a
  now-obsolete binary distribution format
* #11089: Remove deprecated code in ``sphinx.builders.linkcheck``.
  Patch by Daniel Eades
* Remove internal-only ``sphinx.locale.setlocale``

Deprecated
----------

* #11247: Deprecate the legacy ``intersphinx_mapping`` format
* ``sphinx.util.osutil.cd`` is deprecated in favour of ``contextlib.chdir``.

Features added
--------------

* #11277: :rst:dir:`autoproperty` allows the return type to be specified as
  a type comment (e.g., ``# type: () -> int``). Patch by Bénédikt Tran
* #10811: Autosummary: extend ``__all__`` to imported members for template rendering
  when option ``autosummary_ignore_module_all`` is set to ``False``. Patch by
  Clement Pinard
* #11147: Add a ``content_offset`` parameter to ``nested_parse_with_titles()``,
  allowing for correct line numbers during nested parsing.
  Patch by Jeremy Maitin-Shepard
* Update to Unicode CLDR 42
* Add a ``--jobs`` synonym for ``-j``. Patch by Hugo van Kemenade
* LaTeX: a command ``\sphinxbox`` for styling text elements with a (possibly
  rounded) box, optional background color and shadow, has been added.
  See :ref:`sphinxbox`. (refs: #11224)
* LaTeX: add ``\sphinxstylenotetitle``, ..., ``\sphinxstylewarningtitle``, ...,
  for an extra layer of mark-up freeing up ``\sphinxstrong`` for other uses.
  See :ref:`latex-macros`. (refs: #11267)
* LaTeX: :dudir:`note`, :dudir:`hint`, :dudir:`important` and :dudir:`tip` can
  now each be styled as the other admonitions, i.e. possibly with a background
  color, individual border widths and paddings, possibly rounded corners, and
  optional shadow.  See :ref:`additionalcss`. (refs: #11234)
* LaTeX: admonitions and :dudir:`topic` (and
  :dudir:`contents <table-of-contents>`) directives, and not only
  :rst:dir:`code-block`, support ``box-decoration-break=slice``.
* LaTeX: let rounded boxes support up to 4 distinct border-widths (refs: #11243)
* LaTeX: new options ``noteTextColor``, ``noteTeXextras`` et al.
  See :ref:`additionalcss`.
* LaTeX: support elliptical corners in rounded boxes. (refs: #11254)
* #11150: Include source location in highlighting warnings, when lexing fails.
  Patch by Jeremy Maitin-Shepard
* #11281: Support for :confval:`imgmath_latex` ``= 'tectonic'`` or
  ``= 'xelatex'``.  Patch by Dimitar Dimitrov
* #11109, #9643: Add :confval:`python_display_short_literal_types` option for
  condensed rendering of ``Literal`` types.

Bugs fixed
----------

* #11079: LaTeX: figures with align attribute may disappear and strangely impact
  following lists
* #11093: LaTeX: fix "multiply-defined references" PDF build warnings when one or
  more reST labels directly precede an :rst:dir:`py:module` or :rst:dir:`automodule`
  directive. Patch by Bénédikt Tran (picnixz)
* #11110: LaTeX: Figures go missing from latex pdf if their files have the same
  base name and they use a post transform.  Patch by aaron-cooper
* LaTeX: fix potential color leak from shadow to border of rounded boxes, if
  shadow color is set but border color is not
* LaTeX: fix unintended 1pt upwards vertical shift of code blocks frames
  respective to contents (when using rounded corners)
* #11235: LaTeX: added ``\color`` in topic (or admonition) contents may cause color
  leak to the shadow and border at a page break
* #11264: LaTeX: missing space before colon after "Voir aussi" for :rst:dir:`seealso`
  directive in French
* #11268: LaTeX: longtable with left alignment breaks out of current list
  indentation context in PDF.  Thanks to picnixz.
* #11274: LaTeX: external links are not properly escaped for ``\sphinxupquote``
  compatibility
* #11147: Fix source file/line number info in object description content and in
  other uses of ``nested_parse_with_titles``.  Patch by Jeremy Maitin-Shepard.
* #11192: Restore correct parallel search index building.
  Patch by Jeremy Maitin-Shepard
* Use the new Transifex ``tx`` client

Testing
-------

* Fail testing when any Python warnings are emitted
* Migrate remaining ``unittest.TestCase`` style test functions to pytest style
* Remove tests that rely on setuptools

Release 6.1.3 (released Jan 10, 2023)
=====================================

Bugs fixed
----------

* #11116: Reverted to previous Sphinx 5 node copying method
* #11117: Reverted changes to parallel image processing from Sphinx 6.1.0
* #11119: Suppress ``ValueError`` in the ``linkcheck`` builder

Release 6.1.2 (released Jan 07, 2023)
=====================================

Bugs fixed
----------

* #11101: LaTeX: ``div.topic_padding`` key of sphinxsetup documented at 5.1.0 was
  implemented with name ``topic_padding``
* #11099: LaTeX: ``shadowrule`` key of sphinxsetup causes PDF build to crash
  since Sphinx 5.1.0
* #11096: LaTeX: ``shadowsize`` key of sphinxsetup causes PDF build to crash
  since Sphinx 5.1.0
* #11095: LaTeX: shadow of :dudir:`topic` and :dudir:`contents <table-of-contents>`
  boxes not in page margin since Sphinx 5.1.0
* #11100: Fix copying images when running under parallel mode.

Release 6.1.1 (released Jan 05, 2023)
=====================================

Bugs fixed
----------

* #11091: Fix ``util.nodes.apply_source_workaround`` for ``literal_block`` nodes
  with no source information in the node or the node's parents.

Release 6.1.0 (released Jan 05, 2023)
=====================================

Dependencies
------------

* Adopted the `Ruff`_ code linter.

  .. _Ruff: https://github.com/charliermarsh/ruff

Incompatible changes
--------------------

* #10979: gettext: Removed support for pluralisation in ``get_translation``.
  This was unused and complicated other changes to ``sphinx.locale``.

Deprecated
----------

* ``sphinx.util`` functions:

   * Renamed ``sphinx.util.typing.stringify()``
     to ``sphinx.util.typing.stringify_annotation()``
   * Moved ``sphinx.util.xmlname_checker()``
     to ``sphinx.builders.epub3._XML_NAME_PATTERN``

   Moved to ``sphinx.util.display``:

   * ``sphinx.util.status_iterator``
   * ``sphinx.util.display_chunk``
   * ``sphinx.util.SkipProgressMessage``
   * ``sphinx.util.progress_message``

   Moved to ``sphinx.util.http_date``:

   * ``sphinx.util.epoch_to_rfc1123``
   * ``sphinx.util.rfc1123_to_epoch``

   Moved to ``sphinx.util.exceptions``:

   * ``sphinx.util.save_traceback``
   * ``sphinx.util.format_exception_cut_frames``

Features added
--------------

* Cache doctrees in the build environment during the writing phase.
* Make all writing phase tasks support parallel execution.
* #11072: Use PEP 604 (``X | Y``) display conventions for ``typing.Optional``
  and ``typing.Optional`` types within the Python domain and autodoc.
* #10700: autodoc: Document ``typing.NewType()`` types as classes rather than
  'data'.
* Cache doctrees between the reading and writing phases.

Bugs fixed
----------

* #10962: HTML: Fix the multi-word key name lookup table.
* Fixed support for Python 3.12 alpha 3 (changes in the ``enum`` module).
* #11069: HTML Theme: Removed outdated "shortcut" link relation keyword.
* #10952: Properly terminate parallel processes on programme interruption.
* #10988: Speed up ``TocTree.resolve()`` through more efficient copying.
* #6744: LaTeX: support for seealso directive should be via an environment
  to allow styling.
* #11074: LaTeX: Can't change sphinxnote to use sphinxheavybox starting with
  5.1.0

Release 6.0.1 (released Jan 05, 2023)
=====================================

Dependencies
------------

* Require Pygments 2.13 or later.

Bugs fixed
----------

* #10944: imgmath: Fix resolving image paths for files in nested folders.

Release 6.0.0 (released Dec 29, 2022)
=====================================

Dependencies
------------

* #10468: Drop Python 3.6 support
* #10470: Drop Python 3.7, Docutils 0.14, Docutils 0.15, Docutils 0.16, and
  Docutils 0.17 support. Patch by Adam Turner

Incompatible changes
--------------------

* #7405: Removed the jQuery and underscore.js JavaScript frameworks.

  These frameworks are no longer be automatically injected into themes from
  Sphinx 6.0. If you develop a theme or extension that uses the
  ``jQuery``, ``$``, or ``$u`` global objects, you need to update your
  JavaScript to modern standards, or use the mitigation below.

  The first option is to use the sphinxcontrib.jquery_ extension, which has been
  developed by the Sphinx team and contributors. To use this, add
  ``sphinxcontrib.jquery`` to the ``extensions`` list in ``conf.py``, or call
  ``app.setup_extension("sphinxcontrib.jquery")`` if you develop a Sphinx theme
  or extension.

  The second option is to manually ensure that the frameworks are present.
  To re-add jQuery and underscore.js, you will need to copy ``jquery.js`` and
  ``underscore.js`` from `the Sphinx repository`_ to your ``static`` directory,
  and add the following to your ``layout.html``:

  .. code-block:: html+jinja

     {%- block scripts %}
         <script src="{{ pathto('_static/jquery.js', resource=True) }}"></script>
         <script src="{{ pathto('_static/underscore.js', resource=True) }}"></script>
         {{ super() }}
     {%- endblock %}

  .. _sphinxcontrib.jquery: https://github.com/sphinx-contrib/jquery/

  Patch by Adam Turner.
* #10471, #10565: Removed deprecated APIs scheduled for removal in Sphinx 6.0. See
  :ref:`dev-deprecated-apis` for details. Patch by Adam Turner.
* #10901: C Domain: Remove support for parsing pre-v3 style type directives and
  roles. Also remove associated configuration variables ``c_allow_pre_v3`` and
  ``c_warn_on_allowed_pre_v3``. Patch by Adam Turner.

Features added
--------------

* #10924: LaTeX: adopt better looking defaults for tables and code-blocks.
  See :confval:`latex_table_style` and the ``pre_border-radius`` and
  ``pre_background-TeXcolor`` :ref:`additionalcss` for the former defaults
  and how to re-enact them if desired.

Bugs fixed
----------

* #10984: LaTeX: Document :confval:`latex_additional_files` behavior for files
  with ``.tex`` extension.

Release 5.3.0 (released Oct 16, 2022)
=====================================

* #10759: LaTeX: add :confval:`latex_table_style` and support the
  ``'booktabs'``, ``'borderless'``, and ``'colorrows'`` styles.
  (thanks to Stefan Wiehler for initial pull requests #6666, #6671)
* #10840: One can cross-reference including an option value like
  ``:option:`--module=foobar```, ``:option:`--module[=foobar]```,
  or ``:option:`--module foobar```.
  Patch by Martin Liska.
* #10881: autosectionlabel: Record the generated section label to the debug log.
* #10268: Correctly URI-escape image filenames.
* #10887: domains: Allow sections in all the content of all object description
  directives (e.g. :rst:dir:`py:function`). Patch by Adam Turner

Release 5.2.3 (released Sep 30, 2022)
=====================================

* #10878: Fix base64 image embedding in ``sphinx.ext.imgmath``
* #10886: Add ``:nocontentsentry:`` flag and global domain table of contents
  entry control option. Patch by Adam Turner

Release 5.2.2 (released Sep 27, 2022)
=====================================

* #10872: Restore link targets for autodoc modules to the top of content.
  Patch by Dominic Davis-Foster.

Release 5.2.1 (released Sep 25, 2022)
=====================================

Bugs fixed
----------

* #10861: Always normalise the ``pycon3`` lexer to ``pycon``.
* Fix using ``sphinx.ext.autosummary`` with modules containing titles in the
  module-level docstring.

Release 5.2.0.post0 (released Sep 24, 2022)
===========================================

* Recreated source tarballs for Debian maintainers.

Release 5.2.0 (released Sep 24, 2022)
=====================================

Dependencies
------------

* #10356: Sphinx now uses declarative metadata with ``pyproject.toml`` to
  create packages, using PyPA's ``flit`` project as a build backend. Patch by
  Adam Turner.

Deprecated
----------

* #10843: Support for HTML 4 output. Patch by Adam Turner.

Features added
--------------

* #10738: napoleon: Add support for docstring types using 'of', like
  ``type of type``. Example: ``tuple of int``.
* #10286: C++, support requires clauses not just between the template
  parameter lists and the declaration.
* #10755: linkcheck: Check the source URL of raw directives that use the ``url``
  option.
* #10781: Allow :rst:role:`ref` role to be used with definitions and fields.
* #10717: HTML Search: Increase priority for full title and
  subtitle matches in search results
* #10718: HTML Search: Save search result score to the HTML element for debugging
* #10673: Make toctree accept 'genindex', 'modindex' and 'search' docnames
* #6316, #10804: Add domain objects to the table of contents. Patch by Adam Turner
* #6692: HTML Search: Include explicit :rst:dir:`index` directive index entries
  in the search index and search results. Patch by Adam Turner
* #10816: imgmath: Allow embedding images in HTML as base64
* #10854: HTML Search: Use browser localstorage for highlight control, stop
  storing highlight parameters in URL query strings. Patch by Adam Turner.

Bugs fixed
----------

* #10723: LaTeX: 5.1.0 has made the 'sphinxsetup' ``verbatimwithframe=false``
  become without effect.
* #10257: C++, ensure consistent non-specialization template argument
  representation.
* #10729: C++, fix parsing of certain non-type template parameter packs.
* #10715: Revert #10520: "Fix" use of sidebar classes in ``agogo.css_t``

Release 5.1.1 (released Jul 26, 2022)
=====================================

Bugs fixed
----------

* #10701: Fix ValueError in the new ``deque`` based ``sphinx.ext.napoleon``
  iterator implementation.
* #10702: Restore compatibility with third-party builders.

Release 5.1.0 (released Jul 24, 2022)
=====================================

Dependencies
------------

* #10656: Support `Docutils 0.19`_. Patch by Adam Turner.

.. _Docutils 0.19: https://docutils.sourceforge.io/RELEASE-NOTES.html#release-0-19-2022-07-05

Deprecated
----------

* #10467: Deprecated ``sphinx.util.stemmer`` in favour of ``snowballstemmer``.
  Patch by Adam Turner.
* #9856: Deprecated ``sphinx.ext.napoleon.iterators``.

Features added
--------------

* #10444: html theme: Allow specifying multiple CSS files through the ``stylesheet``
  setting in ``theme.conf`` or by setting ``html_style`` to an iterable of strings.
* #10366: std domain: Add support for emphasising placeholders in :rst:dir:`option`
  directives through a new :confval:`option_emphasise_placeholders` configuration
  option.
* #10439: std domain: Use the repr of some variables when displaying warnings,
  making whitespace issues easier to identify.
* #10571: quickstart: Reduce content in the generated ``conf.py`` file. Patch by
  Pradyun Gedam.
* #10648: LaTeX: CSS-named-alike additional :ref:`'sphinxsetup' <latexsphinxsetup>`
  keys allow to configure four separate border-widths, four paddings, four
  corner radii, a shadow (possibly inset), colours for border, background, shadow
  for each of the code-block, topic, attention, caution, danger, error and warning
  directives.
* #10655: LaTeX: Explain non-standard encoding in LatinRules.xdy
* #10599: HTML Theme: Wrap consecutive footnotes in an ``<aside>`` element when
  using Docutils 0.18 or later, to allow for easier styling. This matches the
  behaviour introduced in Docutils 0.19. Patch by Adam Turner.
* #10518: config: Add ``include_patterns`` as the opposite of ``exclude_patterns``.
  Patch by Adam Turner.

Bugs fixed
----------

* #10594: HTML Theme: field term colons are doubled if using Docutils 0.18+
* #10596: Build failure if Docutils version is 0.18 (not 0.18.1) due
  to missing ``Node.findall()``
* #10506: LaTeX: build error if highlighting inline code role in figure caption
  (refs: #10251)
* #10634: Make -P (pdb) option work better with exceptions triggered from events
* #10550: py domain: Fix spurious whitespace in unparsing various operators (``+``,
  ``-``, ``~``, and ``**``). Patch by Adam Turner (refs: #10551).
* #10460: logging: Always show node source locations as absolute paths.
* HTML Search: HTML tags are displayed as a part of object name
* HTML Search: search snippets should not be folded
* HTML Search: Minor errors are emitted on fetching search snippets
* HTML Search: The markers for header links are shown in the search result
* #10520: HTML Theme: Fix use of sidebar classes in ``agogo.css_t``.
* #6679: HTML Theme: Fix inclusion of hidden toctrees in the agogo theme.
* #10566: HTML Theme: Fix enable_search_shortcuts does not work
* #8686: LaTeX: Text can fall out of code-block at end of page and leave artifact
  on next page
* #10633: LaTeX: user injected ``\color`` commands in topic or admonition boxes may
  cause color leaks in PDF due to upstream `framed.sty
  <https://ctan.org/pkg/framed>`_ bug
* #10638: LaTeX: framed coloured boxes in highlighted code (e.g. highlighted
  diffs using Pygments style ``'manni'``) inherit thickness of code-block frame
* #10647: LaTeX: Only one ``\label`` is generated for ``desc_signature`` node
  even if it has multiple node IDs
* #10579: i18n: UnboundLocalError is raised on translating raw directive
* #9577, #10088: py domain: Fix warning for duplicate Python references when
  using ``:any:`` and autodoc.
* #10548: HTML Search: fix minor summary issues.

Release 5.0.2 (released Jun 17, 2022)
=====================================

Features added
--------------

* #10523: HTML Theme: Expose the Docutils's version info tuple as a template
  variable, ``docutils_version_info``. Patch by Adam Turner.

Bugs fixed
----------

* #10538: autodoc: Inherited class attribute having docstring is documented even
  if :confval:`autodoc_inherit_docstring` is disabled
* #10509: autosummary: autosummary fails with a shared library
* #10497: py domain: Failed to resolve strings in Literal. Patch by Adam Turner.
* #10523: HTML Theme: Fix double brackets on citation references in Docutils 0.18+.
  Patch by Adam Turner.
* #10534: Missing CSS for nav.contents in Docutils 0.18+. Patch by Adam Turner.

Release 5.0.1 (released Jun 03, 2022)
=====================================

Bugs fixed
----------

* #10498: gettext: TypeError is raised when sorting warning messages if a node
  has no line number. Patch by Adam Turner.
* #10493: HTML Theme: :dudir:`topic` directive is rendered incorrectly with
  Docutils 0.18. Patch by Adam Turner.
* #10495: IndexError is raised for a :rst:role:`kbd` role having a separator.
  Patch by Adam Turner.

Release 5.0.0 (released May 30, 2022)
=====================================

Dependencies
------------

5.0.0 b1

* #10164: Support `Docutils 0.18`_. Patch by Adam Turner.

.. _Docutils 0.18: https://docutils.sourceforge.io/RELEASE-NOTES.html#release-0-18-2021-10-26

Incompatible changes
--------------------

5.0.0 b1

* #10031: autosummary: ``sphinx.ext.autosummary.import_by_name()`` now raises
  ``ImportExceptionGroup`` instead of ``ImportError`` when it failed to import
  target object.  Please handle the exception if your extension uses the
  function to import Python object.  As a workaround, you can disable the
  behavior via ``grouped_exception=False`` keyword argument until v7.0.
* #9962: texinfo: Customizing styles of emphasized text via ``@definfoenclose``
  command was not supported because the command was deprecated since texinfo 6.8
* #2068: :confval:`intersphinx_disabled_reftypes` has changed default value
  from an empty list to ``['std:doc']`` as avoid too surprising silent
  intersphinx resolutions.
  To migrate: either add an explicit inventory name to the references
  intersphinx should resolve, or explicitly set the value of this configuration
  variable to an empty list.
* #10197: html theme: Reduce ``body_min_width`` setting in basic theme to 360px
* #9999: LaTeX: separate terms from their definitions by a CR (refs: #9985)
* #10062: Change the default language to ``'en'`` if any language is not set in
  ``conf.py``

5.0.0 final

* #10474: :confval:`language` does not accept ``None`` as it value.  The default
  value of ``language`` becomes to ``'en'`` now.
  Patch by Adam Turner and Takeshi KOMIYA.

Deprecated
----------

5.0.0 b1

* #10028: jQuery and underscore.js will no longer be automatically injected into
  themes from Sphinx 6.0. If you develop a theme or extension that uses the
  ``jQuery``, ``$``, or ``$u`` global objects, you need to update your
  JavaScript or use the mitigation below.

  To re-add jQuery and underscore.js, you will need to copy ``jquery.js`` and
  ``underscore.js`` from `the Sphinx repository`_ to your ``static`` directory,
  and add the following to your ``layout.html``:

  .. _the Sphinx repository: https://github.com/sphinx-doc/sphinx/tree/v5.3.0/sphinx/themes/basic/static
  .. code-block:: html+jinja

     {%- block scripts %}
         <script src="{{ pathto('_static/jquery.js', resource=True) }}"></script>
         <script src="{{ pathto('_static/underscore.js', resource=True) }}"></script>
         {{ super() }}
     {%- endblock %}

  Patch by Adam Turner.
* setuptools integration.  The ``build_sphinx`` sub-command for setup.py is
  marked as deprecated to follow the policy of setuptools team.
* The ``locale`` argument of ``sphinx.util.i18n:babel_format_date()`` becomes
  required
* The ``language`` argument of ``sphinx.util.i18n:format_date()`` becomes
  required
* ``sphinx.builders.html.html5_ready``
* ``sphinx.io.read_doc()``
* ``sphinx.util.docutils.__version_info__``
* ``sphinx.util.docutils.is_html5_writer_available()``
* ``sphinx.writers.latex.LaTeXWriter.docclasses``

Features added
--------------

5.0.0 b1

* #9075: autodoc: The default value of :confval:`autodoc_typehints_format` is
  changed to ``'smart'``.  It will suppress the leading module names of
  typehints (ex. ``io.StringIO`` -> ``StringIO``).
* #8417: autodoc: ``:inherited-members:`` option now takes multiple classes.  It
  allows to suppress inherited members of several classes on the module at once
  by specifying the option to :rst:dir:`automodule` directive
* #9792: autodoc: Add new option for ``autodoc_typehints_description_target`` to
  include undocumented return values but not undocumented parameters.
* #10285: autodoc: singledispatch functions having typehints are not documented
* autodoc: :confval:`autodoc_typehints_format` now also applies to attributes,
  data, properties, and type variable bounds.
* #10258: autosummary: Recognize a documented attribute of a module as
  non-imported
* #10028: Removed internal usages of JavaScript frameworks (jQuery and
  underscore.js) and modernised ``doctools.js`` and ``searchtools.js`` to
  EMCAScript 2018. Patch by Adam Turner.
* #10302: C++, add support for conditional expressions (``?:``).
* #5157, #10251: Inline code is able to be highlighted via :dudir:`role`
  directive
* #10337: Make sphinx-build faster by caching Publisher object during build.
  Patch by Adam Turner.

Bugs fixed
----------

5.0.0 b1

* #10200: apidoc: Duplicated submodules are shown for modules having both .pyx
  and .so files. Patch by Adam Turner and Takeshi KOMIYA.
* #10279: autodoc: Default values for keyword only arguments in overloaded
  functions are rendered as a string literal
* #10280: autodoc: :confval:`autodoc_docstring_signature` unexpectedly generates
  return value typehint for constructors if docstring has multiple signatures
* #10266: autodoc: :confval:`autodoc_preserve_defaults` does not work for
  mixture of keyword only arguments with/without defaults
* #10310: autodoc: class methods are not documented when decorated with mocked
  function
* #10305: autodoc: Failed to extract optional forward-ref'ed typehints correctly
  via :confval:`autodoc_type_aliases`
* #10421: autodoc: :confval:`autodoc_preserve_defaults` doesn't work on class
  methods
* #10214: html: invalid language tag was generated if :confval:`language`
  contains a country code (ex. zh_CN)
* #9974: html: Updated jQuery version from 3.5.1 to 3.6.0
* #10236: html search: objects are duplicated in search result
* #9962: texinfo: Deprecation message for ``@definfoenclose`` command on
  building texinfo document
* #10000: LaTeX: glossary terms with common definition are rendered with
  too much vertical whitespace
* #10188: LaTeX: alternating multiply referred footnotes produce a ``?`` in
  pdf output
* #10363: LaTeX: make ``'howto'`` title page rule use ``\linewidth`` for
  compatibility with usage of a ``twocolumn`` class option
* #10318: ``:prepend:`` option of :rst:dir:`literalinclude` directive does not
  work with ``:dedent:`` option

5.0.0 final

* #9575: autodoc: The annotation of return value should not be shown when
  ``autodoc_typehints="description"``
* #9648: autodoc: ``*args`` and ``**kwargs`` entries are duplicated when
  ``autodoc_typehints="description"``
* #8180: autodoc: Docstring metadata ignored for attributes
* #10443: epub: EPUB builder can't detect the mimetype of .webp file
* #10104: gettext: Duplicated locations are shown if 3rd party extension does
  not provide correct information
* #10456: py domain: ``:meta:`` fields are displayed if docstring contains two
  or more meta-field
* #9096: sphinx-build: the value of progress bar for parallel build is wrong
* #10110: sphinx-build: exit code is not changed when error is raised on
  builder-finished event

Release 4.5.0 (released Mar 28, 2022)
=====================================

Incompatible changes
--------------------

* #10112: extlinks: Disable hardcoded links detector by default
* #9993, #10177: std domain: Disallow to refer an inline target via
  :rst:role:`ref` role

Deprecated
----------

* ``sphinx.ext.napoleon.docstring.GoogleDocstring._qualify_name()``

Features added
--------------

* #10260: Enable ``FORCE_COLOR`` and ``NO_COLOR`` for terminal colouring
* #10234: autosummary: Add "autosummary" CSS class to summary tables
* #10125: extlinks: Improve suggestion message for a reference having title
* #10112: extlinks: Add :confval:`extlinks_detect_hardcoded_links` to enable
  hardcoded links detector feature
* #9494, #9456: html search: Add a config variable
  :confval:`html_show_search_summary` to enable/disable the search summaries
* #9337: HTML theme, add option ``enable_search_shortcuts`` that enables :kbd:`/` as
  a Quick search shortcut and :kbd:`Esc` shortcut that
  removes search highlighting.
* #10107: i18n: Allow to suppress translation warnings by adding ``#noqa``
  comment to the tail of each translation message
* #10252: C++, support attributes on classes, unions, and enums.
* #10253: :rst:role:`pep` role now generates URLs based on `peps.python.org
  <https://peps.python.org>`_

Bugs fixed
----------

* #9876: autodoc: Failed to document an imported class that is built from native
  binary module
* #10133: autodoc: Crashed when mocked module is used for type annotation
* #10146: autodoc: :confval:`autodoc_default_options` does not support
  ``no-value`` option
* #9971: autodoc: TypeError is raised when the target object is annotated by
  unhashable object
* #10205: extlinks: Failed to compile regexp on checking hardcoded links
* #10277: html search: Could not search short words (ex. "use")
* #9529: LaTeX: named auto numbered footnote (ex. ``[#named]``) that is referred
  multiple times was rendered to a question mark
* #9924: LaTeX: multi-line :rst:dir:`cpp:function` directive has big vertical
  spacing in Latexpdf
* #10158: LaTeX: excessive whitespace since v4.4.0 for undocumented
  variables/structure members
* #10175: LaTeX: named footnote reference is linked to an incorrect footnote if
  the name is also used in the different document
* #10269: manpage: Failed to resolve the title of :rst:role:`ref` cross references
* #10179: i18n: suppress "rST localization" warning
* #10118: imgconverter: Unnecessary availability check is called for remote URIs
* #10181: napoleon: attributes are displayed like class attributes for google
  style docstrings when :confval:`napoleon_use_ivar` is enabled
* #10122: sphinx-build: make.bat does not check the installation of sphinx-build
  command before showing help

Release 4.4.0 (released Jan 17, 2022)
=====================================

Dependencies
------------

* #10007: Use ``importlib_metadata`` for python-3.9 or older
* #10007: Drop ``setuptools``

Features added
--------------

* #9075: autodoc: Add a config variable :confval:`autodoc_typehints_format`
  to suppress the leading module names of typehints of function signatures (ex.
  ``io.StringIO`` -> ``StringIO``)
* #9831: Autosummary now documents only the members specified in a module's
  ``__all__`` attribute if :confval:`autosummary_ignore_module_all` is set to
  ``False``. The default behaviour is unchanged. Autogen also now supports
  this behavior with the ``--respect-module-all`` switch.
* #9555: autosummary: Improve error messages on failure to load target object
* #9800: extlinks: Emit warning if a hardcoded link is replaceable
  by an extlink, suggesting a replacement.
* #9961: html: Support nested <kbd> HTML elements in other HTML builders
* #10013: html: Allow to change the loading method of JS via ``loading_method``
  parameter for :meth:`.Sphinx.add_js_file()`
* #9551: html search: "Hide Search Matches" link removes "highlight" parameter
  from URL
* #9815: html theme: Wrap sidebar components in div to allow customizing their
  layout via CSS
* #9827: i18n: Sort items in glossary by translated terms
* #9899: py domain: Allows to specify cross-reference specifier (``.`` and
  ``~``) as ``:type:`` option
* #9894: linkcheck: add option ``linkcheck_exclude_documents`` to disable link
  checking in matched documents.
* #9793: sphinx-build: Allow to use the parallel build feature in macOS on macOS
  and Python3.8+
* #10055: sphinx-build: Create directories when ``-w`` option given
* #9993: std domain: Allow to refer an inline target (ex. ``_`target name```)
  via :rst:role:`ref` role
* #9981: std domain: Strip value part of the option directive from general index
* #9391: texinfo: improve variable in ``samp`` role
* #9578: texinfo: Add :confval:`texinfo_cross_references` to disable cross
  references for readability with standalone readers
* #9822, #9062: add new Intersphinx role :rst:role:`external` for explicit
  lookup in the external projects, without resolving to the local project.

Bugs fixed
----------

* #9866: autodoc: doccomment for the imported class was ignored
* #9883: autodoc: doccomment for the alias to mocked object was ignored
* #9908: autodoc: debug message is shown on building document using NewTypes
  with Python 3.10
* #9968: autodoc: instance variables are not shown if __init__ method has
  position-only-arguments
* #9194: autodoc: types under the "typing" module are not hyperlinked
* #10009: autodoc: Crashes if target object raises an error on getting docstring
* #10058: autosummary: Imported members are not shown when
  ``autodoc_class_signature = 'separated'``
* #9947: i18n: topic directive having a bullet list can't be translatable
* #9878: mathjax: MathJax configuration is placed after loading MathJax itself
* #9932: napoleon: empty "returns" section is generated even if no description
* #9857: Generated RFC links use outdated base url
* #9909: HTML, prevent line-wrapping in literal text.
* #10061: html theme: Configuration values added by themes are not be able to
  override from conf.py
* #10073: imgconverter: Unnecessary availability check is called for "data" URIs
* #9925: LaTeX: prohibit also with ``'xelatex'`` line splitting at dashes of
  inline and parsed literals
* #9944: LaTeX: extra vertical whitespace for some nested declarations
* #9940: LaTeX: Multi-function declaration in Python domain has cramped
  vertical spacing in latexpdf output
* #10015: py domain: types under the "typing" module are not hyperlinked defined
  at info-field-list
* #9390: texinfo: Do not emit labels inside footnotes
* #9413: xml: Invalid XML was generated when cross referencing python objects
* #9979: Error level messages were displayed as warning messages
* #10057: Failed to scan documents if the project is placed onto the root
  directory
* #9636: code-block: ``:dedent:`` without argument did strip newlines

Release 4.3.2 (released Dec 19, 2021)
=====================================

Bugs fixed
----------

* #9917: C and C++, parse fundamental types no matter the order of simple type
  specifiers.

Release 4.3.1 (released Nov 28, 2021)
=====================================

Features added
--------------

* #9864: mathjax: Support changing the loading method of MathJax to "defer" via
  :confval:`mathjax_options`

Bugs fixed
----------

* #9838: autodoc: AttributeError is raised on building document for functions
  decorated by functools.lru_cache
* #9879: autodoc: AttributeError is raised on building document for an object
  having invalid __doc__ attribute
* #9844: autodoc: Failed to process a function wrapped with functools.partial if
  :confval:`autodoc_preserve_defaults` enabled
* #9872: html: Class namespace collision between autodoc signatures and
  Docutils 0.17
* #9868: imgmath: Crashed if the dvisvgm command failed to convert equation
* #9864: mathjax: Failed to render equations via MathJax v2.  The loading method
  of MathJax is back to "async" method again

Release 4.3.0 (released Nov 11, 2021)
=====================================

Dependencies
------------

* Support Python 3.10

Incompatible changes
--------------------

* #9649: ``searchindex.js``: the embedded data has changed format to allow
  objects with the same name in different domains.
* #9672: The rendering of Python domain declarations is implemented
  with more Docutils nodes to allow better CSS styling.
  It may break existing styling.
* #9672: the signature of
  ``domains.python.PyObject.get_signature_prefix`` has changed to
  return a list of nodes instead of a plain string.
* #9695: ``domains.js.JSObject.display_prefix`` has been changed into a method
  ``get_display_prefix`` which now returns a list of nodes
  instead of a plain string.
* #9695: The rendering of Javascript domain declarations is implemented
  with more Docutils nodes to allow better CSS styling.
  It may break existing styling.
* #9450: mathjax: Load MathJax via "defer" strategy

Deprecated
----------

* ``sphinx.ext.autodoc.AttributeDocumenter._datadescriptor``
* ``sphinx.writers.html.HTMLTranslator._fieldlist_row_index``
* ``sphinx.writers.html.HTMLTranslator._table_row_index``
* ``sphinx.writers.html5.HTML5Translator._fieldlist_row_index``
* ``sphinx.writers.html5.HTML5Translator._table_row_index``

Features added
--------------

* #9639: autodoc: Support asynchronous generator functions
* #9664: autodoc: ``autodoc-process-bases`` supports to inject reST snippet as a
  base class
* #9691: C, added new info-field ``retval``
  for :rst:dir:`c:function` and :rst:dir:`c:macro`.
* C++, added new info-field ``retval`` for :rst:dir:`cpp:function`.
* #9618: i18n: Add :confval:`gettext_allow_fuzzy_translations` to allow "fuzzy"
  messages for translation
* #9672: More CSS classes on Python domain descriptions
* #9695: More CSS classes on Javascript domain descriptions
* #9683: Revert the removal of ``add_stylesheet()`` API.  It will be kept until
  the Sphinx 6.0 release
* #2068, add :confval:`intersphinx_disabled_reftypes` for disabling
  interphinx resolution of cross-references that do not have an explicit
  inventory specification. Specific types of cross-references can be disabled,
  e.g., ``std:doc`` or all cross-references in a specific domain,
  e.g., ``std:*``.
* #9623: Allow to suppress "toctree contains reference to excluded document"
  warnings using :confval:`suppress_warnings`

Bugs fixed
----------

* #9630: autodoc: Failed to build cross references if :confval:`primary_domain`
  is not 'py'
* #9644: autodoc: Crashed on getting source info from problematic object
* #9655: autodoc: mocked object having doc comment is warned unexpectedly
* #9651: autodoc: return type field is not generated even if
  :confval:`autodoc_typehints_description_target` is set to "documented" when
  its info-field-list contains ``:returns:`` field
* #9657: autodoc: The base class for a subclass of mocked object is incorrect
* #9607: autodoc: Incorrect base class detection for the subclasses of the
  generic class
* #9755: autodoc: memory addresses are shown for aliases
* #9752: autodoc: Failed to detect type annotation for slots attribute
* #9756: autodoc: Crashed if classmethod does not have __func__ attribute
* #9757: autodoc: :confval:`autodoc_inherit_docstrings` does not effect to
  overridden classmethods
* #9781: autodoc: :confval:`autodoc_preserve_defaults` does not support
  hexadecimal numeric
* #9630: autosummary: Failed to build summary table if :confval:`primary_domain`
  is not 'py'
* #9670: html: Fix download file with special characters
* #9710: html: Wrong styles for even/odd rows in nested tables
* #9763: html: parameter name and its type annotation are not separated in HTML
* #9649: HTML search: when objects have the same name but in different domains,
  return all of them as result instead of just one.
* #7634: intersphinx: references on the file in sub directory are broken
* #9737: LaTeX: hlist is rendered as a list containing "aggedright" text
* #9678: linkcheck: file extension was shown twice in warnings
* #9697: py domain: An index entry with parens was registered for ``py:method``
  directive with ``:property:`` option
* #9775: py domain: Literal typehint was converted to a cross reference when
  :confval:`autodoc_typehints`\ ``='description'``
* #9708: needs_extension failed to check double-digit version correctly
* #9688: Fix Sphinx patched :dudir:`code` does not recognize ``:class:`` option
* #9733: Fix for logging handler flushing warnings in the middle of the docs
  build
* #9656: Fix warnings without subtype being incorrectly suppressed
* Intersphinx, for unresolved references with an explicit inventory,
  e.g., ``proj:myFunc``, leave the inventory prefix in the unresolved text.

Release 4.2.0 (released Sep 12, 2021)
=====================================

Features added
--------------

* #9445: autodoc: Support class properties
* #9479: autodoc: Emit a warning if target is a mocked object
* #9560: autodoc: Allow to refer NewType instances with module name in Python
  3.10 or above
* #9447: html theme: Expose the version of Sphinx in the form of tuple as a
  template variable ``sphinx_version_tuple``
* #9594: manpage: Suppress the title of man page if description is empty
* #9445: py domain: :rst:dir:`py:property` directive supports ``:classmethod:``
  option to describe the class property
* #9524: test: SphinxTestApp can take ``builddir`` as an argument
* #9535: C and C++, support more fundamental types, including GNU extensions.

Bugs fixed
----------

* #9608: apidoc: apidoc does not generate a module definition for implicit
  namespace package
* #9504: autodoc: generate incorrect reference to the parent class if the target
  class inherites the class having ``_name`` attribute
* #9537, #9589: autodoc: Some objects under ``typing`` module are not displayed
  well with the HEAD of 3.10
* #9487: autodoc: typehint for cached_property is not shown
* #9509: autodoc: AttributeError is raised on failed resolving typehints
* #9518: autodoc: autodoc_docstring_signature does not effect to ``__init__()``
  and ``__new__()``
* #9522: autodoc: PEP 585 style typehints having arguments (ex. ``list[int]``)
  are not displayed well
* #9481: autosummary: some warnings contain non-existing filenames
* #9568: autosummary: summarise overlined sectioned headings correctly
* #9600: autosummary: Type annotations which contain commas in autosummary table
  are not removed completely
* #9481: c domain: some warnings contain non-existing filenames
* #9481: cpp domain: some warnings contain non-existing filenames
* #9456: html search: abbreation marks are inserted to the search result if
  failed to fetch the content of the page
* #9617: html search: The JS requirement warning is shown if browser is slow
* #9267: html theme: CSS and JS files added by theme were loaded twice
* #9585: py domain: ``:type:`` option for :rst:dir:`py:property` directive does
  not create a hyperlink
* #9576: py domain: Literal typehint was converted to a cross reference
* #9535 comment: C++, fix parsing of defaulted function parameters that are
  function pointers.
* #9564: smartquotes: don't adjust typography for text with
  language-highlighted ``:code:`` role.
* #9512: sphinx-build: crashed with the HEAD of Python 3.10

Release 4.1.2 (released Jul 27, 2021)
=====================================

Incompatible changes
--------------------

* #9435: linkcheck: Disable checking automatically generated anchors on
  github.com (ex. anchors in reST/Markdown documents)

Bugs fixed
----------

* #9489: autodoc: Custom types using ``typing.NewType`` are not displayed well
  with the HEAD of 3.10
* #9490: autodoc: Some objects under ``typing`` module are not displayed well
  with the HEAD of 3.10
* #9436, #9471: autodoc: crashed if ``autodoc_class_signature = "separated"``
* #9456: html search: html_copy_source can't control the search summaries
* #9500: LaTeX: Failed to build Japanese document on Windows
* #9435: linkcheck: Failed to check anchors in github.com

Release 4.1.1 (released Jul 15, 2021)
=====================================

Dependencies
------------

* #9434: sphinxcontrib-htmlhelp-2.0.0 or above
* #9434: sphinxcontrib-serializinghtml-1.1.5 or above

Bugs fixed
----------

* #9438: html: HTML logo or Favicon specified as file not being found on output

Release 4.1.0 (released Jul 12, 2021)
=====================================

Dependencies
------------

* Support jinja2-3.0

Deprecated
----------

* The ``app`` argument of ``sphinx.environment.BuildEnvironment`` becomes
  required
* ``sphinx.application.Sphinx.html_theme``
* ``sphinx.ext.autosummary._app``
* ``sphinx.util.docstrings.extract_metadata()``

Features added
--------------

* #8107: autodoc: Add ``class-doc-from`` option to :rst:dir:`autoclass`
  directive to control the content of the specific class like
  :confval:`autoclass_content`
* #8588: autodoc: :confval:`autodoc_type_aliases` now supports dotted name. It
  allows you to define an alias for a class with module name like
  ``foo.bar.BazClass``
* #9175: autodoc: Special member is not documented in the module
* #9195: autodoc: The arguments of ``typing.Literal`` are wrongly rendered
* #9185: autodoc: :confval:`autodoc_typehints` allows ``'both'`` setting to
  allow typehints to be included both in the signature and description
* #4257: autodoc: Add :confval:`autodoc_class_signature` to separate the class
  entry and the definition of ``__init__()`` method
* #8061, #9218: autodoc: Support variable comment for alias classes
* #3014: autodoc: Add :event:`autodoc-process-bases` to modify the base classes
  of the class definitions
* #9272: autodoc: Render enum values for the default argument value better
* #9384: autodoc: ``autodoc_typehints='none'`` now erases typehints for
  variables, attributes and properties
* #3257: autosummary: Support instance attributes for classes
* #9358: html: Add "heading" role to the toctree items
* #9225: html: Add span tag to the return typehint of method/function
* #9129: html search: Show search summaries when ``html_copy_source = False``
* #9307: html search: Prevent corrections and completions in search field
* #9120: html theme: Eliminate prompt characters of code-block from copyable
  text
* #9176: i18n: Emit a debug message if message catalog file not found under
  :confval:`locale_dirs`
* #9414: LaTeX: Add xeCJKVerbAddon to default fvset config for Chinese documents
* #9016: linkcheck: Support checking anchors on github.com
* #9016: linkcheck: Add a new event :event:`linkcheck-process-uri` to modify
  URIs before checking hyperlinks
* #6525: linkcheck: Add :confval:`linkcheck_allowed_redirects` to mark
  hyperlinks that are redirected to expected URLs as "working"
* #1874: py domain: Support union types using ``|`` in info-field-list
* #9268: py domain: :confval:`python_use_unqualified_type_names` supports type
  field in info-field-list
* #9097: Optimize the parallel build
* #9131: Add :confval:`nitpick_ignore_regex` to ignore nitpicky warnings using
  regular expressions
* #9174: Add ``Sphinx.set_html_assets_policy`` to tell extensions to include
  HTML assets in all the pages. Extensions can check this via
  ``Sphinx.registry.html_assets_policy``
* C++, add support for

  - ``inline`` variables,
  - ``consteval`` functions,
  - ``constinit`` variables,
  - ``char8_t``,
  - ``explicit(<constant expression>)`` specifier,
  - digit separators in literals, and
  - constraints in placeholder type specifiers, aka. adjective syntax
    (e.g., ``Sortable auto &v``).

* C, add support for digit separators in literals.
* #9166: LaTeX: support containers in LaTeX output


Bugs fixed
----------

* #8872: autodoc: stacked singledispatches are wrongly rendered
* #8597: autodoc: a docsting having metadata only should be treated as
  undocumented
* #9185: autodoc: typehints for overloaded functions and methods are inaccurate
* #9250: autodoc: The inherited method not having docstring is wrongly parsed
* #9283: autodoc: autoattribute directive failed to generate document for an
  attribute not having any comment
* #9364: autodoc: single element tuple on the default argument value is wrongly
  rendered
* #9362: autodoc: AttributeError is raised on processing a subclass of Tuple[()]
* #9404: autodoc: TypeError is raised on processing dict-like object (not a
  class) via autoclass directive
* #9317: html: Pushing left key causes visiting the next page at the first page
* #9381: html: URL for html_favicon and html_log does not work
* #9270: html theme : pyramid theme generates incorrect logo links
* #9217: manpage: The name of manpage directory that is generated by
  :confval:`man_make_section_directory` is not correct
* #9350: manpage: Fix font isn't reset after keyword at the top of samp role
* #9306: Linkcheck reports broken link when remote server closes the connection
  on HEAD request
* #9280: py domain: "exceptions" module is not displayed
* #9418: py domain: a Callable annotation with no parameters
  (e.g. ``Callable[[], None])`` will be rendered with a bracket missing
  (``Callable[], None]``)
* #9319: quickstart: Make sphinx-quickstart exit when conf.py already exists
* #9387: xml: XML Builder ignores custom visitors
* #9224: ``:param:`` and ``:type:`` fields does not support a type containing
  whitespace (ex. ``Dict[str, str]``)
* #8945: when transforming typed fields, call the specified role instead of
  making an single xref. For C and C++, use the ``expr`` role for typed fields.

Release 4.0.3 (released Jul 05, 2021)
=====================================

Features added
--------------

* C, add C23 keywords ``_Decimal32``, ``_Decimal64``, and ``_Decimal128``.
* #9354: C, add :confval:`c_extra_keywords` to allow user-defined keywords
  during parsing.
* Revert the removal of ``sphinx.util:force_decode()`` to become some 3rd party
  extensions available again during 5.0

Bugs fixed
----------

* #9330: changeset domain: :rst:dir:`versionchanged` with contents being a list
  will cause error during pdf build
* #9313: LaTeX: complex table with merged cells broken since 4.0
* #9305: LaTeX: backslash may cause Improper discretionary list pdf build error
  with Japanese engines
* #9354: C, remove special macro names from the keyword list.
  See also :confval:`c_extra_keywords`.
* #9322: KeyError is raised on PropagateDescDomain transform

Release 4.0.2 (released May 20, 2021)
=====================================

Dependencies
------------

* #9216: Support jinja2-3.0

Incompatible changes
--------------------

* #9222: Update Underscore.js to 1.13.1
* #9217: manpage: Stop creating a section directory on build manpage by default
  (see :confval:`man_make_section_directory`)

Bugs fixed
----------

* #9210: viewcode: crashed if non importable modules found on parallel build
* #9240: Unknown node error for pending_xref_condition is raised if an extension
  that does not support the node installs a missing-reference handler

Release 4.0.1 (released May 11, 2021)
=====================================

Bugs fixed
----------

* #9189: autodoc: crashed when ValueError is raised on generating signature
  from a property of the class
* #9188: autosummary: warning is emitted if list value is set to
  autosummary_generate
* #8380: html search: tags for search result are broken
* #9198: i18n: Babel emits errors when running compile_catalog
* #9205: py domain: The :canonical: option causes "more than one target for
  cross-reference" warning
* #9201: websupport: UndefinedError is raised: 'css_tag' is undefined

Release 4.0.0 (released May 09, 2021)
=====================================

Dependencies
------------

4.0.0b1

* Drop python 3.5 support
* Drop Docutils 0.12 and 0.13 support
* LaTeX: add ``tex-gyre`` font dependency

4.0.0b2

* Support Docutils 0.17.  Please notice it changes the output of HTML builder.
  Some themes do not support it, and you need to update your custom CSS to
  upgrade it.

Incompatible changes
--------------------

4.0.0b1

* #8539: autodoc: info-field-list is generated into the class description when
  :confval:`autodoc_typehints`\ ``='description'`` and
  :confval:`autoclass_content`\ ``='class'`` set
* #8898: extlinks: "%s" becomes required keyword in the link caption string
* domain: The ``Index`` class becomes subclasses of ``abc.ABC`` to indicate
  methods that must be overridden in the concrete classes
* #4826: py domain: The structure of python objects is changed.  A boolean value
  is added to indicate that the python object is canonical one
* #7425: MathJax: The MathJax was changed from 2 to 3. Users using a custom
  MathJax configuration may have to set the old MathJax path or update their
  configuration for version 3. See :mod:`sphinx.ext.mathjax`.
* #7784: i18n: The msgid for alt text of image is changed
* #5560: napoleon: :confval:`napoleon_use_param` also affect "other parameters"
  section
* #7996: manpage: Make a section directory on build manpage by default (see
  :confval:`man_make_section_directory`)
* #7849: html: Change the default setting of
  :confval:`html_codeblock_linenos_style` to ``'inline'``
* #8380: html search: search results are wrapped with ``<p>`` instead of
  ``<div>``
* html theme: Move a script tag for documentation_options.js in
  basic/layout.html to ``script_files`` variable
* html theme: Move CSS tags in basic/layout.html to ``css_files`` variable
* #8915: html theme: Emit a warning for ``sphinx_rtd_theme`` 0.2.4 or older
* #8508: LaTeX: uplatex becomes a default setting of latex_engine for Japanese
  documents
* #5977: py domain: ``:var:``, ``:cvar:`` and ``:ivar:`` fields do not create
  cross-references
* #4550: The ``align`` attribute of ``figure`` and ``table`` nodes becomes
  ``None`` by default instead of ``'default'``
* #8769: LaTeX refactoring: split sphinx.sty into multiple files and rename
  some auxiliary files created in ``latex`` build output repertory
* #8937: Use explicit title instead of <no title>
* #8487: The :file: option for csv-table directive now recognizes an absolute
  path as a relative path from source directory

4.0.0b2

* #9023: Change the CSS classes on :rst:role:`cpp:expr` and
  :rst:role:`cpp:texpr`.

Deprecated
----------

* :confval:`html_codeblock_linenos_style`
* ``favicon`` and ``logo`` variable in HTML templates
* ``sphinx.directives.patches.CSVTable``
* ``sphinx.directives.patches.ListTable``
* ``sphinx.directives.patches.RSTTable``
* ``sphinx.ext.autodoc.directive.DocumenterBridge.filename_set``
* ``sphinx.ext.autodoc.directive.DocumenterBridge.warn()``
* ``sphinx.registry.SphinxComponentRegistry.get_source_input()``
* ``sphinx.registry.SphinxComponentRegistry.source_inputs``
* ``sphinx.transforms.FigureAligner``
* ``sphinx.util.pycompat.convert_with_2to3()``
* ``sphinx.util.pycompat.execfile_()``
* ``sphinx.util.smartypants``
* ``sphinx.util.typing.DirectiveOption``

Features added
--------------

4.0.0b1

* #8924: autodoc: Support ``bound`` argument for TypeVar
* #7383: autodoc: Support typehints for properties
* #5603: autodoc: Allow to refer to a python class using its canonical name
  when the class has two different names; a canonical name and an alias name
* #8539: autodoc: Add :confval:`autodoc_typehints_description_target` to control
  the behavior of ``autodoc_typehints=description``
* #8841: autodoc: :confval:`autodoc_docstring_signature` will continue to look
  for multiple signature lines without backslash character
* #7549: autosummary: Enable :confval:`autosummary_generate` by default
* #8898: extlinks: Allow %s in link caption string
* #4826: py domain: Add ``:canonical:`` option to python directives to describe
  the location where the object is defined
* #7199: py domain: Add :confval:`python_use_unqualified_type_names` to suppress
  the module name of the python reference if it can be resolved (experimental)
* #7068: py domain: Add :rst:dir:`py:property` directive to describe a property
* #7784: i18n: The alt text for image is translated by default (without
  :confval:`gettext_additional_targets` setting)
* #2018: html: :confval:`html_favicon` and :confval:`html_logo` now accept URL
  for the image
* #8070: html search: Support searching for 2characters word
* #9036: html theme: Allow to inherite the search page
* #8938: imgconverter: Show the error of the command availability check
* #7830: Add debug logs for change detection of sources and templates
* #8201: Emit a warning if toctree contains duplicated entries
* #8326: ``master_doc`` is now renamed to :confval:`root_doc`
* #8942: C++, add support for the C++20 spaceship operator, ``<=>``.
* #7199: A new node, ``sphinx.addnodes.pending_xref_condition`` has been added.
  It can be used to choose appropriate content of the reference by conditions.

4.0.0b2

* #8818: autodoc: Super class having ``Any`` arguments causes nitpicky warning
* #9095: autodoc: TypeError is raised on processing broken metaclass
* #9110: autodoc: metadata of GenericAlias is not rendered as a reference in
  py37+
* #9098: html: copy-range protection for doctests doesn't work in Safari
* #9103: LaTeX: imgconverter: conversion runs even if not needed
* #8127: py domain: Ellipsis in info-field-list causes nitpicky warning
* #9121: py domain: duplicated warning is emitted when both canonical and its
  alias objects are defined on the document
* #9023: More CSS classes on domain descriptions, see :ref:`nodes` for details.
* #8195: mathjax: Rename :confval:`mathjax_config` to
  :confval:`mathjax2_config` and add :confval:`mathjax3_config`

Bugs fixed
----------

4.0.0b1

* #8917: autodoc: Raises a warning if function has wrong __globals__ value
* #8415: autodoc: a TypeVar imported from other module is not resolved (in
  Python 3.7 or above)
* #8992: autodoc: Failed to resolve types.TracebackType type annotation
* #8905: html: ``html_add_permalinks=None`` and ``html_add_permalinks=""``
  are ignored
* #8380: html search: Paragraphs in search results are not identified as ``<p>``
* #8915: html theme: The translation of ``sphinx_rtd_theme`` does not work
* #8342: Emit a warning if a unknown domain is given for directive or role (ex.
  ``:unknown:doc:``)
* #7241: LaTeX: No wrapping for ``cpp:enumerator``
* #8711: LaTeX: backticks in code-blocks trigger latexpdf build warning (and font
  change) with late TeXLive 2019
* #8253: LaTeX: Figures with no size defined get overscaled (compared to images
  with size explicitly set in pixels) (fixed for ``'pdflatex'/'lualatex'`` only)
* #8881: LaTeX: The depth of bookmarks panel in PDF is not enough for navigation
* #8874: LaTeX: the fix to two minor Pygments LaTeXFormatter output issues ignore
  Pygments style
* #8925: LaTeX: 3.5.0 ``verbatimmaxunderfull`` setting does not work as
  expected
* #8980: LaTeX: missing line break in ``\pysigline``
* #8995: LaTeX: legacy ``\pysiglinewithargsret`` does not compute correctly
  available horizontal space and should use a ragged right style
* #9009: LaTeX: "release" value with underscore leads to invalid LaTeX
* #8911: C++: remove the longest matching prefix in
  :confval:`cpp_index_common_prefix` instead of the first that matches.
* C, properly reject function declarations when a keyword is used
  as parameter name.
* #8933: viewcode: Failed to create back-links on parallel build
* #8960: C and C++, fix rendering of (member) function pointer types in
  function parameter lists.
* C++, fix linking of names in array declarators, pointer to member
  (function) declarators, and in the argument to ``sizeof...``.
* C, fix linking of names in array declarators.

4.0.0b2

* C, C++, fix ``KeyError`` when an ``alias`` directive is the first C/C++
  directive in a file with another C/C++ directive later.

4.0.0b3

* #9167: html: Failed to add CSS files to the specific page

Release 3.5.5 (in development)
==============================

Release 3.5.4 (released Apr 11, 2021)
=====================================

Dependencies
------------

* #9071: Restrict Docutils to 0.16

Bugs fixed
----------

* #9078: autodoc: Async staticmethods and classmethods are considered as non
  async coroutine-functions with Python3.10
* #8870, #9001, #9051: html theme: The style are not applied with Docutils 0.17

  - toctree captions
  - The content of ``sidebar`` directive
  - figures

Release 3.5.3 (released Mar 20, 2021)
=====================================

Features added
--------------

* #8959: using UNIX path separator in image directive confuses Sphinx on Windows

Release 3.5.2 (released Mar 06, 2021)
=====================================

Bugs fixed
----------

* #8943: i18n: Crashed by broken translation messages in ES, EL and HR
* #8936: LaTeX: A custom LaTeX builder fails with unknown node error
* #8952: Exceptions raised in a Directive cause parallel builds to hang

Release 3.5.1 (released Feb 16, 2021)
=====================================

Bugs fixed
----------

* #8883: autodoc: AttributeError is raised on assigning __annotations__ on
  read-only class
* #8884: html: minified js stemmers not included in the distributed package
* #8885: html: AttributeError is raised if CSS/JS files are installed via
  :confval:`html_context`
* #8880: viewcode: ExtensionError is raised on incremental build after
  unparsable python module found

Release 3.5.0 (released Feb 14, 2021)
=====================================

Dependencies
------------

* LaTeX: ``multicol`` (it is anyhow a required part of the official latex2e
  base distribution)

Incompatible changes
--------------------

* Update Underscore.js to 1.12.0
* #6550: html: The config variable ``html_add_permalinks`` is replaced by
  :confval:`html_permalinks` and :confval:`html_permalinks_icon`

Deprecated
----------

* pending_xref node for viewcode extension
* ``sphinx.builders.linkcheck.CheckExternalLinksBuilder.anchors_ignore``
* ``sphinx.builders.linkcheck.CheckExternalLinksBuilder.auth``
* ``sphinx.builders.linkcheck.CheckExternalLinksBuilder.broken``
* ``sphinx.builders.linkcheck.CheckExternalLinksBuilder.good``
* ``sphinx.builders.linkcheck.CheckExternalLinksBuilder.redirected``
* ``sphinx.builders.linkcheck.CheckExternalLinksBuilder.rqueue``
* ``sphinx.builders.linkcheck.CheckExternalLinksBuilder.to_ignore``
* ``sphinx.builders.linkcheck.CheckExternalLinksBuilder.workers``
* ``sphinx.builders.linkcheck.CheckExternalLinksBuilder.wqueue``
* ``sphinx.builders.linkcheck.node_line_or_0()``
* ``sphinx.ext.autodoc.AttributeDocumenter.isinstanceattribute()``
* ``sphinx.ext.autodoc.directive.DocumenterBridge.reporter``
* ``sphinx.ext.autodoc.importer.get_module_members()``
* ``sphinx.ext.autosummary.generate._simple_info()``
* ``sphinx.ext.autosummary.generate._simple_warn()``
* ``sphinx.writers.html.HTMLTranslator.permalink_text``
* ``sphinx.writers.html5.HTML5Translator.permalink_text``

Features added
--------------

* #8022: autodoc: autodata and autoattribute directives does not show right-hand
  value of the variable if docstring contains ``:meta hide-value:`` in
  info-field-list
* #8514: autodoc: Default values of overloaded functions are taken from actual
  implementation if they're ellipsis
* #8775: autodoc: Support type union operator (PEP-604) in Python 3.10 or above
* #8297: autodoc: Allow to extend :confval:`autodoc_default_options` via
  directive options
* #759: autodoc: Add a new configuration :confval:`autodoc_preserve_defaults` as
  an experimental feature.  It preserves the default argument values of
  functions in source code and keep them not evaluated for readability.
* #8619: html: kbd role generates customizable HTML tags for compound keys
* #8634: html: Allow to change the order of JS/CSS via ``priority`` parameter
  for :meth:`.Sphinx.add_js_file()` and :meth:`.Sphinx.add_css_file()`
* #6241: html: Allow to add JS/CSS files to the specific page when an extension
  calls ``app.add_js_file()`` or ``app.add_css_file()`` on
  :event:`html-page-context` event
* #6550: html: Allow to use HTML permalink texts via
  :confval:`html_permalinks_icon`
* #1638: html: Add permalink icons to glossary terms
* #8868: html search: performance issue with massive lists
* #8867: html search: Update JavaScript stemmer code to the latest version of
  Snowball (v2.1.0)
* #8852: i18n: Allow to translate heading syntax in MyST-Parser
* #8649: imgconverter: Skip availability check if builder supports the image
  type
* #8573: napoleon: Allow to change the style of custom sections using
  :confval:`napoleon_custom_sections`
* #8004: napoleon: Type definitions in Google style docstrings are rendered as
  references when :confval:`napoleon_preprocess_types` enabled
* #6241: mathjax: Include mathjax.js only on the document using equations
* #8775: py domain: Support type union operator (PEP-604)
* #8651: std domain: cross-reference for a rubric having inline item is broken
* #7642: std domain: Optimize case-insensitive match of term
* #8681: viewcode: Support incremental build
* #8132: Add :confval:`project_copyright` as an alias of :confval:`copyright`
* #207: Now :confval:`highlight_language` supports multiple languages
* #2030: :rst:dir:`code-block` and :rst:dir:`literalinclude` supports automatic
  dedent via no-argument ``:dedent:`` option
* C++, also hyperlink operator overloads in expressions and alias declarations.
* #8247: Allow production lists to refer to tokens from other production groups
* #8813: Show what extension (or module) caused it on errors on event handler
* #8213: C++: add ``maxdepth`` option to :rst:dir:`cpp:alias` to insert nested
  declarations.
* C, add ``noroot`` option to :rst:dir:`c:alias` to render only nested
  declarations.
* C++, add ``noroot`` option to :rst:dir:`cpp:alias` to render only nested
  declarations.

Bugs fixed
----------

* #8727: apidoc: namespace module file is not generated if no submodules there
* #741: autodoc: inherited-members doesn't work for instance attributes on super
  class
* #8592: autodoc: ``:meta public:`` does not effect to variables
* #8594: autodoc: empty ``__all__`` attribute is ignored
* #8315: autodoc: Failed to resolve struct.Struct type annotation
* #8652: autodoc: All variable comments in the module are ignored if the module
  contains invalid type comments
* #8693: autodoc: Default values for overloaded functions are rendered as string
* #8134: autodoc: crashes when mocked decorator takes arguments
* #8800: autodoc: Uninitialized attributes in superclass are recognized as
  undocumented
* #8655: autodoc: Failed to generate document if target module contains an
  object that raises an exception on ``hasattr()``
* #8306: autosummary: mocked modules are documented as empty page when using
  :recursive: option
* #8232: graphviz: Image node is not rendered if graph file is in subdirectory
* #8618: html: kbd role produces incorrect HTML when compound-key separators (-,
  + or ^) are used as keystrokes
* #8629: html: A type warning for html_use_opensearch is shown twice
* #8714: html: kbd role with "Caps Lock" rendered incorrectly
* #8123: html search: fix searching for terms containing + (Requires a custom
  search language that does not split on +)
* #8665: html theme: Could not override globaltoc_maxdepth in theme.conf
* #8446: html: consecutive spaces are displayed as single space
* #8745: i18n: crashes with KeyError when translation message adds a new auto
  footnote reference
* #4304: linkcheck: Fix race condition that could lead to checking the
  availability of the same URL twice
* #8791: linkcheck: The docname for each hyperlink is not displayed
* #7118: sphinx-quickstart: questionnaire got Mojibake if libreadline unavailable
* #8094: texinfo: image files on the different directory with document are not
  copied
* #8782: todo: Cross references in todolist get broken
* #8720: viewcode: module pages are generated for epub on incremental build
* #8704: viewcode: anchors are generated in incremental build after singlehtml
* #8756: viewcode: highlighted code is generated even if not referenced
* #8671: :confval:`highlight_options` is not working
* #8341: C, fix intersphinx lookup types for names in declarations.
* C, C++: in general fix intersphinx and role lookup types.
* #8683: :confval:`html_last_updated_fmt` does not support UTC offset (%z)
* #8683: :confval:`html_last_updated_fmt` generates wrong time zone for %Z
* #1112: ``download`` role creates duplicated copies when relative path is
  specified
* #2616 (fifth item): LaTeX: footnotes from captions are not clickable,
  and for manually numbered footnotes only first one with same number is
  an hyperlink
* #7576: LaTeX with French babel and memoir crash: "Illegal parameter number
  in definition of ``\FNH@prefntext``"
* #8055: LaTeX (docs): A potential display bug with the LaTeX generation step
  in Sphinx (how to generate one-column index)
* #8072: LaTeX: Directive :rst:dir:`hlist` not implemented in LaTeX
* #8214: LaTeX: The :rst:role:`index` role and the glossary generate duplicate
  entries in the LaTeX index (if both used for same term)
* #8735: LaTeX: wrong internal links in pdf to captioned code-blocks when
  :confval:`numfig` is not ``True``
* #8442: LaTeX: some indexed terms are ignored when using xelatex engine
  (or pdflatex and :confval:`latex_use_xindy` set to ``True``) with memoir class
* #8750: LaTeX: URLs as footnotes fail to show in PDF if originating from
  inside function type signatures
* #8780: LaTeX: long words in narrow columns may not be hyphenated
* #8788: LaTeX: ``\titleformat`` last argument in sphinx.sty should be
  bracketed, not braced (and is anyhow not needed)
* #8849: LaTex: code-block printed out of margin (see the opt-in LaTeX syntax
  boolean :ref:`verbatimforcewraps <latexsphinxsetupforcewraps>` for use via
  the :ref:`'sphinxsetup' <latexsphinxsetup>` key of ``latex_elements``)
* #8183: LaTeX: Remove substitution_reference nodes from doctree only on LaTeX
  builds
* #8865: LaTeX: Restructure the index nodes inside title nodes only on LaTeX
  builds
* #8796: LaTeX: potentially critical low level TeX coding mistake has gone
  unnoticed so far
* C, :rst:dir:`c:alias` skip symbols without explicit declarations
  instead of crashing.
* C, :rst:dir:`c:alias` give a warning when the root symbol is not declared.
* C, ``expr`` role should start symbol lookup in the current scope.

Release 3.4.3 (released Jan 08, 2021)
=====================================

Bugs fixed
----------

* #8655: autodoc: Failed to generate document if target module contains an
  object that raises an exception on ``hasattr()``

Release 3.4.2 (released Jan 04, 2021)
=====================================

Bugs fixed
----------

* #8164: autodoc: Classes that inherit mocked class are not documented
* #8602: autodoc: The ``autodoc-process-docstring`` event is emitted to the
  non-datadescriptors unexpectedly
* #8616: autodoc: AttributeError is raised on non-class object is passed to
  autoclass directive

Release 3.4.1 (released Dec 25, 2020)
=====================================

Bugs fixed
----------

* #8559: autodoc: AttributeError is raised when using forward-reference type
  annotations
* #8568: autodoc: TypeError is raised on checking slots attribute
* #8567: autodoc: Instance attributes are incorrectly added to Parent class
* #8566: autodoc: The ``autodoc-process-docstring`` event is emitted to the
  alias classes unexpectedly
* #8583: autodoc: Unnecessary object comparison via ``__eq__`` method
* #8565: linkcheck: Fix PriorityQueue crash when link tuples are not
  comparable

Release 3.4.0 (released Dec 20, 2020)
=====================================

Incompatible changes
--------------------

* #8105: autodoc: the signature of class constructor will be shown for decorated
  classes, not a signature of decorator

Deprecated
----------

* The ``follow_wrapped`` argument of ``sphinx.util.inspect.signature()``
* The ``no_docstring`` argument of
  ``sphinx.ext.autodoc.Documenter.add_content()``
* ``sphinx.ext.autodoc.Documenter.get_object_members()``
* ``sphinx.ext.autodoc.DataDeclarationDocumenter``
* ``sphinx.ext.autodoc.GenericAliasDocumenter``
* ``sphinx.ext.autodoc.InstanceAttributeDocumenter``
* ``sphinx.ext.autodoc.SlotsAttributeDocumenter``
* ``sphinx.ext.autodoc.TypeVarDocumenter``
* ``sphinx.ext.autodoc.importer._getannotations()``
* ``sphinx.ext.autodoc.importer._getmro()``
* ``sphinx.pycode.ModuleAnalyzer.parse()``
* ``sphinx.util.osutil.movefile()``
* ``sphinx.util.requests.is_ssl_error()``

Features added
--------------

* #8119: autodoc: Allow to determine whether a member not included in
  ``__all__`` attribute of the module should be documented or not via
  :event:`autodoc-skip-member` event
* #8219: autodoc: Parameters for generic class are not shown when super class is
  a generic class and show-inheritance option is given (in Python 3.7 or above)
* autodoc: Add ``Documenter.config`` as a shortcut to access the config object
* autodoc: Add ``Optional[t]`` to annotation of function and method if a default
  value equal to ``None`` is set.
* #8209: autodoc: Add ``:no-value:`` option to :rst:dir:`autoattribute` and
  :rst:dir:`autodata` directive to suppress the default value of the variable
* #8460: autodoc: Support custom types defined by typing.NewType
* #8285: napoleon: Add :confval:`napoleon_attr_annotations` to merge type hints
  on source code automatically if any type is specified in docstring
* #8236: napoleon: Support numpydoc's "Receives" section
* #6914: Add a new event :event:`warn-missing-reference` to custom warning
  messages when failed to resolve a cross-reference
* #6914: Emit a detailed warning when failed to resolve a ``:ref:`` reference
* #6629: linkcheck: The builder now handles rate limits. See
  :confval:`linkcheck_rate_limit_timeout` for details.

Bugs fixed
----------

* #7613: autodoc: autodoc does not respect __signature__ of the class
* #4606: autodoc: the location of the warning is incorrect for inherited method
* #8105: autodoc: the signature of class constructor is incorrect if the class
  is decorated
* #8434: autodoc: :confval:`autodoc_type_aliases` does not effect to variables
  and attributes
* #8443: autodoc: autodata directive can't create document for PEP-526 based
  type annotated variables
* #8443: autodoc: autoattribute directive can't create document for PEP-526
  based uninitialized variables
* #8480: autodoc: autoattribute could not create document for __slots__
  attributes
* #8503: autodoc: autoattribute could not create document for a GenericAlias as
  class attributes correctly
* #8534: autodoc: autoattribute could not create document for a commented
  attribute in alias class
* #8452: autodoc: autodoc_type_aliases doesn't work when autodoc_typehints is
  set to "description"
* #8541: autodoc: autodoc_type_aliases doesn't work for the type annotation to
  instance attributes
* #8460: autodoc: autodata and autoattribute directives do not display type
  information of TypeVars
* #8493: autodoc: references to builtins not working in class aliases
* #8522: autodoc: ``__bool__`` method could be called
* #8067: autodoc: A typehint for the instance variable having type_comment on
  super class is not displayed
* #8545: autodoc: a __slots__ attribute is not documented even having docstring
* #741: autodoc: inherited-members doesn't work for instance attributes on super
  class
* #8477: autosummary: non utf-8 reST files are generated when template contains
  multibyte characters
* #8501: autosummary: summary extraction splits text after "el at." unexpectedly
* #8524: html: Wrong url_root has been generated on a document named "index"
* #8419: html search: Do not load ``language_data.js`` in non-search pages
* #8549: i18n: ``-D gettext_compact=0`` is no longer working
* #8454: graphviz: The layout option for graph and digraph directives don't work
* #8131: linkcheck: Use GET when HEAD requests cause Too Many Redirects, to
  accommodate infinite redirect loops on HEAD
* #8437: Makefile: ``make clean`` with empty BUILDDIR is dangerous
* #8365: py domain: ``:type:`` and ``:rtype:`` gives false ambiguous class
  lookup warnings
* #8352: std domain: Failed to parse an option that starts with bracket
* #8519: LaTeX: Prevent page brake in the middle of a seealso
* #8520: C, fix copying of AliasNode.

Release 3.3.1 (released Nov 12, 2020)
=====================================

Bugs fixed
----------

* #8372: autodoc: autoclass directive became slower than Sphinx 3.2
* #7727: autosummary: raise PycodeError when documenting python package
  without __init__.py
* #8350: autosummary: autosummary_mock_imports causes slow down builds
* #8364: C, properly initialize attributes in empty symbols.
* #8399: i18n: Put system locale path after the paths specified by configuration

Release 3.3.0 (released Nov 02, 2020)
=====================================

Deprecated
----------

* ``sphinx.builders.latex.LaTeXBuilder.usepackages``
* ``sphinx.builders.latex.LaTeXBuilder.usepackages_afger_hyperref``
* ``sphinx.ext.autodoc.SingledispatchFunctionDocumenter``
* ``sphinx.ext.autodoc.SingledispatchMethodDocumenter``

Features added
--------------

* #8100: html: Show a better error message for failures on copying
  html_static_files
* #8141: C: added a ``maxdepth`` option to :rst:dir:`c:alias` to insert
  nested declarations.
* #8081: LaTeX: Allow to add LaTeX package via ``app.add_latex_package()`` until
  just before writing .tex file
* #7996: manpage: Add :confval:`man_make_section_directory` to make a section
  directory on build man page
* #8289: epub: Allow to suppress "duplicated ToC entry found" warnings from epub
  builder using :confval:`suppress_warnings`.
* #8298: sphinx-quickstart: Add :option:`sphinx-quickstart --no-sep` option
* #8304: sphinx.testing: Register public markers in sphinx.testing.fixtures
* #8051: napoleon: use the obj role for all See Also items
* #8050: napoleon: Apply :confval:`napoleon_preprocess_types` to every field
* C and C++, show line numbers for previous declarations when duplicates are
  detected.
* #8183: Remove substitution_reference nodes from doctree only on LaTeX builds

Bugs fixed
----------

* #8085: i18n: Add support for having single text domain
* #6640: i18n: Failed to override system message translation
* #8143: autodoc: ``AttributeError`` is raised when ``False`` value is passed to
  :confval:`autodoc_default_options`
* #8103: autodoc: functools.cached_property is not considered as a property
* #8190: autodoc: parsing error is raised if some extension replaces docstring
  by string not ending with blank lines
* #8142: autodoc: Wrong constructor signature for the class derived from
  typing.Generic
* #8157: autodoc: TypeError is raised when annotation has invalid __args__
* #7964: autodoc: Tuple in default value is wrongly rendered
* #8200: autodoc: type aliases break type formatting of autoattribute
* #7786: autodoc: can't detect overloaded methods defined in other file
* #8294: autodoc: single-string __slots__ is not handled correctly
* #7785: autodoc: autodoc_typehints='none' does not effect to overloaded functions
* #8192: napoleon: description is disappeared when it contains inline literals
* #8142: napoleon: Potential of regex denial of service in google style docs
* #8169: LaTeX: pxjahyper loaded even when latex_engine is not platex
* #8215: LaTeX: 'oneside' classoption causes build warning
* #8175: intersphinx: Potential of regex denial of service by broken inventory
* #8277: sphinx-build: missing and redundant spacing (and etc) for console
  output on building
* #7973: imgconverter: Check availability of imagemagick many times
* #8255: py domain: number in default argument value is changed from hexadecimal
  to decimal
* #8316: html: Prevent arrow keys changing page when button elements are focused
* #8343: html search: Fix unnecessary load of images when parsing the document
* #8254: html theme: Line numbers misalign with code lines
* #8093: The highlight warning has wrong location in some builders (LaTeX,
  singlehtml and so on)
* #8215: Eliminate Fancyhdr build warnings for oneside documents
* #8239: Failed to refer a token in productionlist if it is indented
* #8268: linkcheck: Report HTTP errors when ``linkcheck_anchors`` is ``True``
* #8245: linkcheck: take source directory into account for local files
* #8321: linkcheck: ``tel:`` schema hyperlinks are detected as errors
* #8323: linkcheck: An exit status is incorrect when links having unsupported
  schema found
* #8188: C, add missing items to internal object types dictionary,
  e.g., preventing intersphinx from resolving them.
* C, fix anon objects in intersphinx.
* #8270, C++, properly reject functions as duplicate declarations if a
  non-function declaration of the same name already exists.
* C, fix references to function parameters.
  Link to the function instead of a non-existing anchor.
* #6914: figure numbers are unexpectedly assigned to uncaptioned items
* #8320: make "inline" line numbers un-selectable

Testing
-------

* #8257: Support parallel build in sphinx.testing

Release 3.2.1 (released Aug 14, 2020)
=====================================

Features added
--------------

* #8095: napoleon: Add :confval:`napoleon_preprocess_types` to enable the type
  preprocessor for numpy style docstrings
* #8114: C and C++, parse function attributes after parameters and qualifiers.

Bugs fixed
----------

* #8074: napoleon: Crashes during processing C-ext module
* #8088: napoleon: "Inline literal start-string without end-string" warning in
  Numpy style Parameters section
* #8084: autodoc: KeyError is raised on documenting an attribute of the broken
  class
* #8091: autodoc: AttributeError is raised on documenting an attribute on Python
  3.5.2
* #8099: autodoc: NameError is raised when target code uses ``TYPE_CHECKING``
* C++, fix parsing of template template parameters, broken by the fix of #7944

Release 3.2.0 (released Aug 08, 2020)
=====================================

Deprecated
----------

* ``sphinx.ext.autodoc.members_set_option()``
* ``sphinx.ext.autodoc.merge_special_members_option()``
* ``sphinx.writers.texinfo.TexinfoWriter.desc``
* C, parsing of pre-v3 style type directives and roles, along with the options
  :confval:`!c_allow_pre_v3` and :confval:`!c_warn_on_allowed_pre_v3`.

Features added
--------------

* #2076: autodoc: Allow overriding of exclude-members in skip-member function
* #8034: autodoc: ``:private-member:`` can take an explicit list of member names
  to be documented
* #2024: autosummary: Add :confval:`autosummary_filename_map` to avoid conflict
  of filenames between two object with different case
* #8011: autosummary: Support instance attributes as a target of autosummary
  directive
* #7849: html: Add :confval:`html_codeblock_linenos_style` to change the style
  of line numbers for code-blocks
* #7853: C and C++, support parameterized GNU style attributes.
* #7888: napoleon: Add aliases Warn and Raise.
* #7690: napoleon: parse type strings and make them hyperlinks as possible.  The
  conversion rule can be updated via :confval:`napoleon_type_aliases`
* #8049: napoleon: Create a hyperlink for each the type of parameter when
  :confval:`napoleon_use_param` is ``False``
* C, added :rst:dir:`c:alias` directive for inserting copies
  of existing declarations.
* #7745: html: inventory is broken if the docname contains a space
* #7991: html search: Allow searching for numbers
* #7902: html theme: Add a new option :confval:`globaltoc_maxdepth` to control
  the behavior of globaltoc in sidebar
* #7840: i18n: Optimize the dependencies check on bootstrap
* #7768: i18n: :confval:`figure_language_filename` supports ``docpath`` token
* #5208: linkcheck: Support checks for local links
* #5090: setuptools: Link verbosity to distutils' -v and -q option
* #6698: doctest: Add ``:trim-doctest-flags:`` and ``:no-trim-doctest-flags:``
  options to doctest, testcode and testoutput directives
* #7052: add ``:noindexentry:`` to the Python, C, C++, and Javascript domains.
  Update the documentation to better reflect the relationship between this option
  and the ``:noindex:`` option.
* #7899: C, add possibility of parsing of some pre-v3 style type directives and
  roles and try to convert them to equivalent v3 directives/roles.
  Set the new option :confval:`!c_allow_pre_v3` to ``True`` to enable this.
  The warnings printed from this functionality can be suppressed by setting
  :confval:`!c_warn_on_allowed_pre_v3` to ``True``.
  The functionality is immediately deprecated.
* #7999: C, add support for named variadic macro arguments.
* #8071: Allow to suppress "self referenced toctrees" warning

Bugs fixed
----------

* #7886: autodoc: TypeError is raised on mocking generic-typed classes
* #7935: autodoc: function signature is not shown when the function has a
  parameter having ``inspect._empty`` as its default value
* #7901: autodoc: type annotations for overloaded functions are not resolved
* #904: autodoc: An instance attribute cause a crash of autofunction directive
* #1362: autodoc: ``private-members`` option does not work for class attributes
* #7983: autodoc: Generator type annotation is wrongly rendered in py36
* #8030: autodoc: An uninitialized annotated instance variable is not documented
  when ``:inherited-members:`` option given
* #8032: autodoc: A type hint for the instance variable defined at parent class
  is not shown in the document of the derived class
* #8041: autodoc: An annotated instance variable on super class is not
  documented when derived class has other annotated instance variables
* #7839: autosummary: cannot handle umlauts in function names
* #7865: autosummary: Failed to extract summary line when abbreviations found
* #7866: autosummary: Failed to extract correct summary line when docstring
  contains a hyperlink target
* #7469: autosummary: "Module attributes" header is not translatable
* #7940: apidoc: An extra newline is generated at the end of the rst file if a
  module has submodules
* #4258: napoleon: decorated special methods are not shown
* #7799: napoleon: parameters are not escaped for combined params in numpydoc
* #7780: napoleon: multiple parameters declaration in numpydoc was wrongly
  recognized when ``napoleon_use_param=True``
* #7715: LaTeX: ``numfig_secnum_depth > 1`` leads to wrong figure links
* #7846: html theme: XML-invalid files were generated
* #7894: gettext: Wrong source info is shown when using rst_epilog
* #7691: linkcheck: HEAD requests are not used for checking
* #4888: i18n: Failed to add an explicit title to ``:ref:`` role on translation
* #7928: py domain: failed to resolve a type annotation for the attribute
* #8008: py domain: failed to parse a type annotation containing ellipsis
* #7994: std domain: option directive does not generate old node_id compatible
  with 2.x or older
* #7968: i18n: The content of ``math`` directive is interpreted as reST on
  translation
* #7768: i18n: The ``root`` element for :confval:`figure_language_filename` is
  not a path that user specifies in the document
* #7993: texinfo: TypeError is raised for nested object descriptions
* #7993: texinfo: a warning not supporting desc_signature_line node is shown
* #7869: :rst:role:`abbr` role without an explanation will show the explanation
  from the previous abbr role
* #8048: graphviz: graphviz.css was copied on building non-HTML document
* C and C++, removed ``noindex`` directive option as it did
  nothing.
* #7619: Duplicated node IDs are generated if node has multiple IDs
* #2050: Symbols sections are appeared twice in the index page
* #8017: Fix circular import in sphinx.addnodes
* #7986: CSS: make "highlight" selector more robust
* #7944: C++, parse non-type template parameters starting with
  a dependent qualified name.
* C, don't deepcopy the entire symbol table and make a mess every time an
  enumerator is handled.

Release 3.1.2 (released Jul 05, 2020)
=====================================

Incompatible changes
--------------------

* #7650: autodoc: the signature of base function will be shown for decorated
  functions, not a signature of decorator

Bugs fixed
----------

* #7844: autodoc: Failed to detect module when relative module name given
* #7856: autodoc: AttributeError is raised when non-class object is given to
  the autoclass directive
* #7850: autodoc: KeyError is raised for invalid mark up when autodoc_typehints
  is 'description'
* #7812: autodoc: crashed if the target name matches to both an attribute and
  module that are same name
* #7650: autodoc: function signature becomes ``(*args, **kwargs)`` if the
  function is decorated by generic decorator
* #7812: autosummary: generates broken stub files if the target code contains
  an attribute and module that are same name
* #7806: viewcode: Failed to resolve viewcode references on 3rd party builders
* #7838: html theme: List items have extra vertical space
* #7878: html theme: Undesired interaction between "overflow" and "float"

Release 3.1.1 (released Jun 14, 2020)
=====================================

Incompatible changes
--------------------

* #7808: napoleon: a type for attribute are represented as typed field

Features added
--------------

* #7807: autodoc: Show detailed warning when type_comment is mismatched with its
  signature

Bugs fixed
----------

* #7808: autodoc: Warnings raised on variable and attribute type annotations
* #7802: autodoc: EOFError is raised on parallel build
* #7821: autodoc: TypeError is raised for overloaded C-ext function
* #7805: autodoc: an object which descriptors returns is unexpectedly documented
* #7807: autodoc: wrong signature is shown for the function using contextmanager
* #7812: autosummary: generates broken stub files if the target code contains
  an attribute and module that are same name
* #7808: napoleon: Warnings raised on variable and attribute type annotations
* #7811: sphinx.util.inspect causes circular import problem

Release 3.1.0 (released Jun 08, 2020)
=====================================

Dependencies
------------

* #7746: mathjax: Update to 2.7.5

Incompatible changes
--------------------

* #7477: imgconverter: Invoke "magick convert" command by default on Windows

Deprecated
----------

* The first argument for sphinx.ext.autosummary.generate.AutosummaryRenderer has
  been changed to Sphinx object
* ``sphinx.ext.autosummary.generate.AutosummaryRenderer`` takes an object type
  as an argument
* The ``ignore`` argument of ``sphinx.ext.autodoc.Documenter.get_doc()``
* The ``template_dir`` argument of ``sphinx.ext.autosummary.generate.
  AutosummaryRenderer``
* The ``module`` argument of ``sphinx.ext.autosummary.generate.
  find_autosummary_in_docstring()``
* The ``builder`` argument of ``sphinx.ext.autosummary.generate.
  generate_autosummary_docs()``
* The ``template_dir`` argument of ``sphinx.ext.autosummary.generate.
  generate_autosummary_docs()``
* The ``ignore`` argument of ``sphinx.util.docstring.prepare_docstring()``
* ``sphinx.ext.autosummary.generate.AutosummaryRenderer.exists()``
* ``sphinx.util.rpartition()``

Features added
--------------

* LaTeX: Make the ``toplevel_sectioning`` setting optional in LaTeX theme
* LaTeX: Allow to override papersize and pointsize from LaTeX themes
* LaTeX: Add :confval:`latex_theme_options` to override theme options
* #7410: Allow to suppress "circular toctree references detected" warnings using
  :confval:`suppress_warnings`
* C, added scope control directives, :rst:dir:`c:namespace`,
  :rst:dir:`c:namespace-push`, and :rst:dir:`c:namespace-pop`.
* #2044: autodoc: Suppress default value for instance attributes
* #7473: autodoc: consider a member public if docstring contains
  ``:meta public:`` in info-field-list
* #7487: autodoc: Allow to generate docs for singledispatch functions by
  py:autofunction
* #7143: autodoc: Support final classes and methods
* #7384: autodoc: Support signatures defined by ``__new__()``, metaclasses and
  builtin base classes
* #2106: autodoc: Support multiple signatures on docstring
* #4422: autodoc: Support GenericAlias in Python 3.7 or above
* #3610: autodoc: Support overloaded functions
* #7722: autodoc: Support TypeVar
* #7466: autosummary: headings in generated documents are not translated
* #7490: autosummary: Add ``:caption:`` option to autosummary directive to set a
  caption to the toctree
* #7469: autosummary: Support module attributes
* #248, #6040: autosummary: Add ``:recursive:`` option to autosummary directive
  to generate stub files recursively
* #4030: autosummary: Add :confval:`autosummary_context` to add template
  variables for custom templates
* #7530: html: Support nested <kbd> elements
* #7481: html theme: Add right margin to footnote/citation labels
* #7482, #7717: html theme: CSS spacing for code blocks with captions and line
  numbers
* #7443: html theme: Add new options :confval:`globaltoc_collapse` and
  :confval:`globaltoc_includehidden` to control the behavior of globaltoc in
  sidebar
* #7484: html theme: Avoid clashes between sidebar and other blocks
* #7476: html theme: Relbar breadcrumb should contain current page
* #7506: html theme: A canonical URL is not escaped
* #7533: html theme: Avoid whitespace at the beginning of genindex.html
* #7541: html theme: Add a "clearer" at the end of the "body"
* #7542: html theme: Make admonition/topic/sidebar scrollable
* #7543: html theme: Add top and bottom margins to tables
* #7695: html theme: Add viewport meta tag for basic theme
* #7721: html theme: classic: default codetextcolor/codebgcolor doesn't override
  Pygments
* C and C++: allow semicolon in the end of declarations.
* C++, parse parameterized noexcept specifiers.
* #7294: C++, parse expressions with user-defined literals.
* C++, parse trailing return types.
* #7143: py domain: Add ``:final:`` option to :rst:dir:`py:class`,
  :rst:dir:`py:exception` and :rst:dir:`py:method` directives
* #7596: py domain: Change a type annotation for variables to a hyperlink
* #7770: std domain: :rst:dir:`option` directive support arguments in the form
  of ``foo[=bar]``
* #7582: napoleon: a type for attribute are represented like type annotation
* #7734: napoleon: overescaped trailing underscore on attribute
* #7247: linkcheck: Add :confval:`linkcheck_request_headers` to send custom HTTP
  headers for specific host
* #7792: setuptools: Support ``--verbosity`` option
* #7683: Add ``allowed_exceptions`` parameter to ``Sphinx.emit()`` to allow
  handlers to raise specified exceptions
* #7295: C++, parse (trailing) requires clauses.

Bugs fixed
----------

* #6703: autodoc: incremental build does not work for imported objects
* #7564: autodoc: annotations not to be shown for descriptors
* #6588: autodoc: Decorated inherited method has no documentation
* #7469: autodoc: The change of autodoc-process-docstring for variables is
  cached unexpectedly
* #7559: autodoc: misdetects a sync function is async
* #6857: autodoc: failed to detect a classmethod on Enum class
* #7562: autodoc: a typehint contains spaces is wrongly rendered under
  :confval:`autodoc_typehints`\ ``='description'`` mode
* #7551: autodoc: failed to import nested class
* #7362: autodoc: does not render correct signatures for built-in functions
* #7654: autodoc: ``Optional[Union[foo, bar]]`` is presented as
  ``Union[foo, bar, None]``
* #7629: autodoc: autofunction emits an unfriendly warning if an invalid object
  specified
* #7650: autodoc: undecorated signature is shown for decorated functions
* #7676: autodoc: typo in the default value of autodoc_member_order
* #7676: autodoc: wrong value for :member-order: option is ignored silently
* #7676: autodoc: member-order="bysource" does not work for C module
* #3673: autodoc: member-order="bysource" does not work for a module having
  ``__all__``
* #7668: autodoc: wrong retann value is passed to a handler of
  autodoc-process-signature
* #7711: autodoc: fails with ValueError when processing numpy objects
* #7791: autodoc: TypeError is raised on documenting singledispatch function
* #7551: autosummary: a nested class is indexed as non-nested class
* #7661: autosummary: autosummary directive emits warnings twices if failed to
  import the target module
* #7685: autosummary: The template variable "members" contains imported members
  even if :confval:`autossummary_imported_members` is ``False``
* #7671: autosummary: The location of import failure warning is missing
* #7535: sphinx-autogen: crashes when custom template uses inheritance
* #7536: sphinx-autogen: crashes when template uses i18n feature
* #7781: sphinx-build: Wrong error message when outdir is not directory
* #7653: sphinx-quickstart: Fix multiple directory creation for nested relpath
* #2785: html: Bad alignment of equation links
* #7718: html theme: some themes does not respect background color of Pygments
  style (agogo, haiku, nature, pyramid, scrolls, sphinxdoc and traditional)
* #7544: html theme: inconsistent padding in admonitions
* #7581: napoleon: bad parsing of inline code in attribute docstrings
* #7628: imgconverter: runs imagemagick once unnecessary for builders not
  supporting images
* #7610: incorrectly renders consecutive backslashes for Docutils 0.16
* #7646: handle errors on event handlers
* #4187: LaTeX: EN DASH disappears from PDF bookmarks in Japanese documents
* #7701: LaTeX: Anonymous indirect hyperlink target causes duplicated labels
* #7723: LaTeX: pdflatex crashed when URL contains a single quote
* #7756: py domain: The default value for positional only argument is not shown
* #7760: coverage: Add :confval:`coverage_show_missing_items` to show coverage
  result to console
* C++, fix rendering and xrefs in nested names explicitly starting
  in global scope, e.g., ``::A::B``.
* C, fix rendering and xrefs in nested names explicitly starting
  in global scope, e.g., ``.A.B``.
* #7763: C and C++, don't crash during display stringification of unary
  expressions and fold expressions.

Release 3.0.4 (released May 27, 2020)
=====================================

Bugs fixed
----------

* #7567: autodoc: parametrized types are shown twice for generic types
* #7637: autodoc: system defined TypeVars are shown in Python 3.9
* #7696: html: Updated jQuery version from 3.4.1 to 3.5.1 for security reasons
* #7611: md5 fails when OpenSSL FIPS is enabled
* #7626: release package does not contain ``CODE_OF_CONDUCT``

Release 3.0.3 (released Apr 26, 2020)
=====================================

Features added
--------------

* C, parse array declarators with static, qualifiers, and VLA specification.

Bugs fixed
----------

* #7516: autodoc: crashes if target object raises an error on accessing
  its attributes

Release 3.0.2 (released Apr 19, 2020)
=====================================

Features added
--------------

* C, parse attributes and add :confval:`c_id_attributes`
  and :confval:`c_paren_attributes` to support user-defined attributes.

Bugs fixed
----------

* #7461: py domain: fails with IndexError for empty tuple in type annotation
* #7510: py domain: keyword-only arguments are documented as having a default of
  None
* #7418: std domain: :rst:role:`term` role could not match case-insensitively
* #7461: autodoc: empty tuple in type annotation is not shown correctly
* #7479: autodoc: Sphinx builds has been slower since 3.0.0 on mocking
* C++, fix spacing issue in east-const declarations.
* #7414: LaTeX: Xindy language options were incorrect
* Sphinx crashes with ImportError on python3.5.1

Release 3.0.1 (released Apr 11, 2020)
=====================================

Incompatible changes
--------------------

* #7418: std domain: :rst:role:`term` role becomes case sensitive

Bugs fixed
----------

* #7428: py domain: a reference to class ``None`` emits a nitpicky warning
* #7445: py domain: a return annotation ``None`` in the function signature is
  not converted to a hyperlink when using intersphinx
* #7418: std domain: duplication warning for glossary terms is case insensitive
* #7438: C++, fix merging overloaded functions in parallel builds.
* #7422: autodoc: fails with ValueError when using autodoc_mock_imports
* #7435: autodoc: :confval:`autodoc_typehints`\ ``='description'`` doesn't
  suppress typehints in signature for classes/methods
* #7451: autodoc: fails with AttributeError when an object returns non-string
  object as a ``__doc__`` member
* #7423: crashed when giving a non-string object to logger
* #7479: html theme: Do not include xmlns attribute with HTML 5 doctype
* #7426: html theme: Escape some links in HTML templates

Release 3.0.0 (released Apr 06, 2020)
=====================================

Dependencies
------------

3.0.0b1

* LaTeX: drop dependency on :program:`extractbb` for image inclusion in
  Japanese documents as ``.xbb`` files are unneeded by :program:`dvipdfmx`
  since TeXLive2015 (refs: #6189)
* babel-2.0 or above is available (Unpinned)

Incompatible changes
--------------------

3.0.0b1

* Drop features and APIs deprecated in 1.8.x
* #247: autosummary: stub files are overwritten automatically by default.  see
  :confval:`autosummary_generate_overwrite` to change the behavior
* #5923: autodoc: the members of ``object`` class are not documented by default
  when ``:inherited-members:`` and ``:special-members:`` are given.
* #6830: py domain: ``meta`` fields in info-field-list becomes reserved.  They
  are not displayed on output document now
* #6417: py domain: doctree of desc_parameterlist has been changed.  The
  argument names, annotations and default values are wrapped with inline node
* The structure of ``sphinx.events.EventManager.listeners`` has changed
* Due to the scoping changes for :rst:dir:`productionlist` some uses of
  :rst:role:`token` must be modified to include the scope which was previously
  ignored.
* #6903: Internal data structure of Python, reST and standard domains have
  changed.  The node_id is added to the index of objects and modules.  Now they
  contains a pair of docname and node_id for cross reference.
* #7276: C++ domain: Non intended behavior is removed such as ``say_hello_``
  links to ``.. cpp:function:: say_hello()``
* #7210: js domain: Non intended behavior is removed such as ``parseInt_`` links
  to ``.. js:function:: parseInt``
* #7229: rst domain: Non intended behavior is removed such as ``numref_`` links
  to ``.. rst:role:: numref``
* #6903: py domain: Non intended behavior is removed such as ``say_hello_``
  links to ``.. py:function:: say_hello()``
* #7246: py domain: Drop special cross reference helper for exceptions,
  functions and methods
* The C domain has been rewritten, with additional directives and roles.
  The existing ones are now more strict, resulting in new warnings.
* The attribute ``sphinx_cpp_tagname`` in the ``desc_signature_line`` node
  has been renamed to ``sphinx_line_type``.
* #6462: double backslashes in domain directives are no longer replaced by
  single backslashes as default. A new configuration value
  :confval:`strip_signature_backslash` can be used by users to re-enable it.

3.0.0 final

* #7222: ``sphinx.util.inspect.unwrap()`` is renamed to ``unwrap_all()``

Deprecated
----------

3.0.0b1

* ``desc_signature['first']``
* ``sphinx.directives.DescDirective``
* ``sphinx.domains.std.StandardDomain.add_object()``
* ``sphinx.domains.python.PyDecoratorMixin``
* ``sphinx.ext.autodoc.get_documenters()``
* ``sphinx.ext.autosummary.process_autosummary_toc()``
* ``sphinx.parsers.Parser.app``
* ``sphinx.testing.path.Path.text()``
* ``sphinx.testing.path.Path.bytes()``
* ``sphinx.util.inspect.getargspec()``
* ``sphinx.writers.latex.LaTeXWriter.format_docclass()``

Features added
--------------

3.0.0b1

* #247: autosummary: Add :confval:`autosummary_generate_overwrite` to overwrite
  old stub file
* #5923: autodoc: ``:inherited-members:`` option takes a name of ancestor class
  not to document inherited members of the class and uppers
* #6830: autodoc: consider a member private if docstring contains
  ``:meta private:`` in info-field-list
* #7165: autodoc: Support Annotated type (PEP-593)
* #2815: autodoc: Support singledispatch functions and methods
* #7079: autodoc: :confval:`autodoc_typehints` accepts ``"description"``
  configuration.  It shows typehints as object description
* #7314: apidoc: Propagate ``--maxdepth`` option through package documents
* #6558: glossary: emit a warning for duplicated glossary entry
* #3106: domain: Register hyperlink target for index page automatically
* #6558: std domain: emit a warning for duplicated generic objects
* #6830: py domain: Add new event: :event:`object-description-transform`
* #6895: py domain: Do not emit nitpicky warnings for built-in types
* py domain: Support lambda functions in function signature
* #6417: py domain: Allow to make a style for arguments of functions and methods
* #7238, #7239: py domain: Emit a warning on describing a python object if the
  entry is already added as the same name
* #7341: py domain: type annotations in signature are converted to cross refs
* Support priority of event handlers. For more detail, see
  :py:meth:`.Sphinx.connect()`
* #3077: Implement the scoping for :rst:dir:`productionlist` as indicated
  in the documentation.
* #1027: Support backslash line continuation in :rst:dir:`productionlist`.
* #7108: config: Allow to show an error message from conf.py via ``ConfigError``
* #7032: html: :confval:`html_scaled_image_link` will be disabled for images having
  ``no-scaled-link`` class
* #7144: Add CSS class indicating its domain for each desc node
* #7211: latex: Use babel for Chinese document when using XeLaTeX
* #6672: LaTeX: Support LaTeX Theming (experimental)
* #7005: LaTeX: Add LaTeX styling macro for :rst:role:`kbd` role
* #7220: genindex: Show "main" index entries at first
* #7103: linkcheck: writes all links to ``output.json``
* #7025: html search: full text search can be disabled for individual document
  using ``:nosearch:`` file-wide metadata
* #7293: html search: Allow to override JavaScript splitter via
  ``SearchLanguage.js_splitter_code``
* #7142: html theme: Add a theme option: ``pygments_dark_style`` to switch the
  style of code-blocks in dark mode
* The C domain has been rewritten adding for example:

  - Cross-referencing respecting the current scope.
  - Possible to document anonymous entities.
  - More specific directives and roles for each type of entity,
    e.g., handling scoping of enumerators.
  - New role :rst:role:`c:expr` for rendering expressions and types
    in text.

* Added ``SphinxDirective.get_source_info()``
  and ``SphinxRole.get_source_info()``.
* #7324: sphinx-build: Emit a warning if multiple files having different file
  extensions for same document found

3.0.0 final

* Added ``ObjectDescription.transform_content()``.

Bugs fixed
----------

3.0.0b1

* C++, fix cross reference lookup in certain cases involving
  function overloads.
* #5078: C++, fix cross reference lookup when a directive contains multiple
  declarations.
* C++, suppress warnings for directly dependent typenames in cross references
  generated automatically in signatures.
* #5637: autodoc: Incorrect handling of nested class names on show-inheritance
* #7267: autodoc: error message for invalid directive options has wrong location
* #7329: autodoc: info-field-list is wrongly generated from type hints into the
  class description even if ``autoclass_content='class'`` set
* #7331: autodoc: a cython-function is not recognized as a function
* #5637: inheritance_diagram: Incorrect handling of nested class names
* #7139: ``code-block:: guess`` does not work
* #7325: html: source_suffix containing dot leads to wrong source link
* #7357: html: Resizing SVG image fails with ValueError
* #7278: html search: Fix use of ``html_file_suffix`` instead of
  ``html_link_suffix`` in search results
* #7297: html theme: ``bizstyle`` does not support ``sidebarwidth``
* #3842: singlehtml: Path to images broken when master doc is not in source root
* #7179: std domain: Fix whitespaces are suppressed on referring GenericObject
* #7289: console: use bright colors instead of bold
* #1539: C, parse array types.
* #2377: C, parse function pointers even in complex types.
* #7345: sphinx-build: Sphinx crashes if output directory exists as a file
* #7290: sphinx-build: Ignore bdb.BdbQuit when handling exceptions
* #6240: napoleon: Attributes and Methods sections ignore :noindex: option

3.0.0 final

* #7364: autosummary: crashed when :confval:`autosummary_generate` is ``False``
* #7370: autosummary: raises UnboundLocalError when unknown module given
* #7367: C++, alternate operator spellings are now supported.
* C, alternate operator spellings are now supported.
* #7368: C++, comma operator in expressions, pack expansion in template
  argument lists, and more comprehensive error messages in some cases.
* C, C++, fix crash and wrong duplicate warnings related to anon symbols.
* #6477: Escape first "!" in a cross reference linking no longer possible
* #7219: py domain: The index entry generated by ``py:function`` directive is
  different with one from ``index`` directive with "builtin" type
* #7301: capital characters are not allowed for node_id
* #7301: epub: duplicated node_ids are generated
* #6564: html: a width of table was ignored on HTML builder
* #7401: Incorrect argument is passed for :event:`env-get-outdated` handlers
* #7355: autodoc: a signature of cython-function is not recognized well
* #7222: autodoc: ``__wrapped__`` functions are not documented correctly
* #7409: intersphinx: ValueError is raised when an extension sets up
  :confval:`intersphinx_mapping` on :event:`config-inited` event
* #7343: Sphinx builds has been slower since 2.4.0 on debug mode

Release 2.4.5 (released Nov 18, 2021)
=====================================

Dependencies
------------

* #9807: Restrict Docutils to 0.17.x or older

Release 2.4.4 (released Mar 05, 2020)
=====================================

Bugs fixed
----------

* #7197: LaTeX: platex cause error to build image directive with target url
* #7223: Sphinx builds has been slower since 2.4.0

Release 2.4.3 (released Feb 22, 2020)
=====================================

Bugs fixed
----------

* #7184: autodoc: ``*args`` and ``**kwarg`` in type comments are not handled
  properly
* #7189: autodoc: classmethod coroutines are not detected
* #7183: intersphinx: ``:attr:`` reference to property is broken
* #6244, #6387: html search: Search breaks/hangs when built with dirhtml builder
* #7195: todo: emit doctree-resolved event with non-document node incorrectly

Release 2.4.2 (released Feb 19, 2020)
=====================================

Bugs fixed
----------

* #7138: autodoc: ``autodoc.typehints`` crashed when variable has unbound object
  as a value
* #7156: autodoc: separator for keyword only arguments is not shown
* #7146: autodoc: IndexError is raised on suppressed type_comment found
* #7161: autodoc: typehints extension does not support parallel build
* #7178: autodoc: TypeError is raised on fetching type annotations
* #7151: crashed when extension assigns a value to ``env.indexentries``
* #7170: text: Remove debug print
* #7137: viewcode: Avoid to crash when non-python code given

Release 2.4.1 (released Feb 11, 2020)
=====================================

Bugs fixed
----------

* #7120: html: crashed when on scaling SVG images which have float dimensions
* #7126: autodoc: TypeError: 'getset_descriptor' object is not iterable

Release 2.4.0 (released Feb 09, 2020)
=====================================

Deprecated
----------

* The ``decode`` argument of ``sphinx.pycode.ModuleAnalyzer()``
* ``sphinx.directives.other.Index``
* ``sphinx.environment.temp_data['gloss_entries']``
* ``sphinx.environment.BuildEnvironment.indexentries``
* ``sphinx.environment.collectors.indexentries.IndexEntriesCollector``
* ``sphinx.ext.apidoc.INITPY``
* ``sphinx.ext.apidoc.shall_skip()``
* ``sphinx.io.FiletypeNotFoundError``
* ``sphinx.io.get_filetype()``
* ``sphinx.pycode.ModuleAnalyzer.encoding``
* ``sphinx.roles.Index``
* ``sphinx.util.detect_encoding()``
* ``sphinx.util.get_module_source()``
* ``sphinx.util.inspect.Signature``
* ``sphinx.util.inspect.safe_getmembers()``
* ``sphinx.writers.latex.LaTeXTranslator.settings.author``
* ``sphinx.writers.latex.LaTeXTranslator.settings.contentsname``
* ``sphinx.writers.latex.LaTeXTranslator.settings.docclass``
* ``sphinx.writers.latex.LaTeXTranslator.settings.docname``
* ``sphinx.writers.latex.LaTeXTranslator.settings.title``
* ``sphinx.writers.latex.ADDITIONAL_SETTINGS``
* ``sphinx.writers.latex.DEFAULT_SETTINGS``
* ``sphinx.writers.latex.LUALATEX_DEFAULT_FONTPKG``
* ``sphinx.writers.latex.PDFLATEX_DEFAULT_FONTPKG``
* ``sphinx.writers.latex.XELATEX_DEFAULT_FONTPKG``
* ``sphinx.writers.latex.XELATEX_GREEK_DEFAULT_FONTPKG``

Features added
--------------

* #6910: inheritance_diagram: Make the background of diagrams transparent
* #6446: duration: Add ``sphinx.ext.durations`` to inspect which documents slow
  down the build
* #6837: LaTeX: Support a nested table
* #7115: LaTeX: Allow to override LATEXOPTS and LATEXMKOPTS via environment
  variable
* #6966: graphviz: Support ``:class:`` option
* #6696: html: ``:scale:`` option of image/figure directive not working for SVG
  images (imagesize-1.2.0 or above is required)
* #6994: imgconverter: Support illustrator file (.ai) to .png conversion
* autodoc: Support Positional-Only Argument separator (PEP-570 compliant)
* autodoc: Support type annotations for variables
* #2755: autodoc: Add new event: :event:`autodoc-before-process-signature`
* #2755: autodoc: Support type_comment style (ex. ``# type: (str) -> str``)
  annotation (python3.8+ or `typed_ast <https://github.com/python/typed_ast>`_
  is required)
* #7051: autodoc: Support instance variables without defaults (PEP-526)
* #6418: autodoc: Add a new extension ``sphinx.ext.autodoc.typehints``. It shows
  typehints as object description if ``autodoc_typehints = "description"`` set.
  This is an experimental extension and it will be integrated into autodoc core
  in Sphinx 3.0
* SphinxTranslator now calls visitor/departure method for super node class if
  visitor/departure method for original node class not found
* #6418: Add new event: :event:`object-description-transform`
* py domain: :rst:dir:`py:data` and :rst:dir:`py:attribute` take new options
  named ``:type:`` and ``:value:`` to describe its type and initial value
* #6785: py domain: ``:py:attr:`` is able to refer properties again
* #6772: apidoc: Add ``-q`` option for quiet mode

Bugs fixed
----------

* #6925: html: Remove redundant type="text/javascript" from <script> elements
* #7112: html: SVG image is not layouted as float even if aligned
* #6906, #6907: autodoc: failed to read the source codes encoded in cp1251
* #6961: latex: warning for babel shown twice
* #7059: latex: LaTeX compilation falls into infinite loop (wrapfig issue)
* #6581: latex: ``:reversed:`` option for toctree does not effect to LaTeX build
* #6559: Wrong node-ids are generated in glossary directive
* #6986: apidoc: misdetects module name for .so file inside module
* #6899: apidoc: private members are not shown even if ``--private`` given
* #6327: apidoc: Support a python package consisted of __init__.so file
* #6999: napoleon: fails to parse tilde in :exc: role
* #7019: gettext: Absolute path used in message catalogs
* #7023: autodoc: nested partial functions are not listed
* #7023: autodoc: partial functions imported from other modules are listed as
  module members without :impoprted-members: option
* #6889: autodoc: Trailing comma in ``:members::`` option causes cryptic warning
* #6568: autosummary: ``autosummary_imported_members`` is ignored on generating
  a stub file for submodule
* #7055: linkcheck: redirect is treated as an error
* #7088: HTML template: If ``navigation_with_keys`` option is activated,
  modifier keys are ignored, which means the feature can interfere with browser
  features
* #7090: std domain: Can't assign numfig-numbers for custom container nodes
* #7106: std domain: enumerated nodes are marked as duplicated when extensions
  call ``note_explicit_target()``
* #7095: dirhtml: Cross references are broken via intersphinx and ``:doc:`` role
* C++:

  - Don't crash when using the ``struct`` role in some cases.
  - Don't warn when using the ``var``/``member`` role for function
    parameters.
  - Render call and braced-init expressions correctly.
* #7097: Filenames of images generated by
  ``sphinx.transforms.post_transforms.images.ImageConverter``
  or its subclasses (used for latex build) are now sanitized,
  to prevent broken paths

Release 2.3.1 (released Dec 22, 2019)
=====================================

Bugs fixed
----------

* #6936: sphinx-autogen: raises AttributeError

Release 2.3.0 (released Dec 15, 2019)
=====================================

Incompatible changes
--------------------

* #6742: ``end-before`` option of :rst:dir:`literalinclude` directive does not
  match the first line of the code block.
* #1331: Change default User-Agent header to ``"Sphinx/X.Y.Z requests/X.Y.Z
  python/X.Y.Z"``.  It can be changed via :confval:`user_agent`.
* #6867: text: content of admonitions starts after a blank line

Deprecated
----------

* ``sphinx.builders.gettext.POHEADER``
* ``sphinx.io.SphinxStandaloneReader.app``
* ``sphinx.io.SphinxStandaloneReader.env``
* ``sphinx.util.texescape.tex_escape_map``
* ``sphinx.util.texescape.tex_hl_escape_map_new``
* ``sphinx.writers.latex.LaTeXTranslator.no_contractions``

Features added
--------------

* #6707: C++, support bit-fields.
* #267: html: Eliminate prompt characters of doctest block from copyable text
* #6548: html: Use favicon for OpenSearch if available
* #6729: html theme: agogo theme now supports ``rightsidebar`` option
* #6780: Add PEP-561 Support
* #6762: latex: Allow to load additional LaTeX packages via ``extrapackages`` key
  of :confval:`latex_elements`
* #1331: Add new config variable: :confval:`user_agent`
* #6000: LaTeX: have backslash also be an inline literal word wrap break
  character
* #4186: LaTeX: Support upLaTeX as a new :confval:`latex_engine` (experimental)
* #6812: Improve a warning message when extensions are not parallel safe
* #6818: Improve Intersphinx performance for multiple remote inventories.
* #2546: apidoc: .so file support
* #6798: autosummary: emit ``autodoc-skip-member`` event on generating stub file
* #6483: i18n: make explicit titles in toctree translatable
* #6816: linkcheck: Add :confval:`linkcheck_auth` option to provide
  authentication information when doing ``linkcheck`` builds
* #6872: linkcheck: Handles HTTP 308 Permanent Redirect
* #6613: html: Wrap section number in span tag
* #6781: gettext: Add :confval:`gettext_last_translator` and
  :confval:`gettext_language_team` to customize headers of POT file

Bugs fixed
----------

* #6668: LaTeX: Longtable before header has incorrect distance
  (refs: `latex3/latex2e#173`_)

  .. _latex3/latex2e#173: https://github.com/latex3/latex2e/issues/173
* #6618: LaTeX: Avoid section names at the end of a page
* #6738: LaTeX: Do not replace unicode characters by LaTeX macros on unicode
  supported LaTeX engines: ¶, §, €, ∞, ±, →, ‣, –, superscript and subscript
  digits go through "as is" (as default OpenType font supports them)
* #6704: linkcheck: Be defensive and handle newly defined HTTP error code
* #6806: linkcheck: Failure on parsing content
* #6655: image URLs containing ``data:`` causes gettext builder crashed
* #6584: i18n: Error when compiling message catalogs on Hindi
* #6718: i18n: KeyError is raised if section title and table title are same
* #6743: i18n: :confval:`rst_prolog` breaks the translation
* #6708: mathbase: Some deprecated functions have removed
* #6709: autodoc: mock object does not work as a class decorator
* #5070: epub: Wrong internal href fragment links
* #6712: Allow not to install sphinx.testing as runtime (mainly for ALT Linux)
* #6741: html: search result was broken with empty :confval:`html_file_suffix`
* #6001: LaTeX does not wrap long code lines at backslash character
* #6804: LaTeX: PDF build breaks if admonition of danger type contains
  code-block long enough not to fit on one page
* #6809: LaTeX: code-block in a danger type admonition can easily spill over
  bottom of page
* #6793: texinfo: Code examples broken following "sidebar"
* #6813: An orphan warning is emitted for included document on Windows.  Thanks
  to @drillan
* #6850: Fix smartypants module calls re.sub() with wrong options
* #6824: HTML search: If a search term is partially matched in the title and
  fully matched in a text paragraph on the same page, the search does not
  include this match.
* #6848: config.py shouldn't pop extensions from overrides
* #6867: text: extra spaces are inserted to hyphenated words on folding lines
* #6886: LaTeX: xelatex converts straight double quotes into right curly ones
  (shows when :confval:`smartquotes` is ``False``)
* #6890: LaTeX: even with smartquotes off, PDF output transforms straight
  quotes and consecutive hyphens into curly quotes and dashes
* #6876: LaTeX: multi-line display of authors on title page has ragged edges
* #6887: Sphinx crashes with Docutils 0.16b0
* #6920: sphinx-build: A console message is wrongly highlighted
* #6900: sphinx-build: ``-D`` option does not considers ``0`` and ``1`` as a
  boolean value

Release 2.2.2 (released Dec 03, 2019)
=====================================

Incompatible changes
--------------------

* #6803: For security reason of python, parallel mode is disabled on macOS and
  Python3.8+

Bugs fixed
----------

* #6776: LaTeX: 2019-10-01 LaTeX release breaks :file:`sphinxcyrillic.sty`
* #6815: i18n: French, Hindi, Chinese, Japanese and Korean translation messages
  has been broken
* #6803: parallel build causes AttributeError on macOS and Python3.8

Release 2.2.1 (released Oct 26, 2019)
=====================================

Bugs fixed
----------

* #6641: LaTeX: Undefined control sequence ``\sphinxmaketitle``
* #6710: LaTeX not well configured for Greek language as main language
* #6759: validation of html static paths and extra paths no longer throws
  an error if the paths are in different directories

Release 2.2.0 (released Aug 19, 2019)
=====================================

Incompatible changes
--------------------

* apidoc: template files are renamed to ``.rst_t``
* html: Field lists will be styled by grid layout

Deprecated
----------

* ``sphinx.domains.math.MathDomain.add_equation()``
* ``sphinx.domains.math.MathDomain.get_next_equation_number()``
* The ``info`` and ``warn`` arguments of
  ``sphinx.ext.autosummary.generate.generate_autosummary_docs()``
* ``sphinx.ext.autosummary.generate._simple_info()``
* ``sphinx.ext.autosummary.generate._simple_warn()``
* ``sphinx.ext.todo.merge_info()``
* ``sphinx.ext.todo.process_todo_nodes()``
* ``sphinx.ext.todo.process_todos()``
* ``sphinx.ext.todo.purge_todos()``

Features added
--------------

* #5124: graphviz: ``:graphviz_dot:`` option is renamed to ``:layout:``
* #1464: html: emit a warning if :confval:`html_static_path` and
  :confval:`html_extra_path` directories are inside output directory
* #6514: html: Add a label to search input for accessibility purposes
* #5602: apidoc: Add ``--templatedir`` option
* #6475: Add ``override`` argument to ``app.add_autodocumenter()``
* #6310: imgmath: let :confval:`imgmath_use_preview` work also with the SVG
  format for images rendering inline math
* #6533: LaTeX: refactor visit_enumerated_list() to use ``\sphinxsetlistlabels``
* #6628: quickstart: Use ``https://docs.python.org/3/`` for default setting of
  :confval:`intersphinx_mapping`
* #6419: sphinx-build: give reasons why rebuilt

Bugs fixed
----------

* py domain: duplicated warning does not point the location of source code
* #6499: html: Sphinx never updates a copy of :confval:`html_logo` even if
  original file has changed
* #1125: html theme: scrollbar is hard to see on classic theme and macOS
* #5502: linkcheck: Consider HTTP 503 response as not an error
* #6439: Make generated download links reproducible
* #6486: UnboundLocalError is raised if broken extension installed
* #6567: autodoc: :confval:`autodoc_inherit_docstrings` does not effect to
  ``__init__()`` and ``__new__()``
* #6574: autodoc: :confval:`autodoc_member_order` does not refer order of
  imports when ``'bysource'`` order
* #6574: autodoc: missing type annotation for variadic and keyword parameters
* #6589: autodoc: Formatting issues with autodoc_typehints='none'
* #6605: autodoc: crashed when target code contains custom method-like objects
* #6498: autosummary: crashed with wrong autosummary_generate setting
* #6507: autosummary: crashes without no autosummary_generate setting
* #6511: LaTeX: autonumbered list can not be customized in LaTeX
  since Sphinx 1.8.0 (refs: #6533)
* #6531: Failed to load last environment object when extension added
* #736: Invalid sort in pair index
* #6527: :data:`last_updated` wrongly assumes timezone as UTC
* #5592: std domain: :rst:dir:`option` directive registers an index entry for
  each comma separated option
* #6549: sphinx-build: Escaped characters in error messages
* #6545: doctest comments not getting trimmed since Sphinx 1.8.0
* #6561: glossary: Wrong hyperlinks are generated for non alphanumeric terms
* #6620: i18n: classifiers of definition list are not translated with
  Docutils 0.15
* #6474: ``DocFieldTransformer`` raises AttributeError when given directive is
  not a subclass of ObjectDescription

Release 2.1.2 (released Jun 19, 2019)
=====================================

Bugs fixed
----------

* #6497: custom lexers fails highlighting when syntax error
* #6478, #6488: info field lists are incorrectly recognized

Release 2.1.1 (released Jun 10, 2019)
=====================================

Incompatible changes
--------------------

* #6447: autodoc: Stop to generate document for undocumented module variables

Bugs fixed
----------

* #6442: LaTeX: admonitions of :rst:dir:`note` type can get separated from
  immediately preceding section title by pagebreak
* #6448: autodoc: crashed when autodocumenting classes with ``__slots__ = None``
* #6451: autodoc: generates docs for "optional import"ed modules as variables
* #6452: autosummary: crashed when generating document of properties
* #6455: napoleon: docstrings for properties are not processed
* #6436: napoleon: "Unknown target name" error if variable name ends with
  underscore
* #6440: apidoc: missing blank lines between modules

Release 2.1.0 (released Jun 02, 2019)
=====================================

Incompatible changes
--------------------

* Ignore filenames without file extension given to ``Builder.build_specific()``
  API directly
* #6230: The anchor of term in glossary directive is changed if it is consisted
  by non-ASCII characters
* #4550: html: Centering tables by default using CSS
* #6239: latex: xelatex and xeCJK are used for Chinese documents by default
* ``Sphinx.add_lexer()`` now takes a Lexer class instead of instance.  An
  instance of lexers are still supported until Sphinx 3.x.

Deprecated
----------

* ``sphinx.builders.latex.LaTeXBuilder.apply_transforms()``
* ``sphinx.builders._epub_base.EpubBuilder.esc()``
* ``sphinx.directives.Acks``
* ``sphinx.directives.Author``
* ``sphinx.directives.Centered``
* ``sphinx.directives.Class``
* ``sphinx.directives.CodeBlock``
* ``sphinx.directives.Figure``
* ``sphinx.directives.HList``
* ``sphinx.directives.Highlight``
* ``sphinx.directives.Include``
* ``sphinx.directives.Index``
* ``sphinx.directives.LiteralInclude``
* ``sphinx.directives.Meta``
* ``sphinx.directives.Only``
* ``sphinx.directives.SeeAlso``
* ``sphinx.directives.TabularColumns``
* ``sphinx.directives.TocTree``
* ``sphinx.directives.VersionChange``
* ``sphinx.domains.python.PyClassmember``
* ``sphinx.domains.python.PyModulelevel``
* ``sphinx.domains.std.StandardDomain._resolve_citation_xref()``
* ``sphinx.domains.std.StandardDomain.note_citations()``
* ``sphinx.domains.std.StandardDomain.note_citation_refs()``
* ``sphinx.domains.std.StandardDomain.note_labels()``
* ``sphinx.environment.NoUri``
* ``sphinx.ext.apidoc.format_directive()``
* ``sphinx.ext.apidoc.format_heading()``
* ``sphinx.ext.apidoc.makename()``
* ``sphinx.ext.autodoc.importer.MockFinder``
* ``sphinx.ext.autodoc.importer.MockLoader``
* ``sphinx.ext.autodoc.importer.mock()``
* ``sphinx.ext.autosummary.autolink_role()``
* ``sphinx.ext.imgmath.DOC_BODY``
* ``sphinx.ext.imgmath.DOC_BODY_PREVIEW``
* ``sphinx.ext.imgmath.DOC_HEAD``
* ``sphinx.transforms.CitationReferences``
* ``sphinx.transforms.SmartQuotesSkipper``
* ``sphinx.util.docfields.DocFieldTransformer.preprocess_fieldtypes()``
* ``sphinx.util.node.find_source_node()``
* ``sphinx.util.i18n.find_catalog()``
* ``sphinx.util.i18n.find_catalog_files()``
* ``sphinx.util.i18n.find_catalog_source_files()``

For more details, see :ref:`deprecation APIs list <dev-deprecated-apis>`.

Features added
--------------

* Add a helper class ``sphinx.transforms.post_transforms.SphinxPostTransform``
* Add helper methods

  - ``PythonDomain.note_module()``
  - ``PythonDomain.note_object()``
  - ``SphinxDirective.set_source_info()``

* #6180: Support ``--keep-going`` with ``BuildDoc`` setup command
* ``math`` directive now supports ``:class:`` option
* todo: ``todo`` directive now supports ``:name:`` option
* Enable override via environment of ``SPHINXOPTS`` and ``SPHINXBUILD`` Makefile
  variables (refs: #6232, #6303)
* #6287: autodoc: Unable to document bound instance methods exported as module
  functions
* #6289: autodoc: :confval:`autodoc_default_options` now supports
  ``imported-members`` option
* #4777: autodoc: Support coroutine
* #744: autodoc: Support abstractmethod
* #6325: autodoc: Support attributes in __slots__.  For dict-style __slots__,
  autodoc considers values as a docstring of the attribute
* #6361: autodoc: Add :confval:`autodoc_typehints` to suppress typehints from
  signature
* #1063: autodoc: ``automodule`` directive now handles undocumented module level
  variables
* #6212: autosummary: Add :confval:`autosummary_imported_members` to display
  imported members on autosummary
* #6271: ``make clean`` is catastrophically broken if building into '.'
* #6363: Support ``%O%`` environment variable in make.bat
* #4777: py domain: Add ``:async:`` option to :rst:dir:`py:function` directive
* py domain: Add new options to :rst:dir:`py:method` directive

  - ``:abstractmethod:``
  - ``:async:``
  - ``:classmethod:``
  - ``:property:``
  - ``:staticmethod:``

* rst domain: Add :rst:dir:`rst:directive:option` directive to describe the option
  for directive
* #6306: html: Add a label to search form for accessibility purposes
* #4390: html: Consistent and semantic CSS for signatures
* #6358: The ``rawsource`` property of ``production`` nodes now contains the
  full production rule
* #6373: autosectionlabel: Allow suppression of warnings
* coverage: Support a new ``coverage_ignore_pyobjects`` option
* #6239: latex: Support to build Chinese documents

Bugs fixed
----------

* #6230: Inappropriate node_id has been generated by glossary directive if term
  is consisted by non-ASCII characters
* #6213: ifconfig: contents after headings are not shown
* commented term in glossary directive is wrongly recognized
* #6299: rst domain: rst:directive directive generates waste space
* #6379: py domain: Module index (py-modindex.html) has duplicate titles
* #6331: man: invalid output when doctest follows rubric
* #6351: "Hyperlink target is not referenced" message is shown even if
  referenced
* #6165: autodoc: ``tab_width`` setting of Docutils has been ignored
* #6347: autodoc: crashes with a plain Tuple on Python 3.6 and 3.5
* #6311: autosummary: autosummary table gets confused by complex type hints
* #6350: autosummary: confused by an argument having some kind of default value
* Generated Makefiles lack a final EOL (refs: #6232)
* #6375: extlinks: Cannot escape angle brackets in link caption
* #6378: linkcheck: Send commonly used User-Agent
* #6387: html search: failed to search document with haiku and scrolls themes
* #6408: html search: Fix the ranking of search results
* #6406: Wrong year is returned for ``SOURCE_DATE_EPOCH``
* #6402: image directive crashes by unknown image format
* #6286: C++, allow 8 and 9 in hexadecimal integer literals.
* #6305: Fix the string in quickstart for 'path' argument of parser
* LaTeX: Figures in admonitions produced errors (refs: #6364)

Release 2.0.1 (released Apr 08, 2019)
=====================================

Bugs fixed
----------

* LaTeX: some system labels are not translated
* RemovedInSphinx30Warning is marked as pending
* deprecation warnings are not emitted

  - ``sphinx.application.CONFIG_FILENAME``
  - ``sphinx.builders.htmlhelp``
  - :confval:`!viewcode_import`

* #6208: C++, properly parse full xrefs that happen to have a short xref as
  prefix
* #6220, #6225: napoleon: AttributeError is raised for raised section having
  references
* #6245: circular import error on importing SerializingHTMLBuilder
* #6243: LaTeX: 'releasename' setting for latex_elements is ignored
* #6244: html: Search function is broken with 3rd party themes
* #6263: html: HTML5Translator crashed with invalid field node
* #6262: html theme: The style of field lists has changed in bizstyle theme

Release 2.0.0 (released Mar 29, 2019)
=====================================

Dependencies
------------

2.0.0b1

* LaTeX builder now depends on TeX Live 2015 or above.
* LaTeX builder (with ``'pdflatex'`` :confval:`latex_engine`) will process
  Unicode Greek letters in text (not in math mark-up) via the text font and
  will not escape them to math mark-up. See the discussion of the
  ``'fontenc'`` key of :confval:`latex_elements`; such (optional) support for
  Greek adds, for example on Ubuntu xenial, the ``texlive-lang-greek`` and (if
  default font set-up is not modified) ``cm-super(-minimal)`` as additional
  Sphinx LaTeX requirements.
* LaTeX builder with :confval:`latex_engine` set to ``'xelatex'`` or to
  ``'lualatex'`` requires (by default) the ``FreeFont`` fonts,
  which in Ubuntu xenial are provided by package ``fonts-freefont-otf``, and
  e.g. in Fedora 29 via package ``texlive-gnu-freefont``.
* requests 2.5.0 or above
* The six package is no longer a dependency
* The sphinxcontrib-websupport package is no longer a dependency
* Some packages are separated to sub packages:

  - sphinxcontrib.applehelp
  - sphinxcontrib.devhelp
  - sphinxcontrib.htmlhelp
  - sphinxcontrib.jsmath
  - sphinxcontrib.serializinghtml
  - sphinxcontrib.qthelp

Incompatible changes
--------------------

2.0.0b1

* Drop python 2.7 and 3.4 support
* Drop Docutils 0.11 support
* Drop features and APIs deprecated in 1.7.x
* The default setting for :confval:`master_doc` is changed to ``'index'`` which
  has been longly used as default of sphinx-quickstart.
* LaTeX: Move message resources to ``sphinxmessage.sty``
* LaTeX: Stop using ``\captions<lang>`` macro for some labels
* LaTeX: for ``'xelatex'`` and ``'lualatex'``, use the ``FreeFont`` OpenType
  fonts as default choice (refs: #5645)
* LaTeX: ``'xelatex'`` and ``'lualatex'`` now use ``\small`` in code-blocks
  (due to ``FreeMono`` character width) like ``'pdflatex'`` already did (due
  to ``Courier`` character width).  You may need to adjust this via
  :confval:`latex_elements` ``'fvset'`` key, in case of usage of some other
  OpenType fonts (refs: #5768)
* LaTeX: Greek letters in text are not escaped to math mode mark-up, and they
  will use the text font not the math font. The ``LGR`` font encoding must be
  added to the ``'fontenc'`` key of :confval:`latex_elements` for this to work
  (only if it is needed by the document, of course).
* LaTeX: setting the :confval:`language` to ``'en'`` triggered ``Sonny`` option
  of ``fncychap``, now it is ``Bjarne`` to match case of no language specified.
  (refs: #5772)
* #5770: doctest: Follow :confval:`highlight_language` on highlighting doctest
  block.  As a result, they are highlighted as python3 by default.
* The order of argument for ``HTMLTranslator``, ``HTML5Translator`` and
  ``ManualPageTranslator`` are changed
* LaTeX: hard-coded redefinitions of ``\l@section`` and ``\l@subsection``
  formerly done during loading of ``'manual'`` docclass get executed later, at
  time of ``\sphinxtableofcontents``.  This means that custom user definitions
  from LaTeX preamble now get overwritten.  Use ``\sphinxtableofcontentshook``
  to insert custom user definitions.  See :ref:`latex-macros`.
* quickstart: Simplify generated ``conf.py``
* #4148: quickstart: some questions are removed.  They are still able to specify
  via command line options
* websupport: unbundled from Sphinx core. Please use sphinxcontrib-websupport
* C++, the visibility of base classes is now always rendered as present in the
  input. That is, ``private`` is now shown, where it was ellided before.
* LaTeX: graphics inclusion of oversized images rescales to not exceed
  the text width and height, even if width and/or height option were used.
  (refs: #5956)
* epub: ``epub_title`` defaults to the :confval:`project` option
* #4550: All tables and figures without ``align`` option are displayed to center
* #4587: html: Output HTML5 by default

2.0.0b2

* texinfo: image files are copied into ``name-figure`` directory

Deprecated
----------

2.0.0b1

* Support for evaluating Python 2 syntax is deprecated. This includes
  configuration files which should be converted to Python 3.
* The arguments of ``EpubBuilder.build_mimetype()``,
  ``EpubBuilder.build_container()``, ``EpubBuilder.bulid_content()``,
  ``EpubBuilder.build_toc()`` and ``EpubBuilder.build_epub()``
* The arguments of ``Epub3Builder.build_navigation_doc()``
* The config variables

  - :confval:`!html_experimental_html5_writer`

* The ``encoding`` argument of ``autodoc.Documenter.get_doc()``,
  ``autodoc.DocstringSignatureMixin.get_doc()``,
  ``autodoc.DocstringSignatureMixin._find_signature()``, and
  ``autodoc.ClassDocumenter.get_doc()`` are deprecated.
* The ``importer`` argument of ``sphinx.ext.autodoc.importer._MockModule``
* The ``nodetype`` argument of ``sphinx.search.WordCollector.
  is_meta_keywords()``
* The ``suffix`` argument of ``env.doc2path()`` is deprecated.
* The string style ``base`` argument of ``env.doc2path()`` is deprecated.
* The fallback to allow omitting the ``filename`` argument from an overridden
  ``IndexBuilder.feed()`` method is deprecated.
* ``sphinx.addnodes.abbreviation``
* ``sphinx.application.Sphinx._setting_up_extension``
* ``sphinx.builders.epub3.Epub3Builder.validate_config_value()``
* ``sphinx.builders.html.SingleFileHTMLBuilder``
* ``sphinx.builders.htmlhelp.HTMLHelpBuilder.open_file()``
* ``sphinx.cmd.quickstart.term_decode()``
* ``sphinx.cmd.quickstart.TERM_ENCODING``
* ``sphinx.config.check_unicode()``
* ``sphinx.config.string_classes``
* ``sphinx.domains.cpp.DefinitionError.description``
* ``sphinx.domains.cpp.NoOldIdError.description``
* ``sphinx.domains.cpp.UnsupportedMultiCharacterCharLiteral.decoded``
* ``sphinx.ext.autodoc.importer._MockImporter``
* ``sphinx.ext.autosummary.Autosummary.warn()``
* ``sphinx.ext.autosummary.Autosummary.genopt``
* ``sphinx.ext.autosummary.Autosummary.warnings``
* ``sphinx.ext.autosummary.Autosummary.result``
* ``sphinx.ext.doctest.doctest_encode()``
* ``sphinx.io.SphinxBaseFileInput``
* ``sphinx.io.SphinxFileInput.supported``
* ``sphinx.io.SphinxRSTFileInput``
* ``sphinx.registry.SphinxComponentRegistry.add_source_input()``
* ``sphinx.roles.abbr_role()``
* ``sphinx.roles.emph_literal_role()``
* ``sphinx.roles.menusel_role()``
* ``sphinx.roles.index_role()``
* ``sphinx.roles.indexmarkup_role()``
* ``sphinx.testing.util.remove_unicode_literal()``
* ``sphinx.util.attrdict``
* ``sphinx.util.force_decode()``
* ``sphinx.util.get_matching_docs()``
* ``sphinx.util.inspect.Parameter``
* ``sphinx.util.jsonimpl``
* ``sphinx.util.osutil.EEXIST``
* ``sphinx.util.osutil.EINVAL``
* ``sphinx.util.osutil.ENOENT``
* ``sphinx.util.osutil.EPIPE``
* ``sphinx.util.osutil.walk()``
* ``sphinx.util.PeekableIterator``
* ``sphinx.util.pycompat.NoneType``
* ``sphinx.util.pycompat.TextIOWrapper``
* ``sphinx.util.pycompat.UnicodeMixin``
* ``sphinx.util.pycompat.htmlescape``
* ``sphinx.util.pycompat.indent``
* ``sphinx.util.pycompat.sys_encoding``
* ``sphinx.util.pycompat.terminal_safe()``
* ``sphinx.util.pycompat.u``
* ``sphinx.writers.latex.ExtBabel``
* ``sphinx.writers.latex.LaTeXTranslator._make_visit_admonition()``
* ``sphinx.writers.latex.LaTeXTranslator.babel_defmacro()``
* ``sphinx.writers.latex.LaTeXTranslator.collect_footnotes()``
* ``sphinx.writers.latex.LaTeXTranslator.generate_numfig_format()``
* ``sphinx.writers.texinfo.TexinfoTranslator._make_visit_admonition()``
* ``sphinx.writers.text.TextTranslator._make_depart_admonition()``
* template variables for LaTeX template

  - ``logo``
  - ``numfig_format``
  - ``pageautorefname``
  - ``translatablestrings``

For more details, see :ref:`deprecation APIs list <dev-deprecated-apis>`.

Features added
--------------

2.0.0b1

* #1618: The search results preview of generated HTML documentation is
  reader-friendlier: instead of showing the snippets as raw reStructuredText
  markup, Sphinx now renders the corresponding HTML.  This means the Sphinx
  extension `Sphinx: pretty search results`__ is no longer necessary.  Note that
  changes to the search function of your custom or 3rd-party HTML template might
  overwrite this improvement.

  __ https://github.com/sphinx-contrib/sphinx-pretty-searchresults

* #4182: autodoc: Support :confval:`suppress_warnings`
* #5533: autodoc: :confval:`autodoc_default_options` supports ``member-order``
* #5394: autodoc: Display readable names in type annotations for mocked objects
* #5459: autodoc: :confval:`autodoc_default_options` accepts ``True`` as a value
* #1148: autodoc: Add :rst:dir:`autodecorator` directive for decorators
* #5635: autosummary: Add :confval:`autosummary_mock_imports` to mock external
  libraries on importing targets
* #4018: htmlhelp: Add :confval:`htmlhelp_file_suffix` and
  :confval:`htmlhelp_link_suffix`
* #5559: text: Support complex tables (colspan and rowspan)
* LaTeX: support rendering (not in math, yet) of Greek and Cyrillic Unicode
  letters in non-Cyrillic document even with ``'pdflatex'`` as
  :confval:`latex_engine` (refs: #5645)
* #5660: The ``versionadded``, ``versionchanged`` and ``deprecated`` directives
  are now generated with their own specific CSS classes
  (``added``, ``changed`` and ``deprecated``, respectively) in addition to the
  generic ``versionmodified`` class.
* #5841: apidoc: Add --extensions option to sphinx-apidoc
* #4981: C++, added an alias directive for inserting lists of declarations,
  that references existing declarations (e.g., for making a synopsis).
* C++: add ``cpp:struct`` to complement ``cpp:class``.
* #1341: the HTML search considers words that contain a search term of length
  three or longer a match.
* #4611: epub: Show warning for duplicated ToC entries
* #1851: Allow to omit an argument for :rst:dir:`code-block` directive.  If
  omitted, it follows :rst:dir:`highlight` or :confval:`highlight_language`
* #4587: html: Add :confval:`!html4_writer` to use old HTML4 writer
* #6016: HTML search: A placeholder for the search summary prevents search
  result links from changing their position when the search terminates.  This
  makes navigating search results easier.
* #5196: linkcheck also checks remote images exist
* #5924: githubpages: create CNAME file for custom domains when
  :confval:`html_baseurl` set
* #4261: autosectionlabel: restrict the labeled sections by new config value;
  :confval:`autosectionlabel_maxdepth`


Bugs fixed
----------

2.0.0b1

* #1682: LaTeX: writer should not translate Greek unicode, but use textgreek
  package
* #5247: LaTeX: PDF does not build with default font config for Russian
  language and ``'xelatex'`` or ``'lualatex'`` as :confval:`latex_engine`
  (refs: #5251)
* #5248: LaTeX: Greek letters in section titles disappear from PDF bookmarks
* #5249: LaTeX: Unicode Greek letters in math directive break PDF build
  (fix requires extra set-up, see :confval:`latex_elements` ``'textgreek'`` key
  and/or :confval:`latex_engine` setting)
* #5772: LaTeX: should the Bjarne style of fncychap be used for English also
  if passed as language option?
* #5179: LaTeX: (lualatex only) escaping of ``>`` by ``\textgreater{}`` is not
  enough as ``\textgreater{}\textgreater{}`` applies TeX-ligature
* LaTeX: project name is not escaped if :confval:`latex_documents` omitted
* LaTeX: authors are not shown if :confval:`latex_documents` omitted
* HTML: Invalid HTML5 file is generated for a glossary having multiple terms for
  one description (refs: #4611)
* QtHelp: OS dependent path separator is used in .qhp file
* HTML search: search always returns nothing when multiple search terms are
  used and one term is shorter than three characters

2.0.0b2

* #6096: html: Anchor links are not added to figures
* #3620: html: Defer searchindex.js rather than loading it via ajax
* #6113: html: Table cells and list items have large margins
* #5508: ``linenothreshold`` option for ``highlight`` directive was ignored
* texinfo: ``make install-info`` causes syntax error
* texinfo: ``make install-info`` fails on macOS
* #3079: texinfo: image files are not copied on ``make install-info``
* #5391: A cross reference in heading is rendered as literal
* #5946: C++, fix ``cpp:alias`` problems in LaTeX (and singlehtml)
* #6147: classes attribute of ``citation_reference`` node is lost
* AssertionError is raised when custom ``citation_reference`` node having
  classes attribute refers missing citation (refs: #6147)
* #2155: Support ``code`` directive
* C++, fix parsing of braced initializers.
* #6172: AttributeError is raised for old styled index nodes
* #4872: inheritance_diagram: correctly describe behavior of ``parts`` option in
  docs, allow negative values.
* #6178: i18n: Captions missing in translations for hidden TOCs

2.0.0 final

* #6196: py domain: unexpected prefix is generated

Testing
-------

2.0.0b1

* Stop to use ``SPHINX_TEST_TEMPDIR`` envvar

2.0.0b2

* Add a helper function: ``sphinx.testing.restructuredtext.parse()``

Release 1.8.6 (released Nov 18, 2021)
=====================================

Dependencies
------------

* #9807: Restrict Docutils to 0.17.x or older

Release 1.8.5 (released Mar 10, 2019)
=====================================

Bugs fixed
----------

* LaTeX: Remove extraneous space after author names on PDF title page (refs:
  #6004)
* #6026: LaTeX: A cross reference to definition list does not work
* #6046: LaTeX: ``TypeError`` is raised when invalid latex_elements given
* #6067: LaTeX: images having a target are concatenated to next line
* #6067: LaTeX: images having a target are not aligned even if specified
* #6149: LaTeX: ``:index:`` role in titles causes ``Use of \@icentercr doesn't
  match its definition`` error on latexpdf build
* #6019: imgconverter: Including multipage PDF fails
* #6047: autodoc: ``autofunction`` emits a warning for method objects
* #6028: graphviz: Ensure the graphviz filenames are reproducible
* #6068: doctest: ``skipif`` option may remove the code block from documentation
* #6136: ``:name:`` option for ``math`` directive causes a crash
* #6139: intersphinx: ValueError on failure reporting
* #6135: changes: Fix UnboundLocalError when any module found
* #3859: manpage: code-block captions are not displayed correctly

Release 1.8.4 (released Feb 03, 2019)
=====================================

Bugs fixed
----------

* #3707: latex: no bold checkmark (✔) available.
* #5605: with the documentation language set to Chinese, English words could not
  be searched.
* #5889: LaTeX: user ``numfig_format`` is stripped of spaces and may cause
  build failure
* C++, fix hyperlinks for declarations involving east cv-qualifiers.
* #5755: C++, fix duplicate declaration error on function templates with
  constraints in the return type.
* C++, parse unary right fold expressions and binary fold expressions.
* pycode could not handle egg files on windows
* #5928: KeyError: 'DOCUTILSCONFIG' when running build
* #5936: LaTeX: PDF build broken by inclusion of image taller than page height
  in an admonition
* #5231: "make html" does not read and build "po" files in "locale" dir
* #5954: ``:scale:`` image option may break PDF build if image in an admonition
* #5966: mathjax has not been loaded on incremental build
* #5960: LaTeX: modified PDF layout since September 2018 TeXLive update of
  :file:`parskip.sty`
* #5948: LaTeX: duplicated labels are generated for sections
* #5958: versionadded directive causes crash with Python 3.5.0
* #5995: autodoc: autodoc_mock_imports conflict with metaclass on Python 3.7
* #5871: texinfo: a section title ``.`` is not allowed

Release 1.8.3 (released Dec 26, 2018)
=====================================

Features added
--------------

* LaTeX: it is possible to insert custom material to appear on back of title
  page, see discussion of ``'maketitle'`` key of :confval:`latex_elements`
  (``'manual'`` docclass only)

Bugs fixed
----------

* #5725: mathjax: Use CDN URL for "latest" version by default
* #5460: html search does not work with some 3rd party themes
* #5520: LaTeX, caption package incompatibility since Sphinx 1.6
* #5614: autodoc: incremental build is broken when builtin modules are imported
* #5627: qthelp: index.html missing in QtHelp
* #5659: linkcheck: crashes for a hyperlink containing multibyte character
* #5754: DOC: Fix some mistakes in :doc:`/latex`
* #5810: LaTeX: sphinxVerbatim requires explicit "hllines" set-up since 1.6.6
  (refs: #1238)
* #5636: C++, fix parsing of floating point literals.
* #5496 (again): C++, fix assertion in partial builds with duplicates.
* #5724: quickstart: sphinx-quickstart fails when $LC_ALL is empty
* #1956: Default conf.py is not PEP8-compliant
* #5849: LaTeX: document class ``\maketitle`` is overwritten with no
  possibility to use original meaning in place of Sphinx custom one
* #5834: apidoc: wrong help for ``--tocfile``
* #5800: todo: crashed if todo is defined in TextElement
* #5846: htmlhelp: convert hex escaping to decimal escaping in .hhc/.hhk files
* htmlhelp: broken .hhk file generated when title contains a double quote

Release 1.8.2 (released Nov 11, 2018)
=====================================

Incompatible changes
--------------------

* #5497: Do not include MathJax.js and jsmath.js unless it is really needed

Features added
--------------

* #5471: Show appropriate deprecation warnings

Bugs fixed
----------

* #5490: latex: enumerated list causes a crash with recommonmark
* #5492: sphinx-build fails to build docs w/ Python < 3.5.2
* #3704: latex: wrong ``\label`` positioning for figures with a legend
* #5496: C++, fix assertion when a symbol is declared more than twice.
* #5493: gettext: crashed with broken template
* #5495: csv-table directive with file option in included file is broken (refs:
  #4821)
* #5498: autodoc: unable to find type hints for a ``functools.partial``
* #5480: autodoc: unable to find type hints for unresolvable Forward references
* #5419: incompatible math_block node has been generated
* #5548: Fix ensuredir() in case of pre-existing file
* #5549: graphviz Correctly deal with non-existing static dir
* #3002: i18n: multiple footnote_references referring same footnote cause
  duplicated node_ids
* #5563: latex: footnote_references generated by extension causes a LaTeX
  builder crash
* #5561: make all-pdf fails with old xindy version
* #5557: quickstart: --no-batchfile isn't honored
* #3080: texinfo: multiline rubrics are broken
* #3080: texinfo: multiline citations are broken

Release 1.8.1 (released Sep 22, 2018)
=====================================

Incompatible changes
--------------------

* LaTeX ``\pagestyle`` commands have been moved to the LaTeX template. No
  changes in PDF, except possibly if ``\sphinxtableofcontents``, which
  contained them, had been customized in :file:`conf.py`. (refs: #5455)

Bugs fixed
----------

* #5418: Incorrect default path for sphinx-build -d/doctrees files
* #5421: autodoc emits deprecation warning for :confval:`autodoc_default_flags`
* #5422: lambda object causes PicklingError on storing environment
* #5417: Sphinx fails to build with syntax error in Python 2.7.5
* #4911: add latexpdf to make.bat for non make-mode
* #5436: Autodoc does not work with enum subclasses with properties/methods
* #5437: autodoc: crashed on modules importing eggs
* #5433: latex: ImportError: cannot import name 'DEFAULT_SETTINGS'
* #5431: autodoc: ``autofunction`` emits a warning for callable objects
* #5457: Fix TypeError in error message when override is prohibited
* #5453: PDF builds of 'howto' documents have no page numbers
* #5463: mathbase: math_role and MathDirective was disappeared in 1.8.0
* #5454: latex: Index has disappeared from PDF for Japanese documents
* #5432: py domain: ``:type:`` field can't process ``:term:`` references
* #5426: py domain: TypeError has been raised for class attribute

Release 1.8.0 (released Sep 13, 2018)
=====================================

Dependencies
------------

1.8.0b1

* LaTeX: :confval:`latex_use_xindy`, if ``True`` (default for
  ``xelatex/lualatex``), instructs ``make latexpdf`` to use :program:`xindy`
  for general index.  Make sure your LaTeX distribution includes it.
  (refs: #5134)
* LaTeX: ``latexmk`` is required for ``make latexpdf`` on Windows

Incompatible changes
--------------------

1.8.0b2

* #5282: html theme: refer ``pygments_style`` settings of HTML themes
  preferentially
* The URL of download files are changed
* #5127: quickstart: ``Makefile`` and ``make.bat`` are not overwritten if exists

1.8.0b1

* #5156: the :py:mod:`sphinx.ext.graphviz` extension runs ``dot`` in the
  directory of the document being built instead of in the root directory of
  the documentation.
* #4460: extensions which stores any data to environment should return the
  version of its env data structure as metadata.  In detail, please see
  :ref:`ext-metadata`.
* Sphinx expects source parser modules to have supported file formats as
  ``Parser.supported`` attribute
* The default value of :confval:`epub_author` and :confval:`epub_publisher` are
  changed from ``'unknown'`` to the value of :confval:`author`.  This is same as
  a ``conf.py`` file sphinx-build generates.
* The ``gettext_compact`` attribute is removed from ``document.settings``
  object.  Please use ``config.gettext_compact`` instead.
* The processing order on reading phase is changed.  smart_quotes, sphinx
  domains, :event:`doctree-read` event and versioning doctrees are invoked
  earlier than so far. For more details, please read a description of
  :py:meth:`.Sphinx.add_transform()`
* #4827: All ``substitution_definition`` nodes are removed from doctree on
  reading phase
* ``docutils.conf`` in ``$HOME`` or ``/etc`` directories are ignored.  Only
  ``docutils.conf`` from confdir is obeyed.
* #789: ``:samp:`` role supports to escape curly braces with backslash
* #4811: The files under :confval:`html_static_path` are excluded from source
  files.
* latex: Use ``\sphinxcite`` for citation references instead ``\hyperref``
* The config value :confval:`!viewcode_import` is renamed to
  :confval:`viewcode_follow_imported_members` (refs: #4035)
* #1857: latex: :confval:`latex_show_pagerefs` does not add pagerefs for
  citations
* #4648: latex: Now "rubric" elements are rendered as unnumbered section title
* #4983: html: The anchor for productionlist tokens has been changed
* Modifying a template variable ``script_files`` in templates is allowed now.
  Please use ``app.add_js_file()`` instead.
* #5072: Save environment object also with only new documents
* #5035: qthelp builder allows dashes in :confval:`qthelp_namespace`
* LaTeX: with lualatex or xelatex use by default :program:`xindy` as
  UTF-8 able replacement of :program:`makeindex` (refs: #5134).  After
  upgrading Sphinx, please clean latex build repertory of existing project
  before new build.
* #5163: html: hlist items are now aligned to top
* ``highlightlang`` directive is processed on resolving phase
* #4000: LaTeX: template changed.  Following elements moved to it:

  - ``\begin{document}``
  - ``shorthandoff`` variable
  - ``maketitle`` variable
  - ``tableofcontents`` variable

Deprecated
----------

1.8.0b2

* ``sphinx.io.SphinxI18nReader.set_lineno_for_reporter()`` is deprecated
* ``sphinx.io.SphinxI18nReader.line`` is deprecated
* ``sphinx.util.i18n.find_catalog_source_file()`` has changed; the
  *gettext_compact* argument has been deprecated
* #5403: ``sphinx.util.images.guess_mimetype()`` has changed; the *content*
  argument has been deprecated

1.8.0b1

* :confval:`!source_parsers` is deprecated
* :confval:`autodoc_default_flags` is deprecated
* quickstart: ``--epub`` option becomes default, so it is deprecated
* Drop function based directive support.  For now, Sphinx only supports class
  based directives (see :class:`~docutils.parsers.rst.Directive`)
* ``sphinx.util.docutils.directive_helper()`` is deprecated
* ``sphinx.cmdline`` is deprecated
* ``sphinx.make_mode`` is deprecated
* ``sphinx.locale.l_()`` is deprecated
* #2157: helper function ``warn()`` for HTML themes is deprecated
* ``app.override_domain()`` is deprecated
* ``app.add_stylesheet()`` is deprecated
* ``app.add_javascript()`` is deprecated
* ``app.import_object()`` is deprecated
* ``app.add_source_parser()`` has changed;  the *suffix* argument has been
  deprecated
* ``sphinx.versioning.prepare()`` is deprecated
* ``Config.__init__()`` has changed;  the *dirname*, *filename* and *tags*
  argument has been deprecated
* ``Config.check_types()`` is deprecated
* ``Config.check_unicode()`` is deprecated
* ``sphinx.application.CONFIG_FILENAME`` is deprecated
* ``highlightlang`` directive is deprecated
* ``BuildEnvironment.load()`` is deprecated
* ``BuildEnvironment.loads()`` is deprecated
* ``BuildEnvironment.frompickle()`` is deprecated
* ``env.read_doc()`` is deprecated
* ``env.update()`` is deprecated
* ``env._read_serial()`` is deprecated
* ``env._read_parallel()`` is deprecated
* ``env.write_doctree()`` is deprecated
* ``env._nitpick_ignore`` is deprecated
* ``env.versionchanges`` is deprecated
* ``env.dump()`` is deprecated
* ``env.dumps()`` is deprecated
* ``env.topickle()`` is deprecated
* ``env.note_versionchange()`` is deprecated
* ``sphinx.writers.latex.Table.caption_footnotetexts`` is deprecated
* ``sphinx.writers.latex.Table.header_footnotetexts`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.footnotestack`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.in_container_literal_block`` is
  deprecated
* ``sphinx.writers.latex.LaTeXTranslator.next_section_ids`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.next_hyperlink_ids`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.restrict_footnote()`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.unrestrict_footnote()`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.push_hyperlink_ids()`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.pop_hyperlink_ids()`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.check_latex_elements()`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.bibitems`` is deprecated
* ``sphinx.writers.latex.LaTeXTranslator.hlsettingstack`` is deprecated
* ``sphinx.writers.latex.ExtBabel.get_shorthandoff()`` is deprecated
* ``sphinx.writers.html.HTMLTranslator.highlightlang`` is deprecated
* ``sphinx.writers.html.HTMLTranslator.highlightlang_base`` is deprecated
* ``sphinx.writers.html.HTMLTranslator.highlightlangopts`` is deprecated
* ``sphinx.writers.html.HTMLTranslator.highlightlinenothreshold`` is deprecated
* ``sphinx.writers.html5.HTMLTranslator.highlightlang`` is deprecated
* ``sphinx.writers.html5.HTMLTranslator.highlightlang_base`` is deprecated
* ``sphinx.writers.html5.HTMLTranslator.highlightlangopts`` is deprecated
* ``sphinx.writers.html5.HTMLTranslator.highlightlinenothreshold`` is deprecated
* ``sphinx.ext.mathbase`` extension is deprecated
* ``sphinx.ext.mathbase.math`` node is deprecated
* ``sphinx.ext.mathbase.displaymath`` node is deprecated
* ``sphinx.ext.mathbase.eqref`` node is deprecated
* ``sphinx.ext.mathbase.is_in_section_title()`` is deprecated
* ``sphinx.ext.mathbase.MathDomain`` is deprecated
* ``sphinx.ext.mathbase.MathDirective`` is deprecated
* ``sphinx.ext.mathbase.math_role`` is deprecated
* ``sphinx.ext.mathbase.setup_math()`` is deprecated
* ``sphinx.directives.other.VersionChanges`` is deprecated
* ``sphinx.highlighting.PygmentsBridge.unhighlight()`` is deprecated
* ``sphinx.ext.mathbase.get_node_equation_number()`` is deprecated
* ``sphinx.ext.mathbase.wrap_displaymath()`` is deprecated
* The ``trim_doctest_flags`` argument of ``sphinx.highlighting.PygmentsBridge``
  is deprecated

For more details, see :ref:`deprecation APIs list <dev-deprecated-apis>`.

Features added
--------------

1.8.0b2

* #5388: Ensure frozen object descriptions are reproducible
* #5362: apidoc: Add ``--tocfile`` option to change the filename of ToC

1.8.0b1

* Add :event:`config-inited` event
* Add ``sphinx.config.Any`` to represent the config value accepts any type of
  value
* :confval:`source_suffix` allows a mapping fileext to file types
* Add :confval:`author` as a configuration value
* #2852: imgconverter: Support to convert GIF to PNG
* ``sphinx-build`` command supports i18n console output
* Add ``app.add_message_catalog()`` and ``sphinx.locale.get_translations()`` to
  support translation for 3rd party extensions
* helper function ``warning()`` for HTML themes is added
* Add ``Domain.enumerable_nodes`` to manage own enumerable nodes for domains
  (experimental)
* Add a new keyword argument ``override`` to Application APIs
* LaTeX: new key ``'fvset'`` for :confval:`latex_elements`. For
  XeLaTeX/LuaLaTeX its default sets ``fanvyvrb`` to use normal, not small,
  fontsize in code-blocks (refs: #4793)
* Add :confval:`html_css_files` and :confval:`epub_css_files` for adding CSS
  files from configuration
* Add :confval:`html_js_files` for adding JS files from configuration
* #4834: Ensure set object descriptions are reproducible.
* #4828: Allow to override :confval:`numfig_format` partially.  Full definition
  is not needed.
* Improve warning messages during including (refs: #4818)
* LaTeX: separate customizability of :rst:role:`guilabel` and
  :rst:role:`menuselection` (refs: #4830)
* Add ``Config.read()`` classmethod to create a new config object from
  configuration file
* #4866: Wrap graphviz diagrams in ``<div>`` tag
* viewcode: Add :event:`viewcode-find-source` and
  :event:`viewcode-follow-imported` to load source code without loading
* #4785: napoleon: Add strings to translation file for localisation
* #4927: Display a warning when invalid values are passed to linenothreshold
  option of highlight directive
* C++:

  - Add a ``cpp:texpr`` role as a sibling to ``cpp:expr``.
  - Add support for unions.
  - #3593, #2683: add support for anonymous entities using names staring with
    ``@``.
  - #5147: add support for (most) character literals.
  - Cross-referencing entities inside primary templates is supported,
    and now properly documented.
  - #1552: add new cross-referencing format for ``cpp:any`` and ``cpp:func``
    roles, for referencing specific function overloads.

* #3606: MathJax should be loaded with async attribute
* html: Output ``canonical_url`` metadata if :confval:`html_baseurl` set (refs:
  #4193)
* #5029: autosummary: expose ``inherited_members`` to template
* #3784: mathjax: Add :confval:`mathjax_options` to give options to script tag
  for mathjax
* #726, #969: mathjax: Add :confval:`mathjax_config` to give in-line
  configurations for mathjax
* #4362: latex: Don't overwrite .tex file if document not changed
* #1431: latex: Add alphanumeric enumerated list support
* Add :confval:`latex_use_xindy` for UTF-8 savvy indexing, defaults to ``True``
  if :confval:`latex_engine` is ``'xelatex'`` or ``'lualatex'``. (refs: #5134,
  #5192, #5212)
* #4976: ``SphinxLoggerAdapter.info()`` now supports ``location`` parameter
* #5122: setuptools: support nitpicky option
* #2820: autoclass directive supports nested class
* Add ``app.add_html_math_renderer()`` to register a math renderer for HTML
* Apply :confval:`trim_doctest_flags` to all builders (cf. text, manpages)
* #5140: linkcheck: Add better Accept header to HTTP client
* #4614: sphinx-build: Add ``--keep-going`` option to show all warnings
* Add :rst:role:`math:numref` role to refer equations (Same as :rst:role:`eq`)
* quickstart: epub builder is enabled by default
* #5246: Add :confval:`singlehtml_sidebars` to configure sidebars for singlehtml
  builder
* #5273: doctest: Skip doctest conditionally
* #5306: autodoc: emit a warning for invalid typehints
* #4075, #5215: autodoc: Add :confval:`autodoc_default_options` which accepts
  option values as dict

Bugs fixed
----------

1.8.0b2

* html: search box overrides to other elements if scrolled
* i18n: warnings for translation catalogs have wrong line numbers (refs: #5321)
* #5325: latex: cross references has been broken by multiply labeled objects
* C++, fixes for symbol addition and lookup. Lookup should no longer break
  in partial builds. See also #5337.
* #5348: download reference to remote file is not displayed
* #5282: html theme: ``pygments_style`` of theme was overridden by ``conf.py``
  by default
* #4379: toctree shows confusing warning when document is excluded
* #2401: autodoc: ``:members:`` causes ``:special-members:`` not to be shown
* autodoc: ImportError is replaced by AttributeError for deeper module
* #2720, #4034: Incorrect links with ``:download:``, duplicate names, and
  parallel builds
* #5290: autodoc: failed to analyze source code in egg package
* #5399: Sphinx crashes if unknown po file exists

1.8.0b1

* i18n: message catalogs were reset on each initialization
* #4850: latex: footnote inside footnote was not rendered
* #4945: i18n: fix lang_COUNTRY not fallback correctly for IndexBuilder. Thanks
  to Shengjing Zhu.
* #4983: productionlist directive generates invalid IDs for the tokens
* #5132: lualatex: PDF build fails if indexed word starts with Unicode character
* #5133: latex: index headings "Symbols" and "Numbers" not internationalized
* #5114: sphinx-build: Handle errors on scanning documents
* epub: spine has been broken when "self" is listed on toctree (refs: #4611)
* #344: autosummary does not understand docstring of module level attributes
* #5191: C++, prevent nested declarations in functions to avoid lookup problems.
* #5126: C++, add missing isPack method for certain template parameter types.
* #5187: C++, parse attributes on declarators as well.
* C++, parse delete expressions and basic new expressions as well.
* #5002: graphviz: SVGs do not adapt to the column width

Features removed
----------------

1.8.0b1

* ``sphinx.ext.pngmath`` extension

Documentation
-------------

1.8.0b1

* #5083: Fix wrong make.bat option for internationalization.
* #5115: napoleon: add admonitions added by #4613 to the docs.

Release 1.7.9 (released Sep 05, 2018)
=====================================

Features added
--------------

* #5359: Make generated texinfo files reproducible by sorting the anchors

Bugs fixed
----------

* #5361: crashed on incremental build if document uses include directive

Release 1.7.8 (released Aug 29, 2018)
=====================================

Incompatible changes
--------------------

* The type of ``env.included`` has been changed to dict of set

Bugs fixed
----------

* #5320: intersphinx: crashed if invalid url given
* #5326: manpage: crashed when invalid docname is specified as ``man_pages``
* #5322: autodoc: ``Any`` typehint causes formatting error
* #5327: "document isn't included in any toctree" warning on rebuild with
  generated files
* #5335: quickstart: escape sequence has been displayed with MacPorts' python

Release 1.7.7 (released Aug 19, 2018)
=====================================

Bugs fixed
----------

* #5198: document not in toctree warning when including files only for parallel
  builds
* LaTeX: reduce "Token not allowed in a PDF string" hyperref warnings in latex
  console output (refs: #5236)
* LaTeX: suppress "remreset Warning: The remreset package is obsolete" in latex
  console output with recent LaTeX (refs: #5237)
* #5234: PDF output: usage of PAPER environment variable is broken since Sphinx
  1.5
* LaTeX: fix the :confval:`latex_engine` documentation regarding Latin Modern
  font with XeLaTeX/LuaLateX (refs: #5251)
* #5280: autodoc: Fix wrong type annotations for complex typing
* autodoc: Optional types are wrongly rendered
* #5291: autodoc crashed by ForwardRef types
* #5211: autodoc: No docs generated for functools.partial functions
* #5306: autodoc: ``getargspec()`` raises NameError for invalid typehints
* #5298: imgmath: math_number_all causes equations to have two numbers in html
* #5294: sphinx-quickstart blank prompts in PowerShell

Release 1.7.6 (released Jul 17, 2018)
=====================================

Bugs fixed
----------

* #5037: LaTeX ``\sphinxupquote{}`` breaks in Russian
* sphinx.testing uses deprecated pytest API; ``Node.get_marker(name)``
* #5016: crashed when recommonmark.AutoStrictify is enabled
* #5022: latex: crashed with Docutils package provided by Debian/Ubuntu
* #5009: latex: a label for table is vanished if table does not have a caption
* #5048: crashed with numbered toctree
* #2410: C, render empty argument lists for macros.
* C++, fix lookup of full template specializations with no template arguments.
* #4667: C++, fix assertion on missing references in global scope when using
  intersphinx. Thanks to Alan M. Carroll.
* #5019: autodoc: crashed by Form Feed Character
* #5032: autodoc: loses the first staticmethod parameter for old styled classes
* #5036: quickstart: Typing Ctrl-U clears the whole of line
* #5066: html: "relations" sidebar is not shown by default
* #5091: latex: curly braces in index entries are not handled correctly
* #5070: epub: Wrong internal href fragment links
* #5104: apidoc: Interface of ``sphinx.apidoc:main()`` has changed
* #4272: PDF builds of French projects have issues with XeTeX
* #5076: napoleon raises RuntimeError with python 3.7
* #5125: sphinx-build: Interface of ``sphinx:main()`` has changed
* sphinx-build: ``sphinx.cmd.build.main()`` refers ``sys.argv`` instead of given
  argument
* #5146: autosummary: warning is emitted when the first line of docstring ends
  with literal notation
* autosummary: warnings of autosummary indicates wrong location (refs: #5146)
* #5143: autodoc: crashed on inspecting dict like object which does not support
  sorting
* #5139: autodoc: Enum argument missing if it shares value with another
* #4946: py domain: rtype field could not handle "``None``" as a type
* #5176: LaTeX: indexing of terms containing ``@``, ``!``, or ``"`` fails
* #5161: html: crashes if copying static files are failed
* #5167: autodoc: Fix formatting type annotations for tuples with more than two
  arguments
* #3329: i18n: crashed by auto-symbol footnote references
* #5158: autosummary: module summary has been broken when it starts with heading

Release 1.7.5 (released May 29, 2018)
=====================================

Bugs fixed
----------

* #4924: html search: Upper characters problem in any other languages
* #4932: apidoc: some subpackage is ignored if sibling subpackage contains a
  module starting with underscore
* #4863, #4938, #4939: i18n doesn't handle correctly node.title as used for
  contents, topic, admonition, table and section.
* #4913: i18n: literal blocks in bullet list are not translated
* #4962: C++, raised TypeError on duplicate declaration.
* #4825: C++, properly parse expr roles and give better error messages when
  (escaped) line breaks are present.
* C++, properly use ``desc_addname`` nodes for prefixes of names.
* C++, parse pack expansions in function calls.
* #4915, #4916: links on search page are broken when using dirhtml builder
* #4969: autodoc: constructor method should not have return annotation
* latex: deeply nested enumerated list which is beginning with non-1 causes
  LaTeX engine crashed
* #4978: latex: shorthandoff is not set up for Brazil locale
* #4928: i18n: Ignore dot-directories like .git/ in LC_MESSAGES/
* #4946: py domain: type field could not handle "``None``" as a type
* #4979: latex: Incorrect escaping of curly braces in index entries
* #4956: autodoc: Failed to extract document from a subclass of the class on
  mocked module
* #4973: latex: glossary directive adds whitespace to each item
* #4980: latex: Explicit labels on code blocks are duplicated
* #4919: node.asdom() crashes if toctree has :numbered: option
* #4914: autodoc: Parsing error when using dataclasses without default values
* #4931: autodoc: crashed when handler for autodoc-skip-member raises an error
* #4931: autodoc: crashed when subclass of mocked class are processed by
  napoleon module
* #5007: sphinx-build crashes when error log contains a "%" character

Release 1.7.4 (released Apr 25, 2018)
=====================================

Bugs fixed
----------

* #4885, #4887: domains: Crashed with duplicated objects
* #4889: latex: sphinx.writers.latex causes recursive import

Release 1.7.3 (released Apr 23, 2018)
=====================================

Bugs fixed
----------

* #4769: autodoc loses the first staticmethod parameter
* #4790: autosummary: too wide two column tables in PDF builds
* #4795: Latex customization via ``_templates/longtable.tex_t`` is broken
* #4789: imgconverter: confused by convert.exe of Windows
* #4783: On windows, Sphinx crashed when drives of srcdir and outdir are
  different
* #4812: autodoc ignores type annotated variables
* #4817: wrong URLs on warning messages
* #4784: latex: :confval:`latex_show_urls` assigns incorrect footnote numbers if
  hyperlinks exists inside substitutions
* #4837: latex with class memoir Error: Font command ``\sf`` is not supported
* #4803: latex: too slow in proportion to number of auto numbered footnotes
* #4838: htmlhelp: The entries in .hhp file is not ordered
* toctree directive tries to glob for URL having query_string
* #4871: html search: Upper characters problem in German
* #4717: latex: Compilation for German docs failed with LuaLaTeX and XeLaTeX
* #4459: duplicated labels detector does not work well in parallel build
* #4878: Crashed with extension which returns invalid metadata

Release 1.7.2 (released Mar 21, 2018)
=====================================

Incompatible changes
--------------------
* #4520: apidoc: folders with an empty __init__.py are no longer excluded from
  TOC

Bugs fixed
----------

* #4669: sphinx.build_main and sphinx.make_main throw NameError
* #4685: autosummary emits meaningless warnings
* autodoc: crashed when invalid options given
* pydomain: always strip parenthesis if empty (refs: #1042)
* #4689: autosummary: unexpectedly strips docstrings containing "i.e."
* #4701: viewcode: Misplaced ``<div>`` in viewcode html output
* #4444: Don't require numfig to use :numref: on sections
* #4727: Option clash for package textcomp
* #4725: Sphinx does not work with python 3.5.0 and 3.5.1
* #4716: Generation PDF file with TexLive on Windows, file not found error
* #4574: vertical space before equation in latex
* #4720: message when an image is mismatched for builder is not clear
* #4655, #4684: Incomplete localization strings in Polish and Chinese
* #2286: Sphinx crashes when error is happens in rendering HTML pages
* #4688: Error to download remote images having long URL
* #4754: sphinx/pycode/__init__.py raises AttributeError
* #1435: qthelp builder should htmlescape keywords
* epub: Fix docTitle elements of toc.ncx is not escaped
* #4520: apidoc: Subpackage not in toc (introduced in 1.6.6) now fixed
* #4767: html: search highlighting breaks mathjax equations

Release 1.7.1 (released Feb 23, 2018)
=====================================

Deprecated
----------

* #4623: ``sphinx.build_main()`` is deprecated.
* autosummary: The interface of ``sphinx.ext.autosummary.get_documenter()`` has
  been changed (Since 1.7.0)
* #4664: ``sphinx.ext.intersphinx.debug()`` is deprecated.

For more details, see :ref:`deprecation APIs list <dev-deprecated-apis>`.

Bugs fixed
----------

* #4608: epub: Invalid meta tag is generated
* #4260: autodoc: keyword only argument separator is not disappeared if it is
  appeared at top of the argument list
* #4622: epub: :confval:`epub_scheme` does not effect to content.opf
* #4627: graphviz: Fit graphviz images to page
* #4617: quickstart: PROJECT_DIR argument is required
* #4623: sphinx.build_main no longer exists in 1.7.0
* #4615: The argument of ``sphinx.build`` has been changed in 1.7.0
* autosummary: The interface of ``sphinx.ext.autosummary.get_documenter()`` has
  been changed
* #4630: Have order on msgids in sphinx.pot deterministic
* #4563: autosummary: Incorrect end of line punctuation detection
* #4577: Enumerated sublists with explicit start with wrong number
* #4641: A external link in TOC cannot contain "?" with ``:glob:`` option
* C++, add missing parsing of explicit casts and typeid in expression parsing.
* C++, add missing parsing of ``this`` in expression parsing.
* #4655: Fix incomplete localization strings in Polish
* #4653: Fix error reporting for parameterless ImportErrors
* #4664: Reading objects.inv fails again
* #4662: ``any`` refs with ``term`` targets crash when an ambiguity is
  encountered

Release 1.7.0 (released Feb 12, 2018)
=====================================

Dependencies
------------

1.7.0b1

* Add ``packaging`` package

Incompatible changes
--------------------

1.7.0b1

* #3668: The arguments has changed of main functions for each command
* #3893: Unknown html_theme_options throw warnings instead of errors
* #3927: Python parameter/variable types should match classes, not all objects
* #3962: sphinx-apidoc now recognizes given directory as an implicit namespace
  package when ``--implicit-namespaces`` option given, not subdirectories of
  given directory.
* #3929: apidoc: Move sphinx.apidoc to sphinx.ext.apidoc
* #4226: apidoc: Generate new style makefile (make-mode)
* #4274: sphinx-build returns 2 as an exit code on argument error
* #4389: output directory will be created after loading extensions
* autodoc does not generate warnings messages to the generated document even if
  :confval:`keep_warnings` is ``True``.  They are only emitted to stderr.
* shebang line is removed from generated conf.py
* #2557: autodoc: :confval:`autodoc_mock_imports` only mocks specified modules
  with their descendants.  It does not mock their ancestors.  If you want to
  mock them, please specify the name of ancestors explicitly.
* #3620: html theme: move DOCUMENTATION_OPTIONS to independent JavaScript file
  (refs: #4295)
* #4246: Limit width of text body for all themes. Configurable via theme
  options ``body_min_width`` and ``body_max_width``.
* #4771: apidoc: The ``exclude_patterns`` arguments are ignored if they are
  placed just after command line options

1.7.0b2

* #4467: html theme: Rename ``csss`` block to ``css``

Deprecated
----------

1.7.0b1

* using a string value for :confval:`html_sidebars` is deprecated and only list
  values will be accepted at 2.0.
* ``format_annotation()`` and ``formatargspec()`` is deprecated.  Please use
  ``sphinx.util.inspect.Signature`` instead.
* ``sphinx.ext.autodoc.AutodocReporter`` is replaced by ``sphinx.util.docutils.
  switch_source_input()`` and now deprecated.  It will be removed in Sphinx 2.0.
* ``sphinx.ext.autodoc.add_documenter()`` and ``AutoDirective._register`` is now
  deprecated.  Please use ``app.add_autodocumenter()`` instead.
* ``AutoDirective._special_attrgetters`` is now deprecated.  Please use
  ``app.add_autodoc_attrgetter()`` instead.

Features added
--------------

1.7.0b1

* C++, handle ``decltype(auto)``.
* #2406: C++, add proper parsing of expressions, including linking of
  identifiers.
* C++, add a ``cpp:expr`` role for inserting inline C++ expressions or types.
* C++, support explicit member instantiations with shorthand ``template`` prefix
* C++, make function parameters linkable, like template params.
* #3638: Allow to change a label of reference to equation using
  ``math_eqref_format``
* Now :confval:`suppress_warnings` accepts following configurations:

  - ``ref.python`` (ref: #3866)

* #3872: Add latex key to configure literal blocks caption position in PDF
  output (refs #3792, #1723)
* In case of missing docstring try to retrieve doc from base classes (ref:
  #3140)
* #4023: Clarify error message when any role has more than one target.
* #3973: epub: allow to override build date
* #3972: epub: Sort manifest entries by filename
* #4052: viewcode: Sort before highlighting module code
* #1448: qthelp: Add new config value; :confval:`qthelp_namespace`
* #4140: html themes: Make body tag inheritable
* #4168: improve zh search with jieba
* HTML themes can set up default sidebars through ``theme.conf``
* #3160: html: Use ``<kdb>`` to represent ``:kbd:`` role
* #4212: autosummary: catch all exceptions when importing modules
* #4166: Add :confval:`math_numfig` for equation numbering by section (refs:
  #3991, #4080). Thanks to Oliver Jahn.
* #4311: Let LaTeX obey :confval:`numfig_secnum_depth` for figures, tables, and
  code-blocks
* #947: autodoc now supports ignore-module-all to ignore a module's ``__all__``
* #4332: Let LaTeX obey :confval:`math_numfig` for equation numbering
* #4093: sphinx-build creates empty directories for unknown targets/builders
* Add ``top-classes`` option for the ``sphinx.ext.inheritance_diagram``
  extension to limit the scope of inheritance graphs.
* #4183: doctest: ``:pyversion:`` option also follows PEP-440 specification
* #4235: html: Add :confval:`manpages_url` to make manpage roles to hyperlinks
* #3570: autodoc: Do not display 'typing.' module for type hints
* #4354: sphinx-build now emits finish message.  Builders can modify it through
  ``Builder.epilog`` attribute
* #4245: html themes: Add ``language`` to javascript vars list
* #4079: html: Add ``notranslate`` class to each code-blocks, literals and maths
  to let Google Translate know they are not translatable
* #4137: doctest: doctest block is always highlighted as python console (pycon)
* #4137: doctest: testcode block is always highlighted as python
* #3998: text: Assign section numbers by default.  You can control it using
  :confval:`text_add_secnumbers` and :confval:`text_secnumber_suffix`

1.7.0b2

* #4271: sphinx-build supports an option called ``-j auto`` to adjust numbers of
  processes automatically.
* Napoleon: added option to specify custom section tags.


Features removed
----------------

1.7.0b1

* Configuration variables

  - :confval:`!html_use_smartypants`
  - :confval:`!latex_keep_old_macro_names`
  - latex_elements['footer']

* utility methods of ``sphinx.application.Sphinx`` class

  - buildername (property)
  - _display_chunk()
  - old_status_iterator()
  - status_iterator()
  - _directive_helper()

* utility methods of ``sphinx.environment.BuildEnvironment`` class

  - currmodule (property)
  - currclass (property)

* epub2 builder
* prefix and colorfunc parameter for warn()
* ``sphinx.util.compat`` module
* ``sphinx.util.nodes.process_only_nodes()``
* LaTeX environment ``notice``, use ``sphinxadmonition`` instead
* LaTeX ``\sphinxstylethead``, use ``\sphinxstyletheadfamily``
* C++, support of function concepts. Thanks to mickk-on-cpp.
* Not used and previously not documented LaTeX macros ``\shortversion``
  and ``\setshortversion``


Bugs fixed
----------

1.7.0b1

* #3882: Update the order of files for HTMLHelp and QTHelp
* #3962: sphinx-apidoc does not recognize implicit namespace packages correctly
* #4094: C++, allow empty template argument lists.
* C++, also hyperlink types in the name of declarations with qualified names.
* C++, do not add index entries for declarations inside concepts.
* C++, support the template disambiguator for dependent names.
* #4314: For PDF 'howto' documents, numbering of code-blocks differs from the
  one of figures and tables
* #4330: PDF 'howto' documents have an incoherent default LaTeX tocdepth counter
  setting
* #4198: autosummary emits multiple 'autodoc-process-docstring' event. Thanks
  to Joel Nothman.
* #4081: Warnings and errors colored the same when building
* latex: Do not display 'Release' label if :confval:`release` is not set

1.7.0b2

* #4415: autodoc classifies inherited classmethods as regular methods
* #4415: autodoc classifies inherited staticmethods as regular methods
* #4472: DOCUMENTATION_OPTIONS is not defined
* #4491: autodoc: prefer _MockImporter over other importers in sys.meta_path
* #4490: autodoc: type annotation is broken with python 3.7.0a4+
* utils package is no longer installed
* #3952: apidoc: module header is too escaped
* #4275: Formats accepted by sphinx.util.i18n.format_date are limited
* #4493: recommonmark raises AttributeError if AutoStructify enabled
* #4209: intersphinx: In link title, "v" should be optional if target has no
  version
* #4230: slowdown in writing pages with Sphinx 1.6
* #4522: epub: document is not rebuilt even if config changed

1.7.0b3

* #4019: inheritance_diagram AttributeError stopping make process
* #4531: autosummary: methods are not treated as attributes
* #4538: autodoc: ``sphinx.ext.autodoc.Options`` has been moved
* #4539: autodoc emits warnings for partialmethods
* #4223: doctest: failing tests reported in wrong file, at wrong line
* i18n: message catalogs are not compiled if specific filenames are given for
  ``sphinx-build`` as arguments (refs: #4560)
* #4027: sphinx.ext.autosectionlabel now expects labels to be the same as they
  are in the raw source; no smart quotes, nothig fancy.
* #4581: apidoc: Excluded modules still included


Testing
-------

1.7.0b1

* Add support for Docutils 0.14
* Add tests for the ``sphinx.ext.inheritance_diagram`` extension.
