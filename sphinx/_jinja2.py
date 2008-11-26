# -*- coding: utf-8 -*-

"""
    sphinx._jinja2
    ==============

    Glue code for jinja2.

    :author: Sebastian Wiesner
    :contact: basti.wiesner@gmx.net
    :copyright: 2008 by Sebastian Wiesner
    :license: MIT
"""

import codecs
from os import path

import jinja2

from sphinx.util import mtimes_of_files
from sphinx.application import TemplateBridge


class SphinxLoader(jinja2.BaseLoader):
    """
    A jinja2 reimplementation of `sphinx._jinja.SphinxFileSystemLoader`.
    """

    def __init__(self, basepath, extpaths, encoding='utf-8'):
        """
        Creates a new loader for sphinx.

        ``extpaths`` is a list of directories, which provide additional
        templates to sphinx.

        ``encoding`` is used to decode the templates into unicode strings.
        Defaults to utf-8.

        If ``basepath`` is set, this path is used to load sphinx core
        templates.  If False, these templates are loaded from the sphinx
        package.
        """
        self.core_loader = jinja2.FileSystemLoader(basepath)
        self.all_loaders = jinja2.ChoiceLoader(
            [jinja2.FileSystemLoader(extpath) for extpath in extpaths] +
            [self.core_loader])

    def get_source(self, environment, template):
        # exclamation mark forces loading from core
        if template.startswith('!'):
            return self.core_loader.get_source(environment, template[1:])
        # check if the template is probably an absolute path
        fs_path = template.replace('/', path.sep)
        if path.isabs(fs_path):
            if not path.exists(fs_path):
                raise jinja2.TemplateNotFound(template)
            f = codecs.open(fs_path, 'r', self.encoding)
            try:
                mtime = path.getmtime(path)
                return (f.read(), fs_path,
                        lambda: mtime == path.getmtime(path))
            finally:
                f.close()
        # finally try to load from custom templates
        return self.all_loaders.get_source(environment, template)


class BuiltinTemplates(TemplateBridge):
    """
    Interfaces the rendering environment of jinja2 for use in sphinx.
    """

    def init(self, builder):
        base_templates_path = path.join(path.dirname(__file__), 'templates')
        ext_templates_path = [path.join(builder.confdir, dir)
                              for dir in builder.config.templates_path]
        self.templates_path = [base_templates_path] + ext_templates_path
        loader = SphinxLoader(base_templates_path, ext_templates_path)
        use_i18n = builder.translator is not None
        extensions = use_i18n and ['jinja2.ext.i18n'] or []
        self.environment = jinja2.Environment(loader=loader,
                                              extensions=extensions)
        if use_i18n:
            self.environment.install_gettext_translations(builder.translator)

    def render(self, template, context):
        return self.environment.get_template(template).render(context)

    def newest_template_mtime(self):
        return max(mtimes_of_files(self.templates_path, '.html'))
