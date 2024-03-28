"""A builder that creates a lookup for available references in the project."""

from __future__ import annotations

import json
from os import path
from typing import TYPE_CHECKING, Iterator, Literal, TypedDict

from sphinx.builders import Builder
from sphinx.ext.intersphinx import InventoryAdapter
from sphinx.locale import __
from sphinx.util.display import progress_message

if TYPE_CHECKING:
    from docutils.nodes import Node

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


class LocalReference(TypedDict, total=False):
    type: Literal['local']
    document: str
    """The path to the document."""
    dispname: str
    """The implicit display text."""


class RemoteReference(TypedDict, total=False):
    type: Literal['remote']
    key: str
    """The ``intersphinx_mapping`` key."""
    url: str
    """The full URL to this target."""
    dispname: str
    """The implicit display text."""


class ReferenceTargets(TypedDict, total=False):
    items: dict[str, list[LocalReference | RemoteReference]]
    """Mapping of the target name to its data."""
    roles: list[str]
    """List of available roles for this object type."""


ReferenceJson = dict[str, dict[str, ReferenceTargets]]
"""A mapping of ``domain name`` -> ``object type`` -> ``targets``."""


class ReferencesBuilder(Builder):
    name = 'references'
    epilog = __('Generated reference lookup at %(outdir)s/references.json.')

    allow_parallel = True

    def init(self) -> None:
        pass

    def get_outdated_docs(self) -> Iterator[str]:
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = self.doctreedir.joinpath(docname + '.doctree')
            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = path.getmtime(self.env.doc2path(docname))
                if srcmtime > targetmtime:
                    yield docname
            except OSError:
                # source doesn't exist anymore
                pass

    def get_target_uri(self, docname: str, typ: str | None = None) -> str:
        return ''

    def prepare_writing(self, docnames: set[str]) -> None:
        pass

    def write_doc(self, docname: str, doctree: Node) -> None:
        pass

    def finish(self) -> None:
        self.finish_tasks.add_task(self.write_references)

    @progress_message(__('writing references'))
    def write_references(self) -> None:
        data: ReferenceJson = {}
        # local objects
        for domainname, domain in self.env.domains.items():
            for name, dispname, otype_name, docname, _, _ in domain.get_objects():
                dispname = str(dispname)  # can be a _TranslationProxy object
                local_data: LocalReference = {
                    'type': 'local',
                    'document': self.env.doc2path(docname),
                }
                # only add dispname if it is set and not the same as name
                if not (dispname == name or not dispname or dispname == '-'):
                    local_data['dispname'] = dispname
                # record available roles for this object type, if available
                if otype_name not in data.setdefault(domainname, {}):
                    data[domainname][otype_name] = {'items': {}}
                    if otype := domain.object_types.get(otype_name):
                        data[domainname][otype_name]['roles'] = list(otype.roles)
                data.setdefault(domainname, {}).setdefault(otype_name, {})['items'].setdefault(
                    name, []
                ).append(local_data)
        # remote objects (if using intersphinx)
        inventories = InventoryAdapter(self.env)
        for inv_key, invdata in inventories.named_inventory.items():
            for domain_oject, names in invdata.items():
                domainname, otype_name = domain_oject.split(':', 1)
                local_domain = self.env.domains.get(domainname)
                for name, (_, _, url, dispname) in names.items():
                    remote_data: RemoteReference = {
                        'type': 'remote',
                        'key': inv_key,
                        'url': url,
                    }
                    # only add dispname if it is set and not the same as name
                    if not (dispname == name or not dispname or dispname == '-'):
                        remote_data['dispname'] = dispname
                    if otype_name not in data.setdefault(domainname, {}):
                        data[domainname][otype_name] = {'items': {}}
                        # record available roles for this object type, if available
                        if local_domain and (
                            otype := local_domain.object_types.get(otype_name)
                        ):
                            data[domainname][otype_name]['roles'] = list(otype.roles)
                    data.setdefault(domainname, {}).setdefault(otype_name, {})[
                        'items'
                    ].setdefault(name, []).append(remote_data)

        with self.outdir.joinpath('references.json').open('w', encoding='utf-8') as fp:
            json.dump(data, fp, sort_keys=True, indent=2)


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_builder(ReferencesBuilder)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
