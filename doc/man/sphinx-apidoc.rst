:orphan:

sphinx-apidoc manual page
=========================

Synopsis
--------

**sphinx-apidoc** [*options*] -o <*outputdir*> <*sourcedir*> [*pathnames* ...]


Description
-----------

:program:`sphinx-apidoc` is a tool for automatic generation of Sphinx sources
that, using the autodoc extension, document a whole package in the style of
other automatic API documentation tools.

*sourcedir* must point to a Python package.  Any *pathnames* given are paths to
be excluded from the generation.


Options
-------

-o <outputdir>  Directory to place the output files.  If it does not exist,
                it is created.
-f, --force     Usually, apidoc does not overwrite files, unless this option
                is given.
-n, --dry-run   If given, apidoc does not create any files.
-s <suffix>     Suffix for the source files generated, default is ``rst``.
-d <maxdepth>   Maximum depth for the generated table of contents file.
-T, --no-toc    Do not create a table of contents file.
-F, --full      If given, a full Sphinx project is generated (``conf.py``,
                ``Makefile`` etc.) using sphinx-quickstart.

These options are used with ``-F``:

-H <project>    Project name to put into the configuration.
-A <author>     Author name(s) to put into the configuration.
-V <version>    Project version.
-R <release>    Project release.


See also
--------

:manpage:`sphinx-build(1)`


Author
------

Etienne Desautels, <etienne.desautels@gmail.com>, Georg Brandl
<georg@python.org> et al.
