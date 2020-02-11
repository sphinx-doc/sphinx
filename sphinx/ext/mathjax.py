"""
    sphinx.ext.mathjax
    ~~~~~~~~~~~~~~~~~~

    Allow `MathJax <https://www.mathjax.org/>`_ to be used to display math in
    Sphinx's HTML writer -- requires the MathJax JavaScript library on your
    webserver/computer.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import json
from typing import Any, Dict
from typing import cast

from docutils import nodes

import sphinx
from sphinx.application import Sphinx
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.domains.math import MathDomain
from sphinx.environment import BuildEnvironment
from sphinx.errors import ExtensionError
from sphinx.locale import _
from sphinx.util.math import get_node_equation_number
from sphinx.writers.html import HTMLTranslator


def html_visit_math(self: HTMLTranslator, node: nodes.math) -> None:
    self.body.append(self.starttag(node, 'span', '', CLASS='math notranslate nohighlight'))
    self.body.append(self.builder.config.mathjax_inline[0] +
                     self.encode(node.astext()) +
                     self.builder.config.mathjax_inline[1] + '</span>')
    raise nodes.SkipNode


def html_visit_displaymath(self: HTMLTranslator, node: nodes.math_block) -> None:
    self.body.append(self.starttag(node, 'div', CLASS='math notranslate nohighlight'))
    if node['nowrap']:
        self.body.append(self.encode(node.astext()))
        self.body.append('</div>')
        raise nodes.SkipNode

    # necessary to e.g. set the id property correctly
    if node['number']:
        number = get_node_equation_number(self, node)
        self.body.append('<span class="eqno">(%s)' % number)
        self.add_permalink_ref(node, _('Permalink to this equation'))
        self.body.append('</span>')
    self.body.append(self.builder.config.mathjax_display[0])
    parts = [prt for prt in node.astext().split('\n\n') if prt.strip()]
    if len(parts) > 1:  # Add alignment if there are more than 1 equation
        self.body.append(r' \begin{align}\begin{aligned}')
    for i, part in enumerate(parts):
        part = self.encode(part)
        if r'\\' in part:
            self.body.append(r'\begin{split}' + part + r'\end{split}')
        else:
            self.body.append(part)
        if i < len(parts) - 1:  # append new line if not the last equation
            self.body.append(r'\\')
    if len(parts) > 1:  # Add alignment if there are more than 1 equation
        self.body.append(r'\end{aligned}\end{align} ')
    self.body.append(self.builder.config.mathjax_display[1])
    self.body.append('</div>\n')
    raise nodes.SkipNode


def install_mathjax(app: Sphinx, env: BuildEnvironment) -> None:
    if app.builder.format != 'html' or app.builder.math_renderer_name != 'mathjax':  # type: ignore  # NOQA
        return
    if not app.config.mathjax_path:
        raise ExtensionError('mathjax_path config value must be set for the '
                             'mathjax extension to work')

    builder = cast(StandaloneHTMLBuilder, app.builder)
    domain = cast(MathDomain, env.get_domain('math'))
    if domain.has_equations():
        # Enable mathjax only if equations exists
        options = {'async': 'async'}
        if app.config.mathjax_options:
            options.update(app.config.mathjax_options)
        builder.add_js_file(app.config.mathjax_path, **options)

        if app.config.mathjax_config:
            body = "MathJax.Hub.Config(%s)" % json.dumps(app.config.mathjax_config)
            builder.add_js_file(None, type="text/x-mathjax-config", body=body)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_html_math_renderer('mathjax',
                               (html_visit_math, None),
                               (html_visit_displaymath, None))

    # more information for mathjax secure url is here:
    # https://docs.mathjax.org/en/latest/start.html#secure-access-to-the-cdn
    app.add_config_value('mathjax_path',
                         'https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/latest.js?'
                         'config=TeX-AMS-MML_HTMLorMML', 'html')
    app.add_config_value('mathjax_options', {}, 'html')
    app.add_config_value('mathjax_inline', [r'\(', r'\)'], 'html')
    app.add_config_value('mathjax_display', [r'\[', r'\]'], 'html')
    app.add_config_value('mathjax_config', None, 'html')
    app.connect('env-updated', install_mathjax)

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
