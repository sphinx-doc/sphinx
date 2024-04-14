"""Insert links to objects documented in remote Sphinx documentation.

This works as follows:

* Each Sphinx HTML build creates a file named "objects.inv" that contains a
  mapping from object names to URIs relative to the HTML set's root.

* Projects using the Intersphinx extension can specify links to such mapping
  files in the `intersphinx_mapping` config value.  The mapping will then be
  used to resolve otherwise missing references to objects into links to the
  other documentation.

* By default, the mapping file is assumed to be at the same location as the
  rest of the documentation; however, the location of the mapping file can
  also be specified individually, e.g. if the docs should be buildable
  without Internet access.
"""

from __future__ import annotations

import concurrent.futures
import functools
import posixpath
import re
import sys
import time
from os import path
from typing import TYPE_CHECKING, cast
from urllib.parse import urlsplit, urlunsplit

from docutils import nodes

import sphinx
from sphinx.addnodes import pending_xref
from sphinx.builders.html import INVENTORY_FILENAME
from sphinx.deprecation import _deprecation_warning
from sphinx.errors import ExtensionError
from sphinx.locale import __
from sphinx.transforms.post_transforms import ReferencesResolver
from sphinx.util import logging, requests
from sphinx.util.docutils import CustomReSTDispatcher, SphinxRole
from sphinx.util.inventory import InventoryFile, InventoryItemSet

if TYPE_CHECKING:
    from collections.abc import Iterable
    from types import ModuleType
    from typing import IO, Any, Union

    from docutils.nodes import Element, Node, TextElement, system_message
    from docutils.utils import Reporter

    from sphinx.application import Sphinx
    from sphinx.config import Config
    from sphinx.domains import Domain
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import ExtensionMetadata, Inventory, RoleFunction

    InventoryCacheEntry = tuple[Union[str, None], int, Inventory]

logger = logging.getLogger(__name__)


def process_disabled_reftypes(env: BuildEnvironment) -> None:
    # Compile intersphinx_disabled_reftypes into datastructures
    # easier to check during reference resolution.
    # It is a separate function so the tests can use it.
    env.intersphinx_all_disabled = False  # type: ignore[attr-defined]
    env.intersphinx_all_domain_disabled = set()  # type: ignore[attr-defined]
    env.intersphinx_disabled_per_domain = {}  # type: ignore[attr-defined]
    for d in env.config.intersphinx_disabled_reftypes:
        if d == '*':
            env.intersphinx_all_disabled = True  # type: ignore[attr-defined]
        elif ':' in d:
            domain, typ = d.split(':', 1)
            if typ == '*':
                env.intersphinx_all_domain_disabled.add(domain)  # type: ignore[attr-defined]
            else:
                env.intersphinx_disabled_per_domain.setdefault(  # type: ignore[attr-defined]
                    domain, []).append(typ)


class InventoryAdapter:
    """Inventory adapter for environment"""

    def __init__(self, env: BuildEnvironment) -> None:
        _deprecation_warning(
            __name__, f'{self.__class__.__name__}', '', remove=(9, 0)
        )
        self.env = env

        if not hasattr(env, 'intersphinx_cache'):
            # initial storage when fetching inventories before processing
            self.env.intersphinx_cache = {}  # type: ignore[attr-defined]

            self.env.intersphinx_inventory = {}  # type: ignore[attr-defined]
            self.env.intersphinx_named_inventory = {}  # type: ignore[attr-defined]

    @property
    def cache(self) -> dict[str, InventoryCacheEntry]:
        """Intersphinx cache.

        - Key is the URI of the remote inventory
        - Element one is the key given in the Sphinx intersphinx_mapping
          configuration value
        - Element two is a time value for cache invalidation, a float
        - Element three is the loaded remote inventory, type Inventory
        """
        return self.env.intersphinx_cache  # type: ignore[attr-defined]

    @property
    def main_inventory(self) -> Inventory:
        return self.env.intersphinx_inventory  # type: ignore[attr-defined]

    @property
    def named_inventory(self) -> dict[str, Inventory]:
        return self.env.intersphinx_named_inventory  # type: ignore[attr-defined]

    def clear(self) -> None:
        self.env.intersphinx_inventory.clear()  # type: ignore[attr-defined]


class _EnvAdapter:
    """Adapter for environment to set inventory data and configuration settings."""

    def __init__(self, env: BuildEnvironment) -> None:
        self.env = env

        if not hasattr(env, 'intersphinx_cache'):
            process_disabled_reftypes(env)
            # old stuff, RemovedInSphinx90, still used in tests
            self.env.intersphinx_inventory = {}  # type: ignore[attr-defined]
            # old stuff end

            # initial storage when fetching inventories before processing
            self.env.intersphinx_cache = {}  # type: ignore[attr-defined]

            # list of inventory names for validation
            self.env.intersphinx_inventory_names = set()  # type: ignore[attr-defined]
            # store inventory data in domain-specific data structures
            self.env.intersphinx_by_domain_inventory = {}  # type: ignore[attr-defined]
            self._clear_by_domain_inventory()

    @property
    def all_objtypes_disabled(self) -> bool:
        return self.env.intersphinx_all_disabled  # type: ignore[attr-defined]

    def all_domain_objtypes_disabled(self, domain: str) -> bool:
        return domain in self.env.intersphinx_all_domain_disabled  # type: ignore[attr-defined]

    def disabled_objtypes_in_domain(self, domain: str) -> list[str]:
        return self.env.intersphinx_disabled_per_domain.get(domain, [])  # type: ignore[attr-defined]

    def _clear_by_domain_inventory(self) -> None:
        # reinitialize the domain-specific inventory stores
        for domain in self.env.domains.values():
            self.env.intersphinx_by_domain_inventory[domain.name] = {}  # type: ignore[attr-defined]

    @property
    def cache(self) -> dict[str, InventoryCacheEntry]:
        """Intersphinx cache.

        - Key is the URI of the remote inventory
        - Element one is the key given in the Sphinx intersphinx_mapping
          configuration value
        - Element two is a time value for cache invalidation, a float
        - Element three is the loaded remote inventory, type Inventory
        """
        return self.env.intersphinx_cache  # type: ignore[attr-defined]

    @property
    def names(self) -> set[str | None]:
        return self.env.intersphinx_inventory_names  # type: ignore[attr-defined]

    @property
    def by_domain_inventory(self) -> dict[str, dict[str, Any]]:
        return self.env.intersphinx_by_domain_inventory  # type: ignore[attr-defined]

    @property
    def main_inventory(self) -> Inventory:
        # deprecated, still used for setting up old stuff for tests
        return self.env.intersphinx_inventory  # type: ignore[attr-defined]

    def clear(self) -> None:
        # old stuff
        self.env.intersphinx_inventory.clear()  # type: ignore[attr-defined]
        # old stuff end
        self.env.intersphinx_inventory_names.clear()  # type: ignore[attr-defined]
        self.env.intersphinx_by_domain_inventory.clear()  # type: ignore[attr-defined]
        self._clear_by_domain_inventory()


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


def fetch_inventory(app: Sphinx, uri: str, inv: str) -> Inventory:
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
    name: str | None,
    uri: str,
    invs: tuple[str | None, ...],
    cache: dict[str, InventoryCacheEntry],
    app: Sphinx,
    now: int,
) -> bool:
    cache_time = now - app.config.intersphinx_cache_limit * 86400
    failures = []
    try:
        for inv in invs:
            if not inv:
                inv = posixpath.join(uri, INVENTORY_FILENAME)
            # decide whether the inventory must be read: always read local
            # files; remote ones only if the cache time is expired
            if '://' not in inv or uri not in cache or cache[uri][1] < cache_time:
                safe_inv_url = _get_safe_url(inv)
                logger.info(__('loading intersphinx inventory from %s...'), safe_inv_url)
                try:
                    invdata = fetch_inventory(app, uri, inv)
                except Exception as err:
                    failures.append(err.args)
                    continue
                if invdata:
                    cache[uri] = name, now, invdata
                    return True
        return False
    finally:
        if failures == []:
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


_debug = False
_debug_indent = 0
_debug_indent_string = "  "


def _debug_print(*args: Any) -> None:
    msg = _debug_indent_string * _debug_indent
    msg += "".join(str(e) for e in args)
    print(msg)


def load_mappings(app: Sphinx) -> None:
    """Load all intersphinx mappings into the environment."""
    now = int(time.time())
    inventories = _EnvAdapter(app.builder.env)
    intersphinx_cache: dict[str, InventoryCacheEntry] = inventories.cache

    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = []
        name: str | None
        uri: str
        invs: tuple[str | None, ...]
        for name, (uri, invs) in app.config.intersphinx_mapping.values():
            futures.append(pool.submit(
                fetch_inventory_group, name, uri, invs, intersphinx_cache, app, now,
            ))
        updated = [f.result() for f in concurrent.futures.as_completed(futures)]

    if any(updated):
        inventories.clear()

        # old stuff, still used in the tests
        cached_vals = list(inventories.cache.values())
        named_vals = sorted(v for v in cached_vals if v[0])
        unnamed_vals = [v for v in cached_vals if not v[0]]
        for _name, _, invdata in named_vals + unnamed_vals:
            for type, objects in invdata.items():
                inventories.main_inventory.setdefault(type, {}).update(objects)
        # end of old stuff

        # first collect all entries indexed by domain, object name, and object type
        # domain -> object_type -> object_name -> InventoryItemSet([(inv_name, inner_data)])
        entries: dict[str, dict[str, dict[str, InventoryItemSet]]] = {}
        for inv_name, _, inv_data in inventories.cache.values():
            assert inv_name not in inventories.names
            inventories.names.add(inv_name)

            for inv_object_type, inv_objects in inv_data.items():
                domain_name, object_type = inv_object_type.split(':', 1)
                # skip objects in domains we don't use
                if domain_name not in app.env.domains:
                    continue

                domain_entries = entries.setdefault(domain_name, {})
                per_type = domain_entries.setdefault(object_type, {})
                for object_name, object_data in inv_objects.items():
                    item_set = per_type.setdefault(object_name, InventoryItemSet())
                    item_set.append(inv_name, object_data)

        # and then give the data to each domain
        for domain_name, domain_entries in entries.items():
            if _debug:
                global _debug_indent
                _debug_print(f"intersphinx debug(load_mappings): domain={domain_name}")
                _debug_indent += 1
                for objtyp, names in domain_entries.items():
                    _debug_print(f"objtyp={objtyp}:")
                    _debug_indent += 1
                    for name, data in names.items():
                        _debug_print(f"{name}: {data}")
                    _debug_indent -= 1
                _debug_indent -= 1
            domain_store = inventories.by_domain_inventory[domain_name]
            domain_store.update(domain_entries)


def _resolve_reference_in_domain_by_target(
        inventory:  dict[str, dict[str, InventoryItemSet]],
        inv_name: str | None,
        domain: Domain, objtypes: list[str],
        target: str,
        node: pending_xref) -> InventoryItemSet | None:
    if _debug:
        global _debug_indent
        _debug_print("intersphinx debug(_resolve_reference_in_domain_by_target):")
        _debug_indent += 1
        _debug_print(f"inv_name={inv_name}")
        _debug_print(f"domain={domain.name}")
        _debug_print(f"target={target}")
        _debug_print(f"node={node}")
        _debug_indent -= 1
    for objtype in objtypes:
        if _debug:
            _debug_print(_debug_indent_string +
                         f"objtype={objtype}, inInventory={objtype in inventory}")
        if objtype not in inventory:
            # Continue if there's nothing of this kind in the inventory
            continue

        if target in inventory[objtype]:
            # Case-sensitive match, use it
            return inventory[objtype][target]
        elif domain.name == 'std' and objtype in ('label', 'term'):
            # Some types require case insensitive matches:
            # * 'term': https://github.com/sphinx-doc/sphinx/issues/9291
            # * 'label': https://github.com/sphinx-doc/sphinx/issues/12008
            target_lower = target.lower()
            insensitive_matches = list(filter(lambda k: k.lower() == target_lower,
                                              inventory[objtype].keys()))
            if insensitive_matches:
                return inventory[objtype][insensitive_matches[0]]
            else:
                # No case-insensitive match either, continue to the next candidate
                continue
        else:
            # Could reach here if we're not a term but have a case-insensitive match.
            # This is a fix for terms specifically, but potentially should apply to
            # other types.
            continue
        raise AssertionError
    return None


def _resolve_reference_in_domain(env: BuildEnvironment,
                                 inv_name: str | None,
                                 honor_disabled_refs: bool,
                                 domain: Domain,
                                 node: pending_xref, contnode: TextElement
                                 ) -> Element | None:
    if _debug:
        global _debug_indent
        _debug_print("intersphinx debug(_resolve_reference_in_domain):")
        _debug_indent += 1
        _debug_print(f"inv_name={inv_name}")
        _debug_print(f"honor_disabled_refs={honor_disabled_refs}")
        _debug_print(f"domain={domain.name}")
        _debug_print(f"node={node}")
    typ = node['reftype']
    if typ == 'any':
        objtypes = list(domain.object_types)
    else:
        for_role = domain.objtypes_for_role(typ)
        if not for_role:
            if _debug:
                _debug_print("not for_role")
                _debug_indent -= 1
            return None
        objtypes = for_role

    if _debug:
        _debug_print(f"objtypes init={objtypes}")

    # we adjust the object types for backwards compatibility
    if domain.name == 'std' and 'cmdoption' in objtypes:
        # cmdoptions were stored as std:option until Sphinx 1.6
        objtypes.append('option')
    if domain.name == 'py' and 'attribute' in objtypes:
        # properties are stored as py:method since Sphinx 2.1
        objtypes.append('method')

    if _debug:
        _debug_print(f"objtypes adju={objtypes}")

    # now that the objtypes list is complete we can remove the disabled ones
    if honor_disabled_refs:
        conf = _EnvAdapter(env)  # make sure the disabled has been processed
        assert not conf.all_objtypes_disabled
        assert not conf.all_domain_objtypes_disabled(domain.name)
        if _debug:
            _debug_print(f"disabled objt={conf.disabled_objtypes_in_domain(domain.name)}")
        objtypes = [o for o in objtypes
                    if o not in conf.disabled_objtypes_in_domain(domain.name)]
        if _debug:
            _debug_print(f"objtypes filt={objtypes}")

    def resolve() -> InventoryItemSet | None:
        inventory = _EnvAdapter(env).by_domain_inventory[domain.name]
        # without qualification
        res = _resolve_reference_in_domain_by_target(inventory, inv_name, domain, objtypes,
                                                     node['reftarget'], node)
        if _debug:
            _debug_print(f"unqualified lookup: res={res}")
        if res is not None:
            return res

        # try with qualification of the current scope instead
        full_qualified_name = domain.get_full_qualified_name(node)
        if full_qualified_name is None:
            if _debug:
                _debug_print("no full_qualified_name, res=None")
            return None
        res = _resolve_reference_in_domain_by_target(inventory, inv_name, domain, objtypes,
                                                     full_qualified_name, node)
        if _debug:
            _debug_print(f"qualified lookup: res={res}")
        return res

    inv_set = resolve()
    if inv_set is None:
        if _debug:
            _debug_indent -= 1
        return None
    inv_set_restricted = inv_set.select_inventory(inv_name)
    if _debug:
        _debug_print(f"res restricted to inv_name={inv_name}: {inv_set_restricted}")
        _debug_indent -= 1
    try:
        return inv_set_restricted.make_reference_node(domain.name, node, contnode)
    except ValueError:
        return None


def _resolve_reference(env: BuildEnvironment, inv_name: str | None,
                       honor_disabled_refs: bool,
                       node: pending_xref, contnode: TextElement) -> Element | None:
    if _debug:
        global _debug_indent
        _debug_print("intersphinx debug(_resolve_reference):")
        _debug_indent += 1
        _debug_print(f"inv_name={inv_name}")
        _debug_print(f"honor_disabled_refs={honor_disabled_refs}")
        _debug_print(f"node={node}")
    # disabling should only be done if no inventory is given
    honor_disabled_refs = honor_disabled_refs and inv_name is None

    if honor_disabled_refs and _EnvAdapter(env).all_objtypes_disabled:
        if _debug:
            _debug_print("res=None, honor_disabled_refs and all_objtypes_disabled")
            _debug_indent -= 1
        return None

    typ = node['reftype']
    if typ == 'any':
        for domain_name, domain in env.domains.items():
            if _debug:
                _debug_print(f"typ=any, trying domain={domain_name}")
            if (honor_disabled_refs
                    and _EnvAdapter(env).all_domain_objtypes_disabled(domain_name)):
                if _debug:
                    msg = _debug_indent_string
                    msg += "skipping, honor_disabled_refs and all_domain_objtypes_disabled"
                    _debug_print(msg)
                continue
            res = _resolve_reference_in_domain(env, inv_name, honor_disabled_refs,
                                               domain, node, contnode)
            if res is not None:
                if _debug:
                    _debug_print(f"res={res}")
                    _debug_indent -= 1
                return res
        if _debug:
            _debug_print("res=None, no matches in any domain")
            _debug_indent -= 1
        return None
    else:
        domain_name = node.get('refdomain')
        if not domain_name:
            if _debug:
                _debug_print("res=None, no domain in reference")
                _debug_indent -= 1
            # only objects in domains are in the inventory
            return None
        if honor_disabled_refs and _EnvAdapter(env).all_domain_objtypes_disabled(domain_name):
            if _debug:
                _debug_print("res=None, honor_disabled_refs and all_domain_objtypes_disabled")
                _debug_indent -= 1
            return None
        domain = env.get_domain(domain_name)
        res = _resolve_reference_in_domain(env, inv_name, honor_disabled_refs,
                                           domain, node, contnode)
        if _debug:
            _debug_print(f"res={res}")
            _debug_indent -= 1
        return res


def inventory_exists(env: BuildEnvironment, inv_name: str) -> bool:
    return inv_name in _EnvAdapter(env).names


def resolve_reference_in_inventory(env: BuildEnvironment,
                                   inv_name: str,
                                   node: pending_xref, contnode: TextElement,
                                   ) -> Element | None:
    """Attempt to resolve a missing reference via intersphinx references.

    Resolution is tried in the given inventory with the target as is.

    Requires ``inventory_exists(env, inv_name)``.
    """
    assert inventory_exists(env, inv_name)
    if _debug:
        global _debug_indent
        _debug_print("intersphinx debug(resolve_reference_in_inventory):")
        _debug_indent += 1
    res = _resolve_reference(env, inv_name, False, node, contnode)
    if _debug:
        _debug_print(f"res={res}")
        _debug_indent -= 1
    return res


def resolve_reference_any_inventory(env: BuildEnvironment,
                                    honor_disabled_refs: bool,
                                    node: pending_xref, contnode: TextElement,
                                    ) -> Element | None:
    """Attempt to resolve a missing reference via intersphinx references.

    Resolution is tried with the target as is in any inventory.
    """
    if _debug:
        global _debug_indent
        _debug_print("intersphinx debug(resolve_reference_any_inventory):")
        _debug_indent += 1
    res = _resolve_reference(env, None, honor_disabled_refs, node, contnode)
    if _debug:
        _debug_print(f"res={res}")
        _debug_indent -= 1
    return res


def resolve_reference_detect_inventory(env: BuildEnvironment,
                                       node: pending_xref, contnode: TextElement,
                                       ) -> Element | None:
    """Attempt to resolve a missing reference via intersphinx references.

    Resolution is tried first with the target as is in any inventory.
    If this does not succeed, then the target is split by the first ``:``,
    to form ``inv_name:newtarget``. If ``inv_name`` is a named inventory, then resolution
    is tried in that inventory with the new target.
    """
    if _debug:
        global _debug_indent
        _debug_print("intersphinx debug(resolve_reference_detect_inventory):")
        _debug_indent += 1
        _debug_print(f"node={node}")
    # ordinary direct lookup, use data as is
    res = resolve_reference_any_inventory(env, True, node, contnode)
    if res is not None:
        if _debug:
            _debug_print(f"res={res}")
            _debug_indent -= 1
        return res

    # try splitting the target into 'inv_name:target'
    target = node['reftarget']
    if ':' not in target:
        if _debug:
            _debug_print("res=None, can't split into inv_name:target")
            _debug_indent -= 1
        return None
    inv_name, newtarget = target.split(':', 1)
    if not inventory_exists(env, inv_name):
        if _debug:
            _debug_print(f"res=None, inventory ({inv_name}) doesn't exist")
            _debug_indent -= 1
        return None
    node['reftarget'] = newtarget
    node['origtarget'] = target
    res_inv = resolve_reference_in_inventory(env, inv_name, node, contnode)
    node['reftarget'] = target
    del node['origtarget']
    if _debug:
        _debug_print(f"res={res_inv}")
        _debug_indent -= 1
    return res_inv


def missing_reference(app: Sphinx, env: BuildEnvironment, node: pending_xref,
                      contnode: TextElement) -> Element | None:
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
    _re_inv_ref = re.compile(r"(\+([^:]+))?:(.*)")

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
        logger.warning(
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


def normalize_intersphinx_mapping(app: Sphinx, config: Config) -> None:
    for key, value in config.intersphinx_mapping.copy().items():
        try:
            if isinstance(value, (list, tuple)):
                # new format
                name, (uri, inv) = key, value
                if not isinstance(name, str):
                    logger.warning(__('intersphinx identifier %r is not string. Ignored'),
                                   name)
                    config.intersphinx_mapping.pop(key)
                    continue
            else:
                # old format, no name
                # xref RemovedInSphinx80Warning
                name, uri, inv = None, key, value
                msg = (
                    "The pre-Sphinx 1.0 'intersphinx_mapping' format is "
                    "deprecated and will be removed in Sphinx 8. Update to the "
                    "current format as described in the documentation. "
                    f"Hint: \"intersphinx_mapping = {{'<name>': {(uri, inv)!r}}}\"."
                    "https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#confval-intersphinx_mapping"  # NoQA: E501
                )
                logger.warning(msg)

            if not isinstance(inv, tuple):
                config.intersphinx_mapping[key] = (name, (uri, (inv,)))
            else:
                config.intersphinx_mapping[key] = (name, (uri, inv))
        except Exception as exc:
            logger.warning(__('Failed to read intersphinx_mapping[%s], ignored: %r'), key, exc)
            config.intersphinx_mapping.pop(key)


def setup(app: Sphinx) -> ExtensionMetadata:
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
