.. highlight:: python

HTML theming support
====================

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

The :doc:`guide to templating <templating>` is helpful if you want to write your
own templates.  What is important to keep in mind is the order in which Sphinx
searches for templates:

* First, in the user's ``templates_path`` directories.
* Then, in the selected theme.
* Then, in its base theme, its base's base theme, etc.

When extending a template in the base theme with the same name, use the theme
name as an explicit directory: ``{% extends "basic/layout.html" %}``.  From a
user ``templates_path`` template, you can still use the "exclamation mark"
syntax as described in the templating document.

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

.. [1] It is not an executable Python file, as opposed to :file:`conf.py`,
       because that would pose an unnecessary security risk if themes are
       shared.
