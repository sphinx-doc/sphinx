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

... display the whole TOC tree in the sidebar?
   Use the :data:`toctree` callable in a custom layout template, probably in the
   ``sidebartoc`` block.

... write my own extension?
   See the :ref:`extension tutorial <exttut>`.

... convert from my existing docs using MoinMoin markup?
   The easiest way is to convert to xhtml, then convert `xhtml to reST`_.  You'll
   still need to mark up classes and such, but the headings and code examples
   come through cleanly.


Using Sphinx with...
--------------------

Epydoc
   There's a third-party extension providing an `api role`_ which refers to
   Epydoc's API docs for a given identifier.

Doxygen
   Michael Jones is developing a reST/Sphinx bridge to doxygen called `breathe
   <http://github.com/michaeljones/breathe/tree/master>`_.

SCons
   Glenn Hutchings has written a SCons build script to build Sphinx
   documentation; it is hosted here: http://bitbucket.org/zondo/sphinx-scons

PyPI
   Jannis Leidel wrote a `setuptools command
   <http://pypi.python.org/pypi/Sphinx-PyPI-upload>`_ that automatically uploads
   Sphinx documentation to the PyPI package documentation area at
   http://packages.python.org/.

github pages
   You can use `Michael Jones' sphinx-to-github tool
   <http://github.com/michaeljones/sphinx-to-github/tree/master>`_ to prepare
   Sphinx HTML output.


.. _api role: http://git.savannah.gnu.org/cgit/kenozooid.git/tree/doc/extapi.py
.. _xhtml to reST: http://docutils.sourceforge.net/sandbox/xhtml2rest/xhtml2rest.py
