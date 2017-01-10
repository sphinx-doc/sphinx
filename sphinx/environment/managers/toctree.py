# -*- coding: utf-8 -*-
"""
    sphinx.environment.managers.toctree
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Toctree manager for sphinx.environment.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import iteritems

from docutils import nodes

from sphinx import addnodes
from sphinx.util import url_re, logging
from sphinx.transforms import SphinxContentsFilter
from sphinx.environment.adapters.toctree import TocTree as TocTreeAdapter
from sphinx.environment.managers import EnvironmentManager

if False:
    # For type annotation
    from typing import Any, Tuple  # NOQA
    from sphinx.builders import Builder  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA

logger = logging.getLogger(__name__)


class Toctree(EnvironmentManager):
    name = 'toctree'

    def __init__(self, env):
        # type: (BuildEnvironment) -> None
        super(Toctree, self).__init__(env)

        self.tocs = env.tocs
        self.toc_num_entries = env.toc_num_entries
        self.toc_secnumbers = env.toc_secnumbers
        self.toc_fignumbers = env.toc_fignumbers
        self.toctree_includes = env.toctree_includes
        self.files_to_rebuild = env.files_to_rebuild
        self.glob_toctrees = env.glob_toctrees
        self.numbered_toctrees = env.numbered_toctrees

    def clear_doc(self, docname):
        # type: (unicode) -> None
        self.tocs.pop(docname, None)
        self.toc_secnumbers.pop(docname, None)
        self.toc_fignumbers.pop(docname, None)
        self.toc_num_entries.pop(docname, None)
        self.toctree_includes.pop(docname, None)
        self.glob_toctrees.discard(docname)
        self.numbered_toctrees.discard(docname)

        for subfn, fnset in list(self.files_to_rebuild.items()):
            fnset.discard(docname)
            if not fnset:
                del self.files_to_rebuild[subfn]

    def merge_other(self, docnames, other):
        # type: (List[unicode], BuildEnvironment) -> None
        for docname in docnames:
            self.tocs[docname] = other.tocs[docname]
            self.toc_num_entries[docname] = other.toc_num_entries[docname]
            if docname in other.toctree_includes:
                self.toctree_includes[docname] = other.toctree_includes[docname]
            if docname in other.glob_toctrees:
                self.glob_toctrees.add(docname)
            if docname in other.numbered_toctrees:
                self.numbered_toctrees.add(docname)

        for subfn, fnset in other.files_to_rebuild.items():
            self.files_to_rebuild.setdefault(subfn, set()).update(fnset & set(docnames))

    def process_doc(self, docname, doctree):
        # type: (unicode, nodes.Node) -> None
        """Build a TOC from the doctree and store it in the inventory."""
        numentries = [0]  # nonlocal again...

        def traverse_in_section(node, cls):
            """Like traverse(), but stay within the same section."""
            result = []
            if isinstance(node, cls):
                result.append(node)
            for child in node.children:
                if isinstance(child, nodes.section):
                    continue
                result.extend(traverse_in_section(child, cls))
            return result

        def build_toc(node, depth=1):
            entries = []
            for sectionnode in node:
                # find all toctree nodes in this section and add them
                # to the toc (just copying the toctree node which is then
                # resolved in self.get_and_resolve_doctree)
                if isinstance(sectionnode, addnodes.only):
                    onlynode = addnodes.only(expr=sectionnode['expr'])
                    blist = build_toc(sectionnode, depth)
                    if blist:
                        onlynode += blist.children
                        entries.append(onlynode)
                    continue
                if not isinstance(sectionnode, nodes.section):
                    for toctreenode in traverse_in_section(sectionnode,
                                                           addnodes.toctree):
                        item = toctreenode.copy()
                        entries.append(item)
                        # important: do the inventory stuff
                        self.note_toctree(docname, toctreenode)
                    continue
                title = sectionnode[0]
                # copy the contents of the section title, but without references
                # and unnecessary stuff
                visitor = SphinxContentsFilter(doctree)
                title.walkabout(visitor)
                nodetext = visitor.get_entry_text()
                if not numentries[0]:
                    # for the very first toc entry, don't add an anchor
                    # as it is the file's title anyway
                    anchorname = ''
                else:
                    anchorname = '#' + sectionnode['ids'][0]
                numentries[0] += 1
                # make these nodes:
                # list_item -> compact_paragraph -> reference
                reference = nodes.reference(
                    '', '', internal=True, refuri=docname,
                    anchorname=anchorname, *nodetext)
                para = addnodes.compact_paragraph('', '', reference)
                item = nodes.list_item('', para)
                sub_item = build_toc(sectionnode, depth + 1)
                item += sub_item
                entries.append(item)
            if entries:
                return nodes.bullet_list('', *entries)
            return []
        toc = build_toc(doctree)
        if toc:
            self.tocs[docname] = toc
        else:
            self.tocs[docname] = nodes.bullet_list('')
        self.toc_num_entries[docname] = numentries[0]

    def get_updated_docs(self):
        # type: () -> List[unicode]
        return self.assign_section_numbers() + self.assign_figure_numbers()

    def note_toctree(self, docname, toctreenode):
        # type: (unicode, addnodes.toctree) -> None
        """Note a TOC tree directive in a document and gather information about
        file relations from it.
        """
        TocTreeAdapter(self.env).note(docname, toctreenode)

    def get_toc_for(self, docname, builder):
        # type: (unicode, Builder) -> Dict[unicode, nodes.Node]
        """Return a TOC nodetree -- for use on the same page only!"""
        return TocTreeAdapter(self.env).get_toc_for(docname, builder)

    def get_toctree_for(self, docname, builder, collapse, **kwds):
        # type: (unicode, Builder, bool, Any) -> nodes.Node
        """Return the global TOC nodetree."""
        return TocTreeAdapter(self.env).get_toctree_for(docname, builder, collapse, **kwds)

    def resolve_toctree(self, docname, builder, toctree, prune=True, maxdepth=0,
                        titles_only=False, collapse=False, includehidden=False):
        # type: (unicode, Builder, addnodes.toctree, bool, int, bool, bool, bool) -> nodes.Node
        return TocTreeAdapter(self.env).resolve(docname, builder, toctree, prune, maxdepth,
                                                titles_only, collapse, includehidden)

    def assign_section_numbers(self):
        # type: () -> List[unicode]
        """Assign a section number to each heading under a numbered toctree."""
        # a list of all docnames whose section numbers changed
        rewrite_needed = []

        assigned = set()  # type: Set[unicode]
        old_secnumbers = self.toc_secnumbers
        self.toc_secnumbers = self.env.toc_secnumbers = {}

        def _walk_toc(node, secnums, depth, titlenode=None):
            # titlenode is the title of the document, it will get assigned a
            # secnumber too, so that it shows up in next/prev/parent rellinks
            for subnode in node.children:
                if isinstance(subnode, nodes.bullet_list):
                    numstack.append(0)
                    _walk_toc(subnode, secnums, depth - 1, titlenode)
                    numstack.pop()
                    titlenode = None
                elif isinstance(subnode, nodes.list_item):
                    _walk_toc(subnode, secnums, depth, titlenode)
                    titlenode = None
                elif isinstance(subnode, addnodes.only):
                    # at this stage we don't know yet which sections are going
                    # to be included; just include all of them, even if it leads
                    # to gaps in the numbering
                    _walk_toc(subnode, secnums, depth, titlenode)
                    titlenode = None
                elif isinstance(subnode, addnodes.compact_paragraph):
                    numstack[-1] += 1
                    if depth > 0:
                        number = tuple(numstack)
                    else:
                        number = None
                    secnums[subnode[0]['anchorname']] = \
                        subnode[0]['secnumber'] = number
                    if titlenode:
                        titlenode['secnumber'] = number
                        titlenode = None
                elif isinstance(subnode, addnodes.toctree):
                    _walk_toctree(subnode, depth)

        def _walk_toctree(toctreenode, depth):
            if depth == 0:
                return
            for (title, ref) in toctreenode['entries']:
                if url_re.match(ref) or ref == 'self':
                    # don't mess with those
                    continue
                elif ref in assigned:
                    logger.warning('%s is already assigned section numbers '
                                   '(nested numbered toctree?)', ref,
                                   location=toctreenode, type='toc', subtype='secnum')
                elif ref in self.tocs:
                    secnums = self.toc_secnumbers[ref] = {}
                    assigned.add(ref)
                    _walk_toc(self.tocs[ref], secnums, depth,
                              self.env.titles.get(ref))
                    if secnums != old_secnumbers.get(ref):
                        rewrite_needed.append(ref)

        for docname in self.numbered_toctrees:
            assigned.add(docname)
            doctree = self.env.get_doctree(docname)
            for toctreenode in doctree.traverse(addnodes.toctree):
                depth = toctreenode.get('numbered', 0)
                if depth:
                    # every numbered toctree gets new numbering
                    numstack = [0]
                    _walk_toctree(toctreenode, depth)

        return rewrite_needed

    def assign_figure_numbers(self):
        # type: () -> List[unicode]
        """Assign a figure number to each figure under a numbered toctree."""

        rewrite_needed = []

        assigned = set()  # type: Set[unicode]
        old_fignumbers = self.toc_fignumbers
        self.toc_fignumbers = self.env.toc_fignumbers = {}
        fignum_counter = {}  # type: Dict[unicode, Dict[Tuple[int], int]]

        def get_section_number(docname, section):
            anchorname = '#' + section['ids'][0]
            secnumbers = self.toc_secnumbers.get(docname, {})
            if anchorname in secnumbers:
                secnum = secnumbers.get(anchorname)
            else:
                secnum = secnumbers.get('')

            return secnum or tuple()

        def get_next_fignumber(figtype, secnum):
            counter = fignum_counter.setdefault(figtype, {})

            secnum = secnum[:self.env.config.numfig_secnum_depth]
            counter[secnum] = counter.get(secnum, 0) + 1
            return secnum + (counter[secnum],)

        def register_fignumber(docname, secnum, figtype, fignode):
            self.toc_fignumbers.setdefault(docname, {})
            fignumbers = self.toc_fignumbers[docname].setdefault(figtype, {})
            figure_id = fignode['ids'][0]

            fignumbers[figure_id] = get_next_fignumber(figtype, secnum)

        def _walk_doctree(docname, doctree, secnum):
            for subnode in doctree.children:
                if isinstance(subnode, nodes.section):
                    next_secnum = get_section_number(docname, subnode)
                    if next_secnum:
                        _walk_doctree(docname, subnode, next_secnum)
                    else:
                        _walk_doctree(docname, subnode, secnum)
                    continue
                elif isinstance(subnode, addnodes.toctree):
                    for title, subdocname in subnode['entries']:
                        if url_re.match(subdocname) or subdocname == 'self':
                            # don't mess with those
                            continue

                        _walk_doc(subdocname, secnum)

                    continue

                figtype = self.env.get_domain('std').get_figtype(subnode)  # type: ignore
                if figtype and subnode['ids']:
                    register_fignumber(docname, secnum, figtype, subnode)

                _walk_doctree(docname, subnode, secnum)

        def _walk_doc(docname, secnum):
            if docname not in assigned:
                assigned.add(docname)
                doctree = self.env.get_doctree(docname)
                _walk_doctree(docname, doctree, secnum)

        if self.env.config.numfig:
            _walk_doc(self.env.config.master_doc, tuple())
            for docname, fignums in iteritems(self.toc_fignumbers):
                if fignums != old_fignumbers.get(docname):
                    rewrite_needed.append(docname)

        return rewrite_needed
