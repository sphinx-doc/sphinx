"""Creates reST files corresponding to Python modules for code documentation.

Parses a directory tree looking for Python modules and packages and creates
ReST files appropriately to create code documentation with Sphinx.  It also
creates a modules index (named modules.<suffix>).

This is derived from the "sphinx-autopackage" script, which is:
Copyright 2008 Société des arts technologiques (SAT),
https://sat.qc.ca/
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sphinx
from sphinx.ext.apidoc._cli import main

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata

__all__: Sequence[str] = 'main', 'setup'


def setup(app: Sphinx) -> ExtensionMetadata:
    from sphinx.ext.apidoc._extension import run_apidoc

    # Require autodoc
    app.setup_extension('sphinx.ext.autodoc')
    app.add_config_value(
        'apidoc_exclude_patterns', (), 'env', types=frozenset({list, tuple})
    )
    app.add_config_value('apidoc_maxdepth', 4, 'env', types=int)
    app.add_config_value('apidoc_followlinks', False, 'env', types=bool)
    app.add_config_value('apidoc_separatemodules', False, 'env', types=bool)
    app.add_config_value('apidoc_includeprivate', False, 'env', types=bool)
    app.add_config_value('apidoc_noheadings', False, 'env', types=bool)
    app.add_config_value('apidoc_modulefirst', False, 'env', types=bool)
    app.add_config_value('apidoc_implicit_namespaces', False, 'env', types=bool)
    app.add_config_value(
        'apidoc_automodule_options',
        ('members', 'undoc-members', 'show-inheritance'),
        'env',
        types=frozenset({list, set, tuple}),
    )
    app.add_config_value(
        'apidoc_modules',
        (),
        'env',
        types=frozenset((list, set, tuple)),
    )
    app.connect('builder-inited', run_apidoc)
    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
    }
