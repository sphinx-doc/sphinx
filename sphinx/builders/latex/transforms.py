# -*- coding: utf-8 -*-
"""
    sphinx.builders.latex.transforms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Transforms for LaTeX builder.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes

from sphinx import addnodes
from sphinx.transforms import SphinxTransform

if False:
    # For type annotation
    from typing import Dict, List, Set, Tuple, Union  # NOQA

URI_SCHEMES = ('mailto:', 'http:', 'https:', 'ftp:')


class FootnoteDocnameUpdater(SphinxTransform):
    """Add docname to footnote and footnote_reference nodes."""
    default_priority = 200
    TARGET_NODES = (nodes.footnote, nodes.footnote_reference)

    def apply(self):
        for node in self.document.traverse(lambda n: isinstance(n, self.TARGET_NODES)):
            node['docname'] = self.env.docname


class ShowUrlsTransform(SphinxTransform):
    """Expand references to inline text or footnotes.

    For more information, see :confval:`latex_show_urls`.
    """
    default_priority = 400

    # references are expanded to footnotes (or not)
    expanded = False

    def apply(self):
        # type: () -> None
        try:
            # replace id_prefix temporarily
            id_prefix = self.document.settings.id_prefix
            self.document.settings.id_prefix = 'show_urls'

            self.expand_show_urls()
            if self.expanded:
                self.renumber_footnotes()
        finally:
            # restore id_prefix
            self.document.settings.id_prefix = id_prefix

    def expand_show_urls(self):
        # type: () -> None
        show_urls = self.document.settings.env.config.latex_show_urls
        if show_urls is False or show_urls == 'no':
            return

        for node in self.document.traverse(nodes.reference):
            uri = node.get('refuri', '')
            if uri.startswith(URI_SCHEMES):
                if uri.startswith('mailto:'):
                    uri = uri[7:]
                if node.astext() != uri:
                    index = node.parent.index(node)
                    docname = self.get_docname_for_node(node)
                    if show_urls == 'footnote':
                        fn, fnref = self.create_footnote(uri, docname)
                        node.parent.insert(index + 1, fn)
                        node.parent.insert(index + 2, fnref)

                        self.expanded = True
                    else:  # all other true values (b/w compat)
                        textnode = nodes.Text(" (%s)" % uri)
                        node.parent.insert(index + 1, textnode)

    def get_docname_for_node(self, node):
        # type: (nodes.Node) -> unicode
        while node:
            if isinstance(node, nodes.document):
                return self.env.path2doc(node['source'])
            elif isinstance(node, addnodes.start_of_file):
                return node['docname']
            else:
                node = node.parent

        return None  # never reached here. only for type hinting

    def create_footnote(self, uri, docname):
        # type: (unicode, unicode) -> Tuple[nodes.footnote, nodes.footnote_ref]
        label = nodes.label('', '#')
        para = nodes.paragraph()
        para.append(nodes.reference('', nodes.Text(uri), refuri=uri, nolinkurl=True))
        footnote = nodes.footnote(uri, label, para, auto=1, docname=docname)
        footnote['names'].append('#')
        self.document.note_autofootnote(footnote)

        label = nodes.Text('#')
        footnote_ref = nodes.footnote_reference('[#]_', label, auto=1,
                                                refid=footnote['ids'][0], docname=docname)
        self.document.note_autofootnote_ref(footnote_ref)
        footnote.add_backref(footnote_ref['ids'][0])

        return footnote, footnote_ref

    def renumber_footnotes(self):
        # type: () -> None
        collector = FootnoteCollector(self.document)
        self.document.walkabout(collector)

        num = 0
        for footnote in collector.auto_footnotes:
            # search unused footnote number
            while True:
                num += 1
                if str(num) not in collector.used_footnote_numbers:
                    break

            # assign new footnote number
            old_label = footnote[0].astext()
            footnote[0].replace_self(nodes.label('', str(num)))
            if old_label in footnote['names']:
                footnote['names'].remove(old_label)
            footnote['names'].append(str(num))

            # update footnote_references by new footnote number
            docname = footnote['docname']
            for ref in collector.footnote_refs:
                if docname == ref['docname'] and footnote['ids'][0] == ref['refid']:
                    ref.remove(ref[0])
                    ref += nodes.Text(str(num))


class FootnoteCollector(nodes.NodeVisitor):
    """Collect footnotes and footnote references on the document"""

    def __init__(self, document):
        # type: (nodes.document) -> None
        self.auto_footnotes = []            # type: List[nodes.footnote]
        self.used_footnote_numbers = set()  # type: Set[unicode]
        self.footnote_refs = []             # type: List[nodes.footnote_reference]
        nodes.NodeVisitor.__init__(self, document)

    def unknown_visit(self, node):
        # type: (nodes.Node) -> None
        pass

    def unknown_departure(self, node):
        # type: (nodes.Node) -> None
        pass

    def visit_footnote(self, node):
        # type: (nodes.footnote) -> None
        if node.get('auto'):
            self.auto_footnotes.append(node)
        else:
            for name in node['names']:
                self.used_footnote_numbers.add(name)

    def visit_footnote_reference(self, node):
        # type: (nodes.footnote_reference) -> None
        self.footnote_refs.append(node)
