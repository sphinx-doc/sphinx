test-directives-raw
===================

HTML
----

standard
^^^^^^^^

.. raw:: html

   standalone raw directive (HTML)

with substitution
^^^^^^^^^^^^^^^^^

HTML: abc |HTML_RAW| ghi

.. |HTML_RAW| raw:: html

   def

LaTeX
-----

standard
^^^^^^^^

.. raw:: latex

   standalone raw directive (LaTeX)

with substitution
^^^^^^^^^^^^^^^^^

LaTeX: abc |LATEX_RAW| ghi

.. |LATEX_RAW| raw:: latex

   def
