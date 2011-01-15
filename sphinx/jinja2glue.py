# -*- coding: utf-8 -*-
"""
    sphinx.jinja2glue
    ~~~~~~~~~~~~~~~~~

    Glue code for the jinja2 templating engine.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path
from pprint import pformat

from jinja2 import FileSystemLoader, BaseLoader, TemplateNotFound, \
     contextfunction
from jinja2.utils import open_if_exists
from jinja2.sandbox import SandboxedEnvironment

from sphinx.application import TemplateBridge
from sphinx.util.osutil import mtimes_of_files


def _tobool(val):
    if isinstance(val, basestring):
        return val.lower() in ('true', '1', 'yes', 'on')
    return bool(val)

def accesskey(context, key):
    """Helper to output each access key only once."""
    if '_accesskeys' not in context:
        context.vars['_accesskeys'] = {}
    if key and key not in context.vars['_accesskeys']:
        context.vars['_accesskeys'][key] = 1
        return 'accesskey="%s"' % key
    return ''

class idgen(object):
    def __init__(self):
        self.id = 0
    def current(self):
        return self.id
    def next(self):
        self.id += 1
        return self.id


class SphinxFileSystemLoader(FileSystemLoader):
    """FileSystemLoader subclass that is not so strict about '..'
    entries in template names."""

    def get_source(self, environment, template):
        for searchpath in self.searchpath:
            filename = path.join(searchpath, template)
            f = open_if_exists(filename)
            if f is None:
                continue
            try:
                contents = f.read().decode(self.encoding)
            finally:
                f.close()

            mtime = path.getmtime(filename)
            def uptodate():
                try:
                    return path.getmtime(filename) == mtime
                except OSError:
                    return False
            return contents, filename, uptodate
        raise TemplateNotFound(template)



class BuiltinTemplateLoader(TemplateBridge, BaseLoader):
    """
    Interfaces the rendering environment of jinja2 for use in Sphinx.
    """

    # TemplateBridge interface

    def init(self, builder, theme=None, dirs=None):
        # create a chain of paths to search
        if theme:
            # the theme's own dir and its bases' dirs
            chain = theme.get_dirchain()
            # then the theme parent paths
            chain.extend(theme.themepath)
        elif dirs:
            chain = list(dirs)
        else:
            chain = []

        # prepend explicit template paths
        self.templatepathlen = len(builder.config.templates_path)
        if builder.config.templates_path:
            chain[0:0] = [path.join(builder.confdir, tp)
                          for tp in builder.config.templates_path]

        # store it for use in newest_template_mtime
        self.pathchain = chain

        # make the paths into loaders
        self.loaders = map(SphinxFileSystemLoader, chain)

        use_i18n = builder.app.translator is not None
        extensions = use_i18n and ['jinja2.ext.i18n'] or []
        self.environment = SandboxedEnvironment(loader=self,
                                                extensions=extensions)
        self.environment.filters['tobool'] = _tobool
        self.environment.globals['debug'] = contextfunction(pformat)
        self.environment.globals['accesskey'] = contextfunction(accesskey)
        self.environment.globals['idgen'] = idgen
        if use_i18n:
            self.environment.install_gettext_translations(
                builder.app.translator)

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
