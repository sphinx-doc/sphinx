# -*- coding: utf-8 -*-
"""
    sphinx.transforms
    ~~~~~~~~~~~~~~~~~

    Docutils transforms used by Sphinx when reading documents.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from docutils.transforms import Transform
from docutils.transforms.parts import ContentsFilter

from sphinx import addnodes
from sphinx.locale import _
from sphinx.util.i18n import format_date
from sphinx.util.nodes import apply_source_workaround

default_substitutions = set([
    'version',
    'release',
    'today',
])


class DefaultSubstitutions(Transform):
    """
    Replace some substitutions if they aren't defined in the document.
    """
    # run before the default Substitutions
    default_priority = 210

    def apply(self):
        env = self.document.settings.env
        config = self.document.settings.env.config
        # only handle those not otherwise defined in the document
        to_handle = default_substitutions - set(self.document.substitution_defs)
        for ref in self.document.traverse(nodes.substitution_reference):
            refname = ref['refname']
            if refname in to_handle:
                text = config[refname]
                if refname == 'today' and not text:
                    # special handling: can also specify a strftime format
                    text = format_date(config.today_fmt or _('%b %d, %Y'),
                                       language=config.language, warn=env.warn)
                ref.replace_self(nodes.Text(text, text))


class MoveModuleTargets(Transform):
    """
    Move module targets that are the first thing in a section to the section
    title.

    XXX Python specific
    """
    default_priority = 210

    def apply(self):
        for node in self.document.traverse(nodes.target):
            if not node['ids']:
                continue
            if ('ismod' in node and
                    node.parent.__class__ is nodes.section and
                    # index 0 is the section title node
                    node.parent.index(node) == 1):
                node.parent['ids'][0:0] = node['ids']
                node.parent.remove(node)


class HandleCodeBlocks(Transform):
    """
    Several code block related transformations.
    """
    default_priority = 210

    def apply(self):
        # move doctest blocks out of blockquotes
        for node in self.document.traverse(nodes.block_quote):
            if all(isinstance(child, nodes.doctest_block) for child
                   in node.children):
                node.replace_self(node.children)
        # combine successive doctest blocks
        # for node in self.document.traverse(nodes.doctest_block):
        #    if node not in node.parent.children:
        #        continue
        #    parindex = node.parent.index(node)
        #    while len(node.parent) > parindex+1 and \
        #            isinstance(node.parent[parindex+1], nodes.doctest_block):
        #        node[0] = nodes.Text(node[0] + '\n\n' +
        #                             node.parent[parindex+1][0])
        #        del node.parent[parindex+1]


class AutoNumbering(Transform):
    """
    Register IDs of tables, figures and literal_blocks to assign numbers.
    """
    default_priority = 210

    def apply(self):
        domain = self.document.settings.env.domains['std']

        for node in self.document.traverse(nodes.Element):
            if domain.is_enumerable_node(node) and domain.get_numfig_title(node) is not None:
                self.document.note_implicit_target(node)


class SortIds(Transform):
    """
    Sort secion IDs so that the "id[0-9]+" one comes last.
    """
    default_priority = 261

    def apply(self):
        for node in self.document.traverse(nodes.section):
            if len(node['ids']) > 1 and node['ids'][0].startswith('id'):
                node['ids'] = node['ids'][1:] + [node['ids'][0]]


class CitationReferences(Transform):
    """
    Replace citation references by pending_xref nodes before the default
    docutils transform tries to resolve them.
    """
    default_priority = 619

    def apply(self):
        for citnode in self.document.traverse(nodes.citation_reference):
            cittext = citnode.astext()
            refnode = addnodes.pending_xref(cittext, refdomain='std', reftype='citation',
                                            reftarget=cittext, refwarn=True,
                                            ids=citnode["ids"])
            refnode.source = citnode.source or citnode.parent.source
            refnode.line = citnode.line or citnode.parent.line
            refnode += nodes.Text('[' + cittext + ']')
            citnode.parent.replace(citnode, refnode)


TRANSLATABLE_NODES = {
    'literal-block': nodes.literal_block,
    'doctest-block': nodes.doctest_block,
    'raw': nodes.raw,
    'index': addnodes.index,
    'image': nodes.image,
}


class ApplySourceWorkaround(Transform):
    """
    update source and rawsource attributes
    """
    default_priority = 10

    def apply(self):
        for n in self.document.traverse():
            if isinstance(n, nodes.TextElement):
                apply_source_workaround(n)


class AutoIndexUpgrader(Transform):
    """
    Detect old style; 4 column based indices and automatically upgrade to new style.
    """
    default_priority = 210

    def apply(self):
        env = self.document.settings.env
        for node in self.document.traverse(addnodes.index):
            if 'entries' in node and any(len(entry) == 4 for entry in node['entries']):
                msg = ('4 column based index found. '
                       'It might be a bug of extensions you use: %r' % node['entries'])
                env.warn_node(msg, node)
                for i, entry in enumerate(node['entries']):
                    if len(entry) == 4:
                        node['entries'][i] = entry + (None,)


class ExtraTranslatableNodes(Transform):
    """
    make nodes translatable
    """
    default_priority = 10

    def apply(self):
        targets = self.document.settings.env.config.gettext_additional_targets
        target_nodes = [v for k, v in TRANSLATABLE_NODES.items() if k in targets]
        if not target_nodes:
            return

        def is_translatable_node(node):
            return isinstance(node, tuple(target_nodes))

        for node in self.document.traverse(is_translatable_node):
            node['translatable'] = True


class FilterSystemMessages(Transform):
    """Filter system messages from a doctree."""
    default_priority = 999

    def apply(self):
        env = self.document.settings.env
        filterlevel = env.config.keep_warnings and 2 or 5
        for node in self.document.traverse(nodes.system_message):
            if node['level'] < filterlevel:
                env.app.debug('%s [filtered system message]', node.astext())
                node.parent.remove(node)


class SphinxContentsFilter(ContentsFilter):
    """
    Used with BuildEnvironment.add_toc_from() to discard cross-file links
    within table-of-contents link nodes.
    """
    def visit_pending_xref(self, node):
        text = node.astext()
        self.parent.append(nodes.literal(text, text))
        raise nodes.SkipNode

    def visit_image(self, node):
        raise nodes.SkipNode
