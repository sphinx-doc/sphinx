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

The default templating language in Sphinx is Jinja.  It's Django/Smarty inspired
and easy to understand.  The most important concept in Jinja is :dfn:`template
inheritance`, which means that you can overwrite only specific blocks within a
template, customizing it while also keeping the changes at a minimum.

To customize the output of your documentation you can override all the templates
(both the layout templates and the child templates) by adding files with the
same name as the original filename into the template directory of the folder the
Sphinx quickstart generated for you.

Sphinx will look for templates in the folders of :confval:`templates_path`
first, and if it can't find the template it's looking for there, it falls back
to the builtin templates that come with Sphinx.

A template contains **variables**, which are replaced with values when the
template is evaluated, **tags**, which control the logic of the template and
**blocks** which are used for template inheritance.

Sphinx provides base templates with a couple of blocks it will fill with data.
The default templates are located in the :file:`templates` folder of the Sphinx
installation directory.  Templates with the same name in the
:confval:`templates_path` override templates located in the builtin folder.

For example, to add a new link to the template area containing related links all
you have to do is to add a new template called ``layout.html`` with the
following contents:

.. sourcecode:: html+jinja

    {% extends "!layout.html" %}
    {% block rootrellink %}
        <li><a href="http://project.invalid/">Project Homepage</a> &raquo;</li>
        {{ super() }}
    {% endblock %}

By prefixing the name of the extended template with an exclamation mark, Sphinx
will load the builtin layout template.  If you override a block, you should call
``{{ super() }}`` somewhere to render the block's content in the extended
template -- unless you don't want that content to show up.


Blocks
~~~~~~

The following blocks exist in the ``layout`` template:

`doctype`
    The doctype of the output format.  By default this is XHTML 1.0 Transitional
    as this is the closest to what Sphinx and Docutils generate and it's a good
    idea not to change it unless you want to switch to HTML 5 or a different but
    compatible XHTML doctype.

`rellinks`
    This block adds a couple of ``<link>`` tags to the head section of the
    template.

`extrahead`
    This block is empty by default and can be used to add extra contents into
    the ``<head>`` tag of the generated HTML file.  This is the right place to
    add references to JavaScript or extra CSS files.

`relbar1` / `relbar2`
    This block contains the list of related links (the parent documents on the
    left, and the links to index, modules etc. on the right).  `relbar1` appears
    before the document, `relbar2` after the document.  By default, both blocks
    are filled; to show the relbar only before the document, you would override
    `relbar2` like this::

       {% block relbar2 %}{% endblock %}

`rootrellink` / `relbaritems`
    Inside the relbar there are three sections: The `rootrellink`, the links
    from the documentation and the `relbaritems`.  The `rootrellink` is a block
    that by default contains a list item pointing to the master document by
    default, the `relbaritems` is an empty block.  If you override them to add
    extra links into the bar make sure that they are list items and end with the
    :data:`reldelim1`.

`document`
    The contents of the document itself.

`sidebar1` / `sidebar2`
    A possible location for a sidebar.  `sidebar1` appears before the document
    and is empty by default, `sidebar2` after the document and contains the
    default sidebar.  If you want to swap the sidebar location override this and
    call the `sidebar` helper:

    .. sourcecode:: html+jinja

        {% block sidebar1 %}{{ sidebar() }}{% endblock %}
        {% block sidebar2 %}{% endblock %}

    (The `sidebar2` location for the sidebar is needed by the ``sphinxdoc.css``
    stylesheet, for example.)

`footer`
    The block for the footer div.  If you want a custom footer or markup before
    or after it, override this one.


Configuration Variables
~~~~~~~~~~~~~~~~~~~~~~~

Inside templates you can set a couple of variables used by the layout template
using the ``{% set %}`` tag:

.. data:: reldelim1

   The delimiter for the items on the left side of the related bar.  This
   defaults to ``' &raquo;'`` Each item in the related bar ends with the value
   of this variable.

.. data:: reldelim2

   The delimiter for the items on the right side of the related bar.  This
   defaults to ``' |'``.  Each item except of the last one in the related bar
   ends with the value of this variable.

Overriding works like this:

.. sourcecode:: html+jinja

   {% extends "!layout.html" %}
   {% set reldelim1 = ' &gt;' %}


Helper Functions
~~~~~~~~~~~~~~~~

Sphinx provides various Jinja functions as helpers in the template.  You can use
them to generate links or output multiply used elements.

.. function:: pathto(document)

   Return the path to a Sphinx document as a URL.  Use this to refer to built
   documents.

.. function:: pathto(file, 1)

   Return the path to a *file* which is a filename relative to the root of the
   generated output.  Use this to refer to static files.

.. function:: hasdoc(document)

   Check if a document with the name *document* exists.

.. function:: sidebar()

   Return the rendered sidebar.

.. function:: relbar()

   Return the rendered relbar.


Global Variables
~~~~~~~~~~~~~~~~

These global variables are available in every template and are safe to use.
There are more, but most of them are an implementation detail and might change
in the future.

.. data:: docstitle

   The title of the documentation (the value of :confval:`html_title`).

.. data:: sourcename

   The name of the copied source file for the current document.  This is only
   nonempty if the :confval:`html_copy_source` value is true.

.. data:: builder

   The name of the builder (for builtin builders, ``html``, ``htmlhelp``, or
   ``web``).

.. data:: next

   The next document for the navigation.  This variable is either false or has
   two attributes `link` and `title`.  The title contains HTML markup.  For
   example, to generate a link to the next page, you can use this snippet:

   .. sourcecode:: html+jinja

      {% if next %}
      <a href="{{ next.link|e }}">{{ next.title }}</a>
      {% endif %}

.. data:: prev

   Like :data:`next`, but for the previous page.
