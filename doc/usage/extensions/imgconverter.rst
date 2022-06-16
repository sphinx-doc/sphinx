.. _sphinx.ext.imgconverter:

:mod:`sphinx.ext.imgconverter` -- A reference image converter using Imagemagick
===============================================================================

.. module:: sphinx.ext.imgconverter
   :synopsis: Convert images to appropriate format for builders

.. versionadded:: 1.6

This extension converts images in your document to appropriate format for
builders.  For example, it allows you to use SVG images with LaTeX builder.
As a result, you don't mind what image format the builder supports.

By default the extension uses ImageMagick_ to perform conversions,
and will not work if ImageMagick is not installed.

.. _ImageMagick: https://www.imagemagick.org

.. note::

   ImageMagick rasterizes a SVG image on conversion.  As a result, the image
   becomes not scalable.  To avoid that, please use other image converters like
   `sphinxcontrib-svg2pdfconverter`__ (which uses Inkscape or
   ``rsvg-convert``).

.. __: https://github.com/missinglinkelectronics/sphinxcontrib-svg2pdfconverter


Configuration
-------------

.. confval:: image_converter

   A path to a conversion command.  By default, the imgconverter finds
   the command from search paths.

   On Unix platforms, the command :command:`convert` is used by default.

   On Windows, the command :command:`magick` is used by default.

   .. versionchanged:: 3.1

      Use :command:`magick` command by default on windows

.. confval:: image_converter_args

   Additional command-line arguments to give to :command:`convert`, as a list.
   The default is an empty list ``[]``.

   On Windows, it defaults to ``["convert"]``.

   .. versionchanged:: 3.1

      Use ``["convert"]`` by default on Windows
