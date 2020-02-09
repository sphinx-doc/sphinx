"""
    sphinx.builders.html.ogp
    ~~~~~~~~~~~~~~~~~~~~~~~~

    OGP tag plug-in for HTML builders.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import posixpath
from typing import Any, Dict, Generator, List

from docutils import nodes
from docutils.nodes import Element

from sphinx.application import Sphinx
from sphinx.util.osutil import canon_path


class OGDescriptionCollector(nodes.SparseNodeVisitor):
    """A description collector module for OGP metadata."""

    def __init__(self, document: nodes.document) -> None:
        super().__init__(document)
        self.descriptions = []  # type: List[str]
        self.sections = 0       # type: int

    def visit_compact_paragraph(self, node: Element) -> None:
        if node.get('toctree'):
            # ignore toctree
            raise nodes.SkipChildren

    def visit_section(self, node: Element) -> None:
        self.sections += 1
        if self.sections >= 3:
            # stop processing when the 3rd section found
            raise nodes.StopTraversal

    def visit_paragraph(self, node: Element) -> None:
        # collect paragraph as a part of descriptions
        self.descriptions.append(node.astext())


class OGImageCollector(nodes.SparseNodeVisitor):
    """An image collector module for OGP metadata.

    .. note:: This will be removed on dropping docutils-0.15 support.
              Since 0.16, this class will be replaced by
              ``Element.traverse()``.
    """
    def __init__(self, document: nodes.document) -> None:
        super().__init__(document)
        self.image = None  # type: nodes.image

    def visit_image(self, node: nodes.image) -> None:
        self.image = node
        raise nodes.StopTraversal


def get_ogpmeta_from_context(context: Dict) -> Dict:
    """Pick OGP metadata up from the metadata of the document."""
    htmlmeta = context.get('meta') or {}
    return {k: v for k, v in htmlmeta.items() if k.startswith('og:')}


def apply_html_ogp_meta(app: Sphinx, ogpmeta: Dict) -> None:
    """Apply :confval:`html_ogp_meta` to document specific OGP metadata."""
    for key, value in app.config.html_ogp_meta.items():
        ogpmeta.setdefault(key, value)


def extract_ogpmeta_from_content(app: Sphinx, docname: str, context: Dict,
                                 ogpmeta: Dict, doctree: nodes.document) -> None:
    """Extract OGP metadata from contents."""
    # fill system-default OGP metadata
    ogpmeta.setdefault('og:type', 'website')
    ogpmeta.setdefault('og:title', app.env.titles[docname].astext())

    if app.config.html_baseurl:
        url = posixpath.join(app.config.html_baseurl,
                             docname + app.builder.out_suffix)  # type: ignore
        ogpmeta.setdefault('og:url', url)
    if app.config.project:
        ogpmeta.setdefault('og:site_name', app.config.project)

    # collect og:description from doctree
    if 'og:description' not in ogpmeta:
        dcollector = OGDescriptionCollector(doctree)
        doctree.walkabout(dcollector)

        if dcollector.descriptions:
            description = ' '.join(dcollector.descriptions)
            if len(description) > 200:
                description = description[:197] + "..."

            ogpmeta['og:description'] = description

    # collect og:image from doctree
    if 'og:image' not in ogpmeta:
        icollector = OGImageCollector(doctree)
        doctree.walkabout(icollector)

        if icollector.image:
            if app.config.html_baseurl:
                ogpmeta['og:image'] = posixpath.join(app.config.html_baseurl,
                                                     icollector.image['uri'])
            else:
                ogpmeta['og:image'] = icollector.image['uri']


def _generate_ogp_tags(context: Dict, ogpmeta: Dict) -> Generator[str, None, None]:
    """Generate OGP tags from given *ogpmeta*."""
    pathto = context['pathto']
    for key, value in ogpmeta.items():
        if key == 'og:image':
            # convert og:image to a relative URI from current document.
            try:
                value = pathto(value, True)
            except Exception:
                pass

        yield '<meta property="%s" content="%s" />' % (key, value)


def generate_ogp_tags(app: Sphinx, pagename: str, templatename: str,
                      context: Dict, doctree: nodes.document) -> None:
    """Generate OGP tags for current document."""
    if doctree is None:
        # ignore static pages
        return
    if app.config.html_ogp is False:
        # OGP feature is disabled
        return

    ogpmeta = get_ogpmeta_from_context(context)
    apply_html_ogp_meta(app, ogpmeta)

    if 'og:image' in ogpmeta:
        # convert document specific og:image to a relative path from current document
        ogimage = ogpmeta['og:image']
        relpath, abspath = app.env.relfn2path(ogimage, pagename)
        relpath = canon_path(relpath)
        if app.config.html_baseurl:
            relpath = posixpath.join(app.config.html_baseurl, relpath)
        ogpmeta['og:image'] = relpath

    extract_ogpmeta_from_content(app, pagename, context, ogpmeta, doctree)

    if ogpmeta:
        context['metatags'] += '\n    '
        context['metatags'] += '\n    '.join(_generate_ogp_tags(context, ogpmeta))


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_config_value('html_ogp', True, 'html')
    app.add_config_value('html_ogp_meta', {}, 'html')
    app.connect('html-page-context', generate_ogp_tags)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
