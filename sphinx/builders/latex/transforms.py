# -*- coding: utf-8 -*-
"""
    sphinx.builders.latex.transforms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Transforms for LaTeX builder.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from six import iteritems

from sphinx import addnodes
from sphinx.transforms import SphinxTransform
from sphinx.util.nodes import traverse_parent

URI_SCHEMES = ('mailto:', 'http:', 'https:', 'ftp:')


class ShowUrlsTransform(SphinxTransform, object):
    def __init__(self, document, startnode=None):
        # type: (nodes.document, nodes.Node) -> None
        super(ShowUrlsTransform, self).__init__(document, startnode)
        self.expanded = False

    def apply(self):
        # type: () -> None
        # replace id_prefix temporarily
        id_prefix = self.document.settings.id_prefix
        self.document.settings.id_prefix = 'show_urls'

        self.expand_show_urls()
        if self.expanded:
            self.renumber_footnotes()

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
                    if show_urls == 'footnote':
                        footnote_nodes = self.create_footnote(uri)
                        for i, fn in enumerate(footnote_nodes):
                            node.parent.insert(index + i + 1, fn)

                        self.expanded = True
                    else:  # all other true values (b/w compat)
                        textnode = nodes.Text(" (%s)" % uri)
                        node.parent.insert(index + 1, textnode)

    def create_footnote(self, uri):
        # type: (unicode) -> List[Union[nodes.footnote, nodes.footnote_ref]]
        label = nodes.label('', '#')
        para = nodes.paragraph()
        para.append(nodes.reference('', nodes.Text(uri), refuri=uri, nolinkurl=True))
        footnote = nodes.footnote(uri, label, para, auto=1)
        footnote['names'].append('#')
        self.document.note_autofootnote(footnote)

        label = nodes.Text('#')
        footnote_ref = nodes.footnote_reference('[#]_', label, auto=1,
                                                refid=footnote['ids'][0])
        self.document.note_autofootnote_ref(footnote_ref)
        footnote.add_backref(footnote_ref['ids'][0])

        return [footnote, footnote_ref]

    def renumber_footnotes(self):
        # type: () -> None
        def is_used_number(number):
            # type: (unicode) -> bool
            for node in self.document.traverse(nodes.footnote):
                if not node.get('auto') and number in node['names']:
                    return True

            return False

        def is_auto_footnote(node):
            # type: (nodes.Node) -> bool
            return isinstance(node, nodes.footnote) and node.get('auto')

        def footnote_ref_by(node):
            # type: (nodes.Node) -> Callable[[nodes.Node], bool]
            ids = node['ids']
            parent = list(traverse_parent(node, (nodes.document, addnodes.start_of_file)))[0]

            def is_footnote_ref(node):
                # type: (nodes.Node) -> bool
                return (isinstance(node, nodes.footnote_reference) and
                        ids[0] == node['refid'] and
                        parent in list(traverse_parent(node)))

            return is_footnote_ref

        startnum = 1
        for footnote in self.document.traverse(is_auto_footnote):
            while True:
                label = str(startnum)
                startnum += 1
                if not is_used_number(label):
                    break

            old_label = footnote[0].astext()
            footnote.remove(footnote[0])
            footnote.insert(0, nodes.label('', label))
            if old_label in footnote['names']:
                footnote['names'].remove(old_label)
            footnote['names'].append(label)

            for footnote_ref in self.document.traverse(footnote_ref_by(footnote)):
                footnote_ref.remove(footnote_ref[0])
                footnote_ref += nodes.Text(label)
