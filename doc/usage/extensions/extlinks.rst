:mod:`sphinx.ext.extlinks` -- Markup to shorten external links
==============================================================

.. module:: sphinx.ext.extlinks
   :synopsis: Allow inserting external links with common base URLs easily.
.. moduleauthor:: Georg Brandl

.. versionadded:: 1.0

This extension is meant to help with the common pattern of having many external
links that point to URLs on one and the same site, e.g. links to bug trackers,
version control web interfaces, or simply subpages in other websites.  It does
so by providing aliases to base URLs, so that you only need to give the subpage
name when creating a link.

Let's assume that you want to include many links to issues at the Sphinx
tracker, at :samp:`https://github.com/sphinx-doc/sphinx/issues/{num}`.  Typing
this URL again and again is tedious, so you can use :mod:`~sphinx.ext.extlinks`
to avoid repeating yourself.

The extension adds a config value:

.. confval:: extlinks

   This config value must be a dictionary of external sites, mapping unique
   short alias names to a *base URL* and a *caption*.  For example, to create an
   alias for the above mentioned issues, you would add ::

      extlinks = {'issue': ('https://github.com/sphinx-doc/sphinx/issues/%s',
                            'issue %s')}

   Now, you can use the alias name as a new role, e.g. ``:issue:`123```.  This
   then inserts a link to https://github.com/sphinx-doc/sphinx/issues/123.
   As you can see, the target given in the role is substituted in the *base URL*
   in the place of ``%s``.

   The link caption depends on the second item in the tuple, the *caption*:

   - If *caption* is ``None``, the link caption is the full URL.
   - If *caption* is a string, then it must contain ``%s`` exactly once.  In
     this case the link caption is *caption* with the partial URL substituted
     for ``%s`` -- in the above example, the link caption would be
     ``issue 123``.

   To produce a literal ``%`` in either *base URL* or *caption*, use ``%%``::

      extlinks = {'KnR': ('https://example.org/K%%26R/page/%s',
                            '[K&R; page %s]')}

   You can also use the usual "explicit title" syntax supported by other roles
   that generate links, i.e. ``:issue:`this issue <123>```.  In this case, the
   *caption* is not relevant.

   .. versionchanged:: 4.0

      Support to substitute by '%s' in the caption.

.. note::

   Since links are generated from the role in the reading stage, they appear as
   ordinary links to e.g. the ``linkcheck`` builder.

.. confval:: extlinks_detect_hardcoded_links

   If enabled, extlinks emits a warning if a hardcoded link is replaceable
   by an extlink, and suggests a replacement via warning.  It defaults to
   ``False``.

   .. versionadded:: 4.5
