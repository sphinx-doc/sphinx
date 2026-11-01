Test numfig with include
========================

This document tests that :numref: works with figures in included files.

.. include:: _includes/figures.rst

Reference to included figure: :numref:`included-figure`

Reference to local figure: :numref:`local-figure`

.. _local-figure:

.. figure:: img.png

   This is a local figure
