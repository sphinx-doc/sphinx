# -*- coding: utf-8 -*-
"""
    sphinx.setup_command
    ~~~~~~~~~~~~~~~~~~~~

    Setuptools/distutils commands to assist the building of sphinx
    documentation.

    :author: Sebastian Wiesner
    :contact: basti.wiesner@gmx.net
    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import os
from StringIO import StringIO
from distutils.cmd import Command

from sphinx.application import Sphinx
from sphinx.util.console import darkred, nocolor, color_terminal


class BuildDoc(Command):
    """Distutils command to build Sphinx documentation."""

    description = 'Build Sphinx documentation'
    user_options = [
        ('fresh-env', 'E', 'discard saved environment'),
        ('all-files', 'a', 'build all files'),
        ('source-dir=', 's', 'Source directory'),
        ('build-dir=', None, 'Build directory'),
        ('builder=', 'b', 'The builder to use. Defaults to "html"'),
        ]
    boolean_options = ['fresh-env', 'all-files']


    def initialize_options(self):
        self.fresh_env = self.all_files = False
        self.source_dir = self.build_dir = None
        self.conf_file_name = 'conf.py'
        self.builder = 'html'

    def _guess_source_dir(self):
        for guess in ('doc', 'docs'):
            if not os.path.isdir(guess):
                continue
            for root, dirnames, filenames in os.walk(guess):
                if 'conf.py' in filenames:
                    return root

    def finalize_options(self):
        if self.source_dir is None:
            self.source_dir = self._guess_source_dir()
            self.announce('Using source directory %s' % self.source_dir)
        self.ensure_dirname('source_dir')
        self.source_dir = os.path.abspath(self.source_dir)

        if self.build_dir is None:
            build = self.get_finalized_command('build')
            self.build_dir = os.path.join(build.build_base, 'sphinx')
            self.mkpath(self.build_dir)
        self.ensure_dirname('build_dir')
        self.doctree_dir = os.path.join(self.build_dir, 'doctrees')
        self.mkpath(self.doctree_dir)
        self.builder_target_dir = os.path.join(self.build_dir, self.builder)
        self.mkpath(self.builder_target_dir)

    def run(self):
        if not color_terminal():
            # Windows' poor cmd box doesn't understand ANSI sequences
            nocolor()
        if not self.verbose:
            status_stream = StringIO()
        else:
            status_stream = sys.stdout
        app = Sphinx(self.source_dir, self.source_dir,
                     self.builder_target_dir, self.doctree_dir,
                     self.builder, {}, status_stream,
                     freshenv=self.fresh_env)

        try:
            if self.all_files:
                app.builder.build_all()
            else:
                app.builder.build_update()
        except Exception, err:
            from docutils.utils import SystemMessage
            if isinstance(err, SystemMessage):
                sys.stderr, darkred('reST markup error:')
                print >>sys.stderr, err.args[0].encode('ascii',
                                                       'backslashreplace')
            else:
                raise
