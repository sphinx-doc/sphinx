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

* A :file:`theme.conf` file.
* HTML templates, if needed.
* A ``static/`` directory containing any static files that will be copied to the
  output static directory on build.  These can be images, styles, script files.

The :file:`theme.conf` file is in INI format [1]_ (readable by the standard
Python :mod:`ConfigParser` module) and has the following structure:

.. sourcecode:: ini

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

* The **stylesheet** setting gives the name of a CSS file which will be
  referenced in the HTML header.  If you need more than one CSS file, either
  include one from the other via CSS' ``@import``, or use a custom HTML template
  that adds ``<link rel="stylesheet">`` tags as necessary.  Setting the
  :confval:`html_style` config value will override this setting.

* The **pygments_style** setting gives the name of a Pygments style to use for
  highlighting.  This can be overridden by the user in the
  :confval:`pygments_style` config value.

* The **pygments_dark_style** setting gives the name of a Pygments style to use
  for highlighting when the CSS media query ``(prefers-color-scheme: dark)``
  evaluates to true. It is injected into the page using
  :meth:`~Sphinx.add_css_file()`.

* The **sidebars** setting gives the comma separated list of sidebar templates
  for constructing sidebars.  This can be overridden by the user in the
  :confval:`html_sidebars` config value.

* The **options** section contains pairs of variable names and default values.
  These options can be overridden by the user in :confval:`html_theme_options`
  and are accessible from all templates as ``theme_<name>``.

.. versionadded:: 1.7
   sidebar settings


.. _distribute-your-theme:

Distribute your theme as a Python package
-----------------------------------------

As a way to distribute your theme, you can use Python package.  Python package
brings to users easy setting up ways.

To distribute your theme as a Python package, please define an entry point
called ``sphinx.html_themes`` in your ``setup.py`` file, and write a ``setup()``
function to register your themes using ``add_html_theme()`` API in it::

    # 'setup.py'
    setup(
        ...
        entry_points = {
            'sphinx.html_themes': [
                'name_of_theme = your_package',
            ]
        },
        ...
    )

    # 'your_package.py'
    from os import path

    def setup(app):
        app.add_html_theme('name_of_theme', path.abspath(path.dirname(__file__)))

If your theme package contains two or more themes, please call
``add_html_theme()`` twice or more.

.. versionadded:: 1.2
   'sphinx_themes' entry_points feature.

.. deprecated:: 1.6
   ``sphinx_themes`` entry_points has been deprecated.

.. versionadded:: 1.6
   ``sphinx.html_themes`` entry_points feature.


Templating
----------

The :doc:`guide to templating </templating>` is helpful if you want to write your
own templates.  What is important to keep in mind is the order in which Sphinx
searches for templates:

* First, in the user's ``templates_path`` directories.
* Then, in the selected theme.
* Then, in its base theme, its base's base theme, etc.

When extending a template in the base theme with the same name, use the theme
name as an explicit directory: ``{% extends "basic/layout.html" %}``.  From a
user ``templates_path`` template, you can still use the "exclamation mark"
syntax as described in the templating document.


.. _theming-static-templates:

Static templates
~~~~~~~~~~~~~~~~

Since theme options are meant for the user to configure a theme more easily,
without having to write a custom stylesheet, it is necessary to be able to
template static files as well as HTML files.  Therefore, Sphinx supports
so-called "static templates", like this:

If the name of a file in the ``static/`` directory of a theme (or in the user's
static path, for that matter) ends with ``_t``, it will be processed by the
template engine.  The ``_t`` will be left from the final file name.  For
example, the *classic* theme has a file ``static/classic.css_t`` which uses
templating to put the color options into the stylesheet.  When a documentation
is built with the classic theme, the output directory will contain a
``_static/classic.css`` file where all template tags have been processed.


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

Within the registration function, define the template function that you'd like to use
within Jinja. The template function should return a string or Python objects (lists,
dictionaries) with strings inside that Jinja uses in the templating process

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

If you are packaging your own build assets with an extension
(e.g., a CSS or JavaScript file), you need to ensure that they are placed
in the ``_static/`` folder of HTML outputs. To do so, you may copy them directly
into a build's ``_static/`` folder at build time, generally via an event hook.
Here is some sample code to accomplish this:

.. code-block:: python

   def copy_custom_files(app, exc):
       if app.builder.format == 'html' and not exc:
           staticdir = path.join(app.builder.outdir, '_static')
           copy_asset_file('path/to/myextension/_static/myjsfile.js', staticdir)

   def setup(app):
       app.connect('builder-inited', copy_custom_files)


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

.. code-block:: bash

   mymodule/
   ├── _static
   │   └── myjsfile.js_t
   └── mymodule.py

Will result in the following static file placed in your HTML's build output:

.. code-block:: bash

   _build/
   └── html
       └── _static
           └── myjsfile.js

See :ref:`theming-static-templates` for more information.

Second, you may use the :meth:`Sphinx.add_js_file` method without pointing it
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
        app.add_config_value('my_javascript_variable')
        # Run the function after the builder is initialized
        app.connect('builder-inited', add_js_variable)

As a result, in your theme you can use code that depends on the presence of
this variable. Users can control the variable's value by defining it in their
:file:`conf.py` file.


.. [1] It is not an executable Python file, as opposed to :file:`conf.py`,
       because that would pose an unnecessary security risk if themes are
       shared.
