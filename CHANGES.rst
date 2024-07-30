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
