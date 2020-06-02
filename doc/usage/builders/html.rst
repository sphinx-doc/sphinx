=============
HTML Builders
=============

All HTML builders generate HTML output files but vary in how this output is
structured and what additional artifacts are included. Specifically, the
`Directory HTML builder`_ and `Single HTML builder`_ are variants of the
default `Standalone HTML builder`_ that generate output in different formats,
while the remaining builders generate the same output but also generate
additional files required by specific applications or use cases.


Standalone HTML builder
-----------------------

This is the standard HTML builder.  Its output is a directory with HTML files,
complete with style sheets and optionally the reST sources.  There are quite a
few configuration values that customize the output of this builder, see the
chapter :ref:`html-options` for details.

.. module:: sphinx.builders.html
.. class:: StandaloneHTMLBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Directory HTML builder
----------------------

.. versionadded:: 0.6

This is a variant of the standard HTML builder. Its output is a directory
with HTML files, where each file is called ``index.html`` and placed in a
subdirectory named like its page name.  For example, the document
``markup/rest.rst`` will not result in an output file ``markup/rest.html``,
but ``markup/rest/index.html``.  When generating links between pages, the
``index.html`` is omitted, so that the URL would look like ``markup/rest/``.

.. module:: sphinx.builders.dirhtml
.. class:: DirectoryHTMLBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Single HTML builder
-------------------

.. versionadded:: 1.0

This is an HTML builder that combines the whole project in one output file.
(Obviously this only works with smaller projects.)  The file is named like
the master document.  No indices will be generated.

.. module:: sphinx.builders.singlehtml
.. class:: SingleFileHTMLBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


HTML Help builder
-----------------

This builder produces the same output as the standalone HTML builder, but
also generates HTML Help support files that allow the Microsoft HTML Help
Workshop to compile them into a CHM file.

.. module:: sphinxcontrib.htmlhelp
.. class:: HTMLHelpBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Qt Help builder
---------------

.. versionchanged:: 2.0

   Moved to sphinxcontrib.qthelp from sphinx.builders package.

This builder produces the same output as the standalone HTML builder, but
also generates `Qt help <https://doc.qt.io/qt-5/qthelp-framework.html>`__
collection support files that allow the Qt collection generator to compile
them.

.. module:: sphinxcontrib.qthelp
.. class:: QtHelpBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


Apple Help Book builder
-----------------------

.. versionadded:: 1.3

.. versionchanged:: 2.0

   Moved to sphinxcontrib.applehelp from sphinx.builders package.

This builder produces an Apple Help Book based on the same output as the
standalone HTML builder.

If the source directory contains any ``.lproj`` folders, the one
corresponding to the selected language will have its contents merged with
the generated output.  These folders will be ignored by all other
documentation types.

In order to generate a valid help book, this builder requires the command
line tool :program:`hiutil`, which is only available on Mac OS X 10.6 and
above.  You can disable the indexing step by setting
:confval:`applehelp_disable_external_tools` to ``True``, in which case the
output will not be valid until :program:`hiutil` has been run on all of the
``.lproj`` folders within the bundle.

.. module:: sphinxcontrib.applehelp
.. class:: AppleHelpBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


GNOME Devhelp builder
---------------------

.. versionchanged:: 2.0

   Moved to sphinxcontrib.devhelp from sphinx.builders package.

This builder produces the same output as the standalone HTML builder, but
also generates `GNOME Devhelp <https://wiki.gnome.org/Apps/Devhelp>`__
support file that allows the GNOME Devhelp reader to view them.

.. module:: sphinxcontrib.devhelp
.. class:: DevhelpBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


EPUB 3 builder
--------------

.. versionadded:: 1.4

.. versionchanged:: 1.5

   Used for the default builder of the ``epub`` format.

This builder produces the same output as the standalone HTML builder, but
also generates an *EPUB* file for ebook readers.  See :ref:`epub-faq` for
details about it.  For definition of the epub format, refer to
`<http://idpf.org/epub>`__ and `<https://en.wikipedia.org/wiki/EPUB>`__.
The builder creates *EPUB 3* files.

.. module:: sphinx.builders.epub3
.. class:: Epub3Builder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types


.. _html-themes:

Themes
------

.. versionadded:: 0.6

.. note::

   This section provides information about using pre-existing HTML themes. If
   you wish to create your own theme, refer to :doc:`/theming`.

Sphinx supports changing the appearance of its HTML output via *themes*.  A
theme is a collection of HTML templates, stylesheet(s) and other static files.
Additionally, it has a configuration file which specifies from which theme to
inherit, which highlighting style to use, and what options exist for customizing
the theme's look and feel.

Themes are meant to be project-unaware, so they can be used for different
projects without change.

Usage
~~~~~

Using a :ref:`theme provided with Sphinx <builtin-themes>` is easy. Since these
do not need to be installed, you only need to set the :confval:`html_theme`
config value. For example, to enable the ``classic`` theme, add the following
to :file:`conf.py`::

    html_theme = "classic"

You can also set theme-specific options using the :confval:`html_theme_options`
config value.  These options are generally used to change the look and feel of
the theme. For example, to place the sidebar on the right side and a black
background for the relation bar (the bar with the navigation links at the
page's top and bottom), add the following :file:`conf.py`::

    html_theme_options = {
        "rightsidebar": "true",
        "relbarbgcolor": "black"
    }

If the theme does not come with Sphinx, it can be in two static forms or as a
Python package. For the static forms, either a directory (containing
:file:`theme.conf` and other needed files), or a zip file with the same
contents is supported. The directory or zipfile must be put where Sphinx can
find it; for this there is the config value :confval:`html_theme_path`. This
can be a list of directories, relative to the directory containing
:file:`conf.py`, that can contain theme directories or zip files.  For example,
if you have a theme in the file :file:`blue.zip`, you can put it right in the
directory containing :file:`conf.py` and use this configuration::

    html_theme = "blue"
    html_theme_path = ["."]

The third form is a Python package.  If a theme you want to use is distributed
as a Python package, you can use it after installing

.. code-block:: bash

    # installing theme package
    $ pip install sphinxjp.themes.dotted

Once installed, this can be used in the same manner as a directory or
zipfile-based theme::

    html_theme = "dotted"

For more information on the design of themes, including information about
writing your own themes, refer to :doc:`/theming`.

.. _builtin-themes:

Builtin themes
~~~~~~~~~~~~~~

.. cssclass:: longtable

+--------------------+--------------------+
| **Theme overview** |                    |
+--------------------+--------------------+
| |alabaster|        | |classic|          |
|                    |                    |
| *alabaster*        | *classic*          |
+--------------------+--------------------+
| |sphinxdoc|        | |scrolls|          |
|                    |                    |
| *sphinxdoc*        | *scrolls*          |
+--------------------+--------------------+
| |agogo|            | |traditional|      |
|                    |                    |
| *agogo*            | *traditional*      |
+--------------------+--------------------+
| |nature|           | |haiku|            |
|                    |                    |
| *nature*           | *haiku*            |
+--------------------+--------------------+
| |pyramid|          | |bizstyle|         |
|                    |                    |
| *pyramid*          | *bizstyle*         |
+--------------------+--------------------+

.. |alabaster|        image:: /_static/themes/alabaster.png
.. |classic|          image:: /_static/themes/classic.png
.. |sphinxdoc|        image:: /_static/themes/sphinxdoc.png
.. |scrolls|          image:: /_static/themes/scrolls.png
.. |agogo|            image:: /_static/themes/agogo.png
.. |traditional|      image:: /_static/themes/traditional.png
.. |nature|           image:: /_static/themes/nature.png
.. |haiku|            image:: /_static/themes/haiku.png
.. |pyramid|          image:: /_static/themes/pyramid.png
.. |bizstyle|         image:: /_static/themes/bizstyle.png

Sphinx comes with a selection of themes to choose from.

.. cssclass:: clear

These themes are:

**basic**
  This is a basically unstyled layout used as the base for the
  other themes, and usable as the base for custom themes as well.  The HTML
  contains all important elements like sidebar and relation bar.  There are
  these options (which are inherited by the other themes):

  - **nosidebar** (true or false): Don't include the sidebar.  Defaults to
    ``False``.

  - **sidebarwidth** (int or str): Width of the sidebar in pixels.
    This can be an int, which is interpreted as pixels or a valid CSS
    dimension string such as '70em' or '50%'.  Defaults to 230 pixels.

  - **body_min_width** (int or str): Minimal width of the document body.
    This can be an int, which is interpreted as pixels or a valid CSS
    dimension string such as '70em' or '50%'. Use 0 if you don't want
    a width limit. Defaults may depend on the theme (often 450px).

  - **body_max_width** (int or str): Maximal width of the document body.
    This can be an int, which is interpreted as pixels or a valid CSS
    dimension string such as '70em' or '50%'. Use 'none' if you don't
    want a width limit. Defaults may depend on the theme (often 800px).

  - **navigation_with_keys** (true or false): Allow navigating to the
    previous/next page using the keyboard's left and right arrows.  Defaults to
    ``False``.

  - **globaltoc_collapse** (true or false): Only expand subsections
    of the current document in ``globaltoc.html``
    (see :confval:`html_sidebars`).
    Defaults to ``True``.

    .. versionadded:: 3.1

  - **globaltoc_includehidden** (true or false): Show even those
    subsections in ``globaltoc.html`` (see :confval:`html_sidebars`)
    which have been included with the ``:hidden:`` flag of the
    :rst:dir:`toctree` directive.
    Defaults to ``False``.

    .. versionadded:: 3.1

**alabaster**
  `Alabaster theme`_ is a modified "Kr" Sphinx theme from @kennethreitz
  (especially as used in his Requests project), which was itself originally
  based on @mitsuhiko's theme used for Flask & related projects.  Refer to its
  `installation page`_ for information on how to configure
  :confval:`html_sidebars` for its use.

  .. _Alabaster theme: https://pypi.org/project/alabaster/
  .. _installation page: https://alabaster.readthedocs.io/en/latest/installation.html

**classic**
  This is the classic theme, which looks like `the Python 2
  documentation <https://docs.python.org/2/>`_.  It can be customized via
  these options:

  - **rightsidebar** (true or false): Put the sidebar on the right side.
    Defaults to ``False``.

  - **stickysidebar** (true or false): Make the sidebar "fixed" so that it
    doesn't scroll out of view for long body content.  This may not work well
    with all browsers.  Defaults to ``False``.

  - **collapsiblesidebar** (true or false): Add an *experimental* JavaScript
    snippet that makes the sidebar collapsible via a button on its side.
    Defaults to ``False``.

  - **externalrefs** (true or false): Display external links differently from
    internal links.  Defaults to ``False``.

  There are also various color and font options that can change the color scheme
  without having to write a custom stylesheet:

  - **footerbgcolor** (CSS color): Background color for the footer line.
  - **footertextcolor** (CSS color): Text color for the footer line.
  - **sidebarbgcolor** (CSS color): Background color for the sidebar.
  - **sidebarbtncolor** (CSS color): Background color for the sidebar collapse
    button (used when *collapsiblesidebar* is ``True``).
  - **sidebartextcolor** (CSS color): Text color for the sidebar.
  - **sidebarlinkcolor** (CSS color): Link color for the sidebar.
  - **relbarbgcolor** (CSS color): Background color for the relation bar.
  - **relbartextcolor** (CSS color): Text color for the relation bar.
  - **relbarlinkcolor** (CSS color): Link color for the relation bar.
  - **bgcolor** (CSS color): Body background color.
  - **textcolor** (CSS color): Body text color.
  - **linkcolor** (CSS color): Body link color.
  - **visitedlinkcolor** (CSS color): Body color for visited links.
  - **headbgcolor** (CSS color): Background color for headings.
  - **headtextcolor** (CSS color): Text color for headings.
  - **headlinkcolor** (CSS color): Link color for headings.
  - **codebgcolor** (CSS color): Background color for code blocks.
  - **codetextcolor** (CSS color): Default text color for code blocks, if not
    set differently by the highlighting style.

  - **bodyfont** (CSS font-family): Font for normal text.
  - **headfont** (CSS font-family): Font for headings.

**sphinxdoc**
  The theme originally used by this documentation. It features
  a sidebar on the right side. There are currently no options beyond
  *nosidebar* and *sidebarwidth*.

  .. note::

    The Sphinx documentation now uses
    `an adjusted version of the sphinxdoc theme
    <https://github.com/sphinx-doc/sphinx/tree/master/doc/_themes/sphinx13>`_.

**scrolls**
  A more lightweight theme, based on `the Jinja documentation
  <http://jinja.pocoo.org/>`_.  The following color options are available:

  - **headerbordercolor**
  - **subheadlinecolor**
  - **linkcolor**
  - **visitedlinkcolor**
  - **admonitioncolor**

**agogo**
  A theme created by Andi Albrecht.  The following options are supported:

  - **bodyfont** (CSS font family): Font for normal text.
  - **headerfont** (CSS font family): Font for headings.
  - **pagewidth** (CSS length): Width of the page content, default 70em.
  - **documentwidth** (CSS length): Width of the document (without sidebar),
    default 50em.
  - **sidebarwidth** (CSS length): Width of the sidebar, default 20em.
  - **rightsidebar** (true or false): Put the sidebar on the right side.
    Defaults to ``True``.
  - **bgcolor** (CSS color): Background color.
  - **headerbg** (CSS value for "background"): background for the header area,
    default a grayish gradient.
  - **footerbg** (CSS value for "background"): background for the footer area,
    default a light gray gradient.
  - **linkcolor** (CSS color): Body link color.
  - **headercolor1**, **headercolor2** (CSS color): colors for <h1> and <h2>
    headings.
  - **headerlinkcolor** (CSS color): Color for the backreference link in
    headings.
  - **textalign** (CSS *text-align* value): Text alignment for the body, default
    is ``justify``.

**nature**
  A greenish theme.  There are currently no options beyond
  *nosidebar* and *sidebarwidth*.

**pyramid**
  A theme from the Pyramid web framework project, designed by Blaise Laflamme.
  There are currently no options beyond *nosidebar* and *sidebarwidth*.

**haiku**
  A theme without sidebar inspired by the `Haiku OS user guide
  <https://www.haiku-os.org/docs/userguide/en/contents.html>`_.  The following
  options are supported:

  - **full_logo** (true or false, default ``False``): If this is true, the
    header will only show the :confval:`html_logo`.  Use this for large logos.
    If this is false, the logo (if present) will be shown floating right, and
    the documentation title will be put in the header.

  - **textcolor**, **headingcolor**, **linkcolor**, **visitedlinkcolor**,
    **hoverlinkcolor** (CSS colors): Colors for various body elements.

**traditional**
  A theme resembling the old Python documentation.  There are
  currently no options beyond *nosidebar* and *sidebarwidth*.

**epub**
  A theme for the epub builder.  This theme tries to save visual
  space which is a sparse resource on ebook readers.  The following options
  are supported:

  - **relbar1** (true or false, default ``True``): If this is true, the
    `relbar1` block is inserted in the epub output, otherwise it is omitted.

  - **footer**  (true or false, default ``True``): If this is true, the
    `footer` block is inserted in the epub output, otherwise it is omitted.

**bizstyle**
  A simple bluish theme. The following options are supported
  beyond *nosidebar* and *sidebarwidth*:

  - **rightsidebar** (true or false): Put the sidebar on the right side.
    Defaults to ``False``.

.. versionadded:: 1.3
   'alabaster', 'sphinx_rtd_theme' and 'bizstyle' theme.

.. versionchanged:: 1.3
   The 'default' theme has been renamed to 'classic'. 'default' is still
   available, however it will emit a notice that it is an alias for the new
   'alabaster' theme.

Third Party Themes
~~~~~~~~~~~~~~~~~~

.. cssclass:: longtable

+--------------------+--------------------+
| **Theme overview** |                    |
+--------------------+--------------------+
| |sphinx_rtd_theme| |                    |
|                    |                    |
| *sphinx_rtd_theme* |                    |
+--------------------+--------------------+

.. |sphinx_rtd_theme| image:: /_static/themes/sphinx_rtd_theme.png

There are many third-party themes available. Some of these are general use,
while others are specific to an individual project. A section of third-party
themes is listed below. Many more can be found on PyPI__, GitHub__ and
sphinx-themes.org__.

.. cssclass:: clear

**sphinx_rtd_theme**
  `Read the Docs Sphinx Theme`_.
  This is a mobile-friendly sphinx theme that was made for readthedocs.org.
  View a working demo over on readthedocs.org. You can get install and options
  information at `Read the Docs Sphinx Theme`_ page.

  .. _Read the Docs Sphinx Theme: https://pypi.org/project/sphinx_rtd_theme/

  .. versionchanged:: 1.4
     **sphinx_rtd_theme** has become optional.

.. __: https://pypi.org/search/?q=&o=&c=Framework+%3A%3A+Sphinx+%3A%3A+Theme
.. __: https://github.com/search?utf8=%E2%9C%93&q=sphinx+theme&type=
.. __: https://sphinx-themes.org/
