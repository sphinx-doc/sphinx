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
tracker, at :samp:`http://bitbucket.org/birkenfeld/sphinx/issue/{num}`.  Typing
this URL again and again is tedious, so you can use :mod:`~sphinx.ext.extlinks`
to avoid repeating yourself.

The extension adds one new config value:

.. confval:: extlinks

   This config value must be a dictionary of external sites, mapping unique
   short alias names to a base URL and a *prefix*.  For example, to create an
   alias for the above mentioned issues, you would add ::

      extlinks = {'issue': ('https://bitbucket.org/birkenfeld/sphinx/issue/%s',
                            'issue ')}

   Now, you can use the alias name as a new role, e.g. ``:issue:`123```.  This
   then inserts a link to https://bitbucket.org/birkenfeld/sphinx/issue/123.
   As you can see, the target given in the role is substituted in the base URL
   in the place of ``%s``.

   The link *caption* depends on the second item in the tuple, the *prefix*:

   - If the prefix is ``None``, the link caption is the full URL.
   - If the prefix is the empty string, the link caption is the partial URL
     given in the role content (``123`` in this case.)
   - If the prefix is a non-empty string, the link caption is the partial URL,
     prepended by the prefix -- in the above example, the link caption would be
     ``issue 123``.

   You can also use the usual "explicit title" syntax supported by other roles
   that generate links, i.e. ``:issue:`this issue <123>```.  In this case, the
   *prefix* is not relevant.

.. note::

   Since links are generated from the role in the reading stage, they appear as
   ordinary links to e.g. the ``linkcheck`` builder.
