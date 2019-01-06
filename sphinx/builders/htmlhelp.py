"""
    sphinx.builders.htmlhelp
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Build HTML help support files.
    Parts adapted from Python's Doc/tools/prechm.py.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import html
import os
import warnings
from os import path

from docutils import nodes

from sphinx import addnodes
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.environment.adapters.indexentries import IndexEntries
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.nodes import NodeMatcher
from sphinx.util.osutil import make_filename_from_project

if False:
    # For type annotation
    from typing import Any, Dict, IO, List, Match, Tuple  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.config import Config  # NOQA


logger = logging.getLogger(__name__)


# Project file (*.hhp) template.  'outname' is the file basename (like
# the pythlp in pythlp.hhp); 'version' is the doc version number (like
# the 2.2 in Python 2.2).
# The magical numbers in the long line under [WINDOWS] set most of the
# user-visible features (visible buttons, tabs, etc).
# About 0x10384e:  This defines the buttons in the help viewer.  The
# following defns are taken from htmlhelp.h.  Not all possibilities
# actually work, and not all those that work are available from the Help
# Workshop GUI.  In particular, the Zoom/Font button works and is not
# available from the GUI.  The ones we're using are marked with 'x':
#
#    0x000002   Hide/Show   x
#    0x000004   Back        x
#    0x000008   Forward     x
#    0x000010   Stop
#    0x000020   Refresh
#    0x000040   Home        x
#    0x000080   Forward
#    0x000100   Back
#    0x000200   Notes
#    0x000400   Contents
#    0x000800   Locate      x
#    0x001000   Options     x
#    0x002000   Print       x
#    0x004000   Index
#    0x008000   Search
#    0x010000   History
#    0x020000   Favorites
#    0x040000   Jump 1
#    0x080000   Jump 2
#    0x100000   Zoom/Font   x
#    0x200000   TOC Next
#    0x400000   TOC Prev

project_template = '''\
[OPTIONS]
Binary TOC=No
Binary Index=No
Compiled file=%(outname)s.chm
Contents file=%(outname)s.hhc
Default Window=%(outname)s
Default topic=%(master_doc)s
Display compile progress=No
Full text search stop list file=%(outname)s.stp
Full-text search=Yes
Index file=%(outname)s.hhk
Language=%(lcid)#x
Title=%(title)s

[WINDOWS]
%(outname)s="%(title)s","%(outname)s.hhc","%(outname)s.hhk",\
"%(master_doc)s","%(master_doc)s",,,,,0x63520,220,0x10384e,[0,0,1024,768],,,,,,,0

[FILES]
'''

contents_header = '''\
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML//EN">
<HTML>
<HEAD>
<meta name="GENERATOR" content="Microsoft&reg; HTML Help Workshop 4.1">
<!-- Sitemap 1.0 -->
</HEAD><BODY>
<OBJECT type="text/site properties">
        <param name="Window Styles" value="0x801227">
        <param name="ImageType" value="Folder">
</OBJECT>
<UL>
'''

contents_footer = '''\
</UL></BODY></HTML>
'''

object_sitemap = '''\
<OBJECT type="text/sitemap">
    <param name="Name" value="%s">
    <param name="Local" value="%s">
</OBJECT>
'''

# List of words the full text search facility shouldn't index.  This
# becomes file outname.stp.  Note that this list must be pretty small!
# Different versions of the MS docs claim the file has a maximum size of
# 256 or 512 bytes (including \r\n at the end of each line).
# Note that "and", "or", "not" and "near" are operators in the search
# language, so no point indexing them even if we wanted to.
stopwords = """
a  and  are  as  at
be  but  by
for
if  in  into  is  it
near  no  not
of  on  or
such
that  the  their  then  there  these  they  this  to
was  will  with
""".split()

# The following list includes only languages supported by Sphinx. See
# https://docs.microsoft.com/en-us/previous-versions/windows/embedded/ms930130(v=msdn.10)
# for more.
chm_locales = {
    # lang:   LCID,  encoding
    'ca':    (0x403, 'cp1252'),
    'cs':    (0x405, 'cp1250'),
    'da':    (0x406, 'cp1252'),
    'de':    (0x407, 'cp1252'),
    'en':    (0x409, 'cp1252'),
    'es':    (0x40a, 'cp1252'),
    'et':    (0x425, 'cp1257'),
    'fa':    (0x429, 'cp1256'),
    'fi':    (0x40b, 'cp1252'),
    'fr':    (0x40c, 'cp1252'),
    'hr':    (0x41a, 'cp1250'),
    'hu':    (0x40e, 'cp1250'),
    'it':    (0x410, 'cp1252'),
    'ja':    (0x411, 'cp932'),
    'ko':    (0x412, 'cp949'),
    'lt':    (0x427, 'cp1257'),
    'lv':    (0x426, 'cp1257'),
    'nl':    (0x413, 'cp1252'),
    'no_NB': (0x414, 'cp1252'),
    'pl':    (0x415, 'cp1250'),
    'pt_BR': (0x416, 'cp1252'),
    'ru':    (0x419, 'cp1251'),
    'sk':    (0x41b, 'cp1250'),
    'sl':    (0x424, 'cp1250'),
    'sv':    (0x41d, 'cp1252'),
    'tr':    (0x41f, 'cp1254'),
    'uk_UA': (0x422, 'cp1251'),
    'zh_CN': (0x804, 'cp936'),
    'zh_TW': (0x404, 'cp950'),
}


def chm_htmlescape(s, quote=True):
    # type: (str, bool) -> str
    """
    chm_htmlescape() is a wrapper of html.escape().
    .hhc/.hhk files don't recognize hex escaping, we need convert
    hex escaping to decimal escaping. for example: ``&#x27;`` -> ``&#39;``
    html.escape() may generates a hex escaping ``&#x27;`` for single
    quote ``'``, this wrapper fixes this.
    """
    s = html.escape(s, quote)
    s = s.replace('&#x27;', '&#39;')    # re-escape as decimal
    return s


class HTMLHelpBuilder(StandaloneHTMLBuilder):
    """
    Builder that also outputs Windows HTML help project, contents and
    index files.  Adapted from the original Doc/tools/prechm.py.
    """
    name = 'htmlhelp'
    epilog = __('You can now run HTML Help Workshop with the .htp file in '
                '%(outdir)s.')

    # don't copy the reST source
    copysource = False
    supported_image_types = ['image/png', 'image/gif', 'image/jpeg']

    # don't add links
    add_permalinks = False
    # don't add sidebar etc.
    embedded = True

    # don't generate search index or include search page
    search = False

    lcid = 0x409
    encoding = 'cp1252'

    def init(self):
        # type: () -> None
        # the output files for HTML help is .html by default
        self.out_suffix = '.html'
        self.link_suffix = '.html'
        super().init()
        # determine the correct locale setting
        locale = chm_locales.get(self.config.language)
        if locale is not None:
            self.lcid, self.encoding = locale

    def open_file(self, outdir, basename, mode='w'):
        # type: (str, str, str) -> IO
        # open a file with the correct encoding for the selected language
        warnings.warn('HTMLHelpBuilder.open_file() is deprecated.',
                      RemovedInSphinx40Warning)
        return open(path.join(outdir, basename), mode, encoding=self.encoding,
                    errors='xmlcharrefreplace')

    def update_page_context(self, pagename, templatename, ctx, event_arg):
        # type: (str, str, Dict, str) -> None
        ctx['encoding'] = self.encoding

    def handle_finish(self):
        # type: () -> None
        self.build_hhx(self.outdir, self.config.htmlhelp_basename)

    def write_doc(self, docname, doctree):
        # type: (str, nodes.document) -> None
        for node in doctree.traverse(nodes.reference):
            # add ``target=_blank`` attributes to external links
            if node.get('internal') is None and 'refuri' in node:
                node['target'] = '_blank'

        super().write_doc(docname, doctree)

    def build_hhx(self, outdir, outname):
        # type: (str, str) -> None
        logger.info(__('dumping stopword list...'))
        filename = path.join(outdir, outname + '.stp')
        with open(filename, 'w', encoding=self.encoding, errors='xmlcharrefreplace') as f:
            for word in sorted(stopwords):
                print(word, file=f)

        logger.info(__('writing project file...'))
        filename = path.join(outdir, outname + '.hhp')
        with open(filename, 'w', encoding=self.encoding, errors='xmlcharrefreplace') as f:
            f.write(project_template % {
                'outname': outname,
                'title': self.config.html_title,
                'version': self.config.version,
                'project': self.config.project,
                'lcid': self.lcid,
                'master_doc': self.config.master_doc + self.out_suffix
            })
            if not outdir.endswith(os.sep):
                outdir += os.sep
            olen = len(outdir)
            for root, dirs, files in os.walk(outdir):
                dirs.sort()
                files.sort()
                staticdir = root.startswith(path.join(outdir, '_static'))
                for fn in sorted(files):
                    if (staticdir and not fn.endswith('.js')) or \
                       fn.endswith('.html'):
                        print(path.join(root, fn)[olen:].replace(os.sep, '\\'),
                              file=f)

        logger.info(__('writing TOC file...'))
        filename = path.join(outdir, outname + '.hhc')
        with open(filename, 'w', encoding=self.encoding, errors='xmlcharrefreplace') as f:
            f.write(contents_header)
            # special books
            f.write('<LI> ' + object_sitemap % (self.config.html_short_title,
                                                self.config.master_doc + self.out_suffix))
            for indexname, indexcls, content, collapse in self.domain_indices:
                f.write('<LI> ' + object_sitemap % (indexcls.localname,
                                                    '%s.html' % indexname))
            # the TOC
            tocdoc = self.env.get_and_resolve_doctree(
                self.config.master_doc, self, prune_toctrees=False)

            def write_toc(node, ullevel=0):
                # type: (nodes.Node, int) -> None
                if isinstance(node, nodes.list_item):
                    f.write('<LI> ')
                    for subnode in node:
                        write_toc(subnode, ullevel)
                elif isinstance(node, nodes.reference):
                    link = node['refuri']
                    title = chm_htmlescape(node.astext(), True)
                    f.write(object_sitemap % (title, link))
                elif isinstance(node, nodes.bullet_list):
                    if ullevel != 0:
                        f.write('<UL>\n')
                    for subnode in node:
                        write_toc(subnode, ullevel + 1)
                    if ullevel != 0:
                        f.write('</UL>\n')
                elif isinstance(node, addnodes.compact_paragraph):
                    for subnode in node:
                        write_toc(subnode, ullevel)

            matcher = NodeMatcher(addnodes.compact_paragraph, toctree=True)
            for node in tocdoc.traverse(matcher):  # type: addnodes.compact_paragraph
                write_toc(node)
            f.write(contents_footer)

        logger.info(__('writing index file...'))
        index = IndexEntries(self.env).create_index(self)
        filename = path.join(outdir, outname + '.hhk')
        with open(filename, 'w', encoding=self.encoding, errors='xmlcharrefreplace') as f:
            f.write('<UL>\n')

            def write_index(title, refs, subitems):
                # type: (str, List[Tuple[str, str]], List[Tuple[str, List[Tuple[str, str]]]]) -> None  # NOQA
                def write_param(name, value):
                    # type: (str, str) -> None
                    item = '    <param name="%s" value="%s">\n' % (name, value)
                    f.write(item)
                title = chm_htmlescape(title, True)
                f.write('<LI> <OBJECT type="text/sitemap">\n')
                write_param('Keyword', title)
                if len(refs) == 0:
                    write_param('See Also', title)
                elif len(refs) == 1:
                    write_param('Local', refs[0][1])
                else:
                    for i, ref in enumerate(refs):
                        # XXX: better title?
                        write_param('Name', '[%d] %s' % (i, ref[1]))
                        write_param('Local', ref[1])
                f.write('</OBJECT>\n')
                if subitems:
                    f.write('<UL> ')
                    for subitem in subitems:
                        write_index(subitem[0], subitem[1], [])
                    f.write('</UL>')
            for (key, group) in index:
                for title, (refs, subitems, key_) in group:
                    write_index(title, refs, subitems)
            f.write('</UL>\n')


def default_htmlhelp_basename(config):
    # type: (Config) -> str
    """Better default htmlhelp_basename setting."""
    return make_filename_from_project(config.project) + 'doc'


def setup(app):
    # type: (Sphinx) -> Dict[str, Any]
    app.setup_extension('sphinx.builders.html')
    app.add_builder(HTMLHelpBuilder)

    app.add_config_value('htmlhelp_basename', default_htmlhelp_basename, None)
    app.add_config_value('htmlhelp_file_suffix', None, 'html', [str])
    app.add_config_value('htmlhelp_link_suffix', None, 'html', [str])

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
