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
from pprint import pformat

from jinja2 import FileSystemLoader, BaseLoader, TemplateNotFound, contextfunction
from jinja2.sandbox import SandboxedEnvironment

from sphinx.util import mtimes_of_files
from sphinx.application import TemplateBridge


def _tobool(val):
    if isinstance(val, basestring):
        return val.lower() in ('true', '1', 'yes', 'on')
    return bool(val)


class BuiltinTemplateLoader(TemplateBridge, BaseLoader):
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
        self.templatepathlen = len(builder.config.templates_path)
        if builder.config.templates_path:
            chain[0:0] = [path.join(builder.confdir, tp)
                          for tp in builder.config.templates_path]

        # store it for use in newest_template_mtime
        self.pathchain = chain

        # make the paths into loaders
        self.loaders = map(FileSystemLoader, chain)

        use_i18n = builder.translator is not None
        extensions = use_i18n and ['jinja2.ext.i18n'] or []
        self.environment = SandboxedEnvironment(loader=self,
                                                extensions=extensions)
        self.environment.filters['tobool'] = _tobool
        self.environment.globals['debug'] = contextfunction(pformat)
        if use_i18n:
            self.environment.install_gettext_translations(builder.translator)

    def render(self, template, context):
        return self.environment.get_template(template).render(context)

    def render_string(self, source, context):
        return self.environment.from_string(source).render(context)

    def newest_template_mtime(self):
        return max(mtimes_of_files(self.pathchain, '.html'))

    # Loader interface

    def get_source(self, environment, template):
        loaders = self.loaders
        # exclamation mark starts search from theme
        if template.startswith('!'):
            loaders = loaders[self.templatepathlen:]
            template = template[1:]
        for loader in loaders:
            try:
                return loader.get_source(environment, template)
            except TemplateNotFound:
                pass
        raise TemplateNotFound(template)
