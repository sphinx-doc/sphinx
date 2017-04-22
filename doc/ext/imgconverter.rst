.. highlight:: rest

:mod:`sphinx.ext.imgconverter` -- Convert images to appropriate format for builders
===================================================================================

.. module:: sphinx.ext.imgconverter
   :synopsis: Convert images to appropriate format for builders

.. versionadded:: 1.6

This extension converts images in your document to appropriate format for builders.
For example, it allows you to use SVG images with LaTeX builder.
As a result, you don't mind what image format the builder supports.

Internally, this extension uses Imagemagick_ to convert images.

.. _Imagemagick: https://www.imagemagick.org/script/index.php

Configuration
-------------

.. confval:: image_converter

   A path to :command:`convert` command.  By default, the imgconverter uses
   the command from search paths.

.. confval:: image_converter_args

   Additional command-line arguments to give to :command:`convert`, as a list.
   The default is an empty list ``[]``.
