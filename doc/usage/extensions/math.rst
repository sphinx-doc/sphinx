.. highlight:: rest

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
gives a math support to HTML document with several extensions.

:mod:`sphinx.ext.imgmath` -- Render math as images
--------------------------------------------------

.. module:: sphinx.ext.imgmath
   :synopsis: Render math as PNG or SVG images.

.. versionadded:: 1.4

This extension renders math via LaTeX and dvipng_ or dvisvgm_ into PNG or SVG
images. This of course means that the computer where the docs are built must
have both programs available.

There are various config values you can set to influence how the images are
built:

.. confval:: imgmath_image_format

   The output image format. The default is ``'png'``.  It should be either
   ``'png'`` or ``'svg'``.

.. confval:: imgmath_latex

   The command name with which to invoke LaTeX.  The default is ``'latex'``; you
   may need to set this to a full path if ``latex`` is not in the executable
   search path.

   Since this setting is not portable from system to system, it is normally not
   useful to set it in ``conf.py``; rather, giving it on the
   :program:`sphinx-build` command line via the :option:`-D <sphinx-build -D>`
   option should be preferable, like this::

      sphinx-build -b html -D imgmath_latex=C:\tex\latex.exe . _build/html

   This value should only contain the path to the latex executable, not further
   arguments; use :confval:`imgmath_latex_args` for that purpose.

.. confval:: imgmath_dvipng

   The command name with which to invoke ``dvipng``.  The default is
   ``'dvipng'``; you may need to set this to a full path if ``dvipng`` is not in
   the executable search path. This option is only used when
   ``imgmath_image_format`` is set to ``'png'``.

.. confval:: imgmath_dvisvgm

   The command name with which to invoke ``dvisvgm``.  The default is
   ``'dvisvgm'``; you may need to set this to a full path if ``dvisvgm`` is not
   in the executable search path.  This option is only used when
   ``imgmath_image_format`` is ``'svg'``.

.. confval:: imgmath_latex_args

   Additional arguments to give to latex, as a list.  The default is an empty
   list.

.. confval:: imgmath_latex_preamble

   Additional LaTeX code to put into the preamble of the short LaTeX files that
   are used to translate the math snippets.  This is empty by default.  Use it
   e.g. to add more packages whose commands you want to use in the math.

.. confval:: imgmath_dvipng_args

   Additional arguments to give to dvipng, as a list.  The default value is
   ``['-gamma', '1.5', '-D', '110', '-bg', 'Transparent']`` which makes the
   image a bit darker and larger then it is by default, and produces PNGs with a
   transparent background.  This option is used only when
   ``imgmath_image_format`` is ``'png'``.

.. confval:: imgmath_dvisvgm_args

   Additional arguments to give to dvisvgm, as a list.  The default value is
   ``['--no-fonts']``.  This option is used only when ``imgmath_image_format``
   is ``'svg'``.

.. confval:: imgmath_use_preview

   ``dvipng`` has the ability to determine the "depth" of the rendered text: for
   example, when typesetting a fraction inline, the baseline of surrounding text
   should not be flush with the bottom of the image, rather the image should
   extend a bit below the baseline.  This is what TeX calls "depth".  When this
   is enabled, the images put into the HTML document will get a
   ``vertical-align`` style that correctly aligns the baselines.

   Unfortunately, this only works when the `preview-latex package`_ is
   installed. Therefore, the default for this option is ``False``.

   Currently this option is only used when ``imgmath_image_format`` is
   ``'png'``.

.. confval:: imgmath_add_tooltips

   Default: ``True``.  If false, do not add the LaTeX code as an "alt" attribute
   for math images.

.. confval:: imgmath_font_size

   The font size (in ``pt``) of the displayed math.  The default value is
   ``12``.  It must be a positive integer.


:mod:`sphinx.ext.mathjax` -- Render math via JavaScript
-------------------------------------------------------

.. module:: sphinx.ext.mathjax
   :synopsis: Render math using JavaScript via MathJax.

.. versionadded:: 1.1

This extension puts math as-is into the HTML files.  The JavaScript package
MathJax_ is then loaded and transforms the LaTeX markup to readable math live in
the browser.

Because MathJax (and the necessary fonts) is very large, it is not included in
Sphinx.

.. confval:: mathjax_path

   The path to the JavaScript file to include in the HTML files in order to load
   MathJax.

   The default is the ``https://`` URL that loads the JS files from the
   `cdnjs`__ Content Delivery Network. See the `MathJax Getting Started
   page`__ for details. If you want MathJax to be available offline, you have
   to download it and set this value to a different path.

   __ https://cdnjs.com

   __ https://docs.mathjax.org/en/latest/start.html

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

.. confval:: mathjax_config

   The inline configuration options for mathjax.  The value is used as a
   parameter of ``MathJax.Hub.Config()``.  For more information, please
   read `Using in-line configuration options`_.

   For example::

       mathjax_config = {
           'extensions': ['tex2jax.js'],
           'jax': ['input/TeX', 'output/HTML-CSS'],
       }

   The default is empty (not configured).

.. _Using in-line configuration options: https://docs.mathjax.org/en/latest/configuration.html#using-in-line-configuration-options

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
.. _dvisvgm: http://dvisvgm.bplaced.net/
.. _MathJax: https://www.mathjax.org/
.. _jsMath: http://www.math.union.edu/~dpvc/jsmath/
.. _preview-latex package: https://www.gnu.org/software/auctex/preview-latex.html
