# -*- coding: utf-8 -*-
"""
    sphinx.ext.jsmath
    ~~~~~~~~~~~~~~~~~

    Set up everything for use of JSMath to display math in HTML
    via JavaScript.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import cast

from docutils import nodes

import sphinx
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.domains.math import MathDomain
from sphinx.errors import ExtensionError
from sphinx.locale import _
from sphinx.util.math import get_node_equation_number

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA
    from sphinx.writers.html import HTMLTranslator  # NOQA
    from sphinx.util.typing import unicode  # NOQA


def html_visit_math(self, node):
    # type: (HTMLTranslator, nodes.math) -> None
    self.body.append(self.starttag(node, 'span', '', CLASS='math notranslate nohighlight'))
    self.body.append(self.encode(node.astext()) + '</span>')
    raise nodes.SkipNode


def html_visit_displaymath(self, node):
    # type: (HTMLTranslator, nodes.math_block) -> None
    if node['nowrap']:
        self.body.append(self.starttag(node, 'div', CLASS='math notranslate nohighlight'))
        self.body.append(self.encode(node.astext()))
        self.body.append('</div>')
        raise nodes.SkipNode
    for i, part in enumerate(node.astext().split('\n\n')):
        part = self.encode(part)
        if i == 0:
            # necessary to e.g. set the id property correctly
            if node['number']:
                number = get_node_equation_number(self, node)
                self.body.append('<span class="eqno">(%s)' % number)
                self.add_permalink_ref(node, _('Permalink to this equation'))
                self.body.append('</span>')
            self.body.append(self.starttag(node, 'div', CLASS='math notranslate nohighlight'))
        else:
            # but only once!
            self.body.append('<div class="math">')
        if '&' in part or '\\\\' in part:
            self.body.append('\\begin{split}' + part + '\\end{split}')
        else:
            self.body.append(part)
        self.body.append('</div>\n')
    raise nodes.SkipNode


def install_jsmath(app, env):
    # type: (Sphinx, BuildEnvironment) -> None
    if app.builder.format != 'html' or app.builder.math_renderer_name != 'jsmath':  # type: ignore  # NOQA
        return
    if not app.config.jsmath_path:
        raise ExtensionError('jsmath_path config value must be set for the '
                             'jsmath extension to work')

    builder = cast(StandaloneHTMLBuilder, app.builder)
    domain = cast(MathDomain, env.get_domain('math'))
    if domain.has_equations():
        # Enable jsmath only if equations exists
        builder.add_js_file(app.config.jsmath_path)


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_html_math_renderer('jsmath',
                               (html_visit_math, None),
                               (html_visit_displaymath, None))

    app.add_config_value('jsmath_path', '', False)
    app.connect('env-check-consistency', install_jsmath)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
