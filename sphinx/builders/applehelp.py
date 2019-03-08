"""
    sphinx.builders.applehelp
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Build Apple help books.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings

from sphinxcontrib.applehelp import (
    AppleHelpCodeSigningFailed,
    AppleHelpIndexerFailed,
    AppleHelpBuilder,
)

from sphinx.deprecation import RemovedInSphinx40Warning, deprecated_alias

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA


deprecated_alias('sphinx.builders.applehelp',
                 {
                     'AppleHelpCodeSigningFailed': AppleHelpCodeSigningFailed,
                     'AppleHelpIndexerFailed': AppleHelpIndexerFailed,
                     'AppleHelpBuilder': AppleHelpBuilder,
                 },
                 RemovedInSphinx40Warning)


def setup(app):
    # type: (Sphinx) -> Dict[str, Any]
    warnings.warn('sphinx.builders.applehelp has been moved to sphinxcontrib-applehelp.',
                  RemovedInSphinx40Warning)
    app.setup_extension('sphinxcontrib.applehelp')

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
