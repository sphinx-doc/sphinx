:orphan:

Sphinx development
==================

Sphinx is a maintained by a group of volunteers.  We value every contribution!

* The code can be found in a Mercurial repository, at
  http://bitbucket.org/birkenfeld/sphinx/.
* Issues and feature requests should be raised in the `tracker
  <http://bitbucket.org/birkenfeld/sphinx/issues/>`_.
* The mailing list for development is at `Google Groups
  <http://groups.google.com/group/sphinx-dev/>`_.

For more about our development process and methods, see the :doc:`devguide`.

Extensions
==========

The `sphinx-contrib <http://bitbucket.org/birkenfeld/sphinx-contrib/>`_
repository contains many contributed extensions.  Some of them have their own
releases on PyPI, others you can install from a checkout.

This is the current list of contributed extensions in that repository:

- aafig: render embeded ASCII art as nice images using aafigure_.
- actdiag: embed activity diagrams by using actdiag_
- adadomain: an extension for Ada support (Sphinx 1.0 needed)
- ansi: parse ANSI color sequences inside documents
- autorun: Execute code in a runblock directive.
- blockdiag: embed block diagrams by using blockdiag_
- cheeseshop: easily link to PyPI packages
- clearquest: create tables from ClearQuest_ queries.
- coffeedomain: a domain for (auto)documenting CoffeeScript source code.
- context: a builder for ConTeXt.
- doxylink: Link to external Doxygen-generated HTML documentation
- email: obfuscate email addresses
- erlangdomain: an extension for Erlang support (Sphinx 1.0 needed)
- exceltable: embed Excel spreadsheets into documents using exceltable_
- feed: an extension for creating syndication feeds and time-based overviews
  from your site content
- gnuplot: produces images using gnuplot_ language.
- googleanalytics: track html visitors statistics
- googlechart: embed charts by using `Google Chart`_
- googlemaps: embed maps by using `Google Maps`_
- httpdomain: a domain for documenting RESTful HTTP APIs.
- hyphenator: client-side hyphenation of HTML using hyphenator_
- lilypond: an extension inserting music scripts from Lilypond_ in PNG format.
- mscgen: embed mscgen-formatted MSC (Message Sequence Chart)s.
- nicoviceo: embed videos from nicovideo
- nwdiag: embed network diagrams by using nwdiag_
- omegat: support tools to collaborate with OmegaT_ (Sphinx 1.1 needed)
- osaka: convert standard Japanese doc to Osaka dialect (it is joke extension)
- paverutils: an alternate integration of Sphinx with Paver_.
- phpdomain: an extension for PHP support
- plantuml: embed UML diagram by using PlantUML_
- rawfiles: copy raw files, like a CNAME.
- requirements: declare requirements wherever you need (e.g. in test
  docstrings), mark statuses and collect them in a single list
- rubydomain: an extension for Ruby support (Sphinx 1.0 needed)
- sadisplay: display SqlAlchemy model sadisplay_
- sdedit: an extension inserting sequence diagram by using Quick Sequence.
  Diagram Editor (sdedit_)
- seqdiag: embed sequence diagrams by using seqdiag_
- slide: embed presentation slides on slideshare_ and other sites.
- swf: embed flash files
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
.. _paver: http://www.blueskyonmars.com/projects/paver/
.. _Sword: http://www.crosswire.org/sword/
.. _Lilypond: http://lilypond.org/web/
.. _sdedit: http://sdedit.sourceforge.net/
.. _Trac: http://trac.edgewall.org
.. _TracLinks: http://trac.edgewall.org/wiki/TracLinks
.. _OmegaT: http://www.omegat.org/
.. _PlantUML: http://plantuml.sourceforge.net/
.. _PyEnchant: http://www.rfk.id.au/software/pyenchant/
.. _sadisplay: http://bitbucket.org/estin/sadisplay/wiki/Home
.. _blockdiag: http://blockdiag.com/
.. _seqdiag: http://blockdiag.com/
.. _actdiag: http://blockdiag.com/
.. _nwdiag: http://blockdiag.com/
.. _Google Chart: http://code.google.com/intl/ja/apis/chart/
.. _Google Maps: http://maps.google.com/
.. _hyphenator: http://code.google.com/p/hyphenator/
.. _exceltable: http://packages.python.org/sphinxcontrib-exceltable/
.. _YouTube: http://www.youtube.com/
.. _ClearQuest: http://www-01.ibm.com/software/awdtools/clearquest/
.. _Zope interfaces: http://docs.zope.org/zope.interface/README.html
.. _slideshare: http://www.slideshare.net/
.. _TikZ/PGF LaTeX package: http://sourceforge.net/projects/pgf/
