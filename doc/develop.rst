:orphan:

Sphinx development
==================

Sphinx is a maintained by a group of volunteers.  We value every contribution!

* The code can be found in a Git repository, at
  https://github.com/sphinx-doc/sphinx/.
* Issues and feature requests should be raised in the `tracker
  <https://github.com/sphinx-doc/sphinx/issues>`_.
* The mailing list for development is at `Google Groups
  <https://groups.google.com/forum/#!forum/sphinx-dev>`_.
* There is also the #sphinx-doc IRC channel on `freenode
  <http://freenode.net/>`_.

For more about our development process and methods, see the :doc:`devguide`.

Extensions
==========

To learn how to write your own extension, see :ref:`dev-extensions`.

The `sphinx-contrib <https://bitbucket.org/birkenfeld/sphinx-contrib/>`_
repository contains many contributed extensions.  Some of them have their own
releases on PyPI, others you can install from a checkout.

This is the current list of contributed extensions in that repository:

- aafig: render embedded ASCII art as nice images using aafigure_.
- actdiag: embed activity diagrams by using actdiag_
- adadomain: an extension for Ada support (Sphinx 1.0 needed)
- ansi: parse ANSI color sequences inside documents
- autorun: Execute code in a ``runblock`` directive.
- blockdiag: embed block diagrams by using blockdiag_
- cheeseshop: easily link to PyPI packages
- clearquest: create tables from ClearQuest_ queries.
- cmakedomain_: a domain for CMake_
- coffeedomain: a domain for (auto)documenting CoffeeScript source code.
- context: a builder for ConTeXt.
- doxylink: Link to external Doxygen-generated HTML documentation
- domaintools_: A tool for easy domain creation.
- email: obfuscate email addresses
- erlangdomain: an extension for Erlang support (Sphinx 1.0 needed)
- exceltable: embed Excel spreadsheets into documents using exceltable_
- feed: an extension for creating syndication feeds and time-based overviews
  from your site content
- findanything_: an extension to add Sublime Text 2-like findanything panels
  to your documentation to find pages, sections and index entries while typing
- gnuplot: produces images using gnuplot_ language.
- googleanalytics: track web visitor statistics by using `Google Analytics`_
- googlechart: embed charts by using `Google Chart`_
- googlemaps: embed maps by using `Google Maps`_
- httpdomain: a domain for documenting RESTful HTTP APIs.
- hyphenator: client-side hyphenation of HTML using hyphenator_
- inlinesyntaxhighlight_: inline syntax highlighting
- lassodomain: a domain for documenting Lasso_ source code
- libreoffice: an extension to include any drawing supported by LibreOffice (e.g. odg, vsd...).
- lilypond: an extension inserting music scripts from Lilypond_ in PNG format.
- makedomain_: a domain for `GNU Make`_
- matlabdomain: document MATLAB_ code.
- mockautodoc: mock imports.
- mscgen: embed mscgen-formatted MSC (Message Sequence Chart)s.
- napoleon: supports `Google style`_ and `NumPy style`_ docstrings.
- nicoviceo: embed videos from nicovideo
- nwdiag: embed network diagrams by using nwdiag_
- omegat: support tools to collaborate with OmegaT_ (Sphinx 1.1 needed)
- osaka: convert standard Japanese doc to Osaka dialect (it is joke extension)
- paverutils: an alternate integration of Sphinx with Paver_.
- phpdomain: an extension for PHP support
- plantuml: embed UML diagram by using PlantUML_
- py_directive: Execute python code in a ``py`` directive and return a math
  node.
- rawfiles: copy raw files, like a CNAME.
- requirements: declare requirements wherever you need (e.g. in test
  docstrings), mark statuses and collect them in a single list
- restbuilder: a builder for reST (reStructuredText) files.
- rubydomain: an extension for Ruby support (Sphinx 1.0 needed)
- sadisplay: display SqlAlchemy model sadisplay_
- sdedit: an extension inserting sequence diagram by using Quick Sequence
  Diagram Editor (sdedit_)
- seqdiag: embed sequence diagrams by using seqdiag_
- slide: embed presentation slides on slideshare_ and other sites.
- swf_: embed flash files
- sword: an extension inserting Bible verses from Sword_.
- tikz: draw pictures with the `TikZ/PGF LaTeX package`_.
- traclinks: create TracLinks_ to a Trac_ instance from within Sphinx
- whooshindex: whoosh indexer extension
- youtube: embed videos from YouTube_
- zopeext: provide an ``autointerface`` directive for using `Zope interfaces`_.


See the :ref:`extension tutorial <exttut>` on getting started with writing your
own extensions.


.. _aafigure: https://launchpad.net/aafigure
.. _gnuplot: http://www.gnuplot.info/
.. _paver: http://paver.github.io/paver/
.. _Sword: http://www.crosswire.org/sword/
.. _Lilypond: http://lilypond.org/
.. _sdedit: http://sdedit.sourceforge.net/
.. _Trac: http://trac.edgewall.org
.. _TracLinks: http://trac.edgewall.org/wiki/TracLinks
.. _OmegaT: http://www.omegat.org/
.. _PlantUML: http://plantuml.com/
.. _PyEnchant: http://www.rfk.id.au/software/pyenchant/
.. _sadisplay: https://bitbucket.org/estin/sadisplay/wiki/Home
.. _blockdiag: http://blockdiag.com/en/
.. _seqdiag: http://blockdiag.com/en/
.. _actdiag: http://blockdiag.com/en/
.. _nwdiag: http://blockdiag.com/en/
.. _Google Analytics: http://www.google.com/analytics/
.. _Google Chart: https://developers.google.com/chart/
.. _Google Maps: https://www.google.com/maps
.. _Google style: http://google-styleguide.googlecode.com/svn/trunk/pyguide.html
.. _NumPy style: https://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt
.. _hyphenator: https://github.com/mnater/hyphenator
.. _exceltable: http://pythonhosted.org/sphinxcontrib-exceltable/
.. _YouTube: http://www.youtube.com/
.. _ClearQuest: http://www-03.ibm.com/software/products/en/clearquest
.. _Zope interfaces: http://docs.zope.org/zope.interface/README.html
.. _slideshare: http://www.slideshare.net/
.. _TikZ/PGF LaTeX package: https://sourceforge.net/projects/pgf/
.. _MATLAB: http://www.mathworks.com/products/matlab/
.. _swf: https://bitbucket.org/klorenz/sphinxcontrib-swf
.. _findanything: https://bitbucket.org/klorenz/sphinxcontrib-findanything
.. _cmakedomain: https://bitbucket.org/klorenz/sphinxcontrib-cmakedomain
.. _GNU Make: http://www.gnu.org/software/make/
.. _makedomain: https://bitbucket.org/klorenz/sphinxcontrib-makedomain
.. _inlinesyntaxhighlight: http://sphinxcontrib-inlinesyntaxhighlight.readthedocs.org
.. _CMake: https://cmake.org
.. _domaintools: https://bitbucket.org/klorenz/sphinxcontrib-domaintools
.. _restbuilder: https://pypi.python.org/pypi/sphinxcontrib-restbuilder
.. _Lasso: http://www.lassosoft.com/
