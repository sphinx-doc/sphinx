# -*- coding: utf-8 -*-
"""
    sphinx.jinja2glue
    ~~~~~~~~~~~~~~~~~

    Glue code for the jinja2 templating engine.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import codecs
from os import path

import jinja2

from sphinx.util import mtimes_of_files
from sphinx.application import TemplateBridge


class BuiltinTemplateLoader(TemplateBridge, jinja2.BaseLoader):
    """
    Interfaces the rendering environment of jinja2 for use in Sphinx.
    """

    # TemplateBridge interface

    def init(self, builder):
        self.theme = builder.theme
        # create a chain of paths to search:
        # the theme's own dir and its bases' dirs
        chain = self.theme.get_dirchain()
        # then the theme parent paths (XXX doc)
        chain.extend(self.theme.themepath)

        # prepend explicit template paths
        if builder.config.templates_path:
            chain[0:0] = [path.join(builder.confdir, tp)
                          for tp in builder.config.templates_path]

        # make the paths into loaders
        self.loaders = map(jinja2.FileSystemLoader, chain)

        use_i18n = builder.translator is not None
        extensions = use_i18n and ['jinja2.ext.i18n'] or []
        self.environment = jinja2.Environment(loader=self,
                                              extensions=extensions)
        if use_i18n:
            self.environment.install_gettext_translations(builder.translator)

    def render(self, template, context):
        return self.environment.get_template(template).render(context)

    def newest_template_mtime(self):
        return max(mtimes_of_files(self.theme.get_dirchain(), '.html'))

    # Loader interface

    def get_source(self, environment, template):
        loaders = self.loaders
        # exclamation mark starts search from base
        if template.startswith('!'):
            loaders = loaders[1:]
            template = template[1:]
        for loader in loaders:
            try:
                return loader.get_source(environment, template)
            except jinja2.TemplateNotFound:
                pass
        raise jinja2.TemplateNotFound(template)
