"""
    sphinx.builders.applehelp
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Build Apple help books.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings
from typing import Any, Dict

from sphinxcontrib.applehelp import (AppleHelpBuilder, AppleHelpCodeSigningFailed,
                                     AppleHelpIndexerFailed)

from sphinx.application import Sphinx
from sphinx.deprecation import RemovedInSphinx40Warning, deprecated_alias

deprecated_alias('sphinx.builders.applehelp',
                 {
                     'AppleHelpCodeSigningFailed': AppleHelpCodeSigningFailed,
                     'AppleHelpIndexerFailed': AppleHelpIndexerFailed,
                     'AppleHelpBuilder': AppleHelpBuilder,
                 },
                 RemovedInSphinx40Warning,
                 {
                     'AppleHelpCodeSigningFailed':
                     'sphinxcontrib.applehelp.AppleHelpCodeSigningFailed',
                     'AppleHelpIndexerFailed':
                     'sphinxcontrib.applehelp.AppleHelpIndexerFailed',
                     'AppleHelpBuilder': 'sphinxcontrib.applehelp.AppleHelpBuilder',
                 })


def setup(app: Sphinx) -> Dict[str, Any]:
    warnings.warn('sphinx.builders.applehelp has been moved to sphinxcontrib-applehelp.',
                  RemovedInSphinx40Warning, stacklevel=2)
    app.setup_extension('sphinxcontrib.applehelp')

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
