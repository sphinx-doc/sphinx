"""This module contains the code for loading intersphinx inventories."""

from __future__ import annotations

import concurrent.futures
import functools
import posixpath
import time
from operator import itemgetter
from os import path
from typing import TYPE_CHECKING
from urllib.parse import urlsplit, urlunsplit

from sphinx.builders.html import INVENTORY_FILENAME
from sphinx.ext.intersphinx._shared import LOGGER, InventoryAdapter
from sphinx.locale import __
from sphinx.util import requests
from sphinx.util.inventory import InventoryFile

if TYPE_CHECKING:
    from typing import IO

    from sphinx.application import Sphinx
    from sphinx.config import Config
    from sphinx.ext.intersphinx._shared import (
        InventoryCacheEntry,
        InventoryLocation,
        InventoryName,
        InventoryURI,
    )
    from sphinx.util.typing import Inventory


def normalize_intersphinx_mapping(app: Sphinx, config: Config) -> None:
    # URIs should NOT be duplicated, otherwise different builds may use
    # different project names (and thus, the build are no more reproducible)
    # depending on which one is inserted last in the cache.
    seen: dict[InventoryURI, InventoryName] = {}

    for name, value in config.intersphinx_mapping.copy().items():
        if not isinstance(name, str):
            LOGGER.warning(
                __('intersphinx identifier %r is not string. Ignored'),
                name, type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        # ensure that intersphinx projects are always named
        if not name:
            LOGGER.warning(
                __('ignoring empty intersphinx identifier'),
                type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        if not isinstance(value, (tuple, list)):
            LOGGER.warning(
                __('intersphinx_mapping[%r]: expecting a tuple or a list, got: %r; ignoring.'),
                name, value, type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        try:
            uri, inv = value
        except Exception as exc:
            LOGGER.warning(
                __('Failed to read intersphinx_mapping[%s], ignored: %r'),
                name, exc, type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        if not uri or not isinstance(uri, str):
            LOGGER.warning(
                __('intersphinx_mapping[%r]: URI must be a non-empty string, '
                   'got: %r; ignoring.'),
                name, uri, type='intersphinx', subtype='config',
            )
            del config.intersphinx_mapping[name]
            continue

        if (name_for_uri := seen.setdefault(uri, name)) != name:
            LOGGER.warning(
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
                LOGGER.warning(
                    __('intersphinx_mapping[%r]: inventory location must '
                       'be a non-empty string or None, got: %r; ignoring.'),
                    name, target, type='intersphinx', subtype='config',
                )

        config.intersphinx_mapping[name] = (name, (uri, tuple(targets)))


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
                LOGGER.warning(
                    __('intersphinx cache seems corrupted, please rebuild '
                       'the project with the "-E" option (see sphinx --help)'),
                )
                continue

            inventories.named_inventory[name] = invdata
            for objtype, objects in invdata.items():
                inventories.main_inventory.setdefault(objtype, {}).update(objects)


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
            print("nope", uri, inv)
            continue

        safe_inv_url = _get_safe_url(inv)
        inv_descriptor = name or 'main_inventory'
        LOGGER.info(__("loading intersphinx inventory '%s' from %s..."),
                    inv_descriptor, safe_inv_url)

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
        LOGGER.info(__("encountered some issues with some of the inventories,"
                       " but they had working alternatives:"))
        for fail in failures:
            LOGGER.info(*fail)
    else:
        issues = '\n'.join(f[0] % f[1:] for f in failures)
        LOGGER.warning(__("failed to reach any of the inventories "
                          "with the following issues:") + "\n" + issues)
    return updated


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
                LOGGER.info(__('intersphinx inventory has moved: %s -> %s'), inv, newinv)

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
    # swap out 'user[:pass]@hostname' for 'hostname'
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
