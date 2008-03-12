.. _templating:

Templating
==========

Sphinx uses the `Jinja <http://jinja.pocoo.org>` templating engine for its HTML
templates.  Jinja is a text-based engine, and inspired by Django templates, so
anyone having used Django will already be familiar with it.  It also has
excellent documentation for those who need to make themselves familiar with it.

The most important concept in Jinja is :dfn:`template inheritance`, which means
that you can overwrite only specific blocks within a template, customizing it
while also keeping the changes at a minimum.

Inheritance is done via two directives, ``extends`` and ``block``.

.. template path
   blocks
   extends !template

These are the blocks that are predefined in Sphinx' ``layout.html`` template:

**doctype**
   The doctype, by default HTML 4 Transitional.

**rellinks**
   HTML ``<link rel=`` links in the head, by default filled with various links.

**extrahead**
   Block in the ``<head>`` tag, by default empty.

**beforerelbar**
   Block before the "related bar" (the navigation links at the page top), by
   default empty.  Use this to insert a page header.

**relbar**
   The "related bar" by default.  Overwrite this block to customize the entire
   navigation bar.

**rootrellink**
   The most parent relbar link, by default pointing to the "index" document with
   a caption of e.g. "Project v0.1 documentation".

**relbaritems**
   Block in the ``<ul>`` used for relbar items, by default empty.  Use this to
   add more items.

**afterrelbar**
   Block between relbar and document body, by default empty.

**body**
   Block in the document body.  This should be overwritten by every child
   template, e.g. :file:`page.html` puts the page content there.

**beforesidebar**
   Block between body and sidebar, by default empty.

**sidebar**
   Contains the whole sidebar.

**aftersidebar**
   Block between 
