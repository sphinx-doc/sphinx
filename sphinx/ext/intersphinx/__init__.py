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

import sys
from typing import TYPE_CHECKING

import sphinx

from ._load import (
    fetch_inventory,
    fetch_inventory_group,
    load_mappings,
    normalize_intersphinx_mapping,
)
from ._resolve import (
    IntersphinxDispatcher,
    IntersphinxRole,
    IntersphinxRoleResolver,
    install_dispatcher,
    inventory_exists,
    missing_reference,
    resolve_reference_any_inventory,
    resolve_reference_detect_inventory,
    resolve_reference_in_inventory,
)
from ._shared import InventoryAdapter

if TYPE_CHECKING:
    from typing import Any

    from sphinx.application import Sphinx


__all__ = (
    "InventoryAdapter",
    "fetch_inventory",
    "fetch_inventory_group",
    "load_mappings",
    "normalize_intersphinx_mapping",
    "IntersphinxRoleResolver",
    "inventory_exists",
    "install_dispatcher",
    "resolve_reference_in_inventory",
    "resolve_reference_any_inventory",
    "resolve_reference_detect_inventory",
    "missing_reference",
    "IntersphinxDispatcher",
    "IntersphinxRole",
    "inspect_main",
)


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_config_value("intersphinx_mapping", {}, "env")
    app.add_config_value("intersphinx_cache_limit", 5, "")
    app.add_config_value("intersphinx_timeout", None, "")
    app.add_config_value("intersphinx_disabled_reftypes", ["std:doc"], "env")
    app.connect("config-inited", normalize_intersphinx_mapping, priority=800)
    app.connect("builder-inited", load_mappings)
    app.connect("source-read", install_dispatcher)
    app.connect("missing-reference", missing_reference)
    app.add_post_transform(IntersphinxRoleResolver)
    return {
        "version": sphinx.__display_version__,
        "env_version": 1,
        "parallel_read_safe": True,
    }


def inspect_main(argv: list[str], /) -> int:
    """Debug functionality to print out an inventory"""
    if len(argv) < 1:
        print(
            "Print out an inventory file.\n"
            "Error: must specify local path or URL to an inventory file.",
            file=sys.stderr,
        )
        return 1

    class MockConfig:
        intersphinx_timeout: int | None = None
        tls_verify = False
        tls_cacerts: str | dict[str, str] | None = None
        user_agent: str = ""

    class MockApp:
        srcdir = ""
        config = MockConfig()

    try:
        filename = argv[0]
        inv_data = fetch_inventory(MockApp(), "", filename)  # type: ignore[arg-type]
        for key in sorted(inv_data or {}):
            print(key)
            inv_entries = sorted(inv_data[key].items())
            for entry, (_proj, _ver, url_path, display_name) in inv_entries:
                display_name = display_name * (display_name != "-")
                print(f"    {entry:<40} {display_name:<40}: {url_path}")
    except ValueError as exc:
        print(exc.args[0] % exc.args[1:], file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unknown error: {exc!r}", file=sys.stderr)
        return 1
    else:
        return 0
