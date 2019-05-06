"""
    sphinx.util.template
    ~~~~~~~~~~~~~~~~~~~~

    Templates utility functions for Sphinx.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

from jinja2.sandbox import SandboxedEnvironment

from sphinx import package_dir
from sphinx.jinja2glue import SphinxFileSystemLoader
from sphinx.locale import get_translator
from sphinx.util import rst, texescape

if False:
    # For type annotation
    from typing import Dict  # NOQA
    from jinja2.loaders import BaseLoader  # NOQA


class BaseRenderer:
    def __init__(self, loader=None):
        # type: (BaseLoader) -> None
        self.env = SandboxedEnvironment(loader=loader, extensions=['jinja2.ext.i18n'])
        self.env.filters['repr'] = repr
        self.env.install_gettext_translations(get_translator())  # type: ignore

    def render(self, template_name, context):
        # type: (str, Dict) -> str
        return self.env.get_template(template_name).render(context)

    def render_string(self, source, context):
        # type: (str, Dict) -> str
        return self.env.from_string(source).render(context)


class FileRenderer(BaseRenderer):
    def __init__(self, search_path):
        # type: (str) -> None
        loader = SphinxFileSystemLoader(search_path)
        super().__init__(loader)

    @classmethod
    def render_from_file(cls, filename, context):
        # type: (str, Dict) -> str
        dirname = os.path.dirname(filename)
        basename = os.path.basename(filename)
        return cls(dirname).render(basename, context)


class SphinxRenderer(FileRenderer):
    def __init__(self, template_path=None):
        # type: (str) -> None
        if template_path is None:
            template_path = os.path.join(package_dir, 'templates')
        super().__init__(template_path)

    @classmethod
    def render_from_file(cls, filename, context):
        # type: (str, Dict) -> str
        return FileRenderer.render_from_file(filename, context)


class LaTeXRenderer(SphinxRenderer):
    def __init__(self, template_path=None):
        # type: (str) -> None
        if template_path is None:
            template_path = os.path.join(package_dir, 'templates', 'latex')
        super().__init__(template_path)

        # use texescape as escape filter
        self.env.filters['e'] = texescape.escape
        self.env.filters['escape'] = texescape.escape
        self.env.filters['eabbr'] = texescape.escape_abbr

        # use JSP/eRuby like tagging instead because curly bracket; the default
        # tagging of jinja2 is not good for LaTeX sources.
        self.env.variable_start_string = '<%='
        self.env.variable_end_string = '%>'
        self.env.block_start_string = '<%'
        self.env.block_end_string = '%>'


class ReSTRenderer(SphinxRenderer):
    def __init__(self, template_path=None, language=None):
        # type: (str, str) -> None
        super().__init__(template_path)

        # add language to environment
        self.env.extend(language=language)

        # use texescape as escape filter
        self.env.filters['e'] = rst.escape
        self.env.filters['escape'] = rst.escape
        self.env.filters['heading'] = rst.heading
