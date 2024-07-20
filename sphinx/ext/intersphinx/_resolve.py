"""This module provides logic for resolving references to intersphinx targets."""

from __future__ import annotations

import posixpath
import sys
import time
from operator import itemgetter
from os import path
from typing import TYPE_CHECKING, cast

from docutils import nodes
from docutils.utils import relative_path

from sphinx.addnodes import pending_xref
from sphinx.deprecation import _deprecation_warning
from sphinx.errors import ExtensionError
from sphinx.ext.intersphinx._shared import LOGGER, InventoryAdapter
from sphinx.locale import _, __
from sphinx.transforms.post_transforms import ReferencesResolver
from sphinx.util.docutils import CustomReSTDispatcher, SphinxRole

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import ModuleType
    from typing import IO, Any, Optional

    from docutils.nodes import Node, TextElement, system_message
    from docutils.utils import Reporter

    from sphinx.application import Sphinx
    from sphinx.domains import Domain
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import Inventory, InventoryItem, RoleFunction

    #: The inventory project URL to which links are resolved.
    #:
    #: This value is unique in :confval:`intersphinx_mapping`.
    InventoryURI = str

    #: The inventory (non-empty) name.
    #:
    #: It is unique and in bijection with an inventory remote URL.
    InventoryName = str

    #: A target (local or remote) containing the inventory data to fetch.
    #:
    #: Empty strings are not expected and ``None`` indicates the default
    #: inventory file name :data:`~sphinx.builder.html.INVENTORY_FILENAME`.
    InventoryLocation = Optional[str]

    #: Inventory cache entry. The integer field is the cache expiration time.
    InventoryCacheEntry = tuple[InventoryName, int, Inventory]

    #: The type of :confval:`intersphinx_mapping` *after* normalization.
    IntersphinxMapping = dict[
        InventoryName,
        tuple[InventoryName, tuple[InventoryURI, tuple[InventoryLocation, ...]]],
    ]




def _strip_basic_auth(url: str) -> str:
    """Returns *url* with basic auth credentials removed. Also returns the
    basic auth username and password if they're present in *url*.

    E.g.: https://user:pass@example.com => https://example.com

    *url* need not include basic auth credentials.

    :param url: url which may or may not contain basic auth credentials
    :type url: ``str``

    :return: *url* with any basic auth creds removed
    :rtype: ``str``
    """
    frags = list(urlsplit(url))
    # swap out "user[:pass]@hostname" for "hostname"
    if '@' in frags[1]:
        frags[1] = frags[1].split('@')[1]
    return urlunsplit(frags)


def _read_from_url(url: str, *, config: Config) -> IO:
    """Reads data from *url* with an HTTP *GET*.

    This function supports fetching from resources which use basic HTTP auth as
    laid out by RFC1738 § 3.1. See § 5 for grammar definitions for URLs.

    .. seealso:

       https://www.ietf.org/rfc/rfc1738.txt

    :param url: URL of an HTTP resource
    :type url: ``str``

    :return: data read from resource described by *url*
    :rtype: ``file``-like object
    """
    r = requests.get(url, stream=True, timeout=config.intersphinx_timeout,
                     _user_agent=config.user_agent,
                     _tls_info=(config.tls_verify, config.tls_cacerts))
    r.raise_for_status()
    r.raw.url = r.url
    # decode content-body based on the header.
    # ref: https://github.com/psf/requests/issues/2155
    r.raw.read = functools.partial(r.raw.read, decode_content=True)
    return r.raw


def _get_safe_url(url: str) -> str:
    """Gets version of *url* with basic auth passwords obscured. This function
    returns results suitable for printing and logging.

    E.g.: https://user:12345@example.com => https://user@example.com

    :param url: a url
    :type url: ``str``

    :return: *url* with password removed
    :rtype: ``str``
    """
    parts = urlsplit(url)
    if parts.username is None:
        return url
    else:
        frags = list(parts)
        if parts.port:
            frags[1] = f'{parts.username}@{parts.hostname}:{parts.port}'
        else:
            frags[1] = f'{parts.username}@{parts.hostname}'

        return urlunsplit(frags)


def fetch_inventory(app: Sphinx, uri: InventoryURI, inv: str) -> Inventory:
    """Fetch, parse and return an intersphinx inventory file."""
    # both *uri* (base URI of the links to generate) and *inv* (actual
    # location of the inventory file) can be local or remote URIs
    if '://' in uri:
        # case: inv URI points to remote resource; strip any existing auth
        uri = _strip_basic_auth(uri)
    try:
        if '://' in inv:
            f = _read_from_url(inv, config=app.config)
        else:
            f = open(path.join(app.srcdir, inv), 'rb')  # NoQA: SIM115
    except Exception as err:
        err.args = ('intersphinx inventory %r not fetchable due to %s: %s',
                    inv, err.__class__, str(err))
        raise
    try:
        if hasattr(f, 'url'):
            newinv = f.url
            if inv != newinv:
                logger.info(__('intersphinx inventory has moved: %s -> %s'), inv, newinv)

                if uri in (inv, path.dirname(inv), path.dirname(inv) + '/'):
                    uri = path.dirname(newinv)
        with f:
            try:
                invdata = InventoryFile.load(f, uri, posixpath.join)
            except ValueError as exc:
                raise ValueError('unknown or unsupported inventory version: %r' % exc) from exc
    except Exception as err:
        err.args = ('intersphinx inventory %r not readable due to %s: %s',
                    inv, err.__class__.__name__, str(err))
        raise
    else:
        return invdata


def fetch_inventory_group(
    name: InventoryName,
    uri: InventoryURI,
    invs: tuple[InventoryLocation, ...],
    cache: dict[InventoryURI, InventoryCacheEntry],
    app: Sphinx,
    now: int,
) -> bool:
    cache_time = now - app.config.intersphinx_cache_limit * 86400

    def should_store(uri: str, inv: str) -> bool:
        # decide whether the inventory must be read: always read local
        # files; remote ones only if the cache time is expired
        return '://' not in inv or uri not in cache or cache[uri][1] < cache_time

    updated = False
    failures = []

    for location in invs:
        inv: str = location or posixpath.join(uri, INVENTORY_FILENAME)
        if not should_store(uri, inv):
            continue

        safe_inv_url = _get_safe_url(inv)
        logger.info(__('loading intersphinx inventory from %s...'), safe_inv_url)

        try:
            invdata = fetch_inventory(app, uri, inv)
        except Exception as err:
            failures.append(err.args)
            continue

        if invdata:
            cache[uri] = name, now, invdata
            updated = True
            break

    if not failures:
        pass
    elif len(failures) < len(invs):
        logger.info(__("encountered some issues with some of the inventories,"
                       " but they had working alternatives:"))
        for fail in failures:
            logger.info(*fail)
    else:
        issues = '\n'.join(f[0] % f[1:] for f in failures)
        logger.warning(__("failed to reach any of the inventories "
                          "with the following issues:") + "\n" + issues)
    return updated


def load_mappings(app: Sphinx) -> None:
    """Load the (normalized) intersphinx mappings into the environment."""
    now = int(time.time())
    inventories = InventoryAdapter(app.builder.env)
    intersphinx_cache: dict[InventoryURI, InventoryCacheEntry] = inventories.cache
    intersphinx_mapping = app.config.intersphinx_mapping

    expected_uris = {uri for uri, _invs in app.config.intersphinx_mapping.values()}

    # If the current cache contains some (project, uri) pair
    # say ("foo", "foo.com") and if the new intersphinx dict
    # contains the pair ("foo", "bar.com"), we need to remove
    # the ("foo", "foo.com") entry and use ("foo", "bar.com").
    for uri in frozenset(intersphinx_cache):
        if intersphinx_cache[uri][0] not in intersphinx_mapping or uri not in expected_uris:
            # remove a cached inventory if the latter is no more used by intersphinx
            del intersphinx_cache[uri]

    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = [
            pool.submit(fetch_inventory_group, name, uri, invs, intersphinx_cache, app, now)
            for name, (uri, invs) in app.config.intersphinx_mapping.values()
        ]
        updated = [f.result() for f in concurrent.futures.as_completed(futures)]

    if any(updated):
        # clear the local inventories
        inventories.clear()

        # Duplicate values in different inventories will shadow each
        # other and which one will override which varies between builds.
        #
        # We can however order the cache by URIs for reproducibility.
        intersphinx_cache_values = sorted(intersphinx_cache.values(), key=itemgetter(0, 1))
        for name, _timeout, invdata in intersphinx_cache_values:
            if not name:
                logger.warning(
                    __('intersphinx cache seems corrupted, please rebuild '
                       'the project with the "-E" option (see sphinx --help)'),
                )
                continue

            inventories.named_inventory[name] = invdata
            for objtype, objects in invdata.items():
                inventories.main_inventory.setdefault(objtype, {}).update(objects)


def _create_element_from_result(
    domain: Domain, inv_name: InventoryName | None,
    data: InventoryItem,
    node: pending_xref, contnode: TextElement,
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
            newnode.append(contnode.__class__(title[len(inv_name) + 1:],
                                              title[len(inv_name) + 1:]))
        else:
            newnode.append(contnode)
    else:
        # else use the given display name (used for :ref:)
        newnode.append(contnode.__class__(dispname, dispname))
    return newnode


def _resolve_reference_in_domain_by_target(
    inv_name: InventoryName | None, inventory: Inventory,
    domain: Domain, objtypes: Iterable[str],
    target: str,
    node: pending_xref, contnode: TextElement,
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
            insensitive_matches = list(filter(lambda k: k.lower() == target_lower,
                                              inventory[objtype].keys()))
            if len(insensitive_matches) > 1:
                inv_descriptor = inv_name or 'main_inventory'
                LOGGER.warning(__("inventory '%s': multiple matches found for %s:%s"),
                               inv_descriptor, objtype, target,
                               type='intersphinx',  subtype='external', location=node)
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
    inv_name: InventoryName | None, inventory: Inventory,
    honor_disabled_refs: bool,
    domain: Domain, objtypes: Iterable[str],
    node: pending_xref, contnode: TextElement,
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
        obj_types = {obj_type: None
                     for obj_type in obj_types
                     if obj_type not in disabled}

    objtypes = [*obj_types.keys()]

    # without qualification
    res = _resolve_reference_in_domain_by_target(inv_name, inventory, domain, objtypes,
                                                 node['reftarget'], node, contnode)
    if res is not None:
        return res

    # try with qualification of the current scope instead
    full_qualified_name = domain.get_full_qualified_name(node)
    if full_qualified_name is None:
        return None
    return _resolve_reference_in_domain_by_target(inv_name, inventory, domain, objtypes,
                                                  full_qualified_name, node, contnode)


def _resolve_reference(
    env: BuildEnvironment,
    inv_name: InventoryName | None, inventory: Inventory,
    honor_disabled_refs: bool,
    node: pending_xref, contnode: TextElement,
) -> nodes.reference | None:
    # disabling should only be done if no inventory is given
    honor_disabled_refs = honor_disabled_refs and inv_name is None
    intersphinx_disabled_reftypes = env.config.intersphinx_disabled_reftypes

    if honor_disabled_refs and '*' in intersphinx_disabled_reftypes:
        return None

    typ = node['reftype']
    if typ == 'any':
        for domain_name, domain in env.domains.items():
            if honor_disabled_refs and f'{domain_name}:*' in intersphinx_disabled_reftypes:
                continue
            objtypes: Iterable[str] = domain.object_types.keys()
            res = _resolve_reference_in_domain(env, inv_name, inventory,
                                               honor_disabled_refs,
                                               domain, objtypes,
                                               node, contnode)
            if res is not None:
                return res
        return None
    else:
        domain_name = node.get('refdomain')
        if not domain_name:
            # only objects in domains are in the inventory
            return None
        if honor_disabled_refs and f'{domain_name}:*' in intersphinx_disabled_reftypes:
            return None
        domain = env.get_domain(domain_name)
        objtypes = domain.objtypes_for_role(typ) or ()
        if not objtypes:
            return None
        return _resolve_reference_in_domain(env, inv_name, inventory,
                                            honor_disabled_refs,
                                            domain, objtypes,
                                            node, contnode)


def inventory_exists(env: BuildEnvironment, inv_name: InventoryName) -> bool:
    return inv_name in InventoryAdapter(env).named_inventory


def resolve_reference_in_inventory(
    env: BuildEnvironment,
    inv_name: InventoryName,
    node: pending_xref, contnode: TextElement,
) -> nodes.reference | None:
    """Attempt to resolve a missing reference via intersphinx references.

    Resolution is tried in the given inventory with the target as is.

    Requires ``inventory_exists(env, inv_name)``.
    """
    assert inventory_exists(env, inv_name)
    return _resolve_reference(env, inv_name, InventoryAdapter(env).named_inventory[inv_name],
                              False, node, contnode)


def resolve_reference_any_inventory(
    env: BuildEnvironment,
    honor_disabled_refs: bool,
    node: pending_xref, contnode: TextElement,
) -> nodes.reference | None:
    """Attempt to resolve a missing reference via intersphinx references.

    Resolution is tried with the target as is in any inventory.
    """
    return _resolve_reference(env, None, InventoryAdapter(env).main_inventory,
                              honor_disabled_refs,
                              node, contnode)


def resolve_reference_detect_inventory(
    env: BuildEnvironment, node: pending_xref, contnode: TextElement,
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
    app: Sphinx, env: BuildEnvironment, node: pending_xref, contnode: TextElement,
) -> nodes.reference | None:
    """Attempt to resolve a missing reference via intersphinx references."""
    return resolve_reference_detect_inventory(env, node, contnode)


class IntersphinxDispatcher(CustomReSTDispatcher):
    """Custom dispatcher for external role.

    This enables :external:***:/:external+***: roles on parsing reST document.
    """

    def role(
        self, role_name: str, language_module: ModuleType, lineno: int, reporter: Reporter,
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
            self._emit_warning(
                __('inventory for external cross-reference not found: %r'), inventory
            )
            return [], []

        domain_name, role_name = self._get_domain_role(name_suffix)

        if role_name is None:
            self._emit_warning(
                __('invalid external cross-reference suffix: %r'), name_suffix
            )
            return [], []

        # attempt to find a matching role function
        role_func: RoleFunction | None

        if domain_name is not None:
            # the user specified a domain, so we only check that
            if (domain := self.env.domains.get(domain_name)) is None:
                self._emit_warning(
                    __('domain for external cross-reference not found: %r'), domain_name
                )
                return [], []
            if (role_func := domain.roles.get(role_name)) is None:
                msg = 'role for external cross-reference not found in domain %r: %r'
                if (
                    object_types := domain.object_types.get(role_name)
                ) is not None and object_types.roles:
                    self._emit_warning(
                        __(f'{msg} (perhaps you meant one of: %s)'),
                        domain_name,
                        role_name,
                        self._concat_strings(object_types.roles),
                    )
                else:
                    self._emit_warning(__(msg), domain_name, role_name)
                return [], []

        else:
            # the user did not specify a domain,
            # so we check first the default (if available) then standard domains
            domains: list[Domain] = []
            if default_domain := self.env.temp_data.get('default_domain'):
                domains.append(default_domain)
            if (
                std_domain := self.env.domains.get('std')
            ) is not None and std_domain not in domains:
                domains.append(std_domain)

            role_func = None
            for domain in domains:
                if (role_func := domain.roles.get(role_name)) is not None:
                    domain_name = domain.name
                    break

            if role_func is None or domain_name is None:
                domains_str = self._concat_strings(d.name for d in domains)
                msg = 'role for external cross-reference not found in domains %s: %r'
                possible_roles: set[str] = set()
                for d in domains:
                    if o := d.object_types.get(role_name):
                        possible_roles.update(f'{d.name}:{r}' for r in o.roles)
                if possible_roles:
                    msg = f'{msg} (perhaps you meant one of: %s)'
                    self._emit_warning(
                        __(msg),
                        domains_str,
                        role_name,
                        self._concat_strings(possible_roles),
                    )
                else:
                    self._emit_warning(__(msg), domains_str, role_name)
                return [], []

        result, messages = role_func(
            f'{domain_name}:{role_name}',
            self.rawtext,
            self.text,
            self.lineno,
            self.inliner,
            self.options,
            self.content,
        )

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

    def _get_domain_role(self, name: str) -> tuple[str | None, str | None]:
        """Convert the *name* string into a domain and a role name.

        - If *name* contains no ``:``, return ``(None, name)``.
        - If *name* contains a single ``:``, the domain/role is split on this.
        - If *name* contains multiple ``:``, return ``(None, None)``.
        """
        names = name.split(':')
        if len(names) == 1:
            return None, names[0]
        elif len(names) == 2:
            return names[0], names[1]
        else:
            return None, None

    def _emit_warning(self, msg: str, /, *args: Any) -> None:
        LOGGER.warning(
            msg,
            *args,
            type='intersphinx',
            subtype='external',
            location=(self.env.docname, self.lineno),
        )

    def _concat_strings(self, strings: Iterable[str]) -> str:
        return ', '.join(f'{s!r}' for s in sorted(strings))

    # deprecated methods

    def get_role_name(self, name: str) -> tuple[str, str] | None:
        _deprecation_warning(
            __name__, f'{self.__class__.__name__}.get_role_name', '', remove=(9, 0)
        )
        names = name.split(':')
        if len(names) == 1:
            # role
            default_domain = self.env.temp_data.get('default_domain')
            domain = default_domain.name if default_domain else None
            role = names[0]
        elif len(names) == 2:
            # domain:role:
            domain = names[0]
            role = names[1]
        else:
            return None

        if domain and self.is_existent_role(domain, role):
            return (domain, role)
        elif self.is_existent_role('std', role):
            return ('std', role)
        else:
            return None

    def is_existent_role(self, domain_name: str, role_name: str) -> bool:
        _deprecation_warning(
            __name__, f'{self.__class__.__name__}.is_existent_role', '', remove=(9, 0)
        )
        try:
            domain = self.env.get_domain(domain_name)
            return role_name in domain.roles
        except ExtensionError:
            return False

    def invoke_role(self, role: tuple[str, str]) -> tuple[list[Node], list[system_message]]:
        """Invoke the role described by a ``(domain, role name)`` pair."""
        _deprecation_warning(
            __name__, f'{self.__class__.__name__}.invoke_role', '', remove=(9, 0)
        )
        domain = self.env.get_domain(role[0])
        if domain:
            role_func = domain.role(role[1])
            assert role_func is not None

            return role_func(':'.join(role), self.rawtext, self.text, self.lineno,
                             self.inliner, self.options, self.content)
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
                msg = (__('external %s:%s reference target not found: %s') %
                       (node['refdomain'], typ, node['reftarget']))
                LOGGER.warning(msg, location=node, type='ref', subtype=typ)
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


def normalize_intersphinx_mapping(app: Sphinx, config: Config) -> None:
    # URIs should NOT be duplicated, otherwise different builds may use
    # different project names (and thus, the build are no more reproducible)
    # depending on which one is inserted last in the cache.
    seen: dict[InventoryURI, InventoryName] = {}

    for name, value in config.intersphinx_mapping.copy().items():
        if not isinstance(name, str):
            logger.warning(
                __('intersphinx identifier %r is not string. Ignored'),
                name, type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        # ensure that intersphinx projects are always named
        if not name:
            logger.warning(
                __('ignoring empty intersphinx identifier'),
                type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        if not isinstance(value, (tuple, list)):
            logger.warning(
                __('intersphinx_mapping[%r]: expecting a tuple or a list, got: %r; ignoring.'),
                name, value, type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        try:
            uri, inv = value
        except Exception as exc:
            logger.warning(
                __('Failed to read intersphinx_mapping[%s], ignored: %r'),
                name, exc, type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        if not uri or not isinstance(uri, str):
            logger.warning(
                __('intersphinx_mapping[%r]: URI must be a non-empty string, '
                   'got: %r; ignoring.'),
                name, uri, type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        if (name_for_uri := seen.setdefault(uri, name)) != name:
            logger.warning(
                __('intersphinx_mapping[%r]: URI %r shadows URI from intersphinx_mapping[%r]; '
                   'ignoring.'), name, uri, name_for_uri, type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        targets: list[InventoryLocation] = []
        for target in (inv if isinstance(inv, (tuple, list)) else (inv,)):
            if target is None or target and isinstance(target, str):
                targets.append(target)
            else:
                logger.warning(
                    __('intersphinx_mapping[%r]: inventory location must '
                       'be a non-empty string or None, got: %r; ignoring.'),
                    name, target, type='intersphinx', subtype='config',
                )

        config.intersphinx_mapping[name] = (name, (uri, tuple(targets)))


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value('intersphinx_mapping', {}, 'env')
    app.add_config_value('intersphinx_cache_limit', 5, '')
    app.add_config_value('intersphinx_timeout', None, '')
    app.add_config_value('intersphinx_disabled_reftypes', ['std:doc'], 'env')
    app.connect('config-inited', normalize_intersphinx_mapping, priority=800)
    app.connect('builder-inited', load_mappings)
    app.connect('source-read', install_dispatcher)
    app.connect('missing-reference', missing_reference)
    app.add_post_transform(IntersphinxRoleResolver)
    return {
        'version': sphinx.__display_version__,
        'env_version': 1,
        'parallel_read_safe': True,
    }


def inspect_main(argv: list[str], /) -> int:
    """Debug functionality to print out an inventory"""
    if len(argv) < 1:
        print("Print out an inventory file.\n"
              "Error: must specify local path or URL to an inventory file.",
              file=sys.stderr)
        return 1

    class MockConfig:
        intersphinx_timeout: int | None = None
        tls_verify = False
        tls_cacerts: str | dict[str, str] | None = None
        user_agent: str = ''

    class MockApp:
        srcdir = ''
        config = MockConfig()

    try:
        filename = argv[0]
        inv_data = fetch_inventory(MockApp(), '', filename)  # type: ignore[arg-type]
        for key in sorted(inv_data or {}):
            print(key)
            inv_entries = sorted(inv_data[key].items())
            for entry, (_proj, _ver, url_path, display_name) in inv_entries:
                display_name = display_name * (display_name != '-')
                print(f'    {entry:<40} {display_name:<40}: {url_path}')
    except ValueError as exc:
        print(exc.args[0] % exc.args[1:], file=sys.stderr)
        return 1
    except Exception as exc:
        print(f'Unknown error: {exc!r}', file=sys.stderr)
        return 1
    else:
        return 0


if __name__ == '__main__':
    import logging as _logging
    _logging.basicConfig()

    raise SystemExit(inspect_main(sys.argv[1:]))
