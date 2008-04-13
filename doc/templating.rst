.. _templating:

Templating
==========

Sphinx uses the `Jinja <http://jinja.pocoo.org>`_ templating engine for its HTML
templates.  Jinja is a text-based engine, and inspired by Django templates, so
anyone having used Django will already be familiar with it.  It also has
excellent documentation for those who need to make themselves familiar with it.


Do I need to use Sphinx' templates to produce HTML?
---------------------------------------------------

No.  You have several other options:

* You can write a :class:`~sphinx.application.TemplateBridge` subclass that
  calls your template engine of choice, and set the :confval:`template_bridge`
  configuration value accordingly.

* You can :ref:`write a custom builder <writing-builders>` that derives from
  :class:`~sphinx.builder.StandaloneHTMLBuilder` and calls your template engine
  of choice.

* You can use the :class:`~sphinx.builder.PickleHTMLBuilder` that produces
  pickle files with the page contents, and postprocess them using a custom tool,
  or use them in your Web application.


Jinja/Sphinx Templating Primer
------------------------------

The most important concept in Jinja is :dfn:`template inheritance`, which means
that you can overwrite only specific blocks within a template, customizing it
while also keeping the changes at a minimum.

Inheritance is done via two (Jinja) directives, ``extends`` and ``block``.

.. template path
   blocks
   extends !template

   template names for other template engines

.. XXX continue this
