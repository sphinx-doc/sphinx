"""sphinx-build -M command-line handling.

This replaces the old, platform-dependent and once-generated content
of Makefile / make.bat.

This is in its own module so that importing it is fast.  It should not
import the main Sphinx modules (like sphinx.applications, sphinx.builders).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from os import path
from typing import TYPE_CHECKING

import sphinx
from sphinx.cmd.build import build_main
from sphinx.util.console import blue, bold, color_terminal, nocolor
from sphinx.util.osutil import rmtree

if sys.version_info >= (3, 11):
    from contextlib import chdir
else:
    from sphinx.util.osutil import _chdir as chdir

if TYPE_CHECKING:
    from collections.abc import Sequence

BUILDERS = [
    ("",      "html",        "to make standalone HTML files"),
    ("",      "dirhtml",     "to make HTML files named index.html in directories"),
    ("",      "singlehtml",  "to make a single large HTML file"),
    ("",      "pickle",      "to make pickle files"),
    ("",      "json",        "to make JSON files"),
    ("",      "htmlhelp",    "to make HTML files and an HTML help project"),
    ("",      "qthelp",      "to make HTML files and a qthelp project"),
    ("",      "devhelp",     "to make HTML files and a Devhelp project"),
    ("",      "epub",        "to make an epub"),
    ("",      "latex",       "to make LaTeX files, you can set PAPER=a4 or PAPER=letter"),
    ("posix", "latexpdf",    "to make LaTeX and PDF files (default pdflatex)"),
    ("posix", "latexpdfja",  "to make LaTeX files and run them through platex/dvipdfmx"),
    ("",      "text",        "to make text files"),
    ("",      "man",         "to make manual pages"),
    ("",      "texinfo",     "to make Texinfo files"),
    ("posix", "info",        "to make Texinfo files and run them through makeinfo"),
    ("",      "gettext",     "to make PO message catalogs"),
    ("",      "changes",     "to make an overview of all changed/added/deprecated items"),
    ("",      "xml",         "to make Docutils-native XML files"),
    ("",      "pseudoxml",   "to make pseudoxml-XML files for display purposes"),
    ("",      "linkcheck",   "to check all external links for integrity"),
    ("",      "doctest",     "to run all doctests embedded in the documentation "
                             "(if enabled)"),
    ("",      "coverage",    "to run coverage check of the documentation (if enabled)"),
    ("",      "clean",       "to remove everything in the build directory"),
]


class _Make:
    def __init__(
        self,
        *,
        srcdir: str,
        builddir: str,
        filenames: Sequence[str],
        opts: Sequence[str],
    ) -> None:
        self.srcdir = srcdir
        self.builddir = builddir
        self.filenames = list(filenames)
        self.opts = list(opts)

    def builddir_join(self, *comps: str) -> str:
        return path.join(self.builddir, *comps)

    def build_clean(self) -> int:
        srcdir = path.abspath(self.srcdir)
        builddir = path.abspath(self.builddir)
        if not path.exists(self.builddir):
            return 0
        elif not path.isdir(self.builddir):
            print("Error: %r is not a directory!" % self.builddir)
            return 1
        elif srcdir == builddir:
            print("Error: %r is same as source directory!" % self.builddir)
            return 1
        elif path.commonpath([srcdir, builddir]) == builddir:
            print("Error: %r directory contains source directory!" % self.builddir)
            return 1
        print("Removing everything under %r..." % self.builddir)
        for item in os.listdir(self.builddir):
            rmtree(self.builddir_join(item))
        return 0

    def build_help(self) -> None:
        if not color_terminal():
            nocolor()

        print(bold("Sphinx v%s" % sphinx.__display_version__))
        print("Please use `make %s' where %s is one of" % ((blue('target'),) * 2))
        for osname, bname, description in BUILDERS:
            if not osname or os.name == osname:
                print(f'  {blue(bname.ljust(10))}  {description}')

    def build_latexpdf(self) -> int:
        if self.run_generic_build('latex') > 0:
            return 1

        # Use $MAKE to determine the make command
        make_fallback = 'make.bat' if sys.platform == 'win32' else 'make'
        makecmd = os.environ.get('MAKE', make_fallback)
        if not makecmd.lower().startswith('make'):
            raise RuntimeError('Invalid $MAKE command: %r' % makecmd)
        try:
            with chdir(self.builddir_join('latex')):
                if '-Q' in self.opts:
                    with open('__LATEXSTDOUT__', 'w') as outfile:
                        returncode = subprocess.call([makecmd,
                                                      'all-pdf',
                                                      'LATEXOPTS=-halt-on-error',
                                                      ],
                                                     stdout=outfile,
                                                     stderr=subprocess.STDOUT,
                                                     )
                    if returncode:
                        print('Latex error: check %s' %
                              self.builddir_join('latex', '__LATEXSTDOUT__')
                              )
                elif '-q' in self.opts:
                    returncode = subprocess.call(
                        [makecmd,
                         'all-pdf',
                         'LATEXOPTS=-halt-on-error',
                         'LATEXMKOPTS=-silent',
                         ],
                    )
                    if returncode:
                        print('Latex error: check .log file in %s' %
                              self.builddir_join('latex')
                              )
                else:
                    returncode = subprocess.call([makecmd, 'all-pdf'])
                return returncode
        except OSError:
            print('Error: Failed to run: %s' % makecmd)
            return 1

    def build_latexpdfja(self) -> int:
        if self.run_generic_build('latex') > 0:
            return 1

        # Use $MAKE to determine the make command
        make_fallback = 'make.bat' if sys.platform == 'win32' else 'make'
        makecmd = os.environ.get('MAKE', make_fallback)
        if not makecmd.lower().startswith('make'):
            raise RuntimeError('Invalid $MAKE command: %r' % makecmd)
        try:
            with chdir(self.builddir_join('latex')):
                return subprocess.call([makecmd, 'all-pdf'])
        except OSError:
            print('Error: Failed to run: %s' % makecmd)
            return 1

    def build_info(self) -> int:
        if self.run_generic_build('texinfo') > 0:
            return 1

        # Use $MAKE to determine the make command
        makecmd = os.environ.get('MAKE', 'make')
        if not makecmd.lower().startswith('make'):
            raise RuntimeError('Invalid $MAKE command: %r' % makecmd)
        try:
            with chdir(self.builddir_join('texinfo')):
                return subprocess.call([makecmd, 'info'])
        except OSError:
            print('Error: Failed to run: %s' % makecmd)
            return 1

    def build_gettext(self) -> int:
        dtdir = self.builddir_join('gettext', '.doctrees')
        if self.run_generic_build('gettext', doctreedir=dtdir) > 0:
            return 1
        return 0

    def run_generic_build(self, builder: str, doctreedir: str | None = None) -> int:
        # compatibility with old Makefile
        paper_size = os.getenv('PAPER', '')
        if paper_size in {'a4', 'letter'}:
            self.opts.extend(['-D', f'latex_elements.papersize={paper_size}paper'])
        if doctreedir is None:
            doctreedir = self.builddir_join('doctrees')

        args = [
            '--builder', builder,
            '--doctree-dir', doctreedir,
            *self.opts,
            self.srcdir,
            self.builddir_join(builder),
            *self.filenames,
        ]
        return build_main(args)


def _parse_make_args(args: Sequence[str]) -> tuple[str, _Make]:
    parser = argparse.ArgumentParser()
    parser.add_argument('builder_name')
    parser.add_argument('source_dir')
    parser.add_argument('build_dir')
    parser.add_argument('filenames', nargs=argparse.ZERO_OR_MORE)
    make_args, remaining = parser.parse_known_args(args)

    # Check for problems with positional arguments (i.e. [FILENAMES...])
    if pos_args := [arg for arg in remaining if not arg.startswith('-')]:
        msg = f'unrecognized arguments: {" ".join(pos_args)}'
        parser.error(msg)

    return make_args.builder_name, _Make(
        srcdir=make_args.source_dir,
        builddir=make_args.build_dir,
        filenames=make_args.filenames,
        opts=remaining,
    )


def run_make_mode(args: Sequence[str]) -> int:
    if len(args) < 3:
        print('Error: at least 3 arguments (builder, source '
              'dir, build dir) are required.', file=sys.stderr)
        return 1

    builder_name, make = _parse_make_args(args)
    run_method = f'build_{builder_name}'
    if hasattr(make, run_method):
        return getattr(make, run_method)()
    return make.run_generic_build(builder_name)
