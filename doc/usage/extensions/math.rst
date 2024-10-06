.. highlight:: rst

.. _math-support:

Math support for HTML outputs in Sphinx
=======================================

.. module:: sphinx.ext.mathbase
   :synopsis: Common math support for imgmath and mathjax / jsmath.

.. versionadded:: 0.5
.. versionchanged:: 1.8

   Math support for non-HTML builders is integrated to sphinx-core.
   So mathbase extension is no longer needed.

Since mathematical notation isn't natively supported by HTML in any way, Sphinx
gives a math support to HTML document with several extensions.  These use the
reStructuredText math :rst:dir:`directive <math>` and :rst:role:`role <math>`.

:mod:`sphinx.ext.imgmath` -- Render math as images
--------------------------------------------------

.. module:: sphinx.ext.imgmath
   :synopsis: Render math as PNG or SVG images.

.. versionadded:: 1.4

This extension renders math via LaTeX and dvipng_ or dvisvgm_ into PNG or SVG
images. This of course means that the computer where the docs are built must
have both programs available.

There are various configuration values you can set to influence how the images
are built:

.. confval:: imgmath_image_format

   The output image format. The default is ``'png'``. It should be either
   ``'png'`` or ``'svg'``. The image is produced by first executing ``latex``
   on the TeX mathematical mark-up then (depending on the requested format)
   either `dvipng`_ or `dvisvgm`_.

.. confval:: imgmath_use_preview

   ``dvipng`` and ``dvisvgm`` both have the ability to collect from LaTeX the
   "depth" of the rendered math: an inline image should use this "depth" in a
   ``vertical-align`` style to get correctly aligned with surrounding text.

   This mechanism requires the `LaTeX preview package`_ (available as
   ``preview-latex-style`` on Ubuntu xenial).  Therefore, the default for this
   option is ``False`` but it is strongly recommended to set it to ``True``.

   .. versionchanged:: 2.2

      This option can be used with the ``'svg'`` :confval:`imgmath_image_format`.

.. confval:: imgmath_add_tooltips

   Default: ``True``.  If false, do not add the LaTeX code as an "alt" attribute
   for math images.

.. confval:: imgmath_font_size

   The font size (in ``pt``) of the displayed math.  The default value is
   ``12``.  It must be a positive integer.

.. confval:: imgmath_latex

   The command name with which to invoke LaTeX.  The default is ``'latex'``; you
   may need to set this to a full path if ``latex`` is not in the executable
   search path.

   Since this setting is not portable from system to system, it is normally not
   useful to set it in ``conf.py``; rather, giving it on the
   :program:`sphinx-build` command line via the :option:`-D <sphinx-build -D>`
   option should be preferable, like this::

      sphinx-build -M html -D imgmath_latex=C:\tex\latex.exe . _build

   This value should only contain the path to the latex executable, not further
   arguments; use :confval:`imgmath_latex_args` for that purpose.

   .. hint::

      To use `OpenType Math fonts`__ with ``unicode-math``, via a custom
      :confval:`imgmath_latex_preamble`, you can set :confval:`imgmath_latex`
      to ``'dvilualatex'``, but must then set :confval:`imgmath_image_format`
      to ``'svg'``.  Note: this has only been tested with ``dvisvgm 3.0.3``.
      It significantly increases image production duration compared to using
      standard ``'latex'`` with traditional TeX math fonts.

      __ https://tex.stackexchange.com/questions/425098/which-opentype-math-fonts-are-available


   .. hint::

      Some fancy LaTeX mark-up (an example was reported which used TikZ to add
      various decorations to the equation) require multiple runs of the LaTeX
      executable.  To handle this, set this configuration setting to
      ``'latexmk'`` (or a full path to it) as this Perl script reliably
      chooses dynamically how many latex runs are needed.

   .. versionchanged:: 6.2.0

      Using ``'xelatex'`` (or a full path to it) is now supported.  But you
      must then add ``'-no-pdf'`` to the :confval:`imgmath_latex_args` list of
      the command options.  The ``'svg'`` :confval:`imgmath_image_format` is
      required.  Also, you may need the ``dvisvgm`` binary to be relatively
      recent (testing was done only with its ``3.0.3`` release).

      .. note::

         Regarding the previous note, it is currently not supported to use
         ``latexmk`` with option ``-xelatex``.

.. confval:: imgmath_latex_args

   Additional arguments to give to latex, as a list.  The default is an empty
   list.

.. confval:: imgmath_latex_preamble

   Additional LaTeX code to put into the preamble of the LaTeX files used to
   translate the math snippets.  This is left empty by default.  Use it
   e.g. to add packages which modify the fonts used for math, such as
   ``'\\usepackage{newtxsf}'`` for sans-serif fonts, or
   ``'\\usepackage{fouriernc}'`` for serif fonts.  Indeed, the default LaTeX
   math fonts have rather thin glyphs which (in HTML output) often do not
   match well with the font for text.

.. confval:: imgmath_dvipng

   The command name to invoke ``dvipng``.  The default is
   ``'dvipng'``; you may need to set this to a full path if ``dvipng`` is not in
   the executable search path. This option is only used when
   ``imgmath_image_format`` is set to ``'png'``.

.. confval:: imgmath_dvipng_args

   Additional arguments to give to dvipng, as a list.  The default value is
   ``['-gamma', '1.5', '-D', '110', '-bg', 'Transparent']`` which makes the
   image a bit darker and larger then it is by default (this compensates
   somewhat for the thinness of default LaTeX math fonts), and produces PNGs with a
   transparent background.  This option is used only when
   ``imgmath_image_format`` is ``'png'``.

.. confval:: imgmath_dvisvgm

   The command name to invoke ``dvisvgm``.  The default is
   ``'dvisvgm'``; you may need to set this to a full path if ``dvisvgm`` is not
   in the executable search path.  This option is only used when
   ``imgmath_image_format`` is ``'svg'``.

.. confval:: imgmath_dvisvgm_args

   Additional arguments to give to dvisvgm, as a list. The default value is
   ``['--no-fonts']``, which means that ``dvisvgm`` will render glyphs as path
   elements (cf the `dvisvgm FAQ`_). This option is used only when
   ``imgmath_image_format`` is ``'svg'``.

.. confval:: imgmath_embed

   Default: ``False``.  If true, encode LaTeX output images within HTML files
   (base64 encoded) and do not save separate png/svg files to disk.

   .. versionadded:: 5.2

:mod:`sphinx.ext.mathjax` -- Render math via JavaScript
-------------------------------------------------------

.. module:: sphinx.ext.mathjax
   :synopsis: Render math using JavaScript via MathJax.

.. warning::
   Version 4.0 changes the version of MathJax used to version 3. You may need to
   override ``mathjax_path`` to
   ``https://cdn.jsdelivr.net/npm/mathjax@2/MathJax.js?config=TeX-AMS-MML_HTMLorMML``
   or update your configuration options for version 3
   (see :confval:`mathjax3_config`).

.. versionadded:: 1.1

This extension puts math as-is into the HTML files.  The JavaScript package
MathJax_ is then loaded and transforms the LaTeX markup to readable math live in
the browser.

Because MathJax (and the necessary fonts) is very large, it is not included in
Sphinx but is set to automatically include it from a third-party site.

.. attention::

   You should use the math :rst:dir:`directive <math>` and
   :rst:role:`role <math>`, not the native MathJax ``$$``, ``\(``, etc.


.. confval:: mathjax_path

   The path to the JavaScript file to include in the HTML files in order to load
   MathJax.

   The default is the ``https://`` URL that loads the JS files from the
   `jsdelivr`__ Content Delivery Network. See the `MathJax Getting Started
   page`__ for details. If you want MathJax to be available offline or
   without including resources from a third-party site, you have to
   download it and set this value to a different path.

   __ https://www.jsdelivr.com/

   __ https://www.mathjax.org/#gettingstarted

   The path can be absolute or relative; if it is relative, it is relative to
   the ``_static`` directory of the built docs.

   For example, if you put MathJax into the static path of the Sphinx docs, this
   value would be ``MathJax/MathJax.js``.  If you host more than one Sphinx
   documentation set on one server, it is advisable to install MathJax in a
   shared location.

   You can also give a full ``https://`` URL different from the CDN URL.

.. confval:: mathjax_options

   The options to script tag for mathjax.  For example, you can set integrity
   option with following setting::

       mathjax_options = {
           'integrity': 'sha384-......',
       }

   The default is empty (``{}``).

   .. versionadded:: 1.8

   .. versionchanged:: 4.4.1

      Allow to change the loading method (async or defer) of MathJax if "async"
      or "defer" key is set.

.. confval:: mathjax3_config

   The configuration options for MathJax v3 (which is used by default).
   The given dictionary is assigned to the JavaScript variable
   ``window.MathJax``.
   For more information, please read `Configuring MathJax`__.

   __ https://docs.mathjax.org/en/latest/web/configuration.html#configuration

   The default is empty (not configured).

   .. versionadded:: 4.0

.. confval:: mathjax2_config

   The configuration options for MathJax v2 (which can be loaded via
   :confval:`mathjax_path`).
   The value is used as a parameter of ``MathJax.Hub.Config()``.
   For more information, please read `Using in-line configuration options`__.

   __ https://docs.mathjax.org/en/v2.7-latest/
      configuration.html#using-in-line-configuration-options

   For example::

       mathjax2_config = {
           'extensions': ['tex2jax.js'],
           'jax': ['input/TeX', 'output/HTML-CSS'],
       }

   The default is empty (not configured).

   .. versionadded:: 4.0

      :confval:`mathjax_config` has been renamed to :confval:`mathjax2_config`.

.. confval:: mathjax_config

   Former name of :confval:`mathjax2_config`.

   For help converting your old MathJax configuration to to the new
   :confval:`mathjax3_config`, see `Converting Your v2 Configuration to v3`__.

   __ https://docs.mathjax.org/en/latest/web/
      configuration.html#converting-your-v2-configuration-to-v3

   .. versionadded:: 1.8

   .. versionchanged:: 4.0

      This has been renamed to :confval:`mathjax2_config`.
      :confval:`mathjax_config` is still supported for backwards compatibility.

:mod:`sphinx.ext.jsmath` -- Render math via JavaScript
------------------------------------------------------

.. module:: sphinx.ext.jsmath
   :synopsis: Render math using JavaScript via JSMath.

This extension works just as the MathJax extension does, but uses the older
package jsMath_.  It provides this config value:

.. confval:: jsmath_path

   The path to the JavaScript file to include in the HTML files in order to load
   JSMath.  There is no default.

   The path can be absolute or relative; if it is relative, it is relative to
   the ``_static`` directory of the built docs.

   For example, if you put JSMath into the static path of the Sphinx docs, this
   value would be ``jsMath/easy/load.js``.  If you host more than one
   Sphinx documentation set on one server, it is advisable to install jsMath in
   a shared location.


.. _dvipng: https://savannah.nongnu.org/projects/dvipng/
.. _dvisvgm: https://dvisvgm.de/
.. _dvisvgm FAQ: https://dvisvgm.de/FAQ
.. _MathJax: https://www.mathjax.org/
.. _jsMath: https://www.math.union.edu/~dpvc/jsmath/
.. _LaTeX preview package: https://www.gnu.org/software/auctex/preview-latex.html
