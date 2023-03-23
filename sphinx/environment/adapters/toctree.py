"""Toctree adapter for sphinx.environment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, TypeVar, cast

from docutils import nodes
from docutils.nodes import Element, Node

from sphinx import addnodes
from sphinx.locale import __
from sphinx.util import logging, url_re
from sphinx.util.matching import Matcher
from sphinx.util.nodes import clean_astext, process_only_nodes

if TYPE_CHECKING:
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment


logger = logging.getLogger(__name__)


class TocTree:
    def __init__(self, env: BuildEnvironment) -> None:
        self.env = env

    def note(self, docname: str, toctreenode: addnodes.toctree) -> None:
        """Note a TOC tree directive in a document and gather information about
        file relations from it.
        """
        if toctreenode['glob']:
            self.env.glob_toctrees.add(docname)
        if toctreenode.get('numbered'):
            self.env.numbered_toctrees.add(docname)
        includefiles = toctreenode['includefiles']
        for includefile in includefiles:
            # note that if the included file is rebuilt, this one must be
            # too (since the TOC of the included file could have changed)
            self.env.files_to_rebuild.setdefault(includefile, set()).add(docname)
        self.env.toctree_includes.setdefault(docname, []).extend(includefiles)

    def resolve(self, docname: str, builder: Builder, toctree: addnodes.toctree,
                prune: bool = True, maxdepth: int = 0, titles_only: bool = False,
                collapse: bool = False, includehidden: bool = False) -> Element | None:
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
        generated_docnames: dict[str, tuple[str, str]] = self.env.domains['std']._virtual_doc_names.copy()  # NoQA: E501

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
        included = Matcher(self.env.config.include_patterns)
        excluded = Matcher(self.env.config.exclude_patterns)

        def _toctree_add_classes(node: Element, depth: int) -> None:
            """Add 'toctree-l%d' and 'current' classes to the toctree."""
            for subnode in node.children:
                if isinstance(subnode, (addnodes.compact_paragraph,
                                        nodes.list_item)):
                    # for <p> and <li>, indicate the depth level and recurse
                    subnode['classes'].append(f'toctree-l{depth - 1}')
                    _toctree_add_classes(subnode, depth)
                elif isinstance(subnode, nodes.bullet_list):
                    # for <ul>, just recurse
                    _toctree_add_classes(subnode, depth + 1)
                elif isinstance(subnode, nodes.reference):
                    # for <a>, identify which entries point to the current
                    # document and therefore may not be collapsed
                    if subnode['refuri'] == docname:
                        if not subnode['anchorname']:
                            # give the whole branch a 'current' class
                            # (useful for styling it differently)
                            branchnode: Element = subnode
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

        def _entries_from_toctree(toctreenode: addnodes.toctree, parents: list[str],
                                  subtree: bool = False) -> list[Element]:
            """Return TOC entries for a toctree node."""
            refs = [(e[0], e[1]) for e in toctreenode['entries']]
            entries: list[Element] = []
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
                            title = clean_astext(self.env.titles[ref])
                        reference = nodes.reference('', '', internal=True,
                                                    refuri=ref,
                                                    anchorname='',
                                                    *[nodes.Text(title)])
                        para = addnodes.compact_paragraph('', '', reference)
                        item = nodes.list_item('', para)
                        # don't show subitems
                        toc = nodes.bullet_list('', item)
                    elif ref in generated_docnames:
                        docname, sectionname = generated_docnames[ref]
                        if not title:
                            title = sectionname
                        reference = nodes.reference('', title, internal=True,
                                                    refuri=docname, anchorname='')
                        para = addnodes.compact_paragraph('', '', reference)
                        item = nodes.list_item('', para)
                        # don't show subitems
                        toc = nodes.bullet_list('', item)
                    else:
                        if ref in parents:
                            logger.warning(__('circular toctree references '
                                              'detected, ignoring: %s <- %s'),
                                           ref, ' <- '.join(parents),
                                           location=ref, type='toc', subtype='circular')
                            continue
                        refdoc = ref
                        maxdepth = self.env.metadata[ref].get('tocdepth', 0)
                        toc = self.env.tocs[ref]
                        if ref not in toctree_ancestors or (prune and maxdepth > 0):
                            toc = self._toctree_copy(toc, 2, maxdepth, collapse)
                        else:
                            toc = toc.deepcopy()
                        process_only_nodes(toc, builder.tags)
                        if title and toc.children and len(toc.children) == 1:
                            child = toc.children[0]
                            for refnode in child.findall(nodes.reference):
                                if refnode['refuri'] == ref and \
                                   not refnode['anchorname']:
                                    refnode.children = [nodes.Text(title)]
                    if not toc.children:
                        # empty toc means: no titles will show up in the toctree
                        logger.warning(__('toctree contains reference to document %r that '
                                          "doesn't have a title: no link will be generated"),
                                       ref, location=toctreenode)
                except KeyError:
                    # this is raised if the included file does not exist
                    if excluded(self.env.doc2path(ref, False)):
                        message = __('toctree contains reference to excluded document %r')
                    elif not included(self.env.doc2path(ref, False)):
                        message = __('toctree contains reference to non-included document %r')
                    else:
                        message = __('toctree contains reference to nonexisting document %r')

                    logger.warning(message, ref, location=toctreenode)
                else:
                    # children of toc are:
                    # - list_item + compact_paragraph + (reference and subtoc)
                    # - only + subtoc
                    # - toctree
                    children = cast(Iterable[nodes.Element], toc)

                    # if titles_only is given, only keep the main title and
                    # sub-toctrees
                    if titles_only:
                        # delete everything but the toplevel title(s)
                        # and toctrees
                        for toplevel in children:
                            # nodes with length 1 don't have any children anyway
                            if len(toplevel) > 1:
                                subtrees = list(toplevel.findall(addnodes.toctree))
                                if subtrees:
                                    toplevel[1][:] = subtrees  # type: ignore
                                else:
                                    toplevel.pop(1)
                    # resolve all sub-toctrees
                    for sub_toc_node in list(toc.findall(addnodes.toctree)):
                        if sub_toc_node.get('hidden', False) and not includehidden:
                            continue
                        for i, entry in enumerate(
                            _entries_from_toctree(sub_toc_node, [refdoc] + parents,
                                                  subtree=True),
                            start=sub_toc_node.parent.index(sub_toc_node) + 1,
                        ):
                            sub_toc_node.parent.insert(i, entry)
                        sub_toc_node.parent.remove(sub_toc_node)

                    entries.extend(children)
            if not subtree:
                ret = nodes.bullet_list()
                ret += entries
                return [ret]
            return entries

        maxdepth = maxdepth or toctree.get('maxdepth', -1)
        if not titles_only and toctree.get('titlesonly', False):
            titles_only = True
        if not includehidden and toctree.get('includehidden', False):
            includehidden = True

        tocentries = _entries_from_toctree(toctree, [])
        if not tocentries:
            return None

        newnode = addnodes.compact_paragraph('', '')
        caption = toctree.attributes.get('caption')
        if caption:
            caption_node = nodes.title(caption, '', *[nodes.Text(caption)])
            caption_node.line = toctree.line
            caption_node.source = toctree.source
            caption_node.rawsource = toctree['rawcaption']
            if hasattr(toctree, 'uid'):
                # move uid to caption_node to translate it
                caption_node.uid = toctree.uid  # type: ignore
                del toctree.uid
            newnode += caption_node
        newnode.extend(tocentries)
        newnode['toctree'] = True

        # prune the tree to maxdepth, also set toc depth and current classes
        _toctree_add_classes(newnode, 1)
        newnode = self._toctree_copy(newnode, 1, maxdepth if prune else 0, collapse)

        if isinstance(newnode[-1], nodes.Element) and len(newnode[-1]) == 0:  # No titles found
            return None

        # set the target paths in the toctrees (they are not known at TOC
        # generation time)
        for refnode in newnode.findall(nodes.reference):
            if not url_re.match(refnode['refuri']):
                refnode['refuri'] = builder.get_relative_uri(
                    docname, refnode['refuri']) + refnode['anchorname']
        return newnode

    def get_toctree_ancestors(self, docname: str) -> list[str]:
        parent = {}
        for p, children in self.env.toctree_includes.items():
            for child in children:
                parent[child] = p
        ancestors: list[str] = []
        d = docname
        while d in parent and d not in ancestors:
            ancestors.append(d)
            d = parent[d]
        return ancestors

    ET = TypeVar('ET', bound=Element)

    def _toctree_copy(self, node: ET, depth: int, maxdepth: int, collapse: bool) -> ET:
        """Utility: Cut and deep-copy a TOC at a specified depth."""
        keep_bullet_list_sub_nodes = (depth <= 1
                                      or ((depth <= maxdepth or maxdepth <= 0)
                                          and (not collapse or 'iscurrent' in node)))

        copy = node.copy()
        for subnode in node.children:
            if isinstance(subnode, (addnodes.compact_paragraph, nodes.list_item)):
                # for <p> and <li>, just recurse
                copy.append(self._toctree_copy(subnode, depth, maxdepth, collapse))
            elif isinstance(subnode, nodes.bullet_list):
                # for <ul>, copy if the entry is top-level
                # or, copy if the depth is within bounds and;
                # collapsing is disabled or the sub-entry's parent is 'current'.
                # The boolean is constant so is calculated outwith the loop.
                if keep_bullet_list_sub_nodes:
                    copy.append(self._toctree_copy(subnode, depth + 1, maxdepth, collapse))
            else:
                copy.append(subnode.deepcopy())
        return copy

    def get_toc_for(self, docname: str, builder: Builder) -> Node:
        """Return a TOC nodetree -- for use on the same page only!"""
        tocdepth = self.env.metadata[docname].get('tocdepth', 0)
        try:
            toc = self._toctree_copy(self.env.tocs[docname], 2, tocdepth, False)
        except KeyError:
            # the document does not exist anymore: return a dummy node that
            # renders to nothing
            return nodes.paragraph()
        process_only_nodes(toc, builder.tags)
        for node in toc.findall(nodes.reference):
            node['refuri'] = node['anchorname'] or '#'
        return toc

    def get_toctree_for(self, docname: str, builder: Builder, collapse: bool,
                        **kwargs: Any) -> Element | None:
        """Return the global TOC nodetree."""
        doctree = self.env.master_doctree
        toctrees: list[Element] = []
        if 'includehidden' not in kwargs:
            kwargs['includehidden'] = True
        if 'maxdepth' not in kwargs or not kwargs['maxdepth']:
            kwargs['maxdepth'] = 0
        else:
            kwargs['maxdepth'] = int(kwargs['maxdepth'])
        kwargs['collapse'] = collapse
        for toctreenode in doctree.findall(addnodes.toctree):
            toctree = self.resolve(docname, builder, toctreenode, prune=True, **kwargs)
            if toctree:
                toctrees.append(toctree)
        if not toctrees:
            return None
        result = toctrees[0]
        for toctree in toctrees[1:]:
            result.extend(toctree.children)
        return result
