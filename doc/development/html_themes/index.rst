.. _extension-html-theme:

HTML theme development
======================

.. versionadded:: 0.6

.. note::

   This document provides information about creating your own theme. If you
   simply wish to use a pre-existing HTML themes, refer to
   :doc:`/usage/theming`.

Sphinx supports changing the appearance of its HTML output via *themes*.  A
theme is a collection of HTML templates, stylesheet(s) and other static files.
Additionally, it has a configuration file which specifies from which theme to
inherit, which highlighting style to use, and what options exist for customizing
the theme's look and feel.

Themes are meant to be project-unaware, so they can be used for different
projects without change.

.. note::

   See :ref:`dev-extensions` for more information that may
   be helpful in developing themes.


Creating themes
---------------

Themes take the form of either a directory or a zipfile (whose name is the
theme name), containing the following:

* Either a :file:`theme.toml` file (preferred) or a :file:`theme.conf` file.
* HTML templates, if needed.
* A ``static/`` directory containing any static files that will be copied to the
  output static directory on build.  These can be images, styles, script files.

Theme configuration (``theme.toml``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :file:`theme.toml` file is a TOML_ document,
containing two tables: ``[theme]`` and ``[options]``.

The ``[theme]`` table defines the theme's settings:

* **inherit** (string): The name of the base theme from which to inherit
  settings, options, templates, and static files.
  All static files from theme 'ancestors' will be used.
  The theme will use all options defined in inherited themes.
  Finally, inherited themes will be used to locate missing templates
  (for example, if ``"basic"`` is used as the base theme, most templates will
  already be defined).

  If set to ``"none"``, the theme will not inherit from any other theme.
  Inheritance is recursive, forming a chain of inherited themes
  (e.g. ``default`` -> ``classic`` -> ``basic`` -> ``none``).

* **stylesheets** (list of strings): A list of CSS filenames which will be
  included in generated HTML header.
  Setting the   :confval:`html_style` config value will override this setting.

  Other mechanisms for including multiple stylesheets include ``@import`` in CSS
  or using a custom HTML template with appropriate ``<link rel="stylesheet">`` tags.

* **sidebars** (list of strings): A list of sidebar templates.
  This can be overridden by the user via the :confval:`html_sidebars` config value.

* **pygments_style** (table): A TOML table defining the names of Pygments styles
  to use for highlighting syntax.
  The table has two recognised keys: ``default`` and ``dark``.
  The style defined in the ``dark`` key will be used when
  the CSS media query ``(prefers-color-scheme: dark)`` evaluates to true.

  ``[theme.pygments_style.default]`` can be overridden by the user via the
  :confval:`pygments_style` config value.

The ``[options]`` table defines the options for the theme.
It is structured such that each key-value pair corresponds to a variable name
and the corresponding default value.
These options can be overridden by the user in :confval:`html_theme_options`
and are accessible from all templates as ``theme_<name>``.

.. versionadded:: 7.3
   ``theme.toml`` support.

.. _TOML: https://toml.io/en/

Exemplar :file:`theme.toml` file:

.. code-block:: toml

   [theme]
   inherit = "basic"
   stylesheets = [
       "main-CSS-stylesheet.css",
   ]
   sidebars = [
       "localtoc.html",
       "relations.html",
       "sourcelink.html",
       "searchbox.html",
   ]
   # Style names from https://pygments.org/styles/
   pygments_style = { default = "style_name", dark = "dark_style" }

   [options]
   variable = "default value"

Theme configuration (``theme.conf``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :file:`theme.conf` file is in INI format [1]_ (readable by the standard
Python :mod:`configparser` module) and has the following structure:

.. code-block:: ini

    [theme]
    inherit = base theme
    stylesheet = main CSS name
    pygments_style = stylename
    sidebars = localtoc.html, relations.html, sourcelink.html, searchbox.html

    [options]
    variable = default value

* The **inherit** setting gives the name of a "base theme", or ``none``.  The
  base theme will be used to locate missing templates (most themes will not have
  to supply most templates if they use ``basic`` as the base theme), its options
  will be inherited, and all of its static files will be used as well. If you
  want to also inherit the stylesheet, include it via CSS' ``@import`` in your
  own.

* The **stylesheet** setting gives a list of CSS filenames separated commas which
  will be referenced in the HTML header.  You can also use CSS' ``@import``
  technique to include one from the other, or use a custom HTML template that
  adds ``<link rel="stylesheet">`` tags as necessary.  Setting the
  :confval:`html_style` config value will override this setting.

* The **pygments_style** setting gives the name of a Pygments style to use for
  highlighting.  This can be overridden by the user in the
  :confval:`pygments_style` config value.

* The **pygments_dark_style** setting gives the name of a Pygments style to use
  for highlighting when the CSS media query ``(prefers-color-scheme: dark)``
  evaluates to true. It is injected into the page using
  :meth:`~sphinx.application.Sphinx.add_css_file`.

* The **sidebars** setting gives the comma separated list of sidebar templates
  for constructing sidebars.  This can be overridden by the user in the
  :confval:`html_sidebars` config value.

* The **options** section contains pairs of variable names and default values.
  These options can be overridden by the user in :confval:`html_theme_options`
  and are accessible from all templates as ``theme_<name>``.

.. versionadded:: 1.7
   sidebar settings

.. versionchanged:: 5.1

   The stylesheet setting accepts multiple CSS filenames

Convert ``theme.conf`` to ``theme.toml``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

INI-style theme configuration files (``theme.conf``) can be converted to TOML
via a helper programme distributed with Sphinx.
This is intended for one-time use, and may be removed without notice in a future
version of Sphinx.

.. code-block:: console

   $ python -m sphinx.theming conf_to_toml [THEME DIRECTORY PATH]

The required argument is a path to a directory containing a ``theme.conf`` file.
The programme will write a ``theme.toml`` file in the same directory,
and will not modify the original ``theme.conf`` file.

.. versionadded:: 7.3

.. _distribute-your-theme:

Distribute your theme as a Python package
-----------------------------------------

As a way to distribute your theme, you can use a Python package.  This makes it
easier for users to set up your theme.

To distribute your theme as a Python package, please define an entry point
called ``sphinx.html_themes`` in your ``pyproject.toml`` file,
and write a ``setup()`` function to register your theme
using the :meth:`~sphinx.application.Sphinx.add_html_theme` API:

.. code-block:: toml

   # pyproject.toml

   [project.entry-points."sphinx.html_themes"]
   name_of_theme = "your_theme_package"

.. code-block:: python

    # your_theme_package.py
    from pathlib import Path

    def setup(app):
        app.add_html_theme('name_of_theme', Path(__file__).resolve().parent)

If your theme package contains two or more themes, please call
``add_html_theme()`` twice or more.

.. versionadded:: 1.2
   'sphinx_themes' entry_points feature.

.. deprecated:: 1.6
   ``sphinx_themes`` entry_points has been deprecated.

.. versionadded:: 1.6
   ``sphinx.html_themes`` entry_points feature.


Styling with CSS
----------------

The :confval:`!stylesheets` setting can be used to add custom CSS files to a theme.

.. caution::

   The structure of the HTML elements and their classes are currently not a
   well-defined public API. Please infer them from inspecting the built HTML
   pages. While we cannot guarantee full stability, they tend to be fairly
   stable.

Styling search result entries by category
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 8.0

.. note::

    The CSS classes named below are generated by Sphinx's standalone search
    code.  If you are using a third-party search provider, such as
    ReadTheDocs_, to provide search results, then the theming options available
    may vary.

.. _ReadTheDocs: https://docs.readthedocs.io/

The search result items have classes indicating the context in which the
search term was found. You can use the CSS selectors:

- ``ul.search li.kind-index``:
  For results in an index, such as the glossary
- ``ul.search li.kind-object``:
  For results in source code, like Python function definitions
- ``ul.search li.kind-title``:
  For results found in section headings
- ``ul.search li.kind-text``:
  For results found anywhere else in the documentation text

As a base for inheritance by other themes, the ``basic`` theme is
intentionally minimal and does not define CSS rules using these.
Derived themes are encouraged to use these selectors as they see fit.
For example, the following stylesheet adds contextual icons to the
search result list:

.. code-block:: css

    ul.search {
        padding-left: 30px;
    }
    ul.search li {
        padding: 5px 0 5px 10px;
        list-style-type: "\25A1";  /* Unicode: White Square */
    }
    ul.search li.kind-index {
        list-style-type: "\1F4D1";  /* Unicode: Bookmark Tabs */
    }
    ul.search li.kind-object {
        list-style-type: "\1F4E6";  /* Unicode: Package */
    }
    ul.search li.kind-title {
        list-style-type: "\1F4C4";  /* Unicode: Page Facing Up */
    }
    ul.search li.kind-text {
        list-style-type: "\1F4C4";  /* Unicode: Page Facing Up */
    }


Templating
----------

.. toctree::
   :hidden:

   templating

The :doc:`guide to templating <templating>` is helpful if you want to write your
own templates.  What is important to keep in mind is the order in which Sphinx
searches for templates:

* First, in the user's ``templates_path`` directories.
* Then, in the selected theme.
* Then, in its base theme, its base's base theme, etc.

When extending a template in the base theme with the same name, use the theme
name as an explicit directory: ``{% extends "basic/layout.html" %}``.  From a
user ``templates_path`` template, you can still use the "exclamation mark"
syntax as :ref:`described in the templating document <templating-primer>`.


.. _theming-static-templates:

Static templates
~~~~~~~~~~~~~~~~

Since theme options are meant for the user to configure a theme more easily,
without having to write a custom stylesheet, it is necessary to be able to
template static files as well as HTML files.  Therefore, Sphinx supports
so-called "static templates", like this:

If the name of a file in the ``static/`` directory of a theme (or in the user's
static path) ends with ``.jinja`` or ``_t``, it will be processed by the
template engine.  The suffix will be removed from the final file name.

For example, a theme with a ``static/theme_styles.css.jinja`` file could use
templating to put options into the stylesheet.
When a documentation project is built with that theme,
the output directory will contain a ``_static/theme_styles.css`` file
where all template tags have been processed.

.. versionchanged:: 7.4

   The preferred suffix for static templates is now ``.jinja``, in line with
   the Jinja project's `recommended file extension`_.

   The ``_t`` file suffix for static templates is now considered 'legacy', and
   support may eventually be removed.

   If a static template with either a ``_t`` suffix or a ``.jinja`` suffix is
   detected, it will be processed by the template engine, with the suffix
   removed from the final file name.

  .. _recommended file extension: https://jinja.palletsprojects.com/en/latest/templates/#template-file-extension


Use custom page metadata in HTML templates
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Any key / value pairs in :doc:`field lists </usage/restructuredtext/field-lists>`
that are placed *before* the page's title will be available to the Jinja
template when building the page within the :data:`meta` attribute. For example,
if a page had the following text before its first title:

.. code-block:: rst

    :mykey: My value

    My first title
    --------------

Then it could be accessed within a Jinja template like so:

.. code-block:: jinja

    {%- if meta is mapping %}
        {{ meta.get("mykey") }}
    {%- endif %}

Note the check that ``meta`` is a dictionary ("mapping" in Jinja
terminology) to ensure that using it in this way is valid.


Defining custom template functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes it is useful to define your own function in Python that you wish to
then use in a template. For example, if you'd like to insert a template value
with logic that depends on the user's configuration in the project, or if you'd
like to include non-trivial checks and provide friendly error messages for
incorrect configuration in the template.

To define your own template function, you'll need to define two functions
inside your module:

* A **page context event handler** (or **registration**) function. This is
  connected to the :class:`.Sphinx` application via an event callback.
* A **template function** that you will use in your Jinja template.

First, define the registration function, which accepts the arguments for
:event:`html-page-context`.

Within the registration function, define the template function that you'd like to
use within Jinja. The template function should return a string or Python objects
(lists, dictionaries) with strings inside that Jinja uses in the templating process

.. note::

    The template function will have access to all of the variables that
    are passed to the registration function.

At the end of the registration function, add the template function to the
Sphinx application's context with ``context['template_func'] = template_func``.

Finally, in your extension's ``setup()`` function, add your registration
function as a callback for :event:`html-page-context`.

.. code-block:: python

   # The registration function
    def setup_my_func(app, pagename, templatename, context, doctree):
        # The template function
        def my_func(mystring):
            return "Your string is %s" % mystring
        # Add it to the page's context
        context['my_func'] = my_func

    # Your extension's setup function
    def setup(app):
        app.connect("html-page-context", setup_my_func)

Now, you will have access to this function in jinja like so:

.. code-block:: jinja

   <div>
   {{ my_func("some string") }}
   </div>


Add your own static files to the build assets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, Sphinx copies static files on the ``static/`` directory of the template
directory.  However, if your package needs to place static files outside of the
``static/`` directory for some reasons, you need to copy them to the ``_static/``
directory of HTML outputs manually at the build via an event hook.  Here is an
example of code to accomplish this:

.. code-block:: python

   import shutil

   def copy_custom_files(app, exc):
       if app.builder.format == 'html' and not exc:
           static_dir = app.outdir / '_static'
           shutil.copyfile('path/to/myextension/_static/myjsfile.js', static_dir)

   def setup(app):
       app.connect('build-finished', copy_custom_files)


Inject JavaScript based on user configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If your extension makes use of JavaScript, it can be useful to allow users
to control its behavior using their Sphinx configuration. However, this can
be difficult to do if your JavaScript comes in the form of a static library
(which will not be built with Jinja).

There are two ways to inject variables into the JavaScript space based on user
configuration.

First, you may append ``_t`` to the end of any static files included with your
extension. This will cause Sphinx to process these files with the templating
engine, allowing you to embed variables and control behavior.

For example, the following JavaScript structure:

.. code-block:: none

   mymodule/
   ├── _static
   │   └── myjsfile.js_t
   └── mymodule.py

Will result in the following static file placed in your HTML's build output:

.. code-block:: none

   _build/
   └── html
       └── _static
           └── myjsfile.js

See :ref:`theming-static-templates` for more information.

Second, you may use the :meth:`.Sphinx.add_js_file` method without pointing it
to a file. Normally, this method is used to insert a new JavaScript file
into your site. However, if you do *not* pass a file path, but instead pass
a string to the "body" argument, then this text will be inserted as JavaScript
into your site's head. This allows you to insert variables into your project's
JavaScript from Python.

For example, the following code will read in a user-configured value and then
insert this value as a JavaScript variable, which your extension's JavaScript
code may use:

.. code-block:: python

    # This function reads in a variable and inserts it into JavaScript
    def add_js_variable(app):
        # This is a configuration that you've specified for users in `conf.py`
        js_variable = app.config['my_javascript_variable']
        js_text = "var my_variable = '%s';" % js_variable
        app.add_js_file(None, body=js_text)
    # We connect this function to the step after the builder is initialized
    def setup(app):
        # Tell Sphinx about this configuration variable
        app.add_config_value('my_javascript_variable', 0, 'html')
        # Run the function after the builder is initialized
        app.connect('builder-inited', add_js_variable)

As a result, in your theme you can use code that depends on the presence of
this variable. Users can control the variable's value by defining it in their
:file:`conf.py` file.


.. [1] It is not an executable Python file, as opposed to :file:`conf.py`,
       because that would pose an unnecessary security risk if themes are
       shared.
