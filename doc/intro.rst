Introduction
============

This is the documentation for the Sphinx documentation builder.  Sphinx is a
tool that translates a set of reStructuredText_ source files into various output
formats, automatically producing cross-references, indices etc.  That is, if
you have a directory containing a bunch of reST-formatted documents (and
possibly subdirectories of docs in there as well), Sphinx can generate a
nicely-organized arrangement of HTML files (in some other directory) for easy
browsing and navigation.  But from the same source, it can also generate a
LaTeX file that you can compile into a PDF version of the documents, or a
PDF file directly using `rst2pdf <https://github.com/rst2pdf/rst2pdf>`_.

The focus is on hand-written documentation, rather than auto-generated API docs.
Though there is support for that kind of docs as well (which is intended to be
freely mixed with hand-written content), if you need pure API docs have a look
at `Epydoc <http://epydoc.sourceforge.net/>`_, which also understands reST.

For a great "introduction" to writing docs in general -- the whys and hows, see
also `Write the docs <http://write-the-docs.readthedocs.org/>`_, written by Eric
Holscher.


Conversion from other systems
-----------------------------

This section is intended to collect helpful hints for those wanting to migrate
to reStructuredText/Sphinx from other documentation systems.

* Gerard Flanagan has written a script to convert pure HTML to reST; it can be
  found at the `Python Package Index <https://pypi.python.org/pypi/html2rest>`_.

* For converting the old Python docs to Sphinx, a converter was written which
  can be found at `the Python SVN repository
  <http://svn.python.org/projects/doctools/converter>`_.  It contains generic
  code to convert Python-doc-style LaTeX markup to Sphinx reST.

* Marcin Wojdyr has written a script to convert Docbook to reST with Sphinx
  markup; it is at `Google Code <https://github.com/wojdyr/db2rst>`_.

* Christophe de Vienne wrote a tool to convert from Open/LibreOffice documents
  to Sphinx: `odt2sphinx <https://pypi.python.org/pypi/odt2sphinx/>`_.

* To convert different markups, `Pandoc <http://pandoc.org/>`_ is
  a very helpful tool.


Use with other systems
----------------------

See the :ref:`pertinent section in the FAQ list <usingwith>`.


Prerequisites
-------------

Sphinx needs at least **Python 2.7** or **Python 3.4** to run, as well as the
docutils_ and Jinja2_ libraries.  Sphinx should work with docutils version 0.10
or some (not broken) SVN trunk snapshot.  If you like to have source code
highlighting support, you must also install the Pygments_ library.

.. _reStructuredText: http://docutils.sourceforge.net/rst.html
.. _docutils: http://docutils.sourceforge.net/
.. _Jinja2: http://jinja.pocoo.org/
.. _Pygments: http://pygments.org/


Usage
-----

See :doc:`tutorial` for an introduction.  It also contains links to more
advanced sections in this manual for the topics it discusses.
