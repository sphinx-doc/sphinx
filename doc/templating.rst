.. highlight:: html+jinja

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
  :class:`~sphinx.builders.html.StandaloneHTMLBuilder` and calls your template
  engine of choice.

* You can use the :class:`~sphinx.builders.html.PickleHTMLBuilder` that produces
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
same name as the original filename into the template directory of the structure
the Sphinx quickstart generated for you.

Sphinx will look for templates in the folders of :confval:`templates_path`
first, and if it can't find the template it's looking for there, it falls back
to the selected theme's templates.

A template contains **variables**, which are replaced with values when the
template is evaluated, **tags**, which control the logic of the template and
**blocks** which are used for template inheritance.

Sphinx' *basic* theme provides base templates with a couple of blocks it will
fill with data.  These are located in the :file:`themes/basic` subdirectory of
the Sphinx installation directory, and used by all builtin Sphinx themes.
Templates with the same name in the :confval:`templates_path` override templates
supplied by the selected theme.

For example, to add a new link to the template area containing related links all
you have to do is to add a new template called ``layout.html`` with the
following contents::

    {% extends "!layout.html" %}
    {% block rootrellink %}
        <li><a href="http://project.invalid/">Project Homepage</a> &raquo;</li>
        {{ super() }}
    {% endblock %}

By prefixing the name of the overridden template with an exclamation mark,
Sphinx will load the layout template from the underlying HTML theme.

**Important**: If you override a block, call ``{{ super() }}`` somewhere to
render the block's content in the extended template -- unless you don't want
that content to show up.


Working with the builtin templates
----------------------------------

The builtin **basic** theme supplies the templates that all builtin Sphinx
themes are based on.  It has the following elements you can override or use:

Blocks
~~~~~~

The following blocks exist in the ``layout.html`` template:

`doctype`
    The doctype of the output format.  By default this is XHTML 1.0 Transitional
    as this is the closest to what Sphinx and Docutils generate and it's a good
    idea not to change it unless you want to switch to HTML 5 or a different but
    compatible XHTML doctype.

`linktags`
    This block adds a couple of ``<link>`` tags to the head section of the
    template.

`extrahead`
    This block is empty by default and can be used to add extra contents into
    the ``<head>`` tag of the generated HTML file.  This is the right place to
    add references to JavaScript or extra CSS files.

`relbar1` / `relbar2`
    This block contains the *relation bar*, the list of related links (the
    parent documents on the left, and the links to index, modules etc. on the
    right).  `relbar1` appears before the document, `relbar2` after the
    document.  By default, both blocks are filled; to show the relbar only
    before the document, you would override `relbar2` like this::

       {% block relbar2 %}{% endblock %}

`rootrellink` / `relbaritems`
    Inside the relbar there are three sections: The `rootrellink`, the links
    from the documentation and the custom `relbaritems`.  The `rootrellink` is a
    block that by default contains a list item pointing to the master document
    by default, the `relbaritems` is an empty block.  If you override them to
    add extra links into the bar make sure that they are list items and end with
    the :data:`reldelim1`.

`document`
    The contents of the document itself.  It contains the block "body" where the
    individual content is put by subtemplates like ``page.html``.

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

`sidebarlogo`
    The logo location within the sidebar.  Override this if you want to place
    some content at the top of the sidebar.

`footer`
    The block for the footer div.  If you want a custom footer or markup before
    or after it, override this one.

The following four blocks are *only* used for pages that do not have assigned a
list of custom sidebars in the :confval:`html_sidebars` config value.  Their use
is deprecated in favor of separate sidebar templates, which can be included via
:confval:`html_sidebars`.

`sidebartoc`
    The table of contents within the sidebar.

    .. deprecated:: 1.0

`sidebarrel`
    The relation links (previous, next document) within the sidebar.

    .. deprecated:: 1.0

`sidebarsourcelink`
    The "Show source" link within the sidebar (normally only shown if this is
    enabled by :confval:`html_show_sourcelink`).

    .. deprecated:: 1.0

`sidebarsearch`
    The search box within the sidebar.  Override this if you want to place some
    content at the bottom of the sidebar.

    .. deprecated:: 1.0


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

Overriding works like this::

   {% extends "!layout.html" %}
   {% set reldelim1 = ' &gt;' %}

.. data:: script_files

   Add additional script files here, like this::

      {% set script_files = script_files + ["_static/myscript.js"] %}

.. data:: css_files

   Similar to :data:`script_files`, for CSS files.


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

   Return the rendered relation bar.


Global Variables
~~~~~~~~~~~~~~~~

These global variables are available in every template and are safe to use.
There are more, but most of them are an implementation detail and might change
in the future.

.. data:: builder

   The name of the builder (e.g. ``html`` or ``htmlhelp``).

.. data:: copyright

   The value of :confval:`copyright`.

.. data:: docstitle

   The title of the documentation (the value of :confval:`html_title`).

.. data:: embedded

   True if the built HTML is meant to be embedded in some viewing application
   that handles navigation, not the web browser, such as for HTML help or Qt
   help formats.  In this case, the sidebar is not included.

.. data:: favicon

   The path to the HTML favicon in the static path, or ``''``.

.. data:: file_suffix

   The value of the builder's :attr:`~.SerializingHTMLBuilder.out_suffix`
   attribute, i.e. the file name extension that the output files will get.  For
   a standard HTML builder, this is usually ``.html``.

.. data:: has_source

   True if the reST document sources are copied (if :confval:`html_copy_source`
   is true).

.. data:: last_updated

   The build date.

.. data:: logo

   The path to the HTML logo image in the static path, or ``''``.

.. data:: master_doc

   The value of :confval:`master_doc`, for usage with :func:`pathto`.

.. data:: next

   The next document for the navigation.  This variable is either false or has
   two attributes `link` and `title`.  The title contains HTML markup.  For
   example, to generate a link to the next page, you can use this snippet::

      {% if next %}
      <a href="{{ next.link|e }}">{{ next.title }}</a>
      {% endif %}

.. data:: pagename

   The "page name" of the current file, i.e. either the document name if the
   file is generated from a reST source, or the equivalent hierarchical name
   relative to the output directory (``[directory/]filename_without_extension``).

.. data:: parents

   A list of parent documents for navigation, structured like the :data:`next`
   item.

.. data:: prev

   Like :data:`next`, but for the previous page.

.. data:: project

   The value of :confval:`project`.

.. data:: release

   The value of :confval:`release`.

.. data:: rellinks

   A list of links to put at the left side of the relbar, next to "next" and
   "prev".  This usually contains links to the general index and other indices,
   such as the Python module index.  If you add something yourself, it must be a
   tuple ``(pagename, link title, accesskey, link text)``.

.. data:: shorttitle

   The value of :confval:`html_short_title`.

.. data:: show_source

   True if :confval:`html_show_sourcelink` is true.

.. data:: sphinx_version

   The version of Sphinx used to build.

.. data:: style

   The name of the main stylesheet, as given by the theme or
   :confval:`html_style`.

.. data:: title

   The title of the current document, as used in the ``<title>`` tag.

.. data:: use_opensearch

   The value of :confval:`html_use_opensearch`.

.. data:: version

   The value of :confval:`version`.


In addition to these values, there are also all **theme options** available
(prefixed by ``theme_``), as well as the values given by the user in
:confval:`html_context`.

In documents that are created from source files (as opposed to
automatically-generated files like the module index, or documents that already
are in HTML form), these variables are also available:

.. data:: meta

   Document metadata (a dictionary), see :ref:`metadata`.

.. data:: sourcename

   The name of the copied source file for the current document.  This is only
   nonempty if the :confval:`html_copy_source` value is true.

.. data:: toc

   The local table of contents for the current page, rendered as HTML bullet
   lists.

.. data:: toctree

   A callable yielding the global TOC tree containing the current page, rendered
   as HTML bullet lists.  Optional keyword arguments:

   * ``collapse`` (true by default): if true, all TOC entries that are not
     ancestors of the current page are collapsed

   * ``maxdepth`` (defaults to the max depth selected in the toctree directive):
     the maximum depth of the tree; set it to ``-1`` to allow unlimited depth

   * ``titles_only`` (false by default): if true, put only toplevel document
     titles in the tree
