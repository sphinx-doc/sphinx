:orphan:

sphinx-build manual page
========================

Synopsis
--------

**sphinx-build** [*options*] <*sourcedir*> <*outdir*> [*filenames* ...]


Description
-----------

:program:`sphinx-build` generates documentation from the files in
``<sourcedir>`` and places it in the ``<outdir>``.

:program:`sphinx-build` looks for ``<sourcedir>/conf.py`` for the configuration
settings.  :manpage:`sphinx-quickstart(1)` may be used to generate template
files, including ``conf.py``.

:program:`sphinx-build` can create documentation in different formats.  A format
is selected by specifying the builder name on the command line; it defaults to
HTML.  Builders can also perform other tasks related to documentation
processing.

By default, everything that is outdated is built.  Output only for selected
files can be built by specifying individual filenames.

List of available builders:

html
   HTML file generation.  This is the default builder.

htmlhelp
   Generates files for CHM (compiled help files) generation.

qthelp
   Generates files for Qt help collection generation.

devhelp
   Generates files for the GNOME Devhelp help viewer.

latex
   Generates LaTeX output that can be compiled to a PDF document.

man
   Generates manual pages.

texinfo
   Generates Texinfo output that can be processed by :program:`makeinfo` to
   generate an Info document.

text
   Generates a plain-text version of the documentation.

changes
   Generates HTML files listing changed/added/deprecated items for
   the current version of the documented project.

linkcheck
   Checks the integrity of all external links in the source.

pickle / json
   Generates serialized HTML files for use in web applications.


Options
-------

-b <builder>          Builder to use; defaults to html. See the full list
                      of builders above.
-a                    Generate output for all files; without this option only
                      output for new and changed files is generated.
-E                    Ignore cached files, forces to re-read all source files
                      from disk.
-c <path>             Locate the conf.py file in the specified path instead of
                      <sourcedir>.
-C                    Specify that no conf.py file at all is to be used.
                      Configuration can only be set with the -D option.
-D <setting=value>    Override a setting from the configuration file.
-d <path>             Path to cached files; defaults to <outdir>/.doctrees.
-A <name=value>       Pass a value into the HTML templates (only for HTML builders).
-n                    Run in nit-picky mode, warn about all missing references.
-N                    Prevent colored output.
-q                    Quiet operation, just print warnings and errors on stderr.
-Q                    Very quiet operation, don't print anything except for errors.
-w <file>             Write warnings and errors into the given file, in addition
                      to stderr.
-W                    Turn warnings into errors.
-P                    Run Pdb on exception.


See also
--------

:manpage:`sphinx-quickstart(1)`

Author
------

Georg Brandl <georg@python.org>, Armin Ronacher <armin.ronacher@active-4.com> et
al.

This manual page was initially written by Mikhail Gusarov
<dottedmag@dottedmag.net>, for the Debian project.
