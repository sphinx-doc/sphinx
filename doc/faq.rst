.. _faq:

Sphinx FAQ
==========

This is a list of Frequently Asked Questions about Sphinx.  Feel free to
suggest new entries!

How do I...
-----------

... get section numbers?
   They are automatic in LaTeX output; for HTML, give a ``:numbered:`` option to
   the :dir:`toctree` directive where you want to start numbering.

... customize the look of the built HTML files?
   Use themes, see :doc:`theming`.

... add global substitutions or includes?
   Add them in the :confval:`rst_epilog` config value.

... write my own extension?
   See the :ref:`extension tutorial <exttut>`.

... use Sphinx with Epydoc?
   There's a third-party extension providing an `api role`_ which refers to
   Epydoc's API docs for a given identifier.

... use Sphinx with SCons?
   Glenn Hutchings has written a SCons build script to build Sphinx
   documentation; it is hosted here: http://bitbucket.org/zondo/sphinx-scons
   

.. _api role: http://git.savannah.gnu.org/cgit/kenozooid.git/tree/doc/extapi.py
