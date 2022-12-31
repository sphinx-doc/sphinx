"""Add external links to module code in Python object descriptions."""

from typing import Any, Dict, Set

from docutils import nodes
from docutils.nodes import Node

import sphinx
from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.errors import SphinxError
from sphinx.locale import _
from sphinx.pycode import ModuleAnalyzer


class LinkcodeError(SphinxError):
    category = "linkcode error"


def doctree_read(app: Sphinx, doctree: Node) -> None:
    env = app.builder.env

    resolve_target = getattr(env.config, 'linkcode_resolve', None)
    if not callable(env.config.linkcode_resolve):
        raise LinkcodeError(
            "Function `linkcode_resolve` is not given in conf.py")

    domain_keys = {
        'py': ['module', 'fullname'],
        'c': ['names'],
        'cpp': ['names'],
        'js': ['object', 'fullname'],
    }

    for objnode in list(doctree.findall(addnodes.desc)):
        domain = objnode.get('domain')
        uris: Set[str] = set()
        for signode in objnode:
            if not isinstance(signode, addnodes.desc_signature):
                continue

            # Convert signode to a specified format
            info = {}
            for key in domain_keys.get(domain, []):
                value = signode.get(key)
                if not value:
                    value = ''
                info[key] = value
            if not info:
                continue

            # Get the source lines
            info['start_line'] = -1
            info['end_line'] = -1
            tags_source = False
            modname = signode.get('module')
            code_tags = app.emit_firstresult('viewcode-find-source', modname)
            if code_tags is not None:
                tags_source = code_tags[1]
            else:
                if env.config.linkcode_line_try_import:
                    try:
                        analyzer = ModuleAnalyzer.for_module(modname)
                        analyzer.find_tags()
                    except Exception:
                        pass  # Keep tags = False
                    else:
                        tags_source = analyzer.tags
            if tags_source:
                tag_fullname = signode.get('fullname')
                if tag_fullname in tags_source:
                    info['start_line'] = tags_source[tag_fullname][1]
                    info['end_line'] = tags_source[tag_fullname][2]

            # Call user code to resolve the link
            uri = resolve_target(domain, info)
            if not uri:
                # no source
                continue

            if uri in uris or not uri:
                # only one link per name, please
                continue
            uris.add(uri)

            inline = nodes.inline('', _('[source]'), classes=['viewcode-link'])
            onlynode = addnodes.only(expr='html')
            onlynode += nodes.reference('', '', inline, internal=False, refuri=uri)
            signode += onlynode


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_config_value('linkcode_resolve', None, '')
    app.add_config_value('linkcode_line_try_import', False, '')
    app.connect('doctree-read', doctree_read)
    app.add_event('viewcode-find-source')
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
