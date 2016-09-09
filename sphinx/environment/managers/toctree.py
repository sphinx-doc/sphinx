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
from sphinx.util import url_re
from sphinx.util.nodes import clean_astext, process_only_nodes
from sphinx.transforms import SphinxContentsFilter
from sphinx.environment.managers import EnvironmentManager


class Toctree(EnvironmentManager):
    name = 'toctree'

    def __init__(self, env):
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
            self.files_to_rebuild.setdefault(subfn, set()).update(fnset & docnames)

    def process_doc(self, docname, doctree):
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

    def note_toctree(self, docname, toctreenode):
        """Note a TOC tree directive in a document and gather information about
        file relations from it.
        """
        if toctreenode['glob']:
            self.glob_toctrees.add(docname)
        if toctreenode.get('numbered'):
            self.numbered_toctrees.add(docname)
        includefiles = toctreenode['includefiles']
        for includefile in includefiles:
            # note that if the included file is rebuilt, this one must be
            # too (since the TOC of the included file could have changed)
            self.files_to_rebuild.setdefault(includefile, set()).add(docname)
        self.toctree_includes.setdefault(docname, []).extend(includefiles)

    def get_toc_for(self, docname, builder):
        """Return a TOC nodetree -- for use on the same page only!"""
        tocdepth = self.env.metadata[docname].get('tocdepth', 0)
        try:
            toc = self.tocs[docname].deepcopy()
            self._toctree_prune(toc, 2, tocdepth)
        except KeyError:
            # the document does not exist anymore: return a dummy node that
            # renders to nothing
            return nodes.paragraph()
        process_only_nodes(toc, builder.tags, warn_node=self.env.warn_node)
        for node in toc.traverse(nodes.reference):
            node['refuri'] = node['anchorname'] or '#'
        return toc

    def get_toctree_for(self, docname, builder, collapse, **kwds):
        """Return the global TOC nodetree."""
        doctree = self.env.get_doctree(self.env.config.master_doc)
        toctrees = []
        if 'includehidden' not in kwds:
            kwds['includehidden'] = True
        if 'maxdepth' not in kwds:
            kwds['maxdepth'] = 0
        kwds['collapse'] = collapse
        for toctreenode in doctree.traverse(addnodes.toctree):
            toctree = self.env.resolve_toctree(docname, builder, toctreenode,
                                               prune=True, **kwds)
            if toctree:
                toctrees.append(toctree)
        if not toctrees:
            return None
        result = toctrees[0]
        for toctree in toctrees[1:]:
            result.extend(toctree.children)
        return result

    def resolve_toctree(self, docname, builder, toctree, prune=True, maxdepth=0,
                        titles_only=False, collapse=False, includehidden=False):
        """Resolve a *toctree* node into individual bullet lists with titles
        as items, returning None (if no containing titles are found) or
        a new node.

        If *prune* is True, the tree is pruned to *maxdepth*, or if that is 0,
        to the value of the *maxdepth* option on the *toctree* node.
        If *titles_only* is True, only toplevel document titles will be in the
        resulting tree.
        If *collapse* is True, all branches not containing docname will
        be collapsed.
        """
        if toctree.get('hidden', False) and not includehidden:
            return None

        # For reading the following two helper function, it is useful to keep
        # in mind the node structure of a toctree (using HTML-like node names
        # for brevity):
        #
        # <ul>
        #   <li>
        #     <p><a></p>
        #     <p><a></p>
        #     ...
        #     <ul>
        #       ...
        #     </ul>
        #   </li>
        # </ul>
        #
        # The transformation is made in two passes in order to avoid
        # interactions between marking and pruning the tree (see bug #1046).

        toctree_ancestors = self.get_toctree_ancestors(docname)

        def _toctree_add_classes(node, depth):
            """Add 'toctree-l%d' and 'current' classes to the toctree."""
            for subnode in node.children:
                if isinstance(subnode, (addnodes.compact_paragraph,
                                        nodes.list_item)):
                    # for <p> and <li>, indicate the depth level and recurse
                    subnode['classes'].append('toctree-l%d' % (depth-1))
                    _toctree_add_classes(subnode, depth)
                elif isinstance(subnode, nodes.bullet_list):
                    # for <ul>, just recurse
                    _toctree_add_classes(subnode, depth+1)
                elif isinstance(subnode, nodes.reference):
                    # for <a>, identify which entries point to the current
                    # document and therefore may not be collapsed
                    if subnode['refuri'] == docname:
                        if not subnode['anchorname']:
                            # give the whole branch a 'current' class
                            # (useful for styling it differently)
                            branchnode = subnode
                            while branchnode:
                                branchnode['classes'].append('current')
                                branchnode = branchnode.parent
                        # mark the list_item as "on current page"
                        if subnode.parent.parent.get('iscurrent'):
                            # but only if it's not already done
                            return
                        while subnode:
                            subnode['iscurrent'] = True
                            subnode = subnode.parent

        def _entries_from_toctree(toctreenode, parents,
                                  separate=False, subtree=False):
            """Return TOC entries for a toctree node."""
            refs = [(e[0], e[1]) for e in toctreenode['entries']]
            entries = []
            for (title, ref) in refs:
                try:
                    refdoc = None
                    if url_re.match(ref):
                        if title is None:
                            title = ref
                        reference = nodes.reference('', '', internal=False,
                                                    refuri=ref, anchorname='',
                                                    *[nodes.Text(title)])
                        para = addnodes.compact_paragraph('', '', reference)
                        item = nodes.list_item('', para)
                        toc = nodes.bullet_list('', item)
                    elif ref == 'self':
                        # 'self' refers to the document from which this
                        # toctree originates
                        ref = toctreenode['parent']
                        if not title:
                            title = clean_astext(self.titles[ref])
                        reference = nodes.reference('', '', internal=True,
                                                    refuri=ref,
                                                    anchorname='',
                                                    *[nodes.Text(title)])
                        para = addnodes.compact_paragraph('', '', reference)
                        item = nodes.list_item('', para)
                        # don't show subitems
                        toc = nodes.bullet_list('', item)
                    else:
                        if ref in parents:
                            self.env.warn(ref, 'circular toctree references '
                                          'detected, ignoring: %s <- %s' %
                                          (ref, ' <- '.join(parents)))
                            continue
                        refdoc = ref
                        toc = self.tocs[ref].deepcopy()
                        maxdepth = self.env.metadata[ref].get('tocdepth', 0)
                        if ref not in toctree_ancestors or (prune and maxdepth > 0):
                            self._toctree_prune(toc, 2, maxdepth, collapse)
                        process_only_nodes(toc, builder.tags, warn_node=self.env.warn_node)
                        if title and toc.children and len(toc.children) == 1:
                            child = toc.children[0]
                            for refnode in child.traverse(nodes.reference):
                                if refnode['refuri'] == ref and \
                                   not refnode['anchorname']:
                                    refnode.children = [nodes.Text(title)]
                    if not toc.children:
                        # empty toc means: no titles will show up in the toctree
                        self.env.warn_node(
                            'toctree contains reference to document %r that '
                            'doesn\'t have a title: no link will be generated'
                            % ref, toctreenode)
                except KeyError:
                    # this is raised if the included file does not exist
                    self.env.warn_node(
                        'toctree contains reference to nonexisting document %r'
                        % ref, toctreenode)
                else:
                    # if titles_only is given, only keep the main title and
                    # sub-toctrees
                    if titles_only:
                        # delete everything but the toplevel title(s)
                        # and toctrees
                        for toplevel in toc:
                            # nodes with length 1 don't have any children anyway
                            if len(toplevel) > 1:
                                subtrees = toplevel.traverse(addnodes.toctree)
                                if subtrees:
                                    toplevel[1][:] = subtrees
                                else:
                                    toplevel.pop(1)
                    # resolve all sub-toctrees
                    for subtocnode in toc.traverse(addnodes.toctree):
                        if not (subtocnode.get('hidden', False) and
                                not includehidden):
                            i = subtocnode.parent.index(subtocnode) + 1
                            for item in _entries_from_toctree(
                                    subtocnode, [refdoc] + parents,
                                    subtree=True):
                                subtocnode.parent.insert(i, item)
                                i += 1
                            subtocnode.parent.remove(subtocnode)
                    if separate:
                        entries.append(toc)
                    else:
                        entries.extend(toc.children)
            if not subtree and not separate:
                ret = nodes.bullet_list()
                ret += entries
                return [ret]
            return entries

        maxdepth = maxdepth or toctree.get('maxdepth', -1)
        if not titles_only and toctree.get('titlesonly', False):
            titles_only = True
        if not includehidden and toctree.get('includehidden', False):
            includehidden = True

        # NOTE: previously, this was separate=True, but that leads to artificial
        # separation when two or more toctree entries form a logical unit, so
        # separating mode is no longer used -- it's kept here for history's sake
        tocentries = _entries_from_toctree(toctree, [], separate=False)
        if not tocentries:
            return None

        newnode = addnodes.compact_paragraph('', '')
        caption = toctree.attributes.get('caption')
        if caption:
            caption_node = nodes.caption(caption, '', *[nodes.Text(caption)])
            caption_node.line = toctree.line
            caption_node.source = toctree.source
            caption_node.rawsource = toctree['rawcaption']
            if hasattr(toctree, 'uid'):
                # move uid to caption_node to translate it
                caption_node.uid = toctree.uid
                del toctree.uid
            newnode += caption_node
        newnode.extend(tocentries)
        newnode['toctree'] = True

        # prune the tree to maxdepth, also set toc depth and current classes
        _toctree_add_classes(newnode, 1)
        self._toctree_prune(newnode, 1, prune and maxdepth or 0, collapse)

        if len(newnode[-1]) == 0:  # No titles found
            return None

        # set the target paths in the toctrees (they are not known at TOC
        # generation time)
        for refnode in newnode.traverse(nodes.reference):
            if not url_re.match(refnode['refuri']):
                refnode['refuri'] = builder.get_relative_uri(
                    docname, refnode['refuri']) + refnode['anchorname']
        return newnode

    def get_toctree_ancestors(self, docname):
        parent = {}
        for p, children in iteritems(self.toctree_includes):
            for child in children:
                parent[child] = p
        ancestors = []
        d = docname
        while d in parent and d not in ancestors:
            ancestors.append(d)
            d = parent[d]
        return ancestors

    def _toctree_prune(self, node, depth, maxdepth, collapse=False):
        """Utility: Cut a TOC at a specified depth."""
        for subnode in node.children[:]:
            if isinstance(subnode, (addnodes.compact_paragraph,
                                    nodes.list_item)):
                # for <p> and <li>, just recurse
                self._toctree_prune(subnode, depth, maxdepth, collapse)
            elif isinstance(subnode, nodes.bullet_list):
                # for <ul>, determine if the depth is too large or if the
                # entry is to be collapsed
                if maxdepth > 0 and depth > maxdepth:
                    subnode.parent.replace(subnode, [])
                else:
                    # cull sub-entries whose parents aren't 'current'
                    if (collapse and depth > 1 and
                            'iscurrent' not in subnode.parent):
                        subnode.parent.remove(subnode)
                    else:
                        # recurse on visible children
                        self._toctree_prune(subnode, depth+1, maxdepth,  collapse)

    def assign_section_numbers(self):
        """Assign a section number to each heading under a numbered toctree."""
        # a list of all docnames whose section numbers changed
        rewrite_needed = []

        assigned = set()
        old_secnumbers = self.toc_secnumbers
        self.toc_secnumbers = self.env.toc_secnumbers = {}

        def _walk_toc(node, secnums, depth, titlenode=None):
            # titlenode is the title of the document, it will get assigned a
            # secnumber too, so that it shows up in next/prev/parent rellinks
            for subnode in node.children:
                if isinstance(subnode, nodes.bullet_list):
                    numstack.append(0)
                    _walk_toc(subnode, secnums, depth-1, titlenode)
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
                if url_re.match(ref) or ref == 'self' or ref in assigned:
                    # don't mess with those
                    continue
                if ref in self.tocs:
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
        """Assign a figure number to each figure under a numbered toctree."""

        rewrite_needed = []

        assigned = set()
        old_fignumbers = self.toc_fignumbers
        self.toc_fignumbers = self.env.toc_fignumbers = {}
        fignum_counter = {}

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

                figtype = self.env.domains['std'].get_figtype(subnode)
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
