# -*- coding: utf-8 -*-
"""
    sphinx.builders.epub3
    ~~~~~~~~~~~~~~~~~~~~~

    Build epub3 files.
    Originally derived from epub.py.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path
from datetime import datetime
from collections import namedtuple

from sphinx import package_dir
from sphinx.config import string_classes, ENUM
from sphinx.builders.epub import EpubBuilder
from sphinx.util import logging
from sphinx.util.fileutil import copy_asset_file

if False:
    # For type annotation
    from typing import Any, Iterable  # NOQA
    from docutils import nodes  # NOQA
    from sphinx.application import Sphinx  # NOQA

logger = logging.getLogger(__name__)


NavPoint = namedtuple('NavPoint', ['text', 'refuri', 'children'])

# writing modes
PAGE_PROGRESSION_DIRECTIONS = {
    'horizontal': 'ltr',
    'vertical': 'rtl',
}
IBOOK_SCROLL_AXIS = {
    'horizontal': 'vertical',
    'vertical': 'horizontal',
}
THEME_WRITING_MODES = {
    'vertical': 'vertical-rl',
    'horizontal': 'horizontal-tb',
}

DOCTYPE = u'''<!DOCTYPE html>'''


class Epub3Builder(EpubBuilder):
    """
    Builder that outputs epub3 files.

    It creates the metainfo files content.opf, nav.xhtml, toc.ncx, mimetype,
    and META-INF/container.xml. Afterwards, all necessary files are zipped to
    an epub file.
    """
    name = 'epub'

    template_dir = path.join(package_dir, 'templates', 'epub3')
    doctype = DOCTYPE

    # Finish by building the epub file
    def handle_finish(self):
        # type: () -> None
        """Create the metainfo files and finally the epub."""
        self.get_toc()
        self.build_mimetype(self.outdir, 'mimetype')
        self.build_container(self.outdir, 'META-INF/container.xml')
        self.build_content(self.outdir, 'content.opf')
        self.build_navigation_doc(self.outdir, 'nav.xhtml')
        self.build_toc(self.outdir, 'toc.ncx')
        self.build_epub(self.outdir, self.config.epub_basename + '.epub')

    def content_metadata(self):
        # type: () -> Dict
        """Create a dictionary with all metadata for the content.opf
        file properly escaped.
        """
        writing_mode = self.config.epub_writing_mode

        metadata = super(Epub3Builder, self).content_metadata()
        metadata['description'] = self.esc(self.config.epub_description)
        metadata['contributor'] = self.esc(self.config.epub_contributor)
        metadata['page_progression_direction'] = PAGE_PROGRESSION_DIRECTIONS.get(writing_mode)
        metadata['ibook_scroll_axis'] = IBOOK_SCROLL_AXIS.get(writing_mode)
        metadata['date'] = self.esc(datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"))
        metadata['version'] = self.esc(self.config.version)
        return metadata

    def prepare_writing(self, docnames):
        # type: (Iterable[unicode]) -> None
        super(Epub3Builder, self).prepare_writing(docnames)

        writing_mode = self.config.epub_writing_mode
        self.globalcontext['theme_writing_mode'] = THEME_WRITING_MODES.get(writing_mode)

    def build_navlist(self, navnodes):
        # type: (List[nodes.Node]) -> List[NavPoint]
        """Create the toc navigation structure.

        This method is almost same as build_navpoints method in epub.py.
        This is because the logical navigation structure of epub3 is not
        different from one of epub2.

        The difference from build_navpoints method is templates which are used
        when generating navigation documents.
        """
        navstack = []  # type: List[NavPoint]
        navstack.append(NavPoint('', '', []))
        level = 0
        for node in navnodes:
            if not node['text']:
                continue
            file = node['refuri'].split('#')[0]
            if file in self.ignored_files:
                continue
            if node['level'] > self.config.epub_tocdepth:
                continue

            navpoint = NavPoint(node['text'], node['refuri'], [])
            if node['level'] == level:
                navstack.pop()
                navstack[-1].children.append(navpoint)
                navstack.append(navpoint)
            elif node['level'] == level + 1:
                level += 1
                navstack[-1].children.append(navpoint)
                navstack.append(navpoint)
            elif node['level'] < level:
                while node['level'] < len(navstack):
                    navstack.pop()
                level = node['level']
                navstack[-1].children.append(navpoint)
                navstack.append(navpoint)
            else:
                raise

        return navstack[0].children

    def navigation_doc_metadata(self, navlist):
        # type: (List[NavPoint]) -> Dict
        """Create a dictionary with all metadata for the nav.xhtml file
        properly escaped.
        """
        metadata = {}  # type: Dict
        metadata['lang'] = self.esc(self.config.epub_language)
        metadata['toc_locale'] = self.esc(self.guide_titles['toc'])
        metadata['navlist'] = navlist
        return metadata

    def build_navigation_doc(self, outdir, outname):
        # type: (unicode, unicode) -> None
        """Write the metainfo file nav.xhtml."""
        logger.info('writing %s file...', outname)

        if self.config.epub_tocscope == 'default':
            doctree = self.env.get_and_resolve_doctree(
                self.config.master_doc, self,
                prune_toctrees=False, includehidden=False)
            refnodes = self.get_refnodes(doctree, [])
            self.toc_add_files(refnodes)
        else:
            # 'includehidden'
            refnodes = self.refnodes
        navlist = self.build_navlist(refnodes)
        copy_asset_file(path.join(self.template_dir, 'nav.xhtml_t'),
                        path.join(outdir, outname),
                        self.navigation_doc_metadata(navlist))

        # Add nav.xhtml to epub file
        if outname not in self.files:
            self.files.append(outname)


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.setup_extension('sphinx.builders.epub')
    app.add_builder(Epub3Builder)

    app.add_config_value('epub_description', '', 'epub3', string_classes)
    app.add_config_value('epub_contributor', 'unknown', 'epub3', string_classes)
    app.add_config_value('epub_writing_mode', 'horizontal', 'epub3',
                         ENUM('horizontal', 'vertical'))

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
