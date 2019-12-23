==============
LaTeX Builders
==============

LaTeX builder
-------------

.. versionchanged:: 1.6
   ``make latexpdf`` now uses ``latexmk`` on \*nix platforms.

.. versionchanged:: 1.6
   TeXLive 2013 is now required.

.. versionchanged:: 2.0
   TeXLive 2015 is now required.

This builder produces a bunch of LaTeX files in the output directory.  You
have to specify which documents are to be included in which LaTeX files via
the :confval:`latex_documents` configuration value. There are a few
configuration values that customize the output of this builder, see the
chapter :ref:`latex-options` for details.

.. note::

   A direct PDF builder is provided by `rinohtype`__. The builder's name is
   ``rinoh``. Refer to the `rinohtype manual`__ for details.

   __ https://github.com/brechtm/rinohtype
   __ https://www.mos6581.org/rinohtype/quickstart.html#sphinx-builder

The produced LaTeX file uses several LaTeX packages that may not be present
in a "minimal" TeX distribution installation.

On Ubuntu Xenial, the following packages need to be installed for
successful PDF builds:

* ``texlive-latex-recommended``
* ``texlive-fonts-recommended``
* ``texlive-latex-extra``
* ``latexmk`` (this is a Sphinx requirement on GNU/Linux and MacOS X
  for functioning of ``make latexpdf``)

Additional packages are needed in some circumstances (see the discussion of
the ``'fontpkg'`` key of :confval:`latex_elements` for more information):

* To support occasional Cyrillic letters or words, and a fortiori if
  :confval:`language` is set to a Cyrillic language, the package
  ``texlive-lang-cyrillic`` is required, and, with unmodified ``'fontpkg'``,
  also ``cm-super`` or ``cm-super-minimal``,

* To support occasional Greek letters or words (in text, not in
  :rst:dir:`math` directive contents), ``texlive-lang-greek`` is required,
  and, with unmodified ``'fontpkg'``, also ``cm-super`` or
  ``cm-super-minimal``,

* For ``'xelatex'`` or ``'lualatex'`` (see :confval:`latex_engine`),
  ``texlive-xetex`` resp. ``texlive-luatex``, and, if leaving unchanged
  ``'fontpkg'``, ``fonts-freefont-otf``.

Since 1.6, ``make latexpdf`` uses ``latexmk`` (not on Windows).  This
makes sure the needed number of runs is automatically executed to get
the cross-references, bookmarks, indices, and tables of contents right.
One can pass to ``latexmk`` options via the ``LATEXMKOPTS`` Makefile variable.
For example, to reduce console output to a minimum.

.. code-block:: console

  make latexpdf LATEXMKOPTS="-silent"

Also, if ``latexmk`` is at version 4.52b or higher (January 2017)
``LATEXMKOPTS="-xelatex"`` speeds up PDF builds via XeLateX in case
of numerous graphics inclusions.

To pass options directly to the ``(pdf|xe|lua)latex`` binary, use
variable ``LATEXOPTS``, for example:

.. code-block:: console

  make latexpdf LATEXOPTS="--halt-on-error"

The testing of Sphinx LaTeX is done on Ubuntu Xenial whose TeX distribution
is based on a TeXLive 2015 snapshot dated March 2016.

.. module:: sphinx.builders.latex
.. class:: LaTeXBuilder

   .. autoattribute:: name

   .. autoattribute:: format

   .. autoattribute:: supported_image_types
