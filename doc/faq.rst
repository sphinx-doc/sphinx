.. _faq:

Sphinx FAQ
==========

This is a list of Frequently Asked Questions about Sphinx.  Feel free to
suggest new entries!

How do I...
-----------

... customize the look of the built HTML files?
   Use themes, see :doc:`theming`.

... add global substitutions?
   Add them in the :confval:`rst_epilog` config value.

... write my own extension?
   See the :ref:`extension tutorial <exttut>`.
   
... use Sphinx with Epydoc?
   There's a third-party extension providing an `api role`_ which refers to
   Epydoc's API docs for a given identifier.


.. _api role: http://git.savannah.gnu.org/cgit/kenozooid.git/tree/doc/extapi.py
