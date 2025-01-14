"""This module provides contains the code for intersphinx command-line utilities."""

from __future__ import annotations

import sys
from pathlib import Path

from sphinx.ext.intersphinx._load import _fetch_inventory, _InvConfig


def inspect_main(argv: list[str], /) -> int:
    """Debug functionality to print out an inventory"""
    if len(argv) < 1:
        print(
            'Print out an inventory file.\n'
            'Error: must specify local path or URL to an inventory file.',
            file=sys.stderr,
        )
        return 1

    filename = argv[0]
    config = _InvConfig(
        intersphinx_cache_limit=5,
        intersphinx_timeout=None,
        tls_verify=False,
        tls_cacerts=None,
        user_agent='',
    )

    try:
        inv_data = _fetch_inventory(
            target_uri='',
            inv_location=filename,
            config=config,
            srcdir=Path(),
        )
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
