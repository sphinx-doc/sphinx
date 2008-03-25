.. _templating:

Templating
==========

Sphinx uses the `Jinja <http://jinja.pocoo.org>`_ templating engine for its HTML
templates.  Jinja is a text-based engine, and inspired by Django templates, so
anyone having used Django will already be familiar with it.  It also has
excellent documentation for those who need to make themselves familiar with it.

The most important concept in Jinja is :dfn:`template inheritance`, which means
that you can overwrite only specific blocks within a template, customizing it
while also keeping the changes at a minimum.

Inheritance is done via two (Jinja) directives, ``extends`` and ``block``.

.. template path
   blocks
   extends !template

XXX continue this
