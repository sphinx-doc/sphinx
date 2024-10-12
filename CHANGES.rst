Release 8.1.2 (in development)
==============================

Bugs fixed
----------


Release 8.1.1 (released Oct 11, 2024)
=====================================

Bugs fixed
----------

* #13006: Use the preferred https://www.cve.org/ URL for
  the :rst:role:`:cve: <cve>` role.
  Patch by Hugo van Kemenade.
* #13007: LaTeX: Improve resiliency when the required
  ``fontawesome`` or ``fontawesome5`` packages are not installed.
  Patch by Jean-François B.


Release 8.1.0 (released Oct 10, 2024)
=====================================

Dependencies
------------

* #12756: Add lower-bounds to the ``sphinxcontrib-*`` dependencies.
  Patch by Adam Turner.
* #12833: Update the LaTeX ``parskip`` package from 2001 to 2018.
  Patch by Jean-François B.

Incompatible changes
--------------------

* #12763: Remove unused internal class ``sphinx.util.Tee``.
  Patch by Adam Turner.
* #12822: LaTeX: for Unicode engines, the :ref:`fvset` default is changed to
  ``'\\fvset{fontsize=auto}'`` from ``'\\fvset{fontsize=\\small}'``.
  Code-blocks are unchanged as FreeMono is now loaded with ``Scale=0.9``.
  An adjustment to existing projects is needed only if they used a custom
  :ref:`fontpkg` configuration and did not set :ref:`fvset`.
  Patch by Jean-François B.
* #12875: Disable smartquotes for languages: ``zh_CN`` and ``zh_TW`` by default.
  Patch by A. Rafey Khan.

Deprecated
----------

* #12762: Deprecate ``sphinx.util.import_object``.
  Use :py:func:`importlib.import_module` instead.
  Patch by Adam Turner.
* #12766: Deprecate ``sphinx.util.FilenameUniqDict``
  and ``sphinx.util.DownloadFiles``.
  Patch by Adam Turner.

Features added
--------------

* #11328: Mention evaluation of templated content during production of static
  output files.
  Patch by James Addison.
* #12704: LaTeX: make :dudir:`contents <table-of-contents>`, :dudir:`topic`,
  and :dudir:`sidebar` directives separately customizable for PDF output.
  Patch by Jean-François B. and Bénédikt Tran.
* #12474: Support type-dependent search result highlighting via CSS.
  Patch by Tim Hoffmann.
* #12652: LaTeX: Add :confval:`math_numsep` support to latex builder.
  Patch by Thomas Fanning and Jean-François B.
* #12743: No longer exit on the first warning when
  :option:`--fail-on-warning <sphinx-build --fail-on-warning>` is used.
  Instead, exit with a non-zero status if any warnings were generated
  during the build.
  Patch by Adam Turner.
* #12743: Add :option:`sphinx-build --exception-on-warning`,
  to raise an exception when warnings are emitted during the build.
  Patch by Adam Turner and Jeremy Maitin-Shepard.
* #12907: Add :confval:`html_last_updated_use_utc` to allow using
  universal time (GMT/UTC) instead of local time for the date-time
  supplied to :confval:`html_last_updated_fmt`.
  Patch by Adam Turner.
* #12910: Copyright entries now support the ``'%Y'`` placeholder
  to substitute the current year.
  This is helpful for reducing the reliance on Python modules
  such as :py:mod:`time` or :py:mod:`datetime` in :file:`conf.py`.
  See :ref:`the docs <config-copyright>` for further detail.
  Patch by Adam Turner.
* #11781: Add roles for referencing CVEs (:rst:role:`:cve: <cve>`)
  and CWEs (:rst:role:`:cwe: <cwe>`).
  Patch by Hugo van Kemenade.
* #11809: Improve the formatting for RFC section anchors.
  Patch by Jakub Stasiak and Adam Turner.
* #12852: Support a :attr:`.Builder.supported_linkcode` attribute
  for builders to enable use of :mod:`sphinx.ext.linkcode`-generated
  references.
  Patch by James Knight.
* #12949: Print configuration options that differ from the pickled environment.
  This can be helpful in diagnosing the cause of a full rebuild.
  Patch by Adam Turner.

Bugs fixed
----------

* #12514: intersphinx: fix the meaning of a negative value for
  :confval:`intersphinx_cache_limit`.
  Patch by Shengyu Zhang.
* #12722: LaTeX: avoid TeX reporting ``Overfull \hbox`` from too long
  strings in a codeline when the problem has actually been solved thanks
  to :ref:`latexsphinxsetupforcewraps`.
  Patch by Jean-François B.
* #12730: The ``UnreferencedFootnotesDetector`` transform has been improved
  to more consistently detect unreferenced footnotes.
  Note, the priority of the transform has been changed from 200 to 622,
  so that it now runs after the docutils ``Footnotes`` resolution transform.
  Patch by Chris Sewell.
* #12778: LaTeX: let :ref:`'sphinxsetup' <latexsphinxsetup>`
  ``div.topic_box-shadow`` key if used with only one dimension set both
  x-offset and y-offset as per documentation.
  Patch by Jean-François B.
* #12587: Do not warn when potential ambiguity detected during Intersphinx
  resolution occurs due to duplicate targets that differ case-insensitively.
  Patch by James Addison.
* #12639: Fix singular and plural search results text.
  Patch by Hugo van Kemenade.
* #12645: Correctly support custom gettext output templates.
  Patch by Jeremy Bowman.
* #12717: LaTeX: let :option:`-q <sphinx-build -q>` (quiet) option for
  :program:`sphinx-build -M latexpdf` or :program:`make latexpdf` (``O=-q``)
  get passed to :program:`latexmk`.  Let :option:`-Q <sphinx-build -Q>`
  (silent) apply as well to the PDF build phase.
  Patch by Jean-François B.
* #12744: LaTeX: Classes injected by a custom interpreted text role now give
  rise to nested ``\DUrole``'s, rather than a single one with comma separated
  classes.
  Patch by Jean-François B.
* #12831: LaTeX: avoid large voids sometimes occurring at page bottoms.
  Patch by Jean-François B.
* #11970, #12551: singlehtml builder: make target URIs to be same-document
  references in the sense of :rfc:`RFC 3986, §4.4 <3986#section-4.4>`,
  e.g., ``index.html#foo`` becomes ``#foo``.
  (note: continuation of a partial fix added in Sphinx 7.3.0)
  Patch by James Addison (with reference to prior work by Eric Norige).
* #12735: Fix :pep:`695` generic classes LaTeX output formatting.
  Patch by Jean-François B. and Bénédikt Tran.
* #12782: intersphinx: fix double forward slashes when generating the inventory
  file URL (user-defined base URL of an intersphinx project are left untouched
  even if they end with double forward slashes).
  Patch by Bénédikt Tran.
* #12796: Enable parallel reading if requested,
  even if there are fewer than 6 documents.
  Patch by Matthias Geier.
* #12844: Restore support for ``:noindex:`` for the :rst:dir:`js:module`
  and :rst:dir:`py:module` directives.
  Patch by Stephen Finucane.
* #12916: Restore support for custom templates named with the legacy ``_t``
  suffix during ``apidoc`` RST rendering (regression in 7.4.0).
  Patch by James Addison.
* #12451: Only substitute copyright notice years with values from
  ``SOURCE_DATE_EPOCH`` for entries that match the current system clock year,
  and disallow substitution of future years.
  Patch by James Addison and Adam Turner.
* #12905: intersphinx: fix flipped use of :confval:`intersphinx_cache_limit`,
  which always kept the cache for positive values, and always refreshed it for
  negative ones.
  Patch by Nico Madysa.
* #12888: Add a warning when document is included in multiple toctrees
  and ensure deterministic resolution of global toctree in parallel builds
  by choosing the lexicographically greatest parent document.
  Patch by A. Rafey Khan
* #12995: Significantly improve performance when building the search index
  for Chinese languages.
  Patch by Adam Turner.
* #12767: :py:meth:`.Builder.write` is typed as ``final``, meaning that the
  :event:`write-started` event may be relied upon by extensions.
  A new :py:meth:`.Builder.write_documents` method has been added to
  control how documents are written.
  This is intended for builders that do not output a file for each document.
  Patch by Adam Turner.


Testing
-------

* #12141: Migrate from the deprecated ``karma`` JavaScript test framework to
  the actively-maintained ``jasmine`` framework.  Test coverage is unaffected.
  Patch by James Addison.
