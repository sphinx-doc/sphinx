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
and easy to understand.  The most important concept in Jinja is
:dfn:`template inheritance`, which means that you can overwrite only specific
blocks within a template, customizing it while also keeping the changes at a
minimum.

To customize the output of your documentation you can override all the templates
(both the layout templates and the child templates) by adding files with the same
name as the original filename into the template directory of the folder the sphinx
quickstart generated for you.

Sphinx will look for templates in the folders of :confval:`templates_path` first,
and if it can't find the template it's looking for there, it falls back to the
builtin templates that come with sphinx.  You can have a look at them by browsing
the sphinx directory in your site packages folder.

A template contains **variables**, which get replaced with values when the
template is evaluated, **tags**, which control the logic of the template and
**blocks** which are used for template inheritance.

Sphinx provides base templates with a couple of blocks it will fill with data.
The default templates are located in the `templates` folder of the sphinx
installation directory.  Templates with the same name in the
:confval:`templates_path` override templates from the builtin folder.

To add a new link to the template area containing related links all you have
to do is to add a new template called ``layout.html`` with the following
contents:

.. sourcecode:: html+jinja

    {% extends "!layout.html" %}
    {% block rootrellink %}
        <li><a href="http://project.invalid/">Project Homepage</a> &raquo;</li>
        {{ super() }}
    {% endblock %}

By prefixing the parent template with an exclamation mark, sphinx will load
the builtin layout template.  If you override a block you should call
``{{ super() }}`` to render the parent contents unless you don't want the
parent contents to show up.


Blocks
~~~~~~

The following blocks exist in the layout template:

`doctype`
    The doctype of the output format.  By default this is XHTML 1.0
    Transitional as this is the closest to what sphinx generates and it's a
    good idea not to change it unless you want to switch to HTML 5 or a
    different but compatible XHTML doctype.

`rellinks`
    This block adds a couple of `<link>` tags to the head section of the
    template.

`extrahead`
    This block is empty by default and can be used to add extra contents
    into the head section of the generated HTML file.  This is the right
    place to add references to javascript or extra CSS files.

`relbar1` / `relbar2`
    This block contains the list of related links.  `relbar1` appears
    before the document, `relbar2` after.

`rootrellink` / `relbaritems`
    Inside the rel bar there are three sections.  The `rootrellink`, the links
    from the documentation and the `relbaritems`.  The `rootrellink` is a list
    item that points to the index of the documentation by default, the
    `relbaritems` are empty.  If you override them to add extra links into
    the bar make sure that they are list items and end with the `reldelim1`.

`document`
    The contents of the document itself.

`sidebar1` / `sidebar2`
    A possible location for a sidebar.  `sidebar1` appears before the document
    and is empty by default, `sidebar2` after the document and contains the
    default sidebar.  If you want to swap the sidebar location override
    this and call the `sidebar` helper:

    .. sourcecode:: html+jinja

        {% block sidebar1 %}{{ sidebar() }}{% endblock %}
        {% block sidebar2 %}{% endblock %}

`footer`
    The block for the footer div.  If you want a custom footer or markup before
    or after it, override this one.


Configuration Variables
~~~~~~~~~~~~~~~~~~~~~~~

Inside templates you can set a couple of variables used by the layout template
using the ``{% set %}`` tag:

.. data:: reldelim1
    The delimiter for the items on the left side of the related bar.  This
    defaults to ``' &raquo;'``  Each item in the related bar ends with the
    value of this variable.

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

Sphinx provides various helper functions in the template you can use to
generate links or output often used elements.

.. function:: pathto(file)

    Returns the path to a file as URL.

.. function:: hasdoc(target)

    Checks if a document with the name `target` exists.

.. function:: sidebar()

    Returns the rendered sidebar.

.. function:: relbar()

    Returns the rendered relbar.


Global Variables
~~~~~~~~~~~~~~~~

These global variables are available in every template and are safe to use.
There are more, but most of them are an implementation detail and might
change in the future.

.. data:: docstitle

    The title of the documentation.

.. data:: sourcename

    The name of the source file

.. data:: builder

    The name of the builder (``html``, ``htmlhelp``, or ``web``)

.. data:: next

    The next document for the navigation.  This variable is either falsy
    or has two attributes `link` and `title`.  The title contiains HTML
    markup.  For example to generate a link to the next page one can use
    this snippet:

    .. sourcecode:: html+jinja

        {% if next %}
        <a href="{{ next.link|e }}">{{ next.title }}</a>
        {% endif %}

.. data:: prev

    Like `next` but for the previous page.
