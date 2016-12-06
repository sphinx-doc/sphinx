# -*- coding: utf-8 -*-
"""
    sphinx.util.template
    ~~~~~~~~~~~~~~~~~~~~

    Templates utility functions for Sphinx.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from jinja2.sandbox import SandboxedEnvironment

from sphinx import package_dir
from sphinx.jinja2glue import SphinxFileSystemLoader


class BaseRenderer(object):
    def __init__(self, loader=None):
        self.env = SandboxedEnvironment(loader=loader)
        self.env.filters['repr'] = repr

    def render(self, template_name, context):
        return self.env.get_template(template_name).render(context)

    def render_string(self, source, context):
        return self.env.from_string(source).render(context)


class FileRenderer(BaseRenderer):
    def __init__(self, search_path):
        loader = SphinxFileSystemLoader(search_path)
        super(FileRenderer, self).__init__(loader)

    @classmethod
    def render_from_file(cls, filename, context):
        dirname = os.path.dirname(filename)
        basename = os.path.basename(filename)
        return cls(dirname).render(basename, context)


class SphinxRenderer(FileRenderer):
    def __init__(self):
        super(SphinxRenderer, self).__init__(os.path.join(package_dir, 'templates'))

    @classmethod
    def render_from_file(cls, filename, context):
        return FileRenderer.render_from_file(filename, context)


class LaTeXRenderer(SphinxRenderer):
    def __init__(self):
        super(LaTeXRenderer, self).__init__()

        # use JSP/eRuby like tagging instead because curly bracket; the default
        # tagging of jinja2 is not good for LaTeX sources.
        self.env.variable_start_string = '<%='
        self.env.variable_end_string = '%>'
        self.env.block_start_string = '<%'
        self.env.block_end_string = '%>'
