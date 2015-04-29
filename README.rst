
This is the fork of Sphinx documentation generator, see http://sphinx-doc.org/.
In this version implemented proposal from https://github.com/sphinx-doc/issues/759.



Installing
==========

Install from newest dev version in master branch::

   pip install git+https://github.com/hypnocat/sphinx

Install from cloned source::

   pip install .

Install from cloned source as editable::

   pip install -e .


Reading the docs
================

After installing::


   echo "autodoc_dumb_docstring=True" >> conf.py   
   cd doc
   make html

Then, direct your browser to ``_build/html/index.html``.

Or read them online at <http://sphinx-doc.org/>.


