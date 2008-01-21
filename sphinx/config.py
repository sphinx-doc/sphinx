# -*- coding: utf-8 -*-
"""
    sphinx.config
    ~~~~~~~~~~~~~

    Build configuration file handling.

    :copyright: 2008 by Georg Brandl.
    :license: BSD license.
"""

import os
import sys
import types
from os import path


class ConfigError(Exception):
    """Raised if something's wrong with the configuration."""

    def __init__(self, message, orig_exc=None):
        self.message = message
        self.orig_exc = orig_exc

    def __repr__(self):
        if self.orig_exc:
            return 'ConfigError(%r, %r)' % (self.message, self.orig_exc)
        return 'ConfigError(%r)' % self.message

    def __str__(self):
        if self.orig_exc:
            return '%s (exception: %s)' % (self.message, self.orig_exc)
        return self.message


class Config(object):
    """Configuration file abstraction."""

    # the values are: (default, needs fresh doctrees if changed)

    config_values = dict(
        # general substitutions
        project = ('Python', True),
        copyright = ('', False),
        version = ('', True),
        release = ('', True),
        today = ('', True),
        today_fmt = ('%B %d, %Y', True),

        # extensibility
        templates_path = ([], False),
        extensions = ([], True),

        # general reading options
        unused_files = ([], True),
        refcount_file = ('', True),
        add_function_parentheses = (True, True),
        add_module_names = (True, True),

        # HTML options
        html_last_updated_fmt = ('%b %d, %Y', False),
        html_use_smartypants = (True, False),
        html_translator_class = (None, False),
        html_index = ('', False),
        html_sidebars = ({}, False),
        html_additional_pages = ({}, False),

        # HTML help options
        htmlhelp_basename = ('pydoc', False),

        # LaTeX options
        latex_paper_size = ('letter', False),
        latex_font_size = ('10pt', False),
        latex_documents = ([], False),
        latex_preamble = ('', False),
        latex_appendices = ([], False),
    )

    def __init__(self, dirname, filename):
        config = {}
        olddir = os.getcwd()
        try:
            os.chdir(dirname)
            execfile(path.join(dirname, filename), config)
        finally:
            os.chdir(olddir)
        # remove potentially pickling-problematic values
        for key, val in config.items():
            if key.startswith('_') or isinstance(val, types.ModuleType):
                del config[key]
        self.__dict__.update(config)

    def __getattr__(self, name):
        if name in self.config_values:
            defval = self.config_values[name][0]
            setattr(self, name, defval)
            return defval
        if name[0:1] == '_':
            return object.__getattr__(self, name)
        raise AttributeError('no configuration value named %r' % name)

    def __getitem__(self, name):
        return getattr(self, name)
