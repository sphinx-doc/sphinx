:mod:`sphinx.ext.githubpages` -- Publish HTML docs in GitHub Pages
==================================================================

.. module:: sphinx.ext.githubpages
   :synopsis: Publish HTML docs in GitHub Pages

.. versionadded:: 1.4

.. versionchanged:: 2.0
   Support ``CNAME`` file

This extension creates ``.nojekyll`` file on generated HTML directory to publish
the document on GitHub Pages.

It also creates a ``CNAME`` file for custom domains when :confval:`html_baseurl`
set.
