"""This module provides logic for resolving references to intersphinx targets."""

from __future__ import annotations

import posixpath
import re
from typing import TYPE_CHECKING, cast

from docutils import nodes
from docutils.utils import relative_path

from sphinx.addnodes import pending_xref
from sphinx.errors import ExtensionError
from sphinx.locale import _, __
from sphinx.transforms.post_transforms import ReferencesResolver
from sphinx.util import logging
from sphinx.util.docutils import CustomReSTDispatcher, SphinxRole

from ._shared import InventoryAdapter

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import ModuleType
    from typing import Any

    from docutils.nodes import Node, TextElement, system_message
    from docutils.utils import Reporter

    from sphinx.application import Sphinx
    from sphinx.domains import Domain
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import Inventory, InventoryItem, RoleFunction


logger = logging.getLogger(__name__)


def _create_element_from_result(
    domain: Domain,
    inv_name: str | None,
    data: InventoryItem,
    node: pending_xref,
    contnode: TextElement,
) -> nodes.reference:
    proj, version, uri, dispname = data
    if '://' not in uri and node.get('refdoc'):
        # get correct path in case of subdirectories
        uri = posixpath.join(relative_path(node['refdoc'], '.'), uri)
    if version:
        reftitle = _('(in %s v%s)') % (proj, version)
    else:
        reftitle = _('(in %s)') % (proj,)
    newnode = nodes.reference('', '', internal=False, refuri=uri, reftitle=reftitle)
    if node.get('refexplicit'):
        # use whatever title was given
        newnode.append(contnode)
    elif dispname == '-' or (domain.name == 'std' and node['reftype'] == 'keyword'):
        # use whatever title was given, but strip prefix
        title = contnode.astext()
        if inv_name is not None and title.startswith(inv_name + ':'):
            newnode.append(
                contnode.__class__(title[len(inv_name) + 1 :], title[len(inv_name) + 1 :])
            )
        else:
            newnode.append(contnode)
    else:
        # else use the given display name (used for :ref:)
        newnode.append(contnode.__class__(dispname, dispname))
    return newnode


def _resolve_reference_in_domain_by_target(
    inv_name: str | None,
    inventory: Inventory,
    domain: Domain,
    objtypes: Iterable[str],
    target: str,
    node: pending_xref,
    contnode: TextElement,
) -> nodes.reference | None:
    for objtype in objtypes:
        if objtype not in inventory:
            # Continue if there's nothing of this kind in the inventory
            continue

        if target in inventory[objtype]:
            # Case sensitive match, use it
            data = inventory[objtype][target]
        elif objtype in {'std:label', 'std:term'}:
            # Some types require case insensitive matches:
            # * 'term': https://github.com/sphinx-doc/sphinx/issues/9291
            # * 'label': https://github.com/sphinx-doc/sphinx/issues/12008
            target_lower = target.lower()
            insensitive_matches = list(
                filter(lambda k: k.lower() == target_lower, inventory[objtype].keys())
            )
            if insensitive_matches:
                data = inventory[objtype][insensitive_matches[0]]
            else:
                # No case insensitive match either, continue to the next candidate
                continue
        else:
            # Could reach here if we're not a term but have a case insensitive match.
            # This is a fix for terms specifically, but potentially should apply to
            # other types.
            continue
        return _create_element_from_result(domain, inv_name, data, node, contnode)
    return None


def _resolve_reference_in_domain(
    env: BuildEnvironment,
    inv_name: str | None,
    inventory: Inventory,
    honor_disabled_refs: bool,
    domain: Domain,
    objtypes: Iterable[str],
    node: pending_xref,
    contnode: TextElement,
) -> nodes.reference | None:
    obj_types: dict[str, None] = {}.fromkeys(objtypes)

    # we adjust the object types for backwards compatibility
    if domain.name == 'std' and 'cmdoption' in obj_types:
        # cmdoptions were stored as std:option until Sphinx 1.6
        obj_types['option'] = None
    if domain.name == 'py' and 'attribute' in obj_types:
        # properties are stored as py:method since Sphinx 2.1
        obj_types['method'] = None

    # the inventory contains domain:type as objtype
    domain_name = domain.name
    obj_types = {f'{domain_name}:{obj_type}': None for obj_type in obj_types}

    # now that the objtypes list is complete we can remove the disabled ones
    if honor_disabled_refs:
        disabled = set(env.config.intersphinx_disabled_reftypes)
        obj_types = {obj_type: None for obj_type in obj_types if obj_type not in disabled}

    objtypes = [*obj_types.keys()]

    # without qualification
    res = _resolve_reference_in_domain_by_target(
        inv_name, inventory, domain, objtypes, node['reftarget'], node, contnode
    )
    if res is not None:
        return res

    # try with qualification of the current scope instead
    full_qualified_name = domain.get_full_qualified_name(node)
    if full_qualified_name is None:
        return None
    return _resolve_reference_in_domain_by_target(
        inv_name, inventory, domain, objtypes, full_qualified_name, node, contnode
    )


def _resolve_reference(
    env: BuildEnvironment,
    inv_name: str | None,
    inventory: Inventory,
    honor_disabled_refs: bool,
    node: pending_xref,
    contnode: TextElement,
) -> nodes.reference | None:
    # disabling should only be done if no inventory is given
    honor_disabled_refs = honor_disabled_refs and inv_name is None

    if honor_disabled_refs and '*' in env.config.intersphinx_disabled_reftypes:
        return None

    typ = node['reftype']
    if typ == 'any':
        for domain_name, domain in env.domains.items():
            if (
                honor_disabled_refs
                and (domain_name + ':*') in env.config.intersphinx_disabled_reftypes
            ):
                continue
            objtypes: Iterable[str] = domain.object_types.keys()
            res = _resolve_reference_in_domain(
                env, inv_name, inventory, honor_disabled_refs, domain, objtypes, node, contnode
            )
            if res is not None:
                return res
        return None
    else:
        domain_name = node.get('refdomain')
        if not domain_name:
            # only objects in domains are in the inventory
            return None
        if (
            honor_disabled_refs
            and (domain_name + ':*') in env.config.intersphinx_disabled_reftypes
        ):
            return None
        domain = env.get_domain(domain_name)
        objtypes = domain.objtypes_for_role(typ) or ()
        if not objtypes:
            return None
        return _resolve_reference_in_domain(
            env, inv_name, inventory, honor_disabled_refs, domain, objtypes, node, contnode
        )


def inventory_exists(env: BuildEnvironment, inv_name: str) -> bool:
    return inv_name in InventoryAdapter(env).named_inventory


def resolve_reference_in_inventory(
    env: BuildEnvironment,
    inv_name: str,
    node: pending_xref,
    contnode: TextElement,
) -> nodes.reference | None:
    """Attempt to resolve a missing reference via intersphinx references.

    Resolution is tried in the given inventory with the target as is.

    Requires ``inventory_exists(env, inv_name)``.
    """
    assert inventory_exists(env, inv_name)
    return _resolve_reference(
        env, inv_name, InventoryAdapter(env).named_inventory[inv_name], False, node, contnode
    )


def resolve_reference_any_inventory(
    env: BuildEnvironment,
    honor_disabled_refs: bool,
    node: pending_xref,
    contnode: TextElement,
) -> nodes.reference | None:
    """Attempt to resolve a missing reference via intersphinx references.

    Resolution is tried with the target as is in any inventory.
    """
    return _resolve_reference(
        env, None, InventoryAdapter(env).main_inventory, honor_disabled_refs, node, contnode
    )


def resolve_reference_detect_inventory(
    env: BuildEnvironment,
    node: pending_xref,
    contnode: TextElement,
) -> nodes.reference | None:
    """Attempt to resolve a missing reference via intersphinx references.

    Resolution is tried first with the target as is in any inventory.
    If this does not succeed, then the target is split by the first ``:``,
    to form ``inv_name:newtarget``. If ``inv_name`` is a named inventory, then resolution
    is tried in that inventory with the new target.
    """
    # ordinary direct lookup, use data as is
    res = resolve_reference_any_inventory(env, True, node, contnode)
    if res is not None:
        return res

    # try splitting the target into 'inv_name:target'
    target = node['reftarget']
    if ':' not in target:
        return None
    inv_name, newtarget = target.split(':', 1)
    if not inventory_exists(env, inv_name):
        return None
    node['reftarget'] = newtarget
    res_inv = resolve_reference_in_inventory(env, inv_name, node, contnode)
    node['reftarget'] = target
    return res_inv


def missing_reference(
    app: Sphinx, env: BuildEnvironment, node: pending_xref, contnode: TextElement
) -> nodes.reference | None:
    """Attempt to resolve a missing reference via intersphinx references."""
    return resolve_reference_detect_inventory(env, node, contnode)


class IntersphinxDispatcher(CustomReSTDispatcher):
    """Custom dispatcher for external role.

    This enables :external:***:/:external+***: roles on parsing reST document.
    """

    def role(
        self,
        role_name: str,
        language_module: ModuleType,
        lineno: int,
        reporter: Reporter,
    ) -> tuple[RoleFunction, list[system_message]]:
        if len(role_name) > 9 and role_name.startswith(('external:', 'external+')):
            return IntersphinxRole(role_name), []
        else:
            return super().role(role_name, language_module, lineno, reporter)


class IntersphinxRole(SphinxRole):
    # group 1: just for the optionality of the inventory name
    # group 2: the inventory name (optional)
    # group 3: the domain:role or role part
    _re_inv_ref = re.compile(r'(\+([^:]+))?:(.*)')

    def __init__(self, orig_name: str) -> None:
        self.orig_name = orig_name

    def run(self) -> tuple[list[Node], list[system_message]]:
        assert self.name == self.orig_name.lower()
        inventory, name_suffix = self.get_inventory_and_name_suffix(self.orig_name)
        if inventory and not inventory_exists(self.env, inventory):
            logger.warning(
                __('inventory for external cross-reference not found: %s'),
                inventory,
                location=(self.env.docname, self.lineno),
            )
            return [], []

        role_name = self.get_role_name(name_suffix)
        if role_name is None:
            logger.warning(
                __('role for external cross-reference not found: %s'),
                name_suffix,
                location=(self.env.docname, self.lineno),
            )
            return [], []

        result, messages = self.invoke_role(role_name)
        for node in result:
            if isinstance(node, pending_xref):
                node['intersphinx'] = True
                node['inventory'] = inventory

        return result, messages

    def get_inventory_and_name_suffix(self, name: str) -> tuple[str | None, str]:
        """Extract an inventory name (if any) and ``domain+name`` suffix from a role *name*.
        and the domain+name suffix.

        The role name is expected to be of one of the following forms:

        - ``external+inv:name`` -- explicit inventory and name, any domain.
        - ``external+inv:domain:name`` -- explicit inventory, domain and name.
        - ``external:name`` -- any inventory and domain, explicit name.
        - ``external:domain:name`` -- any inventory, explicit domain and name.
        """
        assert name.startswith('external'), name
        suffix = name[9:]
        if name[8] == '+':
            inv_name, suffix = suffix.split(':', 1)
            return inv_name, suffix
        elif name[8] == ':':
            return None, suffix
        else:
            msg = f'Malformed :external: role name: {name}'
            raise ValueError(msg)

    def get_role_name(self, name: str) -> tuple[str, str] | None:
        """Find (if any) the corresponding ``(domain, role name)`` for *name*.

        The *name* can be either a role name (e.g., ``py:function`` or ``function``)
        given as ``domain:role`` or ``role``, or its corresponding object name
        (in this case, ``py:func`` or ``func``) given as ``domain:objname`` or ``objname``.

        If no domain is given, or the object/role name is not found for the requested domain,
        the 'std' domain is used.
        """
        names = name.split(':')
        if len(names) == 1:
            default_domain = self.env.temp_data.get('default_domain')
            domain = default_domain.name if default_domain else None
            name = names[0]
        elif len(names) == 2:
            domain = names[0]
            name = names[1]
        else:
            return None

        if domain and (role := self.get_role_name_from_domain(domain, name)):
            return (domain, role)
        elif role := self.get_role_name_from_domain('std', name):
            return ('std', role)
        else:
            return None

    def is_existent_role(self, domain_name: str, role_or_obj_name: str) -> bool:
        """Check if the given role or object exists in the given domain."""
        return self.get_role_name_from_domain(domain_name, role_or_obj_name) is not None

    def get_role_name_from_domain(self, domain_name: str, role_or_obj_name: str) -> str | None:
        """Check if the given role or object exists in the given domain,
        and return the related role name if it exists, otherwise return None.
        """
        try:
            domain = self.env.get_domain(domain_name)
        except ExtensionError:
            return None
        if role_or_obj_name in domain.roles:
            return role_or_obj_name
        if (
            role_name := domain.role_for_objtype(role_or_obj_name)
        ) and role_name in domain.roles:
            return role_name
        return None

    def invoke_role(self, role: tuple[str, str]) -> tuple[list[Node], list[system_message]]:
        """Invoke the role described by a ``(domain, role name)`` pair."""
        domain = self.env.get_domain(role[0])
        if domain:
            role_func = domain.role(role[1])
            assert role_func is not None

            return role_func(
                ':'.join(role),
                self.rawtext,
                self.text,
                self.lineno,
                self.inliner,
                self.options,
                self.content,
            )
        else:
            return [], []


class IntersphinxRoleResolver(ReferencesResolver):
    """pending_xref node resolver for intersphinx role.

    This resolves pending_xref nodes generated by :intersphinx:***: role.
    """

    default_priority = ReferencesResolver.default_priority - 1

    def run(self, **kwargs: Any) -> None:
        for node in self.document.findall(pending_xref):
            if 'intersphinx' not in node:
                continue
            contnode = cast(nodes.TextElement, node[0].deepcopy())
            inv_name = node['inventory']
            if inv_name is not None:
                assert inventory_exists(self.env, inv_name)
                newnode = resolve_reference_in_inventory(self.env, inv_name, node, contnode)
            else:
                newnode = resolve_reference_any_inventory(self.env, False, node, contnode)
            if newnode is None:
                typ = node['reftype']
                msg = __('external %s:%s reference target not found: %s') % (
                    node['refdomain'],
                    typ,
                    node['reftarget'],
                )
                logger.warning(msg, location=node, type='ref', subtype=typ)
                node.replace_self(contnode)
            else:
                node.replace_self(newnode)


def install_dispatcher(app: Sphinx, docname: str, source: list[str]) -> None:
    """Enable IntersphinxDispatcher.

    .. note:: The installed dispatcher will be uninstalled on disabling sphinx_domain
              automatically.
    """
    dispatcher = IntersphinxDispatcher()
    dispatcher.enable()
