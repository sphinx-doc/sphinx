# -*- coding: utf-8 -*-
"""
    sphinx.builders.qthelp
    ~~~~~~~~~~~~~~~~~~~~~~

    Build input files for the Qt collection generator.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import cgi
import codecs
from os import path

from docutils import nodes

from sphinx import addnodes
from sphinx.locale import _
from sphinx.builders.html import StandaloneHTMLBuilder

_idpattern = re.compile(
    r'(?P<title>.+) (\((?P<id>[\w\.]+)( (?P<descr>\w+))?\))$')


# Qt Help Collection Project (.qhcp).
# Is the input file for the help collection generator.
# It contains references to compressed help files which should be
# included in the collection.
# It may contain various other information for customizing Qt Assistant.
collection_template = u'''\
<?xml version="1.0" encoding="utf-8" ?>
<QHelpCollectionProject version="1.0">
    <docFiles>
        <generate>
            <file>
                <input>%(outname)s.qhp</input>
                <output>%(outname)s.qch</output>
            </file>
        </generate>
        <register>
            <file>%(outname)s.qch</file>
        </register>
    </docFiles>
</QHelpCollectionProject>
'''

# Qt Help Project (.qhp)
# This is the input file for the help generator.
# It contains the table of contents, indices and references to the
# actual documentation files (*.html).
# In addition it defines a unique namespace for the documentation.
project_template = u'''\
<?xml version="1.0" encoding="UTF-8"?>
<QtHelpProject version="1.0">
    <namespace>%(outname)s.org.%(outname)s.%(nversion)s</namespace>
    <virtualFolder>doc</virtualFolder>
    <customFilter name="%(project)s %(version)s">
        <filterAttribute>%(outname)s</filterAttribute>
        <filterAttribute>%(version)s</filterAttribute>
    </customFilter>
    <filterSection>
        <filterAttribute>%(outname)s</filterAttribute>
        <filterAttribute>%(version)s</filterAttribute>
        <toc>
            <section title="%(title)s" ref="%(masterdoc)s.html">
%(sections)s
            </section>
        </toc>
        <keywords>
%(keywords)s
        </keywords>
        <files>
%(files)s
        </files>
    </filterSection>
</QtHelpProject>
'''

section_template = '<section title="%(title)s" ref="%(ref)s"/>'
file_template = ' '*12 + '<file>%(filename)s</file>'


class QtHelpBuilder(StandaloneHTMLBuilder):
    """
    Builder that also outputs Qt help project, contents and index files.
    """
    name = 'qthelp'

    # don't copy the reST source
    copysource = False
    supported_image_types = ['image/svg+xml', 'image/png', 'image/gif',
                             'image/jpeg']

    # don't add links
    add_permalinks = False
    # don't add sidebar etc.
    embedded = True

    def init(self):
        StandaloneHTMLBuilder.init(self)
        # the output files for HTML help must be .html only
        self.out_suffix = '.html'
        #self.config.html_style = 'traditional.css'

    def handle_finish(self):
        self.build_qhcp(self.outdir, self.config.qthelp_basename)
        self.build_qhp(self.outdir, self.config.qthelp_basename)

    def build_qhcp(self, outdir, outname):
        self.info('writing collection project file...')
        f = codecs.open(path.join(outdir, outname+'.qhcp'), 'w', 'utf-8')
        try:
            f.write(collection_template % {'outname': outname})
        finally:
            f.close()

    def build_qhp(self, outdir, outname):
        self.info('writing project file...')

        # sections
        tocdoc = self.env.get_and_resolve_doctree(self.config.master_doc, self,
                                                  prune_toctrees=False)
        istoctree = lambda node: (
                        isinstance(node, addnodes.compact_paragraph)
                            and node.has_key('toctree'))
        sections = []
        for node in tocdoc.traverse(istoctree):
            sections.extend(self.write_toc(node))

        if self.config.html_use_modindex:
            item = section_template % {'title': _('Global Module Index'),
                                       'ref': 'modindex.html'}
            sections.append(' '*4*4 + item)
        sections = '\n'.join(sections)

        # keywords
        keywords = []
        index = self.env.create_index(self)
        for (key, group) in index:
            for title, (refs, subitems) in group:
                keywords.extend(self.build_keywords(title, refs, subitems))
        keywords = '\n'.join(keywords)

        # files
        if not outdir.endswith(os.sep):
            outdir += os.sep
        olen = len(outdir)
        projectfiles = []
        staticdir = path.join(outdir, '_static')
        imagesdir = path.join(outdir, '_images')
        for root, dirs, files in os.walk(outdir):
            resourcedir = root.startswith(staticdir) or \
                          root.startswith(imagesdir)
            for fn in files:
                if (resourcedir and not fn.endswith('.js')) or \
                       fn.endswith('.html'):
                    filename = path.join(root, fn)[olen:]
                    #filename = filename.replace(os.sep, '\\') # XXX
                    projectfiles.append(file_template % {'filename': filename})
        projectfiles = '\n'.join(projectfiles)

        # write the project file
        f = codecs.open(path.join(outdir, outname+'.qhp'), 'w', 'utf-8')
        try:
            nversion = self.config.version.replace('.', '_')
            nversion = nversion.replace(' ', '_')
            f.write(project_template % {'outname': outname,
                                        'title': self.config.html_title,
                                        'version': self.config.version,
                                        'project': self.config.project,
                                        'nversion': nversion,
                                        'masterdoc': self.config.master_doc,
                                        'sections': sections,
                                        'keywords': keywords,
                                        'files': projectfiles})
        finally:
            f.close()

    def isdocnode(self, node):
        if not isinstance(node, nodes.list_item):
            return False
        if len(node.children) != 2:
            return False
        if not isinstance(node.children[0], addnodes.compact_paragraph):
            return False
        if not isinstance(node.children[0][0], nodes.reference):
            return False
        if not isinstance(node.children[1], nodes.bullet_list):
            return False
        return True

    def write_toc(self, node, indentlevel=4):
        parts = []
        if self.isdocnode(node):
            refnode = node.children[0][0]
            link = refnode['refuri']
            title = cgi.escape(refnode.astext()).replace('"','&quot;')
            item = '<section title="%(title)s" ref="%(ref)s">' % {
                                                                'title': title,
                                                                'ref': link}
            parts.append(' '*4*indentlevel + item)
            for subnode in node.children[1]:
                parts.extend(self.write_toc(subnode, indentlevel+1))
            parts.append(' '*4*indentlevel + '</section>')
        elif isinstance(node, nodes.list_item):
            for subnode in node:
                parts.extend(self.write_toc(subnode, indentlevel))
        elif isinstance(node, nodes.reference):
            link = node['refuri']
            title = cgi.escape(node.astext()).replace('"','&quot;')
            item = section_template % {'title': title, 'ref': link}
            item = ' '*4*indentlevel + item.encode('ascii', 'xmlcharrefreplace')
            parts.append(item.encode('ascii', 'xmlcharrefreplace'))
        elif isinstance(node, nodes.bullet_list):
            for subnode in node:
                parts.extend(self.write_toc(subnode, indentlevel))
        elif isinstance(node, addnodes.compact_paragraph):
            for subnode in node:
                parts.extend(self.write_toc(subnode, indentlevel))

        return parts

    def keyword_item(self, name, ref):
        matchobj = _idpattern.match(name)
        if matchobj:
            groupdict = matchobj.groupdict()
            shortname = groupdict['title']
            id = groupdict.get('id')
#            descr = groupdict.get('descr')
            if shortname.endswith('()'):
                shortname = shortname[:-2]
            id = '%s.%s' % (id, shortname)
        else:
            id = None

        if id:
            item = ' '*12 + '<keyword name="%s" id="%s" ref="%s"/>' % (
                                                                name, id, ref)
        else:
            item = ' '*12 + '<keyword name="%s" ref="%s"/>' % (name, ref)
        item.encode('ascii', 'xmlcharrefreplace')
        return item

    def build_keywords(self, title, refs, subitems):
        keywords = []

        title = cgi.escape(title)
#        if len(refs) == 0: # XXX
#            write_param('See Also', title)
        if len(refs) == 1:
            keywords.append(self.keyword_item(title, refs[0]))
        elif len(refs) > 1:
            for i, ref in enumerate(refs):  # XXX
#                item = (' '*12 +
#                        '<keyword name="%s [%d]" ref="%s"/>' % (
#                                                        title, i, ref))
#                item.encode('ascii', 'xmlcharrefreplace')
#                keywords.append(item)
                keywords.append(self.keyword_item(title, ref))

        if subitems:
            for subitem in subitems:
                keywords.extend(self.build_keywords(subitem[0], subitem[1], []))

        return keywords
