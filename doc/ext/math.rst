.. highlight:: rest

Math support in Sphinx
======================

.. module:: sphinx.ext.mathbase
   :synopsis: Common math support for imgmath and mathjax / jsmath.

.. versionadded:: 0.5

Since mathematical notation isn't natively supported by HTML in any way, Sphinx
supports math in documentation with several extensions.

The basic math support is contained in :mod:`sphinx.ext.mathbase`. Other math
support extensions should, if possible, reuse that support too.

.. note::

   :mod:`.mathbase` is not meant to be added to the :confval:`extensions` config
   value, instead, use either :mod:`sphinx.ext.imgmath` or
   :mod:`sphinx.ext.mathjax` as described below.

The input language for mathematics is LaTeX markup.  This is the de-facto
standard for plain-text math notation and has the added advantage that no
further translation is necessary when building LaTeX output.

Keep in mind that when you put math markup in **Python docstrings** read by
:mod:`autodoc <sphinx.ext.autodoc>`, you either have to double all backslashes,
or use Python raw strings (``r"raw"``).

:mod:`.mathbase` provides the following config values:

.. confval:: math_number_all

   Set this option to ``True`` if you want all displayed math to be numbered.
   The default is ``False``.

:mod:`.mathbase` defines these new markup elements:

.. rst:role:: math

   Role for inline math.  Use like this::

      Since Pythagoras, we know that :math:`a^2 + b^2 = c^2`.

.. rst:directive:: math

   Directive for displayed math (math that takes the whole line for itself).

   The directive supports multiple equations, which should be separated by a
   blank line::

      .. math::

         (a + b)^2 = a^2 + 2ab + b^2

         (a - b)^2 = a^2 - 2ab + b^2

   In addition, each single equation is set within a ``split`` environment,
   which means that you can have multiple aligned lines in an equation,
   aligned at ``&`` and separated by ``\\``::

      .. math::

         (a + b)^2  &=  (a + b)(a + b) \\
                    &=  a^2 + 2ab + b^2

   For more details, look into the documentation of the `AmSMath LaTeX
   package`_.

   When the math is only one line of text, it can also be given as a directive
   argument::

      .. math:: (a + b)^2 = a^2 + 2ab + b^2

   Normally, equations are not numbered.  If you want your equation to get a
   number, use the ``label`` option.  When given, it selects an internal label
   for the equation, by which it can be cross-referenced, and causes an equation
   number to be issued.  See :rst:role:`eqref` for an example.  The numbering
   style depends on the output format.

   There is also an option ``nowrap`` that prevents any wrapping of the given
   math in a math environment.  When you give this option, you must make sure
   yourself that the math is properly set up.  For example::

      .. math::
         :nowrap:

         \begin{eqnarray}
            y    & = & ax^2 + bx + c \\
            f(x) & = & x^2 + 2xy + y^2
         \end{eqnarray}

.. rst:role:: eq

   Role for cross-referencing equations via their label.  This currently works
   only within the same document.  Example::

      .. math:: e^{i\pi} + 1 = 0
         :label: euler

      Euler's identity, equation :eq:`euler`, was elected one of the most
      beautiful mathematical formulas.


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

   The default is the ``http://`` URL that loads the JS files from the `MathJax
   CDN <http://docs.mathjax.org/en/latest/start.html>`_.  If you want MathJax to
   be available offline, you have to download it and set this value to a
   different path.

   The path can be absolute or relative; if it is relative, it is relative to
   the ``_static`` directory of the built docs.

   For example, if you put MathJax into the static path of the Sphinx docs, this
   value would be ``MathJax/MathJax.js``.  If you host more than one Sphinx
   documentation set on one server, it is advisable to install MathJax in a
   shared location.

   You can also give a full ``http://`` URL different from the CDN URL.


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


.. _dvipng: http://savannah.nongnu.org/projects/dvipng/
.. _dvisvgm: http://dvisvgm.bplaced.net/
.. _MathJax: https://www.mathjax.org/
.. _jsMath: http://www.math.union.edu/~dpvc/jsmath/
.. _preview-latex package: http://www.gnu.org/software/auctex/preview-latex.html
.. _AmSMath LaTeX package: http://www.ams.org/publications/authors/tex/amslatex
