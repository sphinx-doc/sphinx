.. highlight:: rest

Math support in Sphinx
======================

.. module:: sphinx.ext.mathbase
   :synopsis: Common math support for pngmath and jsmath.

.. versionadded:: 0.5

Since mathematical notation isn't natively supported by HTML in any way, Sphinx
supports math in documentation with two extensions.

The basic math support that is common to both extensions is contained in
:mod:`sphinx.ext.mathbase`.  Other math support extensions should,
if possible, reuse that support too.

.. note::

   :mod:`sphinx.ext.mathbase` is not meant to be added to the
   :confval:`extensions` config value, instead, use either
   :mod:`sphinx.ext.pngmath` or :mod:`sphinx.ext.jsmath` as described below.

The input language for mathematics is LaTeX markup.  This is the de-facto
standard for plain-text math notation and has the added advantage that no
further translation is necessary when building LaTeX output.

:mod:`mathbase` defines these new markup elements:

.. role:: math

   Role for inline math.  Use like this::

      Since Pythagoras, we know that :math:`a^2 + b^2 = c^2`.

.. directive:: math

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
   number, use the ``label`` option.  When given, it selects a label for the
   equation, by which it can be cross-referenced, and causes an equation number
   to be issued.  See :role:`eqref` for an example.  The numbering style depends
   on the output format.

   There is also an option ``nowrap`` that prevents any wrapping of the given
   math in a math environment.  When you give this option, you must make sure
   yourself that the math is properly set up.  For example::

      .. math::
         :nowrap:

         \begin{eqnarray}
            y    & = & ax^2 + bx + c \\
            f(x) & = & x^2 + 2xy + y^2
         \end{eqnarray}

.. role:: eq

   Role for cross-referencing equations via their label.  This currently works
   only within the same document.  Example::

      .. math:: e^{i\pi} + 1 = 0
         :label: euler

      Euler's identity, equation :eq:`euler`, was elected one of the most
      beautiful mathematical formulas.


:mod:`sphinx.ext.pngmath` -- Render math as PNG images
------------------------------------------------------

.. module:: sphinx.ext.pngmath
   :synopsis: Render math as PNG images.

This extension renders math via LaTeX and dvipng_ into PNG images.  This of
course means that the computer where the docs are built must have both programs
available.

There are various config values you can set to influence how the images are built:

.. confval:: pngmath_latex

   The command name with which to invoke LaTeX.  The default is ``'latex'``; you
   may need to set this to a full path if ``latex`` is not in the executable
   search path.

   Since this setting is not portable from system to system, it is normally not
   useful to set it in ``conf.py``; rather, giving it on the
   :program:`sphinx-build` command line via the :option:`-D` option should be
   preferable, like this::

      sphinx-build -b html -D pngmath_latex=C:\tex\latex.exe . _build/html

   .. versionchanged:: 0.5.1
      This value should only contain the path to the latex executable, not
      further arguments; use :confval:`pngmath_latex_args` for that purpose.

.. confval:: pngmath_dvipng

   The command name with which to invoke ``dvipng``.  The default is
   ``'dvipng'``; you may need to set this to a full path if ``dvipng`` is not in
   the executable search path.

.. confval:: pngmath_latex_args

   Additional arguments to give to latex, as a list.  The default is an empty
   list.

   .. versionadded:: 0.5.1

.. confval:: pngmath_latex_preamble

   Additional LaTeX code to put into the preamble of the short LaTeX files that
   are used to translate the math snippets.  This is empty by default.  Use it
   e.g. to add more packages whose commands you want to use in the math.

.. confval:: pngmath_dvipng_args

   Additional arguments to give to dvipng, as a list.  The default value is
   ``['-gamma 1.5', '-D 110']`` which makes the image a bit darker and larger
   then it is by default.

   An arguments you might want to add here is e.g. ``'-bg Transparent'``,
   which produces PNGs with a transparent background.  This is not enabled by
   default because some Internet Explorer versions don't like transparent PNGs.

   .. note::

      When you "add" an argument, you need to reproduce the default arguments if
      you want to keep them; that is, like this::

         pngmath_dvipng_args = ['-gamma 1.5', '-D 110', '-bg Transparent']

.. confval:: pngmath_use_preview

   ``dvipng`` has the ability to determine the "depth" of the rendered text: for
   example, when typesetting a fraction inline, the baseline of surrounding text
   should not be flush with the bottom of the image, rather the image should
   extend a bit below the baseline.  This is what TeX calls "depth".  When this
   is enabled, the images put into the HTML document will get a
   ``vertical-align`` style that correctly aligns the baselines.

   Unfortunately, this only works when the `preview-latex package`_ is
   installed.  Therefore, the default for this option is ``False``.


:mod:`sphinx.ext.jsmath` -- Render math via JavaScript
------------------------------------------------------

.. module:: sphinx.ext.jsmath
   :synopsis: Render math via JavaScript.

This extension puts math as-is into the HTML files.  The JavaScript package
jsMath_ is then loaded and transforms the LaTeX markup to readable math live in
the browser.

Because jsMath (and the necessary fonts) is very large, it is not included in
Sphinx.  You must install it yourself, and give Sphinx its path in this config
value:

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
.. _jsMath: http://www.math.union.edu/~dpvc/jsmath/
.. _preview-latex package: http://www.gnu.org/software/auctex/preview-latex.html
.. _AmSMath LaTeX package: http://www.ams.org/tex/amslatex.html
