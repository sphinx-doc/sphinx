.. highlightlang:: python

HTML theming support
====================

.. versionadded:: 0.6

Sphinx supports changing the appearance of its HTML output via *themes*.  A
theme is a collection of HTML templates, stylesheet(s) and other static files.
Additionally, it has a configuration file which specifies from which theme to
inherit, which highlighting style to use, and what options exist for customizing
the theme's look and feel.

Themes are meant to be project-unaware, so they can be used for different
projects without change.


Using a theme
-------------

Using an existing theme is easy.  If the theme is builtin to Sphinx, you only
need to set the :confval:`html_theme` config value.  With the
:confval:`html_theme_options` config value you can set theme-specific options
that change the look and feel.  For example, you could have the following in
your :file:`conf.py`::

    html_theme = "default"
    html_theme_options = {
        "rightsidebar": "true",
        "relbarbgcolor: "black"
    }

That would give you the default theme, but with a sidebar on the right side and
a black background for the relation bar (the bar with the navigation links at
the page's top and bottom).

If the theme does not come with Sphinx, it can be in two forms: either a
directory (containing :file:`theme.conf` and other needed files), or a zip file
with the same contents.  Either of them must be put where Sphinx can find it;
for this there is the config value :confval:`html_theme_path`.  It gives a list
of directories, relative to the directory containing :file:`conf.py`, that can
contain theme directories or zip files.  For example, if you have a theme in the
file :file:`blue.zip`, you can put it right in the directory containing
:file:`conf.py` and use this configuration::

    html_theme = "blue"
    html_theme_path = ["."]


.. _builtin-themes:

Builtin themes
--------------

Sphinx comes with a selection of themes to choose from:

* **basic** -- This is a basically unstyled layout used as the base for the
  *default* and *sphinxdoc* themes, and usable as the base for custom themes as
  well.  The HTML contains all important elements like sidebar and relation bar.
  There is one option (which is inherited by *default* and *sphinxdoc*):

  - **nosidebar** (true or false): Don't include the sidebar.  Defaults to
    false.

* **default** -- This is the default theme.  It can be customized via these
  options:

  - **rightsidebar** (true or false): Put the sidebar on the right side.
    Defaults to false.

  - **stickysidebar** (true or false): Make the sidebar "fixed" so that it
    doesn't scroll out of view for long body content.  This may not work well
    with all browsers.  Defaults to false.

  There are also various color and font options that can change the color scheme
  without having to write a custom stylesheet:

  - **footerbgcolor** (CSS color): Background color for the footer line.
  - **footertextcolor** (CSS color): Text color for the footer line.
  - **sidebarbgcolor** (CSS color): Background color for the sidebar.
  - **sidebartextcolor** (CSS color): Text color for the sidebar.
  - **sidebarlinkcolor** (CSS color): Link color for the sidebar.
  - **relbarbgcolor** (CSS color): Background color for the relation bar.
  - **relbartextcolor** (CSS color): Text color for the relation bar.
  - **relbarlinkcolor** (CSS color): Link color for the relation bar.
  - **bgcolor** (CSS color): Body background color.
  - **textcolor** (CSS color): Body text color.
  - **linkcolor** (CSS color): Body link color.
  - **headcolor** (CSS color): Text color for headings.
  - **codebgcolor** (CSS color): Background color for code blocks.
  - **codetextcolor** (CSS color): Default text color for code blocks, if not
    set differently by the highlighting style.

  - **bodyfont** (CSS font-family): Font for normal text.
  - **headfont** (CSS font-family): Font for headings.

* **sphinxdoc** -- The theme used for this documentation.  It features a sidebar
  on the right side.  There are currently no options beyond *nosidebar*.

..
 * option specs
 * zipfiles
 * old config values work
 * static/
 * theme.conf
 * _t templates

