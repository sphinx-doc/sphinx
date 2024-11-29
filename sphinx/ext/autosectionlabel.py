"""Allow reference sections by :ref: role using its title."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from docutils import nodes

import sphinx
from sphinx.locale import __
from sphinx.util import logging
from sphinx.util.nodes import clean_astext, make_id, traverse_parent

if TYPE_CHECKING:
    from docutils.nodes import Node

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata

logger = logging.getLogger(__name__)


def get_node_depth(node: Node) -> int:
    i = 0
    cur_node = node
    while cur_node.parent != node.document:
        cur_node = cur_node.parent
        i += 1
    return i


def _get_all_node_parent_section_titles(node: Node) -> list[str]:
    parents = []
    for pnode in traverse_parent(node.parent, nodes.section):
        title = cast(nodes.title, pnode[0])
        ref_name = getattr(title, 'rawsource', title.astext())
        parents.append(ref_name)

    return parents


def register_sections_as_label(app: Sphinx, doctree: nodes.document) -> None:
    domain = app.env.domains.standard_domain
    id_prefix = None

    settings = doctree.settings
    for node in doctree.findall(nodes.section):
        if (app.config.autosectionlabel_maxdepth and
                get_node_depth(node) >= app.config.autosectionlabel_maxdepth):
            continue

        labelid = node['ids'][0]
        docname = app.env.docname
        title = cast(nodes.title, node[0])
        ref_name = getattr(title, 'rawsource', title.astext())

        if app.config.autosectionlabel_prefix_document:
            if app.config.autosectionlabel_full_reference:
                id_array = _get_all_node_parent_section_titles(node)
                id_array = [docname, *reversed(id_array), ref_name]
                # replace id_prefix temporarily
                id_prefix = settings.id_prefix
                settings.id_prefix = '.'.join(id_array)

                labelid = make_id(app.env, doctree, '', '.'.join(id_array))
                doctree.ids[labelid] = labelid
                name = nodes.fully_normalize_name(labelid.replace('.', ':'))

                # restore id_prefix
                settings.id_prefix = id_prefix

                # Add labelid as another reference id
                # Note, cannot replace as this breaks TOC and sectnum functionality.
                node['ids'].append(labelid)
            else:
                name = nodes.fully_normalize_name(f'{docname}:{ref_name}')
        else:
            name = nodes.fully_normalize_name(ref_name)

        sectname = clean_astext(title)

        logger.debug(__('section "%s" is: labeled "%s", id "%s", prefix "%s"'),
                     ref_name, name, labelid, id_prefix,
                     location=node, type='autosectionlabel', subtype=docname)
        if name in domain.labels:
            logger.warning(__('duplicate label %s, other instance in %s'),
                           name, app.env.doc2path(domain.labels[name][0]),
                           location=node, type='autosectionlabel', subtype=docname)

        domain.anonlabels[name] = docname, labelid
        domain.labels[name] = docname, labelid, sectname


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_config_value('autosectionlabel_prefix_document', False, 'env', bool)
    app.add_config_value('autosectionlabel_maxdepth', None, 'env')
    app.add_config_value('autosectionlabel_full_reference', False, 'env', bool)
    app.connect('doctree-read', register_sections_as_label)

    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
