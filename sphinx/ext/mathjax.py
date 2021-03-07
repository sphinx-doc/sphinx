"""
    sphinx.ext.mathjax
    ~~~~~~~~~~~~~~~~~~

    Allow `MathJax <https://www.mathjax.org/>`_ to be used to display math in
    Sphinx's HTML writer -- requires the MathJax JavaScript library on your
    webserver/computer.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import json
from typing import Any, Dict, cast

from docutils import nodes

import sphinx
from sphinx.application import Sphinx
from sphinx.domains.math import MathDomain
from sphinx.errors import ExtensionError
from sphinx.locale import _, __
from sphinx.util import logging
from sphinx.util.math import get_node_equation_number
from sphinx.writers.html import HTMLTranslator

logger = logging.getLogger(__name__)

# more information for mathjax secure url is here:
# https://docs.mathjax.org/en/latest/web/configuration.html#loading-mathjax
MATHJAX_URL = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js'


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


def install_mathjax(app: Sphinx, pagename: str, templatename: str, context: Dict,
                    event_arg: Any) -> None:
    if app.builder.format != 'html' or app.builder.math_renderer_name != 'mathjax':  # type: ignore  # NOQA
        return
    if not app.config.mathjax_path:
        raise ExtensionError('mathjax_path config value must be set for the '
                             'mathjax extension to work')

    domain = cast(MathDomain, app.env.get_domain('math'))

    # Enable mathjax only if equations exists
    if domain.has_equations(pagename):
        # The configuration script must come before the MathJax script
        if app.config.mathjax_config:
            mathjax2_options = {
                # Core options: https://docs.mathjax.org/en/v2.7-latest/options/hub.html
                "jax", "extensions", "config", "styleSheets", "styles", "preJax", "postJax",
                "preRemoveClass", "showProcessingMessages", "messageStyle", "displayAlign",
                "displayIndent", "delayStartupUntil", "skipStartupTypeset", "elements",
                "positionToHash", "showMathMenu", "showMathMenuMSIE", "menuSettings",
                "errorSettings", "ignoreMMLattributes", "root", "v1.0-compatible",
                # TeX preprocessor and processor options
                # https://docs.mathjax.org/en/v2.7-latest/options/preprocessors/tex2jax.html
                # https://docs.mathjax.org/en/v2.7-latest/options/input-processors/TeX.html
                "tex2jax", "TeX",
                # Output processor options
                # https://docs.mathjax.org/en/v2.7-latest/options/output-processors/HTML-CSS.html
                "HTML-CSS",
                # https://docs.mathjax.org/en/v2.7-latest/options/output-processors/CommonHTML.html
                "CommonHTML"
            }
            configured_for_v2 = set(app.config.mathjax_config.keys()) & mathjax2_options
            default_url = app.config.mathjax_path == MATHJAX_URL
            if (configured_for_v2 and default_url and not app.config.mathjax_no_v2_warning):
                mj2_url = ("https://docs.mathjax.org/en/v2.7-latest/start.html#using-a-"
                           "content-delivery-network-cdn")
                logger.warning(__("'mathjax_config' appears to be for MathJax v2. You may "
                                  "need to set the 'mathjax_path' option to load MathJax v2, "
                                  "see %s.\nThis message can be suppressed by setting "
                                  "'mathjax_no_v2_warning' to be 'True' in conf.py."), mj2_url)
            body = "window.MathJax = {:s}".format(json.dumps(app.config.mathjax_config))
            app.add_js_file(None, body=body)

        options = {'async': 'async'}
        if app.config.mathjax_options:
            options.update(app.config.mathjax_options)
        app.add_js_file(app.config.mathjax_path, **options)  # type: ignore


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_html_math_renderer('mathjax',
                               (html_visit_math, None),
                               (html_visit_displaymath, None))

    app.add_config_value('mathjax_path', MATHJAX_URL, 'html')
    app.add_config_value('mathjax_options', {}, 'html')
    app.add_config_value('mathjax_inline', [r'\(', r'\)'], 'html')
    app.add_config_value('mathjax_display', [r'\[', r'\]'], 'html')
    app.add_config_value('mathjax_config', None, 'html')
    app.add_config_value('mathjax_no_v2_warning', False, 'html')
    app.connect('html-page-context', install_mathjax)

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
