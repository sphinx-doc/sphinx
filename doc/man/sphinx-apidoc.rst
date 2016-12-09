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

.. warning::

   ``sphinx-apidoc`` generates source files that use :mod:`sphinx.ext.autodoc`
   to document all found modules.  If any modules have side effects on import,
   these will be executed by ``autodoc`` when ``sphinx-build`` is run.

   If you document scripts (as opposed to library modules), make sure their main
   routine is protected by a ``if __name__ == '__main__'`` condition.


Options
-------

-o <outputdir>      Directory to place the output files.  If it does not exist,
                    it is created.
-f, --force         Usually, apidoc does not overwrite files, unless this option
                    is given.
-l, --follow-links  Follow symbolic links.
-n, --dry-run       If given, apidoc does not create any files.
-s <suffix>         Suffix for the source files generated, default is ``rst``.
-d <maxdepth>       Maximum depth for the generated table of contents file.
-T, --no-toc        Do not create a table of contents file.
-F, --full          If given, a full Sphinx project is generated (``conf.py``,
                    ``Makefile`` etc.) using sphinx-quickstart.
-e, --separate      Put each module file in its own page.
-E, --no-headings   Don't create headings for the modules/packages
-P, --private       Include "_private" modules

These options are used with ``-F``:

-a              Append module_path to sys.path.
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
