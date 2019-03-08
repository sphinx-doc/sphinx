"""
    sphinx.ext.jsmath
    ~~~~~~~~~~~~~~~~~

    Set up everything for use of JSMath to display math in HTML
    via JavaScript.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings

from sphinxcontrib.jsmath import (  # NOQA
    html_visit_math,
    html_visit_displaymath,
    install_jsmath,
)

import sphinx
from sphinx.deprecation import RemovedInSphinx40Warning

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA


def setup(app):
    # type: (Sphinx) -> Dict[str, Any]
    warnings.warn('sphinx.ext.jsmath has been moved to sphinxcontrib-jsmath.',
                  RemovedInSphinx40Warning)

    app.setup_extension('sphinxcontrib.jsmath')

    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
