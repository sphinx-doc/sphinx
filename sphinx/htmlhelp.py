# -*- coding: utf-8 -*-
"""
    sphinx.htmlhelp
    ~~~~~~~~~~~~~~~

    Build HTML help support files.
    Adapted from the original Doc/tools/prechm.py.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import os
import cgi
from os import path

from docutils import nodes

from sphinx import addnodes

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
Compiled file=%(outname)s.chm
Contents file=%(outname)s.hhc
Default Window=%(outname)s
Default topic=index.html
Display compile progress=No
Full text search stop list file=%(outname)s.stp
Full-text search=Yes
Index file=%(outname)s.hhk
Language=0x409
Title=%(project)s %(version)s Documentation

[WINDOWS]
%(outname)s="%(project)s %(version)s Documentation","%(outname)s.hhc","%(outname)s.hhk",\
"index.html","index.html",,,,,0x63520,220,0x10384e,[0,0,1024,768],,,,,,,0

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


def build_hhx(builder, outdir, outname):
    builder.info('dumping stopword list...')
    f = open(path.join(outdir, outname+'.stp'), 'w')
    try:
        for word in sorted(stopwords):
            print >>f, word
    finally:
        f.close()

    builder.info('writing project file...')
    f = open(path.join(outdir, outname+'.hhp'), 'w')
    try:
        f.write(project_template % {'outname': outname,
                                    'version': builder.config.version,
                                    'project': builder.config.project})
        if not outdir.endswith(os.sep):
            outdir += os.sep
        olen = len(outdir)
        for root, dirs, files in os.walk(outdir):
            staticdir = (root == path.join(outdir, '_static'))
            for fn in files:
                if (staticdir and not fn.endswith('.js')) or fn.endswith('.html'):
                    print >>f, path.join(root, fn)[olen:].replace(os.sep, '\\')
    finally:
        f.close()

    builder.info('writing TOC file...')
    f = open(path.join(outdir, outname+'.hhc'), 'w')
    try:
        f.write(contents_header)
        # special books
        f.write('<LI> ' + object_sitemap % ('Main page', 'index.html'))
        if builder.config.html_use_modindex:
            f.write('<LI> ' + object_sitemap % ('Global Module Index', 'modindex.html'))
        # the TOC
        tocdoc = builder.env.get_and_resolve_doctree(builder.config.master_doc, builder,
                                                     prune_toctrees=False)
        def write_toc(node, ullevel=0):
            if isinstance(node, nodes.list_item):
                f.write('<LI> ')
                for subnode in node:
                    write_toc(subnode, ullevel)
            elif isinstance(node, nodes.reference):
                item = object_sitemap % (cgi.escape(node.astext()), node['refuri'])
                f.write(item.encode('ascii', 'xmlcharrefreplace'))
            elif isinstance(node, nodes.bullet_list):
                if ullevel != 0:
                    f.write('<UL>\n')
                for subnode in node:
                    write_toc(subnode, ullevel+1)
                if ullevel != 0:
                    f.write('</UL>\n')
            elif isinstance(node, addnodes.compact_paragraph):
                for subnode in node:
                    write_toc(subnode, ullevel)
        istoctree = lambda node: isinstance(node, addnodes.compact_paragraph) and \
                    node.has_key('toctree')
        for node in tocdoc.traverse(istoctree):
            write_toc(node)
        f.write(contents_footer)
    finally:
        f.close()

    builder.info('writing index file...')
    f = open(path.join(outdir, outname+'.hhk'), 'w')
    try:
        f.write('<UL>\n')
        def write_index(title, refs, subitems):
            if refs:
                f.write('<LI> ')
                item = object_sitemap % (cgi.escape(title), refs[0])
                f.write(item.encode('ascii', 'xmlcharrefreplace'))
                for ref in refs[1:]:
                    f.write(object_sitemap % ('[Link]', ref))
            if subitems:
                f.write('<UL> ')
                for subitem in subitems:
                    write_index(subitem[0], subitem[1], [])
                f.write('</UL>')
        for (key, group) in builder.env.index:
            for title, (refs, subitems) in group:
                write_index(title, refs, subitems)
        f.write('</UL>\n')
    finally:
        f.close()
