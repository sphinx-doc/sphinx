Test numfig with only directive
================================

This is a test to reproduce issue #4726.

.. only:: latex

   .. figure:: latex-image.png

      Fig for latex

.. only:: html

   .. figure:: html-image.png

      Fig for html

.. figure:: common-image.png

   Fig for all formats

The figures should be numbered consistently:
- In HTML: "Fig for html" should be Fig. 1, "Fig for all formats" should be Fig. 2
- In LaTeX: "Fig for latex" should be Fig. 1, "Fig for all formats" should be Fig. 2