# -*- coding: utf-8 -*-
"""
    sphinx.config
    ~~~~~~~~~~~~~

    Build configuration file handling.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
from os import path

from sphinx.errors import ConfigError
from sphinx.locale import l_
from sphinx.util.osutil import make_filename
from sphinx.util.pycompat import bytes, b, execfile_

nonascii_re = re.compile(b(r'[\x80-\xff]'))

CONFIG_SYNTAX_ERROR = "There is a syntax error in your configuration file: %s"
if sys.version_info >= (3, 0):
    CONFIG_SYNTAX_ERROR += "\nDid you change the syntax from 2.x to 3.x?"

class Config(object):
    """
    Configuration file abstraction.
    """

    # the values are: (default, what needs to be rebuilt if changed)

    # If you add a value here, don't forget to include it in the
    # quickstart.py file template as well as in the docs!

    config_values = dict(
        # general options
        project = ('Python', 'env'),
        copyright = ('', 'html'),
        version = ('', 'env'),
        release = ('', 'env'),
        today = ('', 'env'),
        today_fmt = (None, 'env'),  # the real default is locale-dependent

        language = (None, 'env'),
        locale_dirs = ([], 'env'),

        master_doc = ('contents', 'env'),
        source_suffix = ('.rst', 'env'),
        source_encoding = ('utf-8-sig', 'env'),
        exclude_patterns = ([], 'env'),
        # the next three are all deprecated now
        unused_docs = ([], 'env'),
        exclude_trees = ([], 'env'),
        exclude_dirnames = ([], 'env'),
        default_role = (None, 'env'),
        add_function_parentheses = (True, 'env'),
        add_module_names = (True, 'env'),
        trim_footnote_reference_space = (False, 'env'),
        show_authors = (False, 'env'),
        pygments_style = (None, 'html'),
        highlight_language = ('python', 'env'),
        templates_path = ([], 'html'),
        template_bridge = (None, 'html'),
        keep_warnings = (False, 'env'),
        modindex_common_prefix = ([], 'html'),
        rst_epilog = (None, 'env'),
        rst_prolog = (None, 'env'),
        trim_doctest_flags = (True, 'env'),
        primary_domain = ('py', 'env'),
        needs_sphinx = (None, None),
        nitpicky = (False, 'env'),
        nitpick_ignore = ([], 'html'),

        # HTML options
        html_theme = ('default', 'html'),
        html_theme_path = ([], 'html'),
        html_theme_options = ({}, 'html'),
        html_title = (lambda self: l_('%s %s documentation') %
                                   (self.project, self.release),
                      'html'),
        html_short_title = (lambda self: self.html_title, 'html'),
        html_style = (None, 'html'),
        html_logo = (None, 'html'),
        html_favicon = (None, 'html'),
        html_static_path = ([], 'html'),
        html_extra_path = ([], 'html'),
        # the real default is locale-dependent
        html_last_updated_fmt = (None, 'html'),
        html_use_smartypants = (True, 'html'),
        html_translator_class = (None, 'html'),
        html_sidebars = ({}, 'html'),
        html_additional_pages = ({}, 'html'),
        html_use_modindex = (True, 'html'),  # deprecated
        html_domain_indices = (True, 'html'),
        html_add_permalinks = (u'\u00B6', 'html'),
        html_use_index = (True, 'html'),
        html_split_index = (False, 'html'),
        html_copy_source = (True, 'html'),
        html_show_sourcelink = (True, 'html'),
        html_use_opensearch = ('', 'html'),
        html_file_suffix = (None, 'html'),
        html_link_suffix = (None, 'html'),
        html_show_copyright = (True, 'html'),
        html_show_sphinx = (True, 'html'),
        html_context = ({}, 'html'),
        html_output_encoding = ('utf-8', 'html'),
        html_compact_lists = (True, 'html'),
        html_secnumber_suffix = ('. ', 'html'),
        html_search_language = (None, 'html'),
        html_search_options = ({}, 'html'),
        html_search_scorer = ('', None),

        # HTML help only options
        htmlhelp_basename = (lambda self: make_filename(self.project), None),

        # Qt help only options
        qthelp_basename = (lambda self: make_filename(self.project), None),

        # Devhelp only options
        devhelp_basename = (lambda self: make_filename(self.project), None),

        # Epub options
        epub_basename = (lambda self: make_filename(self.project), None),
        epub_theme = ('epub', 'html'),
        epub_theme_options = ({}, 'html'),
        epub_title = (lambda self: self.html_title, 'html'),
        epub_author = ('unknown', 'html'),
        epub_language = (lambda self: self.language or 'en', 'html'),
        epub_publisher = ('unknown', 'html'),
        epub_copyright = (lambda self: self.copyright, 'html'),
        epub_identifier = ('unknown', 'html'),
        epub_scheme = ('unknown', 'html'),
        epub_uid = ('unknown', 'env'),
        epub_cover = ((), 'env'),
        epub_guide = ((), 'env'),
        epub_pre_files = ([], 'env'),
        epub_post_files = ([], 'env'),
        epub_exclude_files = ([], 'env'),
        epub_tocdepth = (3, 'env'),
        epub_tocdup = (True, 'env'),
        epub_tocscope = ('default', 'env'),
        epub_fix_images = (False, 'env'),
        epub_max_image_width = (0, 'env'),
        epub_show_urls = ('inline', 'html'),
        epub_use_index = (lambda self: self.html_use_index, 'html'),

        # LaTeX options
        latex_documents = (lambda self: [(self.master_doc,
                                          make_filename(self.project) + '.tex',
                                          self.project,
                                          '', 'manual')],
                           None),
        latex_logo = (None, None),
        latex_appendices = ([], None),
        latex_use_parts = (False, None),
        latex_use_modindex = (True, None),  # deprecated
        latex_domain_indices = (True, None),
        latex_show_urls = ('no', None),
        latex_show_pagerefs = (False, None),
        # paper_size and font_size are still separate values
        # so that you can give them easily on the command line
        latex_paper_size = ('letter', None),
        latex_font_size = ('10pt', None),
        latex_elements = ({}, None),
        latex_additional_files = ([], None),
        latex_docclass = ({}, None),
        # now deprecated - use latex_elements
        latex_preamble = ('', None),

        # text options
        text_sectionchars = ('*=-~"+`', 'env'),
        text_newlines = ('unix', 'env'),

        # manpage options
        man_pages = (lambda self: [(self.master_doc,
                                    make_filename(self.project).lower(),
                                    '%s %s' % (self.project, self.release),
                                    [], 1)],
                     None),
        man_show_urls = (False, None),

        # Texinfo options
        texinfo_documents = (lambda self: [(self.master_doc,
                                            make_filename(self.project).lower(),
                                            self.project, '',
                                            make_filename(self.project),
                                            'The %s reference manual.' %
                                            make_filename(self.project),
                                            'Python')],
                             None),
        texinfo_appendices = ([], None),
        texinfo_elements = ({}, None),
        texinfo_domain_indices = (True, None),
        texinfo_show_urls = ('footnote', None),
        texinfo_no_detailmenu = (False, None),

        # linkcheck options
        linkcheck_ignore = ([], None),
        linkcheck_timeout = (None, None),
        linkcheck_workers = (5, None),
        linkcheck_anchors = (True, None),

        # gettext options
        gettext_compact = (True, 'gettext'),

        # XML options
        xml_pretty = (True, 'env'),
    )

    def __init__(self, dirname, filename, overrides, tags):
        self.overrides = overrides
        self.values = Config.config_values.copy()
        config = {}
        if "extensions" in overrides:
            config["extensions"] = overrides["extensions"]
        if dirname is not None:
            config_file = path.join(dirname, filename)
            config['__file__'] = config_file
            config['tags'] = tags
            olddir = os.getcwd()
            try:
                # we promise to have the config dir as current dir while the
                # config file is executed
                os.chdir(dirname)
                try:
                    execfile_(filename, config)
                except SyntaxError, err:
                    raise ConfigError(CONFIG_SYNTAX_ERROR % err)
            finally:
                os.chdir(olddir)

        self._raw_config = config
        # these two must be preinitialized because extensions can add their
        # own config values
        self.setup = config.get('setup', None)
        self.extensions = config.get('extensions', [])

    def check_unicode(self, warn):
        # check all string values for non-ASCII characters in bytestrings,
        # since that can result in UnicodeErrors all over the place
        for name, value in self._raw_config.iteritems():
            if isinstance(value, bytes) and nonascii_re.search(value):
                warn('the config value %r is set to a string with non-ASCII '
                     'characters; this can lead to Unicode errors occurring. '
                     'Please use Unicode strings, e.g. %r.' % (name, u'Content')
                )

    def init_values(self):
        config = self._raw_config
        for valname, value in self.overrides.iteritems():
            if '.' in valname:
                realvalname, key = valname.split('.', 1)
                config.setdefault(realvalname, {})[key] = value
            else:
                config[valname] = value
        for name in config:
            if name in self.values:
                self.__dict__[name] = config[name]
        del self._raw_config

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        if name not in self.values:
            raise AttributeError('No such config value: %s' % name)
        default = self.values[name][0]
        if hasattr(default, '__call__'):
            return default(self)
        return default

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        setattr(self, name, value)

    def __delitem__(self, name):
        delattr(self, name)

    def __contains__(self, name):
        return name in self.values
