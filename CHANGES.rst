Release 8.2.0 (in development)
==============================

Dependencies
------------

* #13000: Drop Python 3.10 support.

Incompatible changes
--------------------

* #13044: Remove the internal and undocumented ``has_equations`` data
  from the :py:class:`!MathDomain`` domain.
  The undocumented :py:meth:`!MathDomain.has_equations` method
  now unconditionally returns ``True``.
  These are replaced by the ``has_maths_elements`` key of the page context dict.
  Patch by Adam Turner.
* #13227: HTML output for sequences of keys in the :rst:role:`kbd` role
  no longer uses a ``<kbd class="kbd compound">`` element to wrap
  the keys and separators, but places them directly in the relevant parent node.
  This means that CSS rulesets targeting ``kbd.compound`` or ``.kbd.compound``
  will no longer have any effect.
  Patch by Adam Turner.

Deprecated
----------

* #13037: Deprecate the ``SingleHTMLBuilder.fix_refuris`` method.
  Patch by James Addison.

Features added
--------------

* Add a new ``duplicate_declaration`` warning type,
  with ``duplicate_declaration.c`` and ``duplicate_declaration.cpp`` subtypes.
  Patch by Julien Lecomte and Adam Turner.
* #11824: linkcode: Allow extensions to add support for a domain by defining
  the keys that should be present.
  Patch by Nicolas Peugnet.
* #13144: Add a ``class`` option to the :rst:dir:`autosummary` directive.
  Patch by Tim Hoffmann.
* #13146: Napoleon: Unify the type preprocessing logic to allow
  Google-style docstrings to use the optional and default keywords.
  Patch by Chris Barrick.
* #13227: Implement the :rst:role:`kbd` role as a ``SphinxRole``.
  Patch by Adam Turner.
* #13163: Always print tracebacks in full when Sphinx encounters an internal
  error.
  Patch by Kevin Deldycke.

Bugs fixed
----------

* #13060: HTML Search: use ``Map`` to store per-file term scores.
  Patch by James Addison
* #13130: LaTeX docs: ``pdflatex`` index creation may fail for index entries
  in French.  See :confval:`latex_use_xindy`.
  Patch by Jean-François B.
* LaTeX: fix a ``7.4.0`` typo in a default for ``\sphinxboxsetup``
  (refs: PR #13152).
  Patch by Jean-François B.
* #13096: HTML Search: check that query terms exist as properties in
  term indices before accessing them.
* #11233: linkcheck: match redirect URIs against :confval:`linkcheck_ignore` by
  overriding session-level ``requests.get_redirect_target``.
* #13195: viewcode: Fix issue where import paths differ from the directory
  structure.
  Patch by Ben Egan and Adam Turner.
* #13188: autodoc: fix detection of class methods implemented in C.
  Patch by Bénédikt Tran.

Testing
-------

* #13224: Correctness fixup for ``test_html_multi_line_copyright``.
  Patch by Colin Watson, applied by James Addison.
